import streamlit as st
import anthropic
from document_processor import DocumentProcessor, Document
from matter_manager import MatterManager, Matter
from export_utils import export_draft_to_docx, export_research_to_markdown, export_summary_to_markdown, create_matter_report
from workflow_engine import WorkflowEngine, WorkflowStatus, StepStatus
from litigation_workflow import create_litigation_workflow, LitigationWorkflowExecutor
from workflow_exports import (
    export_memo_to_markdown, 
    export_audit_pack_to_json,
    export_verification_report_to_markdown,
    export_issue_tree_to_markdown
)
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Steve Wan's AI Legal Assistant", layout="wide")

# Initialize document processor lazily
@st.cache_resource
def get_document_processor():
    """Initialize document processor (cached to avoid reloading)"""
    return DocumentProcessor()

@st.cache_resource
def get_matter_manager():
    """Initialize matter manager (cached)"""
    return MatterManager()

# Get processors
doc_processor = get_document_processor()
matter_manager = get_matter_manager()

@st.cache_resource
def get_workflow_engine():
    """Initialize workflow engine (cached)"""
    engine = WorkflowEngine()
    # Register the litigation workflow if not already registered
    litigation_wf = create_litigation_workflow()
    if not engine.get_workflow(litigation_wf.workflow_id):
        engine.register_workflow(litigation_wf)
    return engine

# Get workflow engine
workflow_engine = get_workflow_engine()

# Get API key from Streamlit secrets (for cloud deployment)
# or from local config for local testing
try:
    api_key = st.secrets["api_key"]
    model = st.secrets.get("model", "claude-sonnet-4-20250514")
except:
    # Fallback to config.yaml for local development
    import yaml
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            api_key = config["api_key"]
            model = config.get("model", "claude-sonnet-4-20250514")
    except:
        st.error("Please configure your API key in Streamlit secrets or config.yaml")
        st.stop()

client = anthropic.Anthropic(api_key=api_key)

st.title("⚖️ Steve Wan's AI Legal Assistant")

# Matter Management Section at the top
st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.subheader("📁 Current Matter")
    matters = matter_manager.list_matters()
    
    if matters:
        matter_options = ["[No Matter Selected]"] + [f"{m.matter_name} - {m.client_name}" for m in matters]
        selected_matter_idx = st.selectbox(
            "Select a matter:",
            range(len(matter_options)),
            format_func=lambda x: matter_options[x],
            key="matter_select"
        )
        
        if selected_matter_idx > 0:
            st.session_state['current_matter'] = matters[selected_matter_idx - 1]
        else:
            st.session_state['current_matter'] = None
    else:
        st.info("No matters created yet. Create one below.")
        st.session_state['current_matter'] = None

with col2:
    if st.session_state.get('current_matter'):
        matter = st.session_state['current_matter']
        st.write(f"**Client:** {matter.client_name}")
        st.write(f"**Documents:** {len(matter.doc_ids)}")
        st.write(f"**History:** {len(matter.history)} actions")
    else:
        st.write("*No matter selected*")

with col3:
    if st.button("➕ New Matter", key="new_matter_btn"):
        st.session_state['show_create_matter'] = True

# Create Matter Form
if st.session_state.get('show_create_matter'):
    with st.form("create_matter_form"):
        st.subheader("Create New Matter")
        matter_name = st.text_input("Matter Name:", placeholder="e.g., Smith v. Jones Contract Dispute")
        client_name = st.text_input("Client Name:", placeholder="e.g., John Smith")
        description = st.text_area("Description:", placeholder="Brief description of the matter")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Create Matter"):
                if matter_name and client_name:
                    new_matter = matter_manager.create_matter(matter_name, client_name, description)
                    st.session_state['current_matter'] = new_matter
                    st.session_state['show_create_matter'] = False
                    st.success(f"Matter '{matter_name}' created!")
                    st.rerun()
                else:
                    st.error("Matter name and client name are required")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state['show_create_matter'] = False
                st.rerun()

st.markdown("---")

