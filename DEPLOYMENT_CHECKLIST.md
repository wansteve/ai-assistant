# Workflow Feature - Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ Files to Add to Repository

Copy these new files to your GitHub repository:

1. **workflow_engine.py** - Core orchestration engine
2. **litigation_workflow.py** - Litigation research memo workflow
3. **workflow_verification.py** - Verification suite (HARD GATE)
4. **workflow_exports.py** - Export utilities

### ✅ Files to Modify

1. **app.py** - Add workflow tab and integration code
   - See WORKFLOW_INTEGRATION_GUIDE.md for detailed instructions
   - Key changes:
     - Add imports (lines 6-10)
     - Add workflow_engine initialization (lines 26-35)
     - Update tab declaration (line 230)
     - Add workflow tab implementation (end of file)

### ✅ No Changes Needed

- **requirements.txt** - No new dependencies required!
- **config.yaml** - Uses existing API key configuration
- **document_processor.py** - No changes
- **matter_manager.py** - No changes
- **vector_store.py** - No changes
- **export_utils.py** - No changes

## 🚀 Deployment Steps

### Step 1: Local Testing

```bash
# 1. Copy new files to your project directory
cp workflow_engine.py /path/to/your/project/
cp litigation_workflow.py /path/to/your/project/
cp workflow_verification.py /path/to/your/project/
cp workflow_exports.py /path/to/your/project/

# 2. Update app.py with workflow tab integration
# (Follow WORKFLOW_INTEGRATION_GUIDE.md)

# 3. Test locally
streamlit run app.py

# 4. Verify:
# - Workflow tab appears
# - Can create workflow runs
# - Progress updates work
# - Artifacts are generated
```

### Step 2: Git Commit

```bash
# Add new files
git add workflow_engine.py
git add litigation_workflow.py
git add workflow_verification.py
git add workflow_exports.py

# Add modified file
git add app.py

# Commit
git commit -m "Add verifiable workflow capability with litigation research memo workflow"

# Push to GitHub
git push origin main
```

### Step 3: Streamlit Cloud Deployment

1. **Push triggers automatic deployment** - Streamlit Cloud will detect the changes
2. **Monitor deployment logs** - Check for any errors
3. **Verify deployment** - Visit your app URL and test the workflow tab

### Step 4: Post-Deployment Verification

Test these scenarios in production:

1. ✅ Create a matter
2. ✅ Upload legal documents (PDF/DOCX of cases, statutes)
3. ✅ Navigate to Workflow tab
4. ✅ Fill in workflow form and submit
5. ✅ Monitor progress through all phases
6. ✅ View generated artifacts
7. ✅ Download exports (Memo, Verification Report, Audit Pack)
8. ✅ Check verification tests pass/fail correctly

## 📊 Feature Summary

### What This Adds

**New Capability**: Structured, verifiable legal research workflows

**Key Features**:
1. **11-Phase Workflow** - From intake to export
2. **Citation Verification** - Every claim must cite sources
3. **HARD GATE Tests** - 6 verification tests that must pass
4. **Authority Validation** - Checks for negative treatment
5. **Issue Decomposition** - Structured legal analysis
6. **Conditional Reasoning** - No outcome predictions
7. **Audit Trail** - Complete provenance tracking
8. **Multiple Exports** - Markdown, JSON, audit packs

### Integration Points

- **Matter System** - All runs tied to matters
- **Document Processor** - Uses existing vector search
- **Anthropic API** - Uses configured Claude Sonnet 4
- **Export System** - Compatible with existing exports

## 🎯 Success Criteria

Deployment is successful if:

1. ✅ Workflow tab appears in UI
2. ✅ Can select workflow and fill form
3. ✅ Workflow executes all phases without errors
4. ✅ Generates research memo with citations
5. ✅ Verification suite runs and reports results
6. ✅ Can export all artifact types
7. ✅ Run history shows in matter context
8. ✅ No performance degradation in other tabs

## 🐛 Known Limitations

1. **Phase 9 (Human Review)** - Currently skipped in execution
   - Manual review UI can be added later
   
2. **Authority Validation** - Local-only proxy
   - Cannot access true Shepardizing services
   - Relies on negative treatment signals in uploaded docs

3. **Large Documents** - May hit token limits
   - Workflow chunks documents appropriately
   - Some phases may need multiple LLM calls

4. **Execution Time** - Complete workflow takes 2-5 minutes
   - Progress bar shows current phase
   - Asynchronous execution can be added later

## 📈 Future Enhancements

Potential improvements for future iterations:

1. **Resume Capability** - Resume failed workflows
2. **Human Review UI** - Interactive Phase 9 interface
3. **Custom Workflows** - User-defined workflow builder
4. **Async Execution** - Background processing
5. **Collaboration** - Multi-user review and editing
6. **Template Library** - Additional workflow types
7. **Advanced Verification** - External API integration
8. **Export to DOCX** - Word document exports

## 📞 Support & Troubleshooting

### Common Issues

**"No documents uploaded" warning**
- Solution: Upload PDF/DOCX files with legal content before running workflow

**"Not supported by provided documents" error**
- Solution: Ensure uploaded docs contain relevant statutes/cases for the jurisdiction

**Verification tests fail**
- Solution: Review correction plan, adjust uploaded docs or re-run with clearer inputs

**Workflow runs slowly**
- Solution: Normal for first run; subsequent runs faster due to caching

### Debug Mode

To enable detailed logging:

```python
# In litigation_workflow.py, add at start of execute_step:
print(f"DEBUG: Executing {step.step_id}")
print(f"DEBUG: Run inputs: {run.inputs}")
```

### Performance Monitoring

Track these metrics:
- Average execution time per phase
- Token usage per workflow run
- Success rate of verification tests
- Most common failure points

## ✅ Final Checklist

Before considering deployment complete:

- [ ] All 4 new files added to repository
- [ ] app.py updated with workflow tab code
- [ ] Local testing successful
- [ ] Git commit and push completed
- [ ] Streamlit Cloud deployed successfully
- [ ] Production testing completed
- [ ] Documentation reviewed
- [ ] Team trained on new feature

## 🎉 You're Done!

Once all checklist items are complete, your legal automation platform now has enterprise-grade workflow capabilities with:
- Verifiable citations
- Authority validation
- Structured legal analysis
- Complete audit trails
- Professional exports

Your users can now run comprehensive legal research workflows with confidence in the verifiability of the results!
