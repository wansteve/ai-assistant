# Workflow Feature - User Quick Reference

## 🎯 What is the Workflow Feature?

The Workflow feature provides a structured, verifiable process for creating legal research memoranda. Unlike the free-form Research tab, Workflows enforce:

✅ **Citation verification** - Every legal claim must cite a source
✅ **Authority validation** - Checks for overruled/abrogated cases  
✅ **Structured analysis** - Issue trees, rule extraction, conditional reasoning
✅ **Quality gates** - 6 verification tests that must pass
✅ **Complete audit trail** - Full provenance from sources to conclusions

## 📝 How to Use

### Step 1: Prepare Your Matter

1. Create or select a **Matter**
2. Upload **legal documents**:
   - Court opinions/cases
   - Statutes and regulations
   - Legal treatises
   - Prior research memos

**Tip**: The more relevant documents you upload, the better the results!

### Step 2: Start a Workflow

1. Go to the **⚖️ Workflow** tab
2. Select **"Verifiability-First Litigation Research Memo"**
3. Click **"Start New Workflow Run"**

### Step 3: Fill in the Intake Form

**Required Fields**:
- **Research Question**: The specific legal issue (e.g., "Can plaintiff establish breach under CA law?")
- **Jurisdiction(s)**: Comma-separated (e.g., "California, 9th Circuit")
- **Court Level**: trial, appellate, or supreme
- **Matter Posture**: MTD, SJ, appeal, discovery, trial, or other

**Optional Fields**:
- **Known Facts**: Bullet list of established facts
- **Adverse Authority Awareness**: Check if you know of contrary cases
- **Risk Posture**: Conservative, neutral, or aggressive
- **Memo Format**: IRAC, CREAC, or narrative

### Step 4: Run the Workflow

1. Click **"🚀 Run Workflow"**
2. Watch the progress bar advance through 11 phases
3. Each phase completes automatically
4. Total time: 2-5 minutes depending on complexity

## 📊 The 11 Phases

| Phase | Name | What It Does |
|-------|------|--------------|
| 0 | Human Intake & Framing | Validates inputs, locks research question |
| 1 | Authority Grounding | Finds statutes/rules/doctrines in your docs |
| 2 | Case Law Retrieval | Identifies relevant court opinions |
| 3 | Authority Validation | Checks for negative treatment (overruled, etc.) |
| 4 | Issue Decomposition | Builds issue tree with elements |
| 5 | Rule Extraction | Extracts governing legal standards with quotes |
| 6 | Rule Application | Applies rules to facts with conditional language |
| 7 | Memo Drafting | Drafts complete research memo with citations |
| 8 | Verification Suite | **HARD GATE** - runs 6 verification tests |
| 9 | Human Review | (Currently skipped - for future enhancement) |
| 10 | Export & Audit Pack | Prepares final deliverables |

## ✅ Verification Tests (Phase 8)

The workflow MUST pass these 6 tests:

1. **Citation Integrity**: Every [1][2] reference must map to a real source
2. **Quote Accuracy**: All quoted text must appear verbatim in cited documents
3. **Precedential Status**: No overruled cases cited as controlling law
4. **Jurisdiction Consistency**: Out-of-jurisdiction cases must be labeled "persuasive"
5. **Adverse Disclosure**: Negative treatment must be disclosed in memo
6. **Reasoning Structure**: Must use conditional language, no outcome predictions

**If any test fails**: The workflow status becomes FAILED and provides a correction plan.

## 📥 Viewing Results

After completion, expand the workflow run to see:

### Artifacts Available

1. **Research Memo** - Full memorandum with:
   - Question Presented
   - Short Answer (conditional)
   - Background Law
   - Analysis (issue-by-issue)
   - Adverse Authority section (if applicable)
   - Open Questions

2. **Authority Table** - List of all authorities with:
   - Name/caption
   - Type (case/statute/rule)
   - Precedential status
   - Jurisdiction

3. **Issue Tree** - Structured breakdown of:
   - Main issues
   - Sub-elements
   - Governing authorities
   - Uncertainties/gaps

4. **Verification Report** - Pass/fail for each test with details

5. **Provenance Bundle** - Complete citation mapping from claims to sources

6. **Run Metadata** - Timestamps, inputs, workflow version

### Export Options

Click the download buttons for:

- **📥 Memo (MD)** - Markdown file with memo and sources
- **📥 Verification Report** - Detailed test results
- **📥 Issue Tree** - Structured issue analysis
- **📥 Audit Pack (JSON)** - Complete audit trail in JSON