# Sidebar for document upload and management
with st.sidebar:
    st.header("📄 Document Management")
    
    # Show current matter context
    current_matter = st.session_state.get('current_matter')
    if current_matter:
        st.success(f"**Matter:** {current_matter.matter_name}")
        st.caption(f"Client: {current_matter.client_name}")
    else:
        st.warning("No matter selected")
    
    st.divider()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['pdf', 'docx', 'txt'],
        help="Upload PDF, DOCX, or TXT files for processing"
    )
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                try:
                    doc = doc_processor.process_file(uploaded_file)
                    
                    # Add to current matter if one is selected
                    if current_matter:
                        matter_manager.add_document_to_matter(current_matter.matter_id, doc.doc_id)
                        matter_manager.add_history(
                            current_matter.matter_id,
                            "upload",
                            f"Uploaded document: {doc.title}",
                            f"Document ID: {doc.doc_id}"
                        )
                        st.success(f"✅ Document added to matter: {doc.title}")
                    else:
                        st.success(f"✅ Document processed: {doc.title}")
                        st.info("💡 Select a matter to associate this document")
                    
                    st.json({
                        "Document ID": doc.doc_id,
                        "Title": doc.title,
                        "Type": doc.file_type,
                        "Pages": doc.page_count if doc.page_count else "N/A",
                        "Text Length": f"{len(doc.text)} characters"
                    })
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")
    
    # List uploaded documents
    st.divider()
    st.subheader("Documents")
    
    # Filter documents by current matter if selected
    if current_matter:
        documents = [doc_processor.get_document(doc_id) for doc_id in current_matter.doc_ids]
        documents = [d for d in documents if d is not None]
        st.caption(f"Showing {len(documents)} document(s) in this matter")
    else:
        documents = doc_processor.list_documents()
        st.caption(f"Showing all {len(documents)} document(s)")
    
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc.title}"):
                st.write(f"**Type:** {doc.file_type}")
                st.write(f"**ID:** {doc.doc_id[:8]}...")
                if doc.page_count:
                    st.write(f"**Pages:** {doc.page_count}")
                st.write(f"**Uploaded:** {doc.upload_date[:10]}")
                st.write(f"**Characters:** {len(doc.text):,}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📊 Use", key=f"use_{doc.doc_id}"):
                        st.session_state['selected_doc'] = doc
                        st.rerun()
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"del_{doc.doc_id}", type="secondary"):
                        if doc_processor.delete_document(doc.doc_id):
                            # Remove from current matter if applicable
                            if current_matter and doc.doc_id in current_matter.doc_ids:
                                matter_manager.remove_document_from_matter(current_matter.matter_id, doc.doc_id)
                            # Clear selection if this was the selected doc
                            if st.session_state.get('selected_doc') and st.session_state['selected_doc'].doc_id == doc.doc_id:
                                st.session_state['selected_doc'] = None
                            st.success(f"Deleted: {doc.title}")
                            st.rerun()
                        else:
                            st.error("Failed to delete document")
    else:
        st.info("No documents uploaded yet")
    
    # Matter History
    if current_matter and current_matter.history:
        st.divider()
        st.subheader("📜 Matter History")
        for entry in reversed(current_matter.history[-5:]):  # Show last 5
            with st.expander(f"{entry.action_type.title()} - {entry.timestamp[:10]}"):
                st.caption(entry.description)
    
    # Export Matter Report
    if current_matter:
        st.divider()
        if st.button("📥 Export Matter Report"):
            matter_docs = [doc_processor.get_document(doc_id) for doc_id in current_matter.doc_ids]
            matter_docs = [d for d in matter_docs if d is not None]
            report_md = create_matter_report(current_matter, matter_docs, current_matter.history)
            
            st.download_button(
                label="Download Matter Report (MD)",
                data=report_md,
                file_name=f"{current_matter.matter_name.replace(' ', '_')}_report.md",
                mime="text/markdown"
            )

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Summarize", 
    "✍️ Draft", 
    "🔍 Research", 
    "📄 Document Analysis", 
    "🔎 Semantic Search",
    "⚖️ Workflow"
])

with tab1:
    st.header("📝 Document Summary with Grounding")
    st.info("Generate grounded summaries from your uploaded documents. Every point is cited with source references.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to generate summaries.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    # Summary mode selection
    summary_mode = st.selectbox(
        "Select Summary Mode",
        ["Executive Summary", "Issue Spotting", "Chronology"],
        help="Choose the type of summary you want to generate"
    )
    
    # Topic/focus input
    summary_topic = st.text_area(
        "Topic or focus (optional):",
        placeholder="e.g., contract terms, merger analysis, case facts",
        help="Leave blank to summarize all documents, or specify a topic to focus on"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        num_sources = st.slider("Number of sources to retrieve", min_value=5, max_value=20, value=10)
    
    if st.button("Generate Summary", key="sum_btn", type="primary"):
        if stats['total_chunks'] == 0:
            st.error("Please upload documents before generating summaries.")
        else:
            with st.spinner("Retrieving relevant information..."):
                try:
                    # Determine search query
                    if summary_topic.strip():
                        search_query = summary_topic
                    else:
                        search_query = "main points key information important details"
                    
                    # Retrieve relevant chunks
                    results = doc_processor.search_documents(search_query, top_k=num_sources)
                    
                    if not results:
                        st.warning("No relevant information found in your documents.")
                    else:
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
                                'snippet': result['chunk_text'][:200] + "...",
                                'full_text': result['chunk_text'],
                                'similarity': result['similarity']
                            })
                        
                        context = "\n\n".join(context_parts)
                        
                        # Create mode-specific prompt
                        if summary_mode == "Executive Summary":
                            prompt = f"""You are creating an executive summary based strictly on the provided sources.

GROUNDING RULES:
1. Provide EXACTLY 5 key points in bullet format
2. EVERY bullet point MUST include at least one citation [1], [2], etc.
3. Only include information explicitly stated in the sources
4. If a point cannot be supported by the sources, write "Not supported by provided documents" instead

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General summary of all documents'}

Generate an executive summary with exactly 5 bullet points. Each bullet must cite sources [1][2] etc."""

                        elif summary_mode == "Issue Spotting":
                            prompt = f"""You are identifying issues, ambiguities, and missing facts based strictly on the provided sources.

GROUNDING RULES:
1. Identify issues, ambiguities, and missing information
2. EVERY issue MUST include at least one citation [1], [2], etc. to show where the issue appears
3. Only identify issues that are evident from the sources
4. If you cannot identify issues from the sources, write "Not supported by provided documents"
5. Format as bullet points under categories: Issues, Ambiguities, Missing Facts

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General analysis of all documents'}

Identify and categorize issues with citations for each point."""

                        else:  # Chronology
                            prompt = f"""You are creating a chronological timeline based strictly on the provided sources.

GROUNDING RULES:
1. Create a timeline of events in chronological order
2. EVERY event MUST include at least one citation [1], [2], etc.
3. Only include events explicitly mentioned in the sources with dates or temporal references
4. If no chronological information exists, write "Not supported by provided documents"
5. Format as a table with columns: Date/Time | Event | Source Citation

Sources:
{context}

Topic focus: {summary_topic if summary_topic.strip() else 'General chronology from all documents'}

Create a chronological timeline table. Each row must cite sources."""

                        with st.spinner(f"Generating {summary_mode}..."):
                            message = client.messages.create(
                                model=model,
                                max_tokens=3000,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            
                            summary = message.content[0].text
                            
                            # Display summary
                            st.success(f"📋 {summary_mode}:")
                            st.markdown(summary)
                            
                            # Save to matter history
                            current_matter = st.session_state.get('current_matter')
                            if current_matter:
                                cited_nums = [s['citation'] for s in sources if f"[{s['citation']}]" in summary]
                                matter_manager.add_history(
                                    current_matter.matter_id,
                                    "summary",
                                    f"{summary_mode}: {summary_topic if summary_topic else 'General'}",
                                    summary,
                                    cited_nums
                                )
                            
                            # Export button
                            summary_md = export_summary_to_markdown(summary,
                                current_matter.matter_name if current_matter else "Summary",
                                sources, summary_mode)
                            
                            st.download_button(
                                label="📥 Download Summary (Markdown)",
                                data=summary_md,
                                file_name=f"summary_{summary_mode.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown",
                                key="download_summary"
                            )
                            
                            # Analyze which sources were cited
                            cited_sources = []
                            uncited_sources = []
                            
                            for source in sources:
                                citation_pattern = f"[{source['citation']}]"
                                if citation_pattern in summary:
                                    cited_sources.append(source)
                                else:
                                    uncited_sources.append(source)
                            
                            # Display sources
                            st.divider()
                            st.subheader("📚 Supporting Sources")
                            
                            # Display cited sources
                            if cited_sources:
                                st.markdown("**✅ Cited Sources:**")
                                for source in cited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"sum_source_{source['citation']}", label_visibility="collapsed")
                            
                            # Display uncited sources
                            if uncited_sources:
                                st.markdown("**ℹ️ Additional Retrieved Sources** (not cited):")
                                st.caption("These sources were retrieved but not used in the summary.")
                                
                                for source in uncited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"sum_uncited_{source['citation']}", label_visibility="collapsed")
                        
                except Exception as e:
                    st.error(f"Summary error: {str(e)}")

