# Workflow Feature - Implementation Guide

## 🎯 Overview

The Workflow feature adds orchestrated, verifiable legal research capabilities to your Matter Management System. It implements a "Verifiability-First Litigation Research Memo" workflow that ensures every legal claim is grounded in source documents with strict citation verification.

## 📦 New Files Added

1. **workflow_engine.py** - Core orchestration framework
   - WorkflowDefinition, WorkflowRun, StepResult classes
   - WorkflowRegistry for managing workflow templates
   - WorkflowManager for persistence and run management

2. **workflow_executor.py** - Workflow execution logic
   - WorkflowExecutor class that runs each workflow phase
   - 11-phase litigation research memo workflow implementation
   - Verification suite with 6 automated tests

3. **workflow_export.py** - Export utilities
   - Export memo to Markdown
   - Export authority table to Markdown
   - Export issue tree to Markdown
   - Export complete audit pack (JSON + Markdown)

4. **app.py** (updated) - New Workflow tab in UI
   - Workflow selection and intake form
   - Real-time progress tracking
   - Step-by-step results display
   - Export capabilities

## ✨ Key Features

### 1. Workflow #1: Verifiability-First Litigation Research Memo

**11-Phase Orchestrated Workflow:**

- **Phase 0: Human Intake & Framing**
  - Validates required inputs
  - Locks research question, jurisdictions, court level, posture
  - Identifies assumptions and clarifying questions

- **Phase 1: Authority Grounding**
  - Retrieves statutes, rules, regulations, doctrines from local docs
  - Every authority must have supporting quotes with citations
  - HARD RULE: "Not supported by provided documents" if no authorities found

- **Phase 2: Case Law Retrieval**
  - Retrieves relevant court opinions from local docs
  - Extracts key quotes with citations
  - Validates every case has supporting text

- **Phase 3: Authority Validation**
  - Searches for negative treatment signals (overruled, abrogated, etc.)
  - Marks precedential status: unknown / negative_treatment_found / treated_as_good_law_in_docs
  - HARD RULE: Negative authorities cannot be cited as controlling

- **Phase 4: Issue Decomposition**
  - Builds hierarchical issue tree
  - Maps each issue to governing authorities
  - Flags uncertainties

- **Phase 5: Rule Extraction**
  - Extracts governing tests/standards with quoted language
  - Every rule must include pinpoint citation
  - Links rules to source chunks

- **Phase 6: Rule Application**
  - Applies rules to known facts using conditional language
  - Identifies gaps and uncertainties
  - Lists adverse interpretations
  - CHECKPOINT: Pauses if gaps/uncertainties exceed threshold

- **Phase 7: Memo Drafting**
  - Drafts structured legal memo with sections:
    - Question Presented
    - Short Answer (qualified, conditional)
    - Background Law
    - Analysis (issue-by-issue)
    - Adverse Authority (mandatory if negative treatment found)
    - Open Questions
  - NO outcome predictions
  - Uses conditional language throughout

- **Phase 8: Verification Suite (HARD GATE)**
  - **6 Automated Tests:**
    1. Citation Integrity - every [n] references real source
    2. Quote Accuracy - quotes match source text verbatim
    3. Precedential Status - no negative authorities as controlling
    4. Jurisdiction Consistency - authorities match jurisdictions or marked "persuasive"
    5. Adverse Disclosure - negative authorities must be in Adverse section
    6. Reasoning Structure - conditional language, no banned outcome phrases
  - **IF ANY FAIL:** status=FAILED, returns correction plan

- **Phase 9: Human Review**
  - Placeholder for manual review step
  - Captures reviewer name and notes

- **Phase 10: Export & Audit Pack**
  - Prepares complete audit package:
    - Research memo
    - Authority table
    - Issue tree
    - Verification report
    - Provenance bundle
    - Run metadata

### 2. Hard Rules Enforcement

**The system enforces these non-negotiable rules:**

- ✅ Local docs only - no web search, no external sources
- ✅ No uncited facts - every legal claim must cite an authority chunk
- ✅ No legal advice - no outcome predictions, only conditional analysis
- ✅ Citation traceability - every [n] maps to sources[].id
- ✅ Verification gate - if any test fails, workflow stops with correction plan

### 3. UI Features

**Workflow Tab includes:**

- Workflow selection dropdown
- Dynamic intake form based on workflow schema
- Real-time progress timeline showing:
  - Completed steps (✅)
  - Current step (▶️)
  - Failed steps (❌)
  - Pending steps (⏳)
- Expandable step details with logs, errors, artifacts
- Verification report display
- Export buttons for:
  - Memo (Markdown)
  - Authority Table (Markdown)
  - Issue Tree (Markdown)
  - Complete Report (Markdown)
  - Audit Pack (JSON)

## 🚀 Usage Instructions

