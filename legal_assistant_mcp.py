"""
MCP Server for Legal Assistant Integration with ChatGPT Apps SDK
Exposes workflow and research tools to ChatGPT
"""

import os
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import anthropic
import json
import os
from typing import Any, Dict, List
from document_processor import DocumentProcessor
from matter_manager import MatterManager
from workflow_engine import WorkflowEngine, WorkflowStatus
from litigation_workflow import create_litigation_workflow, LitigationWorkflowExecutor

# Initialize components
doc_processor = DocumentProcessor()
matter_manager = MatterManager()
workflow_engine = WorkflowEngine()

# Register litigation workflow
litigation_wf = create_litigation_workflow()
if not workflow_engine.get_workflow(litigation_wf.workflow_id):
    workflow_engine.register_workflow(litigation_wf)

# Get API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable required")

client = anthropic.Anthropic(api_key=api_key)
model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Create MCP server
app = Server("legal-assistant")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for ChatGPT"""
    return [
        Tool(
            name="research_legal_question",
            description="Research a legal question using uploaded documents. Returns a cited answer with source references. Use this for quick legal research questions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The legal research question to answer"
                    },
                    "matter_id": {
                        "type": "string",
                        "description": "Optional matter ID to search within specific matter documents"
                    },
                    "num_sources": {
                        "type": "integer",
                        "description": "Number of source documents to retrieve (default: 10)",
                        "minimum": 5,
                        "maximum": 20,
                        "default": 10
                    }
                },
                "required": ["question"]
            },
            _meta={
                "openai/toolInvocation/invoking": "Researching legal documents...",
                "openai/toolInvocation/invoked": "Research complete"
            }
        ),
        Tool(
            name="run_litigation_workflow",
            description="Run a comprehensive verifiable litigation research workflow. This creates a full research memo with citation verification, authority validation, and quality checks. Use for formal legal research memos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "matter_id": {
                        "type": "string",
                        "description": "Matter ID to associate the workflow with"
                    },
                    "research_question": {
                        "type": "string",
                        "description": "The specific legal question to research"
                    },
                    "jurisdictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of jurisdictions (e.g., ['California', '9th Circuit'])"
                    },
                    "court_level": {
                        "type": "string",
                        "enum": ["trial", "appellate", "supreme"],
                        "description": "Court level for the matter"
                    },
                    "matter_posture": {
                        "type": "string",
                        "enum": ["MTD", "SJ", "appeal", "discovery", "trial", "other"],
                        "description": "Current posture of the matter"
                    },
                    "known_facts": {
                        "type": "string",
                        "description": "Optional: Known facts about the case (bullet points)"
                    },
                    "memo_format": {
                        "type": "string",
                        "enum": ["IRAC", "CREAC", "narrative"],
                        "default": "IRAC",
                        "description": "Preferred memo format"
                    }
                },
                "required": ["matter_id", "research_question", "jurisdictions", "court_level", "matter_posture"]
            },
            _meta={
                "openai/toolInvocation/invoking": "Running litigation workflow (this may take 2-5 minutes)...",
                "openai/toolInvocation/invoked": "Workflow execution complete"
            }
        ),
        Tool(
            name="create_matter",
            description="Create a new legal matter to organize documents and work product",
            inputSchema={
                "type": "object",
                "properties": {
                    "matter_name": {
                        "type": "string",
                        "description": "Name of the matter (e.g., 'Smith v. Jones Contract Dispute')"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the matter"
                    }
                },
                "required": ["matter_name", "client_name"]
            },
            _meta={
                "openai/toolInvocation/invoking": "Creating matter...",
                "openai/toolInvocation/invoked": "Matter created"
            }
        ),
        Tool(
            name="list_matters",
            description="List all available legal matters",
            inputSchema={
                "type": "object",
                "properties": {}
            },
            _meta={
                "openai/toolInvocation/invoking": "Retrieving matters...",
                "openai/toolInvocation/invoked": "Matters retrieved"
            }
        ),
        Tool(
            name="get_workflow_status",
            description="Get the status of a workflow run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Workflow run ID to check"
                    }
                },
                "required": ["run_id"]
            },
            _meta={
                "openai/toolInvocation/invoking": "Checking workflow status...",
                "openai/toolInvocation/invoked": "Status retrieved"
            }
        ),
        Tool(
            name="get_workflow_memo",
            description="Retrieve the research memo from a completed workflow run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Workflow run ID"
                    }
                },
                "required": ["run_id"]
            },
            _meta={
                "openai/toolInvocation/invoking": "Retrieving memo...",
                "openai/toolInvocation/invoked": "Memo retrieved"
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from ChatGPT"""
    
    if name == "research_legal_question":
        return await research_legal_question(arguments)
    elif name == "run_litigation_workflow":
        return await run_litigation_workflow(arguments)
    elif name == "create_matter":
        return await create_matter_tool(arguments)
    elif name == "list_matters":
        return await list_matters_tool(arguments)
    elif name == "get_workflow_status":
        return await get_workflow_status_tool(arguments)
    elif name == "get_workflow_memo":
        return await get_workflow_memo_tool(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def research_legal_question(args: Dict[str, Any]) -> List[TextContent]:
    """Research a legal question using RAG"""
    question = args["question"]
    num_sources = args.get("num_sources", 10)
    
    # Search documents
    results = doc_processor.search_documents(question, top_k=num_sources)
    
    if not results:
        return [TextContent(
            type="text",
            text="No relevant documents found. Please upload legal documents first."
        )]
    
    # Build context with citations
    context_parts = []
    sources = []
    
    for idx, result in enumerate(results, 1):
        page_info = f" (Page {result['page']})" if result['page'] else ""
        context_parts.append(f"[{idx}] From '{result['doc_title']}'{page_info}:\n{result['chunk_text']}")
        
        sources.append({
            'citation': idx,
            'document': result['doc_title'],
            'page': result['page'],
            'excerpt': result['chunk_text'][:200] + "..."
        })
    
    context = "\n\n".join(context_parts)
    
    # Generate answer with Claude
    prompt = f"""You are a legal research assistant. Answer the following question based ONLY on the provided sources.

GROUNDING RULES:
1. Every statement must be supported by at least one citation [1], [2], etc.
2. Use multiple citations [1][2] when multiple sources support the same point
3. Only include information explicitly stated in the sources
4. If the sources don't support an answer, state "Not supported by provided documents"

Sources:
{context}

Question: {question}

Provide a well-structured answer with citations."""
    
    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    answer = message.content[0].text
    
    # Format response
    response_text = f"**Answer:**\n\n{answer}\n\n**Sources:**\n\n"
    for source in sources:
        response_text += f"[{source['citation']}] {source['document']}"
        if source.get('page'):
            response_text += f" - Page {source['page']}"
        response_text += f"\n{source['excerpt']}\n\n"
    
    return [TextContent(type="text", text=response_text)]

async def run_litigation_workflow(args: Dict[str, Any]) -> List[TextContent]:
    """Run the litigation research workflow"""
    matter_id = args["matter_id"]
    
    # Verify matter exists
    matter = matter_manager.get_matter(matter_id)
    if not matter:
        return [TextContent(type="text", text=f"Matter {matter_id} not found. Please create a matter first.")]
    
    # Create workflow inputs
    workflow_inputs = {
        'research_question': args['research_question'],
        'jurisdictions': args['jurisdictions'],
        'court_level': args['court_level'],
        'matter_posture': args['matter_posture'],
        'known_facts': args.get('known_facts', ''),
        'adverse_authority_awareness': False,
        'risk_posture': 'neutral',
        'memo_format_preference': args.get('memo_format', 'IRAC')
    }
    
    # Create workflow run
    workflow_id = "litigation_research_memo_v1"
    new_run = workflow_engine.create_run(matter_id, workflow_id, workflow_inputs)
    
    # Execute workflow
    workflow_def = workflow_engine.get_workflow(workflow_id)
    executor = LitigationWorkflowExecutor(
        doc_processor=doc_processor,
        anthropic_client=client,
        model=model
    )
    
    workflow_engine.update_run_status(new_run.run_id, WorkflowStatus.RUNNING)
    
    # Execute each step
    for step_index in range(len(workflow_def.steps)):
        step = workflow_def.steps[step_index]
        
        # Skip human review for now
        if step.requires_human_input and step.phase_number == 9:
            continue
        
        # Execute step
        step_result = executor.execute_step(new_run, step_index, workflow_def)
        workflow_engine.update_step_result(new_run.run_id, step_index, step_result)
        
        # Reload run
        new_run = workflow_engine.get_run(new_run.run_id)
        
        # Check if failed
        if step_result.status.value == "failed":
            workflow_engine.update_run_status(
                new_run.run_id,
                WorkflowStatus.FAILED,
                error_message=f"Phase {step_index} failed: {', '.join(step_result.errors)}"
            )
            
            # Build failure response
            response = f"❌ **Workflow Failed at Phase {step_index}: {step.name}**\n\n"
            response += f"**Error:** {', '.join(step_result.errors)}\n\n"
            
            if 'correction_plan' in step_result.artifacts:
                response += f"**Correction Plan:**\n{step_result.artifacts['correction_plan']}\n\n"
            
            response += f"**Run ID:** {new_run.run_id[:8]}...\n\n"
            response += "The workflow has been saved. You can review the partial results using the `get_workflow_status` tool."
            
            return [TextContent(type="text", text=response)]
    
    # All steps completed
    workflow_engine.update_run_status(new_run.run_id, WorkflowStatus.COMPLETED)
    
    # Add to matter history
    matter_manager.add_history(
        matter_id,
        "workflow",
        f"Completed workflow: {workflow_def.name}",
        f"Run ID: {new_run.run_id}"
    )
    
    # Get final memo
    final_artifacts = new_run.step_results[10].artifacts if len(new_run.step_results) > 10 else {}
    memo = final_artifacts.get('final_memo', 'Memo not generated')
    
    response = f"✅ **Workflow Completed Successfully**\n\n"
    response += f"**Run ID:** {new_run.run_id[:8]}...\n\n"
    response += f"**Research Memo:**\n\n{memo}\n\n"
    response += f"Use `get_workflow_memo` with run_id '{new_run.run_id}' to retrieve the full memo and artifacts."
    
    return [TextContent(type="text", text=response)]

async def create_matter_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Create a new matter"""
    matter = matter_manager.create_matter(
        args['matter_name'],
        args['client_name'],
        args.get('description', '')
    )
    
    response = f"✅ **Matter Created**\n\n"
    response += f"**Matter ID:** {matter.matter_id}\n"
    response += f"**Name:** {matter.matter_name}\n"
    response += f"**Client:** {matter.client_name}\n\n"
    response += "You can now use this matter_id for workflows and research."
    
    return [TextContent(type="text", text=response)]

async def list_matters_tool(args: Dict[str, Any]) -> List[TextContent]:
    """List all matters"""
    matters = matter_manager.list_matters()
    
    if not matters:
        return [TextContent(type="text", text="No matters found. Create a matter first.")]
    
    response = "**Available Matters:**\n\n"
    for matter in matters:
        response += f"**{matter.matter_name}**\n"
        response += f"  - Matter ID: {matter.matter_id}\n"
        response += f"  - Client: {matter.client_name}\n"
        response += f"  - Documents: {len(matter.doc_ids)}\n"
        response += f"  - Actions: {len(matter.history)}\n\n"
    
    return [TextContent(type="text", text=response)]

async def get_workflow_status_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Get workflow run status"""
    run_id = args['run_id']
    run = workflow_engine.get_run(run_id)
    
    if not run:
        return [TextContent(type="text", text=f"Workflow run {run_id} not found.")]
    
    response = f"**Workflow Status**\n\n"
    response += f"**Run ID:** {run.run_id[:8]}...\n"
    response += f"**Status:** {run.status.value.upper()}\n"
    response += f"**Started:** {run.started_at}\n"
    
    if run.finished_at:
        response += f"**Finished:** {run.finished_at}\n"
    
    response += f"**Current Phase:** {run.current_step}\n\n"
    
    if run.error_message:
        response += f"**Error:** {run.error_message}\n\n"
    
    # Show phase statuses
    response += "**Phase Status:**\n"
    for idx, step_result in enumerate(run.step_results):
        status_icon = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(step_result.status.value, "❓")
        response += f"{status_icon} Phase {idx}: {step_result.step_id}\n"
    
    return [TextContent(type="text", text=response)]

async def get_workflow_memo_tool(args: Dict[str, Any]) -> List[TextContent]:
    """Get workflow memo"""
    run_id = args['run_id']
    run = workflow_engine.get_run(run_id)
    
    if not run:
        return [TextContent(type="text", text=f"Workflow run {run_id} not found.")]
    
    if run.status != WorkflowStatus.COMPLETED:
        return [TextContent(type="text", text=f"Workflow is not completed yet. Status: {run.status.value}")]
    
    # Get final artifacts
    final_artifacts = run.step_results[10].artifacts if len(run.step_results) > 10 else {}
    
    if 'final_memo' not in final_artifacts:
        return [TextContent(type="text", text="Memo not found in workflow artifacts.")]
    
    memo = final_artifacts['final_memo']
    authority_table = final_artifacts.get('authority_table', [])
    verification_report = final_artifacts.get('verification_report', [])
    
    response = f"**Research Memorandum**\n\n{memo}\n\n"
    
    # Add authority table
    if authority_table:
        response += "---\n\n**Authority Table:**\n\n"
        for auth in authority_table:
            name = auth.get('name', auth.get('caption', 'N/A'))
            status = auth.get('precedential_status', 'unknown')
            response += f"- **{name}** ({auth.get('type', 'case')}) - Status: {status}\n"
        response += "\n"
    
    # Add verification summary
    if verification_report:
        passed = sum(1 for t in verification_report if t.get('pass_fail'))
        total = len(verification_report)
        response += f"**Verification:** {passed}/{total} tests passed\n"
    
    return [TextContent(type="text", text=response)]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