## ⚠️ Common Issues

### "No documents uploaded"
**Problem**: Workflow needs legal sources to cite
**Solution**: Upload relevant cases, statutes, or regulations first

### "Not supported by provided documents"
**Problem**: Your uploaded docs don't contain relevant authorities
**Solution**: 
- Upload more documents on this topic
- Try a different jurisdiction
- Broaden your research question

### Verification Failed - Citation Integrity
**Problem**: Memo includes citations that don't map to sources
**Solution**: Re-run workflow or manually fix citations in memo

### Verification Failed - Adverse Disclosure
**Problem**: Found overruled cases but memo doesn't disclose them
**Solution**: System should auto-include Adverse Authority section; check if it's missing

### Workflow Runs Slowly
**Problem**: 11 phases with LLM calls takes time
**Solution**: This is normal! Future versions may add async processing

## 💡 Best Practices

### Document Preparation
1. Upload documents **before** starting workflow
2. Include **primary sources** (cases, statutes) not just summaries
3. Use **multiple documents** for better context
4. Ensure documents are **text-based PDFs** (not scanned images)

### Research Questions
- Be **specific**: "Can plaintiff pierce the corporate veil under Delaware law?" ✅
- Not too broad: "Tell me about corporate law" ❌
- Include **jurisdiction**: Helps system find relevant authorities
- Frame as a **yes/no or which** question

### Known Facts
- Use **bullet points** for clarity
- Include only **established facts**, not arguments
- Be **specific** with dates, amounts, parties
- Mark **assumptions** clearly

### Reviewing Results
1. Read the **Short Answer** first for the conclusion
2. Review **verification report** to ensure quality
3. Check **authority table** for negative treatment
4. Read **open questions** to identify gaps
5. Review **sources** to verify citations

## 🔄 Workflow vs. Research Tab

| Feature | Research Tab | Workflow Tab |
|---------|--------------|--------------|
| **Structure** | Free-form Q&A | 11-phase process |
| **Citations** | Optional | Mandatory |
| **Verification** | Manual | Automated tests |
| **Format** | Conversational | Formal memo |
| **Time** | Instant | 2-5 minutes |
| **Best For** | Quick questions | Formal research |
| **Output** | Answer + sources | Complete memo + audit trail |

## 🎯 When to Use Workflows

**Use Workflows when you need**:
- Formal legal research memo
- Citation verification
- Authority validation
- Audit trail for file
- Client-ready deliverable
- Issue tree analysis

**Use Research tab when you need**:
- Quick answer to a question
- Exploratory research
- Draft ideas
- Informal analysis
- Speed over structure

## 📞 Getting Help

**Workflow stuck on a phase**:
- Check the logs in the phase details
- Ensure you have enough relevant documents
- Try with more specific inputs

**Verification keeps failing**:
- Review the correction plan provided
- Check that your documents support your research question
- Consider uploading additional authorities

**Can't find workflow runs**:
- Make sure you have a matter selected
- Check you're looking at the correct matter
- Runs are matter-specific

**Export buttons not working**:
- Ensure workflow completed successfully (✅ status)
- Try refreshing the page
- Check browser console for errors

## ✨ Tips for Success

1. **Start small**: Test with 2-3 documents before large batches
2. **Review verification**: Always check what tests passed/failed
3. **Iterate**: If verification fails, adjust inputs and re-run
4. **Save exports**: Download memo and audit pack for records
5. **Use matter context**: Keep related runs in the same matter
6. **Read correction plans**: They tell you exactly what to fix

## 🚀 Quick Start Example

**Scenario**: Research contract breach question

1. **Create matter**: "ABC Corp v. XYZ Ltd - Contract Dispute"
2. **Upload docs**: ABC-XYZ contract, relevant CA case law PDFs
3. **Go to Workflow tab**
4. **Fill form**:
   - Research Question: "Did XYZ materially breach Section 5.2 of the contract under California law?"
   - Jurisdiction: "California"
   - Court Level: "trial"
   - Matter Posture: "MTD"
   - Known Facts: "• Contract signed 1/15/2023\n• Payment due 3/1/2023\n• Payment not received until 4/15/2023"
5. **Run workflow** - Wait 3 minutes
6. **Review memo** - Check verification passed
7. **Export** - Download memo and audit pack

You now have a verifiable, citation-backed legal research memo ready for file or client!