### Running a Workflow

1. **Select or Create a Matter**
   - Navigate to the top of the app
   - Select an existing matter or create a new one

2. **Upload Documents**
   - Upload relevant legal documents (PDFs, DOCX, TXT)
   - These provide the source material for citations

3. **Navigate to Workflow Tab**
   - Click on "⚙️ Workflow" tab

4. **Select Workflow**
   - Choose "Verifiability-First Litigation Research Memo"

5. **Fill Intake Form**
   - **Required Fields:**
     - Research Question (free text)
     - Jurisdiction(s) (multi-select)
     - Court Level (trial/appellate/supreme)
     - Matter Posture (MTD/SJ/appeal/etc.)
   
   - **Optional Fields:**
     - Known Facts (textarea)
     - Adverse Authority Awareness (checkbox)
     - Risk Posture (conservative/neutral/aggressive)
     - Memo Format (IRAC/CREAC/Narrative)

6. **Run Workflow**
   - Click "▶️ Run Workflow"
   - Watch progress in real-time
   - Each phase executes sequentially

7. **Review Results**
   - Expand each step to see logs and artifacts
   - Check verification report
   - Review correction plan if workflow failed

8. **Export Outputs**
   - Download memo as Markdown
   - Download authority table
   - Download complete report
   - Download audit pack (JSON) for full traceability

### Viewing Past Runs

- Recent runs are listed at the top of Workflow tab
- Click "View" to see detailed results
- All artifacts are preserved
- Complete audit trail maintained

## 📊 Data Storage

### Storage Structure

```
matters/
  {matter_id}/
    workflows/
      {run_id}/
        run.json              # Workflow run metadata
        artifacts/
          phase_0_intake.json
          phase_1_authority_grounding.json
          ...
          phase_10_export.json
```

### Run Metadata (run.json)

```json
{
  "run_id": "uuid",
  "matter_id": "matter-uuid",
  "workflow_id": "litigation_research_memo",
  "status": "completed",
  "inputs": { ... },
  "current_step": 11,
  "step_results": [ ... ],
  "started_at": "2024-01-04T10:00:00",
  "finished_at": "2024-01-04T10:15:00",
  "correction_plan": null
}
```

## 🔍 Verification Tests Explained

### Test 1: Citation Integrity
- Scans memo for all bracket citations [1], [2], etc.
- Verifies each citation maps to a real source
- **Fails if:** Citations reference non-existent sources

### Test 2: Quote Accuracy
- Checks all quoted rule statements
- Verifies quotes appear verbatim in source chunks
- **Fails if:** Quotes don't match source text exactly

### Test 3: Precedential Status
- Ensures no authorities with "negative_treatment_found" are cited as controlling
- **Fails if:** Negative authorities used outside Adverse Authority section

### Test 4: Jurisdiction Consistency
- Checks all authorities match selected jurisdictions
- Out-of-jurisdiction authorities must be marked "persuasive"
- **Fails if:** Out-of-jurisdiction authorities not properly labeled

### Test 5: Adverse Disclosure
- If any authorities have negative treatment, memo must include Adverse Authority section
- **Fails if:** Negative treatment exists but no disclosure section

### Test 6: Reasoning Structure
- Checks for conditional language: "if", "assuming", "to the extent"
- Scans for banned outcome phrases: "will win", "likely succeed", "guaranteed"
- **Fails if:** Uses outcome predictions or lacks conditional framing

## 🛠️ Technical Architecture

### Workflow Engine (workflow_engine.py)

```python
# Core classes
WorkflowDefinition  # Template for workflow
WorkflowRun         # Instance of running workflow
StepResult          # Result of single step
WorkflowRegistry    # Registry of available workflows
WorkflowManager     # Persistence and run management
```

### Workflow Executor (workflow_executor.py)

```python
class WorkflowExecutor:
    def execute_step(workflow_run, step_id, workflow_def, matter)
        # Routes to phase-specific handler
        
    def _phase_N_name(workflow_run, step_result, matter)
        # Implements specific phase logic
        # Returns StepResult with artifacts, logs, errors
```

### Integration with Existing System

- Uses existing `DocumentProcessor` for retrieval
- Integrates with `MatterManager` for persistence
- Calls Anthropic API through existing `client`
- Leverages existing vector store for semantic search

## 📋 Deployment Instructions

### 1. Update Repository

```bash
# Copy all new files to your repo
cp workflow_engine.py your-repo/
cp workflow_executor.py your-repo/
cp workflow_export.py your-repo/
cp app.py your-repo/  # Updated version
```

### 2. Commit and Push

```bash
git add .
git commit -m "Add Workflow orchestration feature with verifiability-first litigation memo"
git push origin main
```

### 3. Streamlit Cloud Auto-Deploy

