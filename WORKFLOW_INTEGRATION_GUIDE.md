# Workflow Feature Integration Guide

## Overview
This guide explains how to integrate the new Workflow capability into your existing legal automation app.

## New Files Added

1. **workflow_engine.py** - Core orchestration framework
   - Manages workflow definitions, runs, and step results
   - Handles persistence of workflow data
   - Provides CRUD operations for workflows and runs

2. **litigation_workflow.py** - Litigation Research Memo workflow implementation
   - Implements all 10 phases of the workflow
   - Executes steps sequentially with proper validation
   - Uses existing document processor and Anthropic client

3. **workflow_verification.py** - Verification suite (HARD GATE)
   - 6 verification tests that must pass
   - Citation integrity, quote accuracy, precedential status, etc.
   - Returns pass/fail with correction plans

4. **workflow_exports.py** - Export utilities for workflow artifacts
   - Export memo to Markdown
   - Export audit pack to JSON
   - Export verification report and issue tree

## Integration Steps

### Step 1: Add New Imports to app.py

Add these imports at the top of app.py (after existing imports):

```python
from workflow_engine import WorkflowEngine, WorkflowStatus, StepStatus
from litigation_workflow import create_litigation_workflow, LitigationWorkflowExecutor
from workflow_exports import (
    export_memo_to_markdown, 
    export_audit_pack_to_json,
    export_verification_report_to_markdown,
    export_issue_tree_to_markdown
)
```

### Step 2: Initialize Workflow Engine

Add after the existing cached resource functions (around line 25):

```python
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
```

### Step 3: Update Tab Declaration

Change line 230 from:
```python
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summarize", "✍️ Draft", "🔍 Research", "📄 Document Analysis", "🔎 Semantic Search"])
```

To:
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Summarize", 
    "✍️ Draft", 
    "🔍 Research", 
    "📄 Document Analysis", 
    "🔎 Semantic Search",
    "⚖️ Workflow"
])
```

### Step 4: Add Workflow Tab Implementation

Add this code at the end of app.py (after tab5, around line 963):

```python
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
                        st.error(f"Error: {run.error_message}")
                    
                    # Show step status
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
            
            st.divider()
        
        # Check if viewing a specific run
        for run in workflow_runs:
            if st.session_state.get(f'viewing_run_{run.run_id}'):
                st.subheader(f"📄 Workflow Artifacts - Run {run.run_id[:8]}...")
                
                # Get final artifacts from Phase 10
                if len(run.step_results) > 10:
                    final_artifacts = run.step_results[10].artifacts
                    
                    # Display memo
                    if 'final_memo' in final_artifacts:
                        with st.expander("📝 Research Memo", expanded=True):
                            st.markdown(final_artifacts['final_memo'])
                        
                        # Export buttons
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            memo_md = export_memo_to_markdown(
                                final_artifacts['final_memo'],
                                current_matter.matter_name,
                                final_artifacts.get('run_metadata', {}),
                                final_artifacts.get('authority_table', []),
                                run.step_results[1].sources_used + run.step_results[2].sources_used
                            )
                            st.download_button(
                                "📥 Memo (MD)",
                                memo_md,
                                f"memo_{run.run_id[:8]}.md",
                                mime="text/markdown"
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
                                    mime="text/markdown"
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
                                    mime="text/markdown"
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
                                mime="application/json"
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
```

### Step 5: Update requirements.txt

No new dependencies are needed! The workflow feature uses existing libraries.

### Step 6: Test the Integration

1. Start Streamlit: `streamlit run app.py`
2. Create or select a matter
3. Upload legal documents (cases, statutes, regulations)
4. Navigate to the new "⚖️ Workflow" tab
5. Fill in the workflow intake form
6. Run the workflow and monitor progress
7. View and export artifacts

## File Structure

After integration, your project should have:

```
project/
├── app.py (updated)
├── document_processor.py
├── matter_manager.py
├── vector_store.py
├── export_utils.py
├── workflow_engine.py (new)
├── litigation_workflow.py (new)
├── workflow_verification.py (new)
├── workflow_exports.py (new)
├── requirements.txt
├── config.yaml
└── workflows/ (created automatically)
    ├── workflow_definitions.json
    └── runs/
        ├── {run_id}.json
        └── {run_id}_artifacts/
```

## Features

1. **Workflow Selection** - Choose from registered workflows
2. **Intake Form** - Structured input collection
3. **Progress Tracking** - Real-time step execution updates
4. **Artifact Viewing** - Review memos, authority tables, issue trees
5. **Verification Reports** - See which tests passed/failed
6. **Multiple Exports** - Markdown, JSON, audit packs
7. **Matter Integration** - All runs tied to matters
8. **Run History** - View and resume previous runs

## Next Steps

1. Test with real legal documents
2. Review generated memos for quality
3. Iterate on prompts in litigation_workflow.py
4. Add additional workflow types
5. Enhance verification tests
6. Add human review interface for Phase 9

## Troubleshooting

**Issue**: Workflow fails immediately
- Check that documents are uploaded and indexed
- Verify API key is configured
- Check logs for specific error messages

**Issue**: No authorities found
- Ensure uploaded documents contain statutory/case law
- Try broader search terms
- Upload more relevant documents

**Issue**: Verification tests fail
- Review the correction plan provided
- Check citation formatting in memo
- Verify quotes appear in source documents

## Support

For issues or questions:
1. Check the logs in step_result.logs
2. Review the correction_plan if verification fails
3. Examine the artifacts in the run directory