with tab2:
    st.header("✍️ Draft Documents with Grounding")
    st.info("Generate legal documents grounded in your uploaded documents. All facts are cited, assumptions are flagged, and open questions are identified.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to generate drafts.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    # Template selection
    template = st.selectbox(
        "Select Document Template",
        ["Client Update Email", "Internal Case Memo", "Demand Letter Skeleton"],
        help="Choose the type of document you want to draft"
    )
    
    # Context/instructions
    col1, col2 = st.columns([2, 1])
    with col1:
        draft_instructions = st.text_area(
            "Drafting Instructions:",
            placeholder="e.g., Focus on timeline of events, highlight key contractual obligations, emphasize damages",
            height=100,
            help="Provide specific instructions for what to include in the draft"
        )
    
    with col2:
        recipient = st.text_input("Recipient (if applicable):", placeholder="e.g., John Smith, Client")
        num_sources = st.slider("Number of sources to retrieve", min_value=5, max_value=20, value=12)
    
    if st.button("Generate Draft", key="draft_btn", type="primary"):
        if stats['total_chunks'] == 0:
            st.error("Please upload documents before generating drafts.")
        else:
            with st.spinner("Retrieving relevant information..."):
                try:
                    # Retrieve relevant chunks
                    search_query = draft_instructions if draft_instructions.strip() else "key facts important information"
                    results = doc_processor.search_documents(search_query, top_k=num_sources)
                    
                    if not results:
                        st.warning("No relevant information found in your documents.")
                    else:
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
                                'snippet': result['chunk_text'][:200] + "...",
                                'full_text': result['chunk_text'],
                                'similarity': result['similarity']
                            })
                        
                        context = "\n\n".join(context_parts)
                        
                        # Template-specific prompts
                        if template == "Client Update Email":
                            template_guidance = f"""Draft a professional client update email to {recipient if recipient else '[Client Name]'}.

FORMAT:
Subject: [Appropriate subject line]

Dear {recipient if recipient else '[Client Name]'},

[Opening paragraph with context]

[Body paragraphs with updates - cite all facts with [1][2] etc.]

[Closing with next steps]

Best regards,
[Your name]"""

                        elif template == "Internal Case Memo":
                            template_guidance = """Draft an internal case memorandum.

FORMAT:
TO: [Team/Supervisor]
FROM: [Your name]
RE: [Case name/matter]
DATE: [Date]

SUMMARY:
[Brief overview with key facts - cite sources [1][2]]

FACTS:
[Detailed factual background - every fact must cite sources]

ANALYSIS:
[Legal analysis based on facts - cite supporting sources]

RECOMMENDATION:
[Recommended course of action]"""

                        else:  # Demand Letter Skeleton
                            template_guidance = f"""Draft a demand letter skeleton to {recipient if recipient else '[Recipient]'}.

FORMAT:
[Date]

{recipient if recipient else '[Recipient Name]'}
[Address]

Re: [Matter description]

Dear {recipient if recipient else '[Recipient]'}:

[Opening - establish relationship/context]

[Statement of facts - cite all facts with [1][2]]

[Statement of claims/demands - cite supporting sources]

[Demand for relief/action]

[Consequences if demand not met]

Sincerely,
[Your name]"""

                        # Create comprehensive prompt
                        prompt = f"""You are drafting a legal document based strictly on provided sources.

CRITICAL GROUNDING RULES:
1. Every factual statement MUST cite sources using [1], [2], etc.
2. If you make an assumption or inference, explicitly label it as "ASSUMPTION: [statement]"
3. Do NOT invent facts - only use information from the sources
4. Identify gaps in information as open questions

TEMPLATE GUIDANCE:
{template_guidance}

DRAFTING INSTRUCTIONS:
{draft_instructions if draft_instructions.strip() else 'Create a comprehensive document based on available information'}

SOURCES:
{context}

Generate the document in four sections:

**SECTION 1: DRAFT**
[The actual document following the template format. Cite all facts with [1][2] etc. Label assumptions clearly.]

**SECTION 2: FACTS USED (WITH CITATIONS)**
List all factual statements used in the draft with their citations:
- [Fact 1] [1][2]
- [Fact 2] [3]
etc.

**SECTION 3: OPEN QUESTIONS / MISSING INFORMATION**
Identify information gaps that would strengthen the document:
- [Question/gap 1]
- [Question/gap 2]
etc.

**SECTION 4: RISKS / ASSUMPTIONS**
List any assumptions made and potential risks:
- ASSUMPTION: [Any assumptions made]
- RISK: [Potential weaknesses or risks]
etc.

Generate all four sections."""

                        with st.spinner(f"Generating {template}..."):
                            message = client.messages.create(
                                model=model,
                                max_tokens=4096,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            
                            output = message.content[0].text
                            
                            # Display the output
                            st.success(f"📄 {template} Generated:")
                            st.markdown(output)
                            
                            # Save to matter history
                            current_matter = st.session_state.get('current_matter')
                            if current_matter:
                                cited_nums = [s['citation'] for s in sources if f"[{s['citation']}]" in output]
                                matter_manager.add_history(
                                    current_matter.matter_id,
                                    "draft",
                                    f"{template}: {draft_instructions[:50] if draft_instructions else 'Generated'}...",
                                    output,
                                    cited_nums
                                )
                            
                            # Export buttons
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Export to DOCX
                                docx_file = export_draft_to_docx(output,
                                    current_matter.matter_name if current_matter else template,
                                    sources)
                                
                                # Save DOCX to bytes
                                docx_bytes = BytesIO()
                                docx_file.save(docx_bytes)
                                docx_bytes.seek(0)
                                
                                st.download_button(
                                    label="📥 Download Draft (DOCX)",
                                    data=docx_bytes,
                                    file_name=f"draft_{template.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key="download_draft_docx"
                                )
                            
                            with col2:
                                # Export to Markdown
                                st.download_button(
                                    label="📥 Download Draft (Markdown)",
                                    data=output,
                                    file_name=f"draft_{template.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                    mime="text/markdown",
                                    key="download_draft_md"
                                )
                            
                            # Analyze which sources were cited
                            cited_sources = []
                            uncited_sources = []
                            
                            for source in sources:
                                citation_pattern = f"[{source['citation']}]"
                                if citation_pattern in output:
                                    cited_sources.append(source)
                                else:
                                    uncited_sources.append(source)
                            
                            # Display sources
                            st.divider()
                            st.subheader("📚 Source Documents")
                            
                            # Display cited sources
                            if cited_sources:
                                st.markdown("**✅ Cited Sources:**")
                                for source in cited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"draft_source_{source['citation']}", label_visibility="collapsed")
                            
                            # Display uncited sources
                            if uncited_sources:
                                st.markdown("**ℹ️ Additional Retrieved Sources** (not cited):")
                                st.caption("These sources were retrieved but not used in the draft.")
                                
                                for source in uncited_sources:
                                    with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                        st.markdown("**Preview:**")
                                        st.write(source['snippet'])
                                        st.markdown("**Full Text:**")
                                        st.text_area("", source['full_text'], height=200, key=f"draft_uncited_{source['citation']}", label_visibility="collapsed")
                        
                except Exception as e:
                    st.error(f"Drafting error: {str(e)}")

