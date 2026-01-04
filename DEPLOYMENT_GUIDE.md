# Workflow Feature - Deployment Guide

## 🚀 Quick Deployment Steps

### Step 1: Review Files

All files have been generated and are ready to deploy:

**New Files:**
- `workflow_engine.py` - Workflow orchestration framework
- `workflow_executor.py` - Workflow execution logic (11 phases)
- `workflow_export.py` - Export utilities for memo/reports

**Updated Files:**
- `app.py` - Added Workflow tab (tab6)

**Unchanged Files:**
- `document_processor.py` - No changes
- `vector_store.py` - No changes
- `matter_manager.py` - No changes
- `export_utils.py` - No changes
- `requirements.txt` - No changes needed (all dependencies already present)
- `config.yaml` - No changes

### Step 2: Update Your Repository

```bash
# Navigate to your repository
cd /path/to/your/repo

# Copy new files
cp workflow_engine.py your-repo/
cp workflow_executor.py your-repo/
cp workflow_export.py your-repo/

# Replace app.py with updated version
cp app.py your-repo/

# Verify files are in place
ls -l your-repo/*.py
```

### Step 3: Test Locally (Recommended)

```bash
# Make sure you're in your repo directory
cd your-repo

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Run Streamlit locally
streamlit run app.py

# Open browser to http://localhost:8501
# Test the Workflow tab:
#   1. Select or create a matter
#   2. Upload a document (PDF/DOCX)
#   3. Click "Workflow" tab
#   4. Fill in the intake form
#   5. Click "Run Workflow"
#   6. Watch progress and verify completion
```

### Step 4: Commit to GitHub

```bash
# Add all new and modified files
git add workflow_engine.py
git add workflow_executor.py
git add workflow_export.py
git add app.py

# Commit with descriptive message
git commit -m "Add Workflow orchestration feature

- Implement verifiability-first litigation research memo workflow
- Add 11-phase orchestrated workflow with LLM integration
- Add 6-test verification suite (hard gate)
- Add Workflow tab to UI with progress tracking
- Add export capabilities (memo, authority table, complete report)
- Enforce hard rules: local docs only, no uncited facts, no outcome predictions
- Complete audit trail with provenance bundle

New files:
- workflow_engine.py (orchestration framework)
- workflow_executor.py (phase implementations)
- workflow_export.py (export utilities)

Modified files:
- app.py (added tab6 with workflow UI)"

# Push to GitHub
git push origin main
```

### Step 5: Verify Streamlit Cloud Deployment

1. **Check Deployment Status**
   - Go to https://share.streamlit.io
   - Find your app in the dashboard
   - Watch deployment progress (usually 2-5 minutes)

2. **Verify New Features**
   - Open deployed app
   - Should see 6 tabs now (including "⚙️ Workflow")
   - Test workflow functionality

3. **If Deployment Fails**
   - Check logs in Streamlit Cloud dashboard
   - Verify all files were pushed to GitHub
   - Check requirements.txt includes all dependencies
   - Ensure API key is set in Streamlit secrets

## 📋 Pre-Deployment Checklist

Before pushing to production:

- [ ] All new files copied to repository
- [ ] Updated app.py copied to repository
- [ ] Tested locally with `streamlit run app.py`
- [ ] Verified Workflow tab appears
- [ ] Tested creating a matter
- [ ] Tested uploading a document
- [ ] Tested running a workflow
- [ ] Verified progress tracking works
- [ ] Tested export functionality
- [ ] Checked verification tests run
- [ ] Reviewed git diff to confirm changes
- [ ] Committed with descriptive message
- [ ] Pushed to GitHub main branch

## 🧪 Verification Commands

### Test Application Locally

```bash
# Start the app
streamlit run app.py

# In another terminal, check if files are loaded correctly
python3 << EOF
from workflow_engine import WorkflowManager
from workflow_executor import WorkflowExecutor

# Test registry
wm = WorkflowManager()
workflows = wm.registry.list_workflows()
print(f"Found {len(workflows)} workflows")
for wf in workflows:
    print(f"  - {wf.name}: {len(wf.steps)} steps")
EOF
```

### Verify Dependencies

```bash
# Check all required packages are installed
python3 << EOF
import streamlit
import anthropic
import PyPDF2
import docx
import sentence_transformers
import numpy
import torch
print("✅ All dependencies installed")
EOF
```

### Test Workflow Engine

```bash
# Test workflow creation
python3 << EOF
from workflow_engine import WorkflowManager, WorkflowRegistry

wm = WorkflowManager()
registry = WorkflowRegistry()

# Get workflow
workflow = registry.get_workflow("litigation_research_memo")
print(f"Workflow: {workflow.name}")
print(f"Steps: {workflow.steps}")
print(f"Required inputs: {workflow.input_schema['required']}")
print("✅ Workflow engine working")
EOF
```