- Streamlit Cloud will automatically detect changes
- New deployment will include Workflow tab
- No additional configuration needed

### 4. Test Locally First (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

## 🧪 Testing Checklist

### Functional Tests

- [ ] Can select matter
- [ ] Can upload documents
- [ ] Can navigate to Workflow tab
- [ ] Can select workflow from dropdown
- [ ] Intake form displays all fields correctly
- [ ] Can submit workflow with valid inputs
- [ ] Progress bar updates during execution
- [ ] Each phase completes successfully
- [ ] Verification tests run and pass
- [ ] Can view completed workflow details
- [ ] Can export memo to Markdown
- [ ] Can export authority table
- [ ] Can export complete report
- [ ] Can view past workflow runs

### Verification Tests

- [ ] Citation integrity catches invalid citations
- [ ] Quote accuracy detects mismatched quotes
- [ ] Precedential status blocks negative authorities
- [ ] Jurisdiction consistency flags out-of-jurisdiction authorities
- [ ] Adverse disclosure requires section when needed
- [ ] Reasoning structure blocks outcome predictions

### Edge Cases

- [ ] Workflow handles no documents gracefully
- [ ] Workflow fails gracefully when no authorities found
- [ ] Correction plan displays when verification fails
- [ ] Can view failed workflow runs
- [ ] Multiple workflows can run on same matter
- [ ] Workflow persists across page reloads

## 🐛 Troubleshooting

### "No documents uploaded" Warning

**Problem:** Workflow requires source documents  
**Solution:** Upload PDFs, DOCX, or TXT files in sidebar before running workflow

### Verification Failed

**Problem:** One or more verification tests failed  
**Solution:** Review correction plan, check source documents, re-run if needed

### "Not supported by provided documents"

**Problem:** No relevant authorities found in uploaded documents  
**Solution:** Upload more comprehensive source materials (statutes, cases, etc.)

### Workflow Stuck on Step

**Problem:** Step appears to be running indefinitely  
**Solution:** Check browser console for errors, refresh page, check API key

### Export Buttons Not Appearing

**Problem:** Workflow not completed  
**Solution:** Wait for workflow to complete all phases, check for failures

## 🔮 Future Enhancements

Potential improvements for future versions:

1. **Resume Failed Workflows** - Allow restarting from failed step
2. **Custom Workflow Templates** - User-defined workflow schemas
3. **Parallel Step Execution** - Run independent steps concurrently
4. **Advanced Citation Formats** - Support Bluebook, APA, MLA
5. **Interactive Verification** - Manual override for failed tests
6. **Collaborative Review** - Multi-user review and approval
7. **Version Control** - Track changes to workflow outputs
8. **Integration with Citation Tools** - Connect to Westlaw, Lexis
9. **AI-Assisted Fact Finding** - Smart gap identification
10. **Jurisdiction-Specific Rules** - Customize by court/state

## 📚 Additional Resources

- **Anthropic API Docs:** https://docs.anthropic.com
- **Streamlit Docs:** https://docs.streamlit.io
- **Legal Citation Guide:** https://www.law.cornell.edu/citation

## 💡 Best Practices

1. **Upload Quality Documents**
   - Include full case opinions, not just headnotes
   - Ensure statutes are complete and current
   - Provide comprehensive factual record

2. **Write Clear Research Questions**
   - Be specific about the legal issue
   - Include relevant factual context
   - Avoid overly broad questions

3. **Select Appropriate Jurisdictions**
   - Choose all relevant jurisdictions
   - Consider both binding and persuasive authority
   - Be mindful of jurisdiction hierarchy

4. **Review Verification Reports**
   - Address all failed tests before relying on output
   - Understand correction plans
   - Manually verify critical citations

5. **Use Conditional Language**
   - The system enforces this, but understand why
   - Avoid outcome predictions
   - Qualify all conclusions appropriately

6. **Maintain Audit Trail**
   - Save all exported reports
   - Document workflow run IDs
   - Preserve correction plans for learning

## 🎓 Understanding the Workflow Philosophy

This workflow implementation is based on the principle of **verifiable, grounded legal research**. Unlike traditional AI legal tools that may hallucinate citations or make unsupported claims, this system:

- **Requires proof** - Every claim must cite a source
- **Validates quotes** - Quoted text must match source exactly
- **Checks precedent** - Authority status must be verified
- **Enforces honesty** - No predictions, only conditional analysis
- **Provides audit trail** - Complete provenance for all outputs

This approach prioritizes **reliability over comprehensiveness** and **accuracy over speed**. It's designed for legal professionals who need defensible, citeable work product.

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review error logs in workflow step details
- Examine correction plans for guidance
- Test with simpler documents first

---

**Version:** 1.0.0  
**Last Updated:** January 4, 2026  
**Author:** Workflow Feature Implementation