with tab3:
    st.header("🔍 Research with RAG")
    st.info("Research using Retrieval-Augmented Generation. Answers are strictly grounded in your uploaded documents with citations.")
    
    # Show if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload documents first to use RAG research.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    research_topic = st.text_input("Enter your research question:", placeholder="e.g., What are the key obligations in the contract?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        num_chunks = st.slider("Number of sources to retrieve", min_value=3, max_value=15, value=8)
    
    if st.button("Research", key="research_btn", type="primary"):
        if research_topic:
            if stats['total_chunks'] == 0:
                st.error("Please upload documents before using RAG research.")
            else:
                with st.spinner("Retrieving relevant information..."):
                    try:
                        # Retrieve relevant chunks
                        results = doc_processor.search_documents(research_topic, top_k=num_chunks)
                        
                        if not results:
                            st.warning("No relevant information found in your documents.")
                        else:
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
                                    'snippet': result['chunk_text'][:200] + "...",
                                    'full_text': result['chunk_text'],
                                    'similarity': result['similarity']
                                })
                            
                            context = "\n\n".join(context_parts)
                            
                            # Create strict grounding prompt
                            prompt = f"""You are a research assistant that provides answers strictly based on the provided sources. You must follow these rules:

1. ONLY use information from the provided sources below
2. Every statement must be cited with [1], [2], etc. matching the source numbers
3. If the sources don't contain information to answer the question, say "The provided documents do not contain information about [topic]"
4. Do not add any information not present in the sources
5. Include multiple citations [1][2] when multiple sources support a point

Sources:
{context}

Question: {research_topic}

Provide a comprehensive answer with citations after every claim."""

                            with st.spinner("Generating research answer..."):
                                message = client.messages.create(
                                    model=model,
                                    max_tokens=3000,
                                    messages=[{
                                        "role": "user",
                                        "content": prompt
                                    }]
                                )
                                
                                answer = message.content[0].text
                                
                                # Display answer
                                st.success("📝 Research Answer:")
                                st.markdown(answer)
                                
                                # Save to matter history
                                current_matter = st.session_state.get('current_matter')
                                if current_matter:
                                    cited_nums = [s['citation'] for s in sources if f"[{s['citation']}]" in answer]
                                    matter_manager.add_history(
                                        current_matter.matter_id,
                                        "research",
                                        f"Research: {research_topic}",
                                        answer,
                                        cited_nums
                                    )
                                
                                # Export button
                                research_md = export_research_to_markdown(answer, 
                                    current_matter.matter_name if current_matter else "Research Report",
                                    sources, research_topic)
                                
                                st.download_button(
                                    label="📥 Download Research Report (Markdown)",
                                    data=research_md,
                                    file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                    mime="text/markdown",
                                    key="download_research"
                                )
                                
                                # Analyze which sources were cited
                                cited_sources = []
                                uncited_sources = []
                                
                                for source in sources:
                                    citation_pattern = f"[{source['citation']}]"
                                    if citation_pattern in answer:
                                        cited_sources.append(source)
                                    else:
                                        uncited_sources.append(source)
                                
                                # Display sources
                                st.divider()
                                st.subheader("📚 Sources")
                                
                                # Display cited sources first
                                if cited_sources:
                                    st.markdown("**✅ Cited Sources** (used in answer above):")
                                    for source in cited_sources:
                                        with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                            st.markdown("**Preview:**")
                                            st.write(source['snippet'])
                                            st.markdown("**Full Text:**")
                                            st.text_area("", source['full_text'], height=200, key=f"source_{source['citation']}", label_visibility="collapsed")
                                
                                # Display uncited sources with explanation
                                if uncited_sources:
                                    st.markdown("**ℹ️ Additional Retrieved Sources** (not directly cited):")
                                    st.caption("These sources were retrieved but not cited in the answer. They may contain redundant information already covered by cited sources, or less relevant details.")
                                    
                                    for source in uncited_sources:
                                        with st.expander(f"[{source['citation']}] {source['document']}" + (f" - Page {source['page']}" if source['page'] else "") + f" (Relevance: {source['similarity']:.2%})"):
                                            st.markdown("**Preview:**")
                                            st.write(source['snippet'])
                                            st.markdown("**Full Text:**")
                                            st.text_area("", source['full_text'], height=200, key=f"source_uncited_{source['citation']}", label_visibility="collapsed")
                                
                    except Exception as e:
                        st.error(f"Research error: {str(e)}")
        else:
            st.warning("Please enter a research question")