## 🔍 Post-Deployment Verification

After deploying to Streamlit Cloud:

### 1. UI Verification

- [ ] App loads without errors
- [ ] All 6 tabs visible
- [ ] Workflow tab accessible
- [ ] Workflow dropdown shows "Verifiability-First Litigation Research Memo"
- [ ] Intake form displays correctly with all fields
- [ ] Required fields are marked

### 2. Functionality Verification

- [ ] Can create a matter
- [ ] Can upload a document
- [ ] Can navigate to Workflow tab
- [ ] Can select workflow
- [ ] Can fill intake form
- [ ] Can submit workflow
- [ ] Progress bar updates
- [ ] Steps execute sequentially
- [ ] Can view step details
- [ ] Can export results

### 3. Error Handling Verification

- [ ] Missing required fields shows error
- [ ] No documents shows warning
- [ ] Failed verification shows correction plan
- [ ] Failed step shows error message
- [ ] Can view failed workflow runs

## 🐛 Common Deployment Issues

### Issue: "ModuleNotFoundError: No module named 'workflow_engine'"

**Cause:** Files not in repository or not deployed  
**Solution:**
```bash
# Verify files exist
ls -l workflow_engine.py workflow_executor.py workflow_export.py

# Verify files are committed
git status

# If not committed:
git add workflow_*.py
git commit -m "Add workflow modules"
git push origin main
```

### Issue: Workflow tab doesn't appear

**Cause:** app.py not updated  
**Solution:**
```bash
# Verify app.py has the import lines
grep "workflow_engine" app.py

# Should see:
# from workflow_engine import WorkflowManager, WorkflowStatus, StepStatus
# from workflow_executor import WorkflowExecutor
# from workflow_export import ...

# Verify tabs definition
grep "tab6" app.py

# Should see:
# tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([...])

# If missing, copy the updated app.py and push again
```

### Issue: Streamlit Cloud deployment fails

**Cause:** Various reasons  
**Solution:**
1. Check Streamlit Cloud logs
2. Verify requirements.txt has all dependencies:
   ```
   streamlit==1.40.0
   anthropic>=0.40.0
   pyyaml==6.0.2
   PyPDF2==3.0.1
   python-docx==1.1.0
   sentence-transformers>=2.3.0
   numpy>=1.26.0
   torch>=2.0.0
   ```
3. Verify API key is in Streamlit secrets
4. Try redeploying from Streamlit dashboard

### Issue: Workflow execution errors

**Cause:** API issues or document processing errors  
**Solution:**
- Check Streamlit logs for detailed error
- Verify API key is valid
- Test with simple documents first
- Check documents are properly indexed

## 📊 Monitoring

### Check Application Health

After deployment, monitor:

1. **Deployment Logs**
   - Streamlit Cloud dashboard → Your App → Logs
   - Watch for import errors or startup issues

2. **Runtime Logs**
   - Check logs while running workflows
   - Look for API errors or timeout issues

3. **Storage**
   - Monitor matters/ directory growth
   - Check workflow run storage

4. **Performance**
   - Workflow execution time (typically 2-5 minutes)
   - LLM API latency
   - Document indexing time

## 🎯 Success Criteria

Deployment is successful when:

- ✅ App loads without errors
- ✅ All 6 tabs visible and functional
- ✅ Can create matters and upload documents
- ✅ Can select and configure workflow
- ✅ Can run workflow end-to-end
- ✅ Progress tracking works
- ✅ Verification tests execute
- ✅ Can export results
- ✅ Can view past workflow runs
- ✅ No console errors
- ✅ All features from previous version still work

## 📞 Getting Help

If you encounter issues:

1. **Check the logs first**
   - Streamlit Cloud dashboard logs
   - Browser console (F12 → Console)

2. **Review the error message**
   - Most errors are descriptive
   - Check which file/line is causing the issue

3. **Verify file versions**
   - Ensure you're using the latest versions
   - Check git status and commits

4. **Test locally**
   - Always test locally before pushing
   - Easier to debug than on Streamlit Cloud

5. **Common fixes**
   - Clear Streamlit cache
   - Restart the app
   - Re-deploy from dashboard
   - Check API key

## 🎉 Next Steps After Deployment

Once deployed successfully:

1. **Create your first workflow run**
   - Select a matter
   - Upload relevant legal documents
   - Run the litigation research memo workflow
   - Review the generated memo and verification report

2. **Test with different scenarios**
   - Different jurisdictions
   - Various case types
   - Edge cases (no authorities found, etc.)

3. **Share with team**
   - Invite colleagues to test
   - Gather feedback on workflow design
   - Iterate based on real usage

4. **Monitor usage**
   - Track workflow success rates
   - Identify common failure points
   - Optimize based on patterns

---

**Deployment Version:** 1.0.0  
**Last Updated:** January 4, 2026  
**Status:** Ready for Production