with tab4:
    st.header("Document Analysis")
    
    # Check if a document is selected
    selected_doc = st.session_state.get('selected_doc', None)
    
    if selected_doc:
        st.info(f"📄 Analyzing: **{selected_doc.title}** ({selected_doc.file_type})")
        
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Summarize Document", "Extract Key Points", "Legal Review", "Custom Query"]
        )
        
        custom_query = ""
        if analysis_type == "Custom Query":
            custom_query = st.text_area("Enter your question about the document:")
        
        if st.button("Analyze Document", key="analyze_btn"):
            with st.spinner("Analyzing document..."):
                try:
                    # Prepare prompt based on analysis type
                    if analysis_type == "Summarize Document":
                        prompt = f"Provide a comprehensive summary of this legal document:\n\n{selected_doc.text}"
                    elif analysis_type == "Extract Key Points":
                        prompt = f"Extract and list the key points, clauses, and important terms from this document:\n\n{selected_doc.text}"
                    elif analysis_type == "Legal Review":
                        prompt = f"Perform a legal review of this document. Identify potential issues, risks, and areas that may need attention:\n\n{selected_doc.text}"
                    else:
                        prompt = f"Document: {selected_doc.text}\n\nQuestion: {custom_query}"
                    
                    message = client.messages.create(
                        model=model,
                        max_tokens=4096,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    st.success("Analysis Complete:")
                    st.write(message.content[0].text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Show document preview
        with st.expander("📄 View Document Text"):
            st.text_area("Document Content", selected_doc.text, height=400)
    else:
        st.warning("⬅️ Please upload and select a document from the sidebar to analyze.")

with tab5:
    st.header("🔎 Semantic Search")
    st.info("Search across all uploaded documents using natural language queries. The system will find the most relevant passages.")
    
    # Show vector store stats
    stats = doc_processor.get_vector_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents Indexed", stats['total_documents'])
    with col2:
        st.metric("Text Chunks", stats['total_chunks'])
    with col3:
        st.metric("Embedding Dimension", stats['embedding_dim'])
    
    st.divider()
    
    # Search interface
    search_query = st.text_input("Enter your search query:", placeholder="e.g., What are the payment terms?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        top_k = st.slider("Number of results", min_value=1, max_value=10, value=5)
    
    if st.button("Search", key="search_btn", type="primary"):
        if search_query:
            if stats['total_chunks'] == 0:
                st.warning("No documents have been uploaded yet. Please upload documents first.")
            else:
                with st.spinner("Searching..."):
                    try:
                        results = doc_processor.search_documents(search_query, top_k=top_k)
                        
                        if results:
                            st.success(f"Found {len(results)} relevant results:")
                            
                            for i, result in enumerate(results, 1):
                                with st.expander(f"Result {i}: {result['doc_title']} (Score: {result['similarity']:.3f})"):
                                    st.markdown(f"**Document:** {result['doc_title']}")
                                    if result['page']:
                                        st.markdown(f"**Page:** {result['page']}")
                                    st.markdown(f"**Similarity Score:** {result['similarity']:.3f}")
                                    st.divider()
                                    st.markdown("**Content:**")
                                    st.write(result['chunk_text'])
                                    
                                    # Option to use this result with Claude
                                    if st.button(f"Analyze with AI", key=f"analyze_result_{i}"):
                                        with st.spinner("Analyzing..."):
                                            message = client.messages.create(
                                                model=model,
                                                max_tokens=2048,
                                                messages=[{
                                                    "role": "user",
                                                    "content": f"Based on this document excerpt from '{result['doc_title']}':\n\n{result['chunk_text']}\n\nAnswer this question: {search_query}"
                                                }]
                                            )
                                            st.success("AI Analysis:")
                                            st.write(message.content[0].text)
                        else:
                            st.warning("No relevant results found. Try a different query.")
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")
        else:
            st.warning("Please enter a search query")

with tab6:
    st.header("⚖️ Litigation Research Workflow")
    st.info("Structured workflow for creating verifiable legal research memos with citation checking.")
    
    # Check if matter is selected
    current_matter = st.session_state.get('current_matter')
    
    if not current_matter:
        st.warning("⚠️ Please select a matter to run a workflow")
        st.stop()
    
    st.success(f"📁 Current Matter: **{current_matter.matter_name}**")
    
    # Check if documents are available
    stats = doc_processor.get_vector_stats()
    if stats['total_chunks'] == 0:
        st.warning("⚠️ No documents uploaded. Please upload legal documents (cases, statutes, regulations) to run workflows.")
    else:
        st.success(f"✅ {stats['total_documents']} documents indexed with {stats['total_chunks']} chunks")
    
    st.divider()
    
    # Workflow selection
    workflows = workflow_engine.list_workflows()
    
    if workflows:
        workflow_names = [f"{w.name} (v{w.version})" for w in workflows]
        selected_wf_idx = st.selectbox(
            "Select Workflow",
            range(len(workflows)),
            format_func=lambda x: workflow_names[x]
        )
        
        selected_workflow = workflows[selected_wf_idx]
        
        st.markdown(f"**Description:** {selected_workflow.description}")
        st.divider()
        
        # Show existing runs for this matter
        existing_runs = workflow_engine.list_runs(matter_id=current_matter.matter_id)
        workflow_runs = [r for r in existing_runs if r.workflow_id == selected_workflow.workflow_id]
        
        if workflow_runs:
            st.subheader(f"📊 Previous Runs ({len(workflow_runs)})")
            for run in workflow_runs[:5]:  # Show last 5
                status_emoji = {
                    WorkflowStatus.COMPLETED: "✅",
                    WorkflowStatus.FAILED: "❌",
                    WorkflowStatus.RUNNING: "🔄",
                    WorkflowStatus.NEEDS_INPUT: "⏸️",
                    WorkflowStatus.PENDING: "⏳"
                }.get(run.status, "❓")
                
                with st.expander(f"{status_emoji} Run {run.run_id[:8]}... - {run.status.value.upper()} - {run.started_at[:10]}"):
                    st.write(f"**Started:** {run.started_at}")
                    if run.finished_at:
                        st.write(f"**Finished:** {run.finished_at}")
                    st.write(f"**Current Step:** Phase {run.current_step}")
                    
                    if run.error_message:
                        st.error(f"**Error:** {run.error_message}")
                        
                        # Show detailed correction plan for failed runs
                        for idx, step_result in enumerate(run.step_results):
                            if step_result.status == StepStatus.FAILED:
                                st.subheader(f"❌ Failed Step Details - Phase {idx}")
                                
                                # Show errors
                                if step_result.errors:
                                    st.error("**Error Details:**")
                                    for error in step_result.errors:
                                        st.write(f"• {error}")
                                
                                # Show correction plan if available
                                if 'correction_plan' in step_result.artifacts:
                                    st.warning("**📋 Correction Plan:**")
                                    st.markdown(step_result.artifacts['correction_plan'])
                                
                                # Show verification report if this was Phase 8
                                if step_result.step_id == "phase_8_verification" and 'verification_report' in step_result.artifacts:
                                    st.info("**📊 Verification Test Results:**")
                                    verification_report = step_result.artifacts['verification_report']
                                    
                                    passed_count = sum(1 for t in verification_report if t.get('pass_fail'))
                                    total_count = len(verification_report)
                                    st.write(f"**Result:** {passed_count}/{total_count} tests passed")
                                    st.write("")
                                    
                                    for test in verification_report:
                                        status_icon = "✅" if test.get('pass_fail') else "❌"
                                        with st.expander(f"{status_icon} {test['test']}", expanded=not test.get('pass_fail')):
                                            st.write(f"**Status:** {'PASSED' if test.get('pass_fail') else 'FAILED'}")
                                            st.write(f"**Details:** {test.get('details', 'N/A')}")
                                            if test.get('blocked_step'):
                                                st.write(f"**Blocked Step:** {test['blocked_step']}")
                                
                                break
                    
                    # Show step status
                    st.write("")
                    st.write("**Phase Execution Status:**")
                    for idx, step_result in enumerate(run.step_results):
                        step_status_emoji = {
                            StepStatus.COMPLETED: "✅",
                            StepStatus.FAILED: "❌",
                            StepStatus.RUNNING: "🔄",
                            StepStatus.PENDING: "⏳",
                            StepStatus.SKIPPED: "⏭️"
                        }.get(step_result.status, "❓")
                        st.caption(f"{step_status_emoji} Phase {idx}: {step_result.step_id}")
                    
                    # View/download artifacts button
                    if run.status == WorkflowStatus.COMPLETED:
                        if st.button(f"📥 View Artifacts", key=f"view_artifacts_{run.run_id}"):
                            st.session_state[f'viewing_run_{run.run_id}'] = True
                    elif run.status == WorkflowStatus.FAILED:
                        # Add button to view partial artifacts even for failed runs
                        if st.button(f"📥 View Partial Artifacts", key=f"view_partial_{run.run_id}"):
                            st.session_state[f'viewing_run_{run.run_id}'] = True
            
            st.divider()
        
        # Check if viewing a specific run
        for run in workflow_runs:
            if st.session_state.get(f'viewing_run_{run.run_id}'):
                st.subheader(f"📄 Workflow Artifacts - Run {run.run_id[:8]}...")
                
                # For failed runs, show what we have from Phase 7 (memo drafting)
                if run.status == WorkflowStatus.FAILED:
                    st.warning("⚠️ This workflow run failed verification. Showing partial artifacts from completed phases.")
                    
                    # Try to show the memo from Phase 7 if available
                    if len(run.step_results) > 7 and run.step_results[7].artifacts:
                        phase_7_artifacts = run.step_results[7].artifacts
                        
                        if 'research_memo' in phase_7_artifacts:
                            with st.expander("📝 Draft Research Memo (Failed Verification)", expanded=True):
                                st.info("This memo was generated but failed verification tests. Review the correction plan above before using.")
                                st.markdown(phase_7_artifacts['research_memo'])
                    
                    # Show what verification tests failed
                    if len(run.step_results) > 8 and run.step_results[8].artifacts:
                        phase_8_artifacts = run.step_results[8].artifacts
                        
                        if 'verification_report' in phase_8_artifacts:
                            with st.expander("❌ Verification Report (FAILED)", expanded=True):
                                verification_report = phase_8_artifacts['verification_report']
                                
                                for test in verification_report:
                                    status_icon = "✅" if test.get('pass_fail') else "❌"
                                    st.write(f"{status_icon} **{test['test']}**: {test.get('details', 'N/A')}")
                        
                        if 'correction_plan' in phase_8_artifacts:
                            with st.expander("📋 Correction Plan", expanded=True):
                                st.markdown(phase_8_artifacts['correction_plan'])
                    
                    # Show authority table if available
                    if len(run.step_results) > 3 and run.step_results[3].artifacts:
                        if 'validated_authorities' in run.step_results[3].artifacts:
                            with st.expander("📚 Authority Table"):
                                authorities = run.step_results[3].artifacts['validated_authorities']
                                if authorities:
                                    for auth in authorities:
                                        name = auth.get('name', auth.get('caption', 'N/A'))
                                        status = auth.get('precedential_status', 'unknown')
                                        status_emoji = "⚠️" if status == "negative_treatment_found" else "✅"
                                        st.write(f"{status_emoji} **{name}** ({auth.get('type', 'case')}) - {status}")
                
                # Get final artifacts from Phase 10 (for successful runs)
                elif len(run.step_results) > 10 and run.step_results[10].artifacts:
                    final_artifacts = run.step_results[10].artifacts
                    
                    # Display memo
                    if 'final_memo' in final_artifacts:
                        with st.expander("📝 Research Memo", expanded=True):
                            st.markdown(final_artifacts['final_memo'])
                        
                        # Export buttons
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            all_sources = []
                            for result in run.step_results:
                                all_sources.extend(result.sources_used)
                            
                            memo_md = export_memo_to_markdown(
                                final_artifacts['final_memo'],
                                current_matter.matter_name,
                                final_artifacts.get('run_metadata', {}),
                                final_artifacts.get('authority_table', []),
                                all_sources
                            )
                            st.download_button(
                                "📥 Memo (MD)",
                                memo_md,
                                f"memo_{run.run_id[:8]}.md",
                                mime="text/markdown",
                                key=f"download_memo_{run.run_id}"
                            )
                        
                        with col2:
                            if 'verification_report' in final_artifacts:
                                verification_md = export_verification_report_to_markdown(
                                    final_artifacts['verification_report']
                                )
                                st.download_button(
                                    "📥 Verification Report",
                                    verification_md,
                                    f"verification_{run.run_id[:8]}.md",
                                    mime="text/markdown",
                                    key=f"download_verification_{run.run_id}"
                                )
                        
                        with col3:
                            if 'issue_tree' in final_artifacts:
                                issue_tree_md = export_issue_tree_to_markdown(
                                    final_artifacts['issue_tree']
                                )
                                st.download_button(
                                    "📥 Issue Tree",
                                    issue_tree_md,
                                    f"issue_tree_{run.run_id[:8]}.md",
                                    mime="text/markdown",
                                    key=f"download_issue_tree_{run.run_id}"
                                )
                        
                        with col4:
                            audit_pack = export_audit_pack_to_json(
                                final_artifacts.get('run_metadata', {}),
                                final_artifacts['final_memo'],
                                final_artifacts.get('authority_table', []),
                                final_artifacts.get('issue_tree', []),
                                final_artifacts.get('verification_report', []),
                                final_artifacts.get('provenance_bundle', {})
                            )
                            st.download_button(
                                "📥 Audit Pack (JSON)",
                                audit_pack,
                                f"audit_pack_{run.run_id[:8]}.json",
                                mime="application/json",
                                key=f"download_audit_{run.run_id}"
                            )
                    
                    # Show authority table
                    if 'authority_table' in final_artifacts:
                        with st.expander("📚 Authority Table"):
                            authorities = final_artifacts['authority_table']
                            if authorities:
                                for auth in authorities:
                                    name = auth.get('name', auth.get('caption', 'N/A'))
                                    status = auth.get('precedential_status', 'unknown')
                                    status_emoji = "⚠️" if status == "negative_treatment_found" else "✅"
                                    st.write(f"{status_emoji} **{name}** ({auth.get('type', 'case')}) - {status}")
                    
                    # Show verification report
                    if 'verification_report' in final_artifacts:
                        with st.expander("✓ Verification Report"):
                            report = final_artifacts['verification_report']
                            passed = all(r.get('pass_fail', False) for r in report)
                            
                            if passed:
                                st.success("✅ All verification tests passed!")
                            else:
                                st.error("❌ Some verification tests failed")
                            
                            for test in report:
                                status_icon = "✅" if test.get('pass_fail') else "❌"
                                st.write(f"{status_icon} **{test['test']}**: {test.get('details', 'N/A')}")
                
                if st.button("Close Artifacts View", key=f"close_view_{run.run_id}"):
                    st.session_state[f'viewing_run_{run.run_id}'] = False
                    st.rerun()
                
                st.divider()
        
        # New workflow run form
        st.subheader("🚀 Start New Workflow Run")
        
        with st.form("workflow_intake_form"):
            # Required fields
            research_question = st.text_area(
                "Research Question*",
                placeholder="e.g., Can the plaintiff establish breach of contract under California law?",
                help="The specific legal question you need answered"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                jurisdictions_input = st.text_input(
                    "Jurisdiction(s)*",
                    placeholder="e.g., California, 9th Circuit",
                    help="Comma-separated list of jurisdictions"
                )
                
                court_level = st.selectbox(
                    "Court Level*",
                    ["trial", "appellate", "supreme"]
                )
            
            with col2:
                matter_posture = st.selectbox(
                    "Matter Posture*",
                    ["MTD", "SJ", "appeal", "discovery", "trial", "other"]
                )
                
                risk_posture = st.selectbox(
                    "Risk Posture",
                    ["conservative", "neutral", "aggressive"],
                    index=1
                )
            
            # Optional fields
            known_facts = st.text_area(
                "Known Facts (optional)",
                placeholder="• Fact 1\n• Fact 2\n• Fact 3",
                help="Bullet list of known facts"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                adverse_authority_awareness = st.checkbox("Aware of adverse authority?")
            
            with col2:
                memo_format_preference = st.selectbox(
                    "Memo Format",
                    ["IRAC", "CREAC", "narrative"]
                )
            
            submitted = st.form_submit_button("🚀 Run Workflow", type="primary")
            
            if submitted:
                # Validate required fields
                if not research_question or not jurisdictions_input or not court_level or not matter_posture:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    # Parse jurisdictions
                    jurisdictions = [j.strip() for j in jurisdictions_input.split(',')]
                    
                    # Create workflow inputs
                    workflow_inputs = {
                        'research_question': research_question,
                        'jurisdictions': jurisdictions,
                        'court_level': court_level,
                        'matter_posture': matter_posture,
                        'known_facts': known_facts,
                        'adverse_authority_awareness': adverse_authority_awareness,
                        'risk_posture': risk_posture,
                        'memo_format_preference': memo_format_preference
                    }
                    
                    # Create workflow run
                    with st.spinner("Creating workflow run..."):
                        try:
                            new_run = workflow_engine.create_run(
                                matter_id=current_matter.matter_id,
                                workflow_id=selected_workflow.workflow_id,
                                inputs=workflow_inputs
                            )
                            
                            st.success(f"✅ Workflow run created: {new_run.run_id[:8]}...")
                            
                            # Execute workflow
                            st.info("🔄 Executing workflow phases...")
                            
                            executor = LitigationWorkflowExecutor(
                                doc_processor=doc_processor,
                                anthropic_client=client,
                                model=model
                            )
                            
                            # Update run status to running
                            workflow_engine.update_run_status(new_run.run_id, WorkflowStatus.RUNNING)
                            
                            # Progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Execute each step
                            for step_index in range(len(selected_workflow.steps)):
                                step = selected_workflow.steps[step_index]
                                
                                # Skip human review steps for now
                                if step.requires_human_input and step.phase_number == 9:
                                    continue
                                
                                status_text.text(f"Phase {step_index}: {step.name}")
                                progress_bar.progress((step_index + 1) / len(selected_workflow.steps))
                                
                                # Execute step
                                step_result = executor.execute_step(new_run, step_index, selected_workflow)
                                
                                # Update step result
                                workflow_engine.update_step_result(new_run.run_id, step_index, step_result)
                                
                                # Reload run
                                new_run = workflow_engine.get_run(new_run.run_id)
                                
                                # Check if step failed
                                if step_result.status == StepStatus.FAILED:
                                    workflow_engine.update_run_status(
                                        new_run.run_id, 
                                        WorkflowStatus.FAILED,
                                        error_message=f"Phase {step_index} failed: {', '.join(step_result.errors)}"
                                    )
                                    st.error(f"❌ Workflow failed at Phase {step_index}: {step.name}")
                                    st.error(f"Errors: {', '.join(step_result.errors)}")
                                    
                                    # Show correction plan if available
                                    if 'correction_plan' in step_result.artifacts:
                                        st.warning("Correction Plan:")
                                        st.text(step_result.artifacts['correction_plan'])
                                    
                                    break
                            else:
                                # All steps completed
                                workflow_engine.update_run_status(new_run.run_id, WorkflowStatus.COMPLETED)
                                st.success("✅ Workflow completed successfully!")
                                
                                # Add to matter history
                                matter_manager.add_history(
                                    current_matter.matter_id,
                                    "workflow",
                                    f"Completed workflow: {selected_workflow.name}",
                                    f"Run ID: {new_run.run_id}",
                                    sources_used=[]
                                )
                                
                                st.info("View the artifacts by expanding the run above")
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error running workflow: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())