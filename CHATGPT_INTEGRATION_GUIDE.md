# ChatGPT Apps SDK Integration Guide
## Connecting Your Legal Assistant to ChatGPT

This guide walks you through integrating your Streamlit legal assistant with ChatGPT using the OpenAI Apps SDK and Model Context Protocol (MCP).

---

## 📋 Overview

### What This Integration Does

Your legal assistant will be accessible directly in ChatGPT conversations. Users can:

1. **Create and manage legal matters** through natural conversation
2. **Run legal research** with cited answers from uploaded documents
3. **Execute full litigation workflows** for comprehensive research memos
4. **Get workflow status** and retrieve generated memos
5. **All within ChatGPT's interface** - no switching between apps

### Architecture

```
ChatGPT <--> MCP Server <--> Your Legal Assistant Backend
         (Apps SDK)        (Python modules)
```

- **MCP Server**: Exposes your app's capabilities as "tools" ChatGPT can call
- **Apps SDK**: Handles communication between ChatGPT and your server
- **Your Backend**: Existing Streamlit app components (document_processor, workflow_engine, etc.)

---

## 🚀 Phase 1: MCP Server Setup (Text-Only Integration)

This phase focuses on getting input/output working in ChatGPT's chat interface without custom UI.

### Step 1: Install MCP Dependencies

Update your `requirements.txt`:

```bash
# Add to your existing requirements.txt
mcp>=1.0.0
fastapi>=0.115.0
uvicorn>=0.30.0
httpx>=0.27.0
```

Install:
```bash
pip install mcp fastapi uvicorn httpx
```

### Step 2: Add MCP Server File

Copy `legal_assistant_mcp.py` to your project root alongside `app.py`.

**What this file does:**
- Exposes 6 tools to ChatGPT:
  1. `research_legal_question` - Quick RAG-based research
  2. `run_litigation_workflow` - Full 11-phase workflow
  3. `create_matter` - Create new matters
  4. `list_matters` - View all matters
  5. `get_workflow_status` - Check workflow progress
  6. `get_workflow_memo` - Retrieve completed memos

### Step 3: Set Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
export ANTHROPIC_API_KEY="your-api-key-here"

# Optional
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"

# For MCP server with tunneling (see Step 5)
export MCP_ALLOWED_HOSTS="your-subdomain.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://your-subdomain.ngrok-free.app"
```

### Step 4: Test MCP Server Locally

Start the server:

```bash
python legal_assistant_mcp.py
```

Test with MCP Inspector:
```bash
npx @modelcontextprotocol/inspector@latest --server-url http://localhost:8787/mcp --transport http
```

This opens a web interface where you can test tool calls before connecting to ChatGPT.

### Step 5: Expose Server with Ngrok

For ChatGPT to access your local server during development, use ngrok:

```bash
# Install ngrok
brew install ngrok  # Mac
# OR download from https://ngrok.com/

# Start tunnel
ngrok http 8787
```

You'll get a public URL like:
```
https://abc123.ngrok-free.app
```

**Important:** Update your environment variables with this URL:
```bash
export MCP_ALLOWED_HOSTS="abc123.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://abc123.ngrok-free.app"
```

Restart your MCP server after setting these.

### Step 6: Connect to ChatGPT

1. **Open ChatGPT** (Plus, Pro, Business, or Enterprise account required)
2. **Enable Developer Mode**:
   - Go to Settings → Beta Features
   - Enable "Developer Mode"
3. **Add Your Connector**:
   - Click "More" (•••) in chat input
   - Select "Connectors"
   - Click "Add Connector"
   - Enter: `https://your-subdomain.ngrok-free.app/mcp`
   - Give it a name: "Legal Assistant"
4. **Test the Connection**:
   - ChatGPT will verify the server responds
   - You should see your tools listed

### Step 7: Test in ChatGPT

Start a conversation and test each tool:

**Example 1: Create a Matter**
```
User: Create a new matter called "Smith v. Jones" for client "John Smith"
ChatGPT: [calls create_matter tool]
```

**Example 2: Research Question**
```
User: Research: Can plaintiff pierce the corporate veil under Delaware law?
ChatGPT: [calls research_legal_question tool, returns cited answer]
```

**Example 3: Run Workflow**
```
User: Run a litigation workflow for matter [matter-id] with question "Can defendant be liable for breach?"
ChatGPT: [calls run_litigation_workflow tool, shows progress]
```

---

## 📊 What Users See in ChatGPT

### Tool Call Flow

1. **User asks question** in natural language
2. **ChatGPT decides** which tool to use
3. **Tool is called** (you see "Researching..." or "Running workflow...")
4. **Result displayed** as formatted text in the chat
5. **User can follow up** with more questions

### Example Conversation

```
User: I need to research contract law for my client

ChatGPT: I'd be happy to help with contract law research. First, let's create a 
matter to organize your work. What's the matter name and client name?

User: "ABC Corp v. XYZ Ltd" for client ABC Corp

ChatGPT: [calls create_matter] ✅ Matter created! 
Matter ID: abc-123-def
You can now upload documents and run research.

User: Research: What are the elements of breach of contract under California law?

ChatGPT: [calls research_legal_question]
**Answer:**

A breach of contract under California law requires four elements [1][2]:

1. The existence of a valid contract [1]
2. Plaintiff's performance or excuse for non-performance [1][2]
3. Defendant's breach [2]
4. Resulting damage to the plaintiff [1][2]

**Sources:**
[1] California Civil Code § 1549 - Page 12
"A contract requires mutual consent..."
[2] Civ. Code § 1550 - Page 18
...
```

---

## 🔧 Deployment Options

### Option 1: Development (Current)

**Setup:**
- Local MCP server
- Ngrok tunnel
- ChatGPT connects via tunnel

**Pros:** Quick testing, easy debugging
**Cons:** Ngrok URL changes, not production-ready

### Option 2: Production Server

**Deploy MCP server to:**
- Railway.app
- Render.com
- Fly.io
- Your own VPS

**Steps:**
1. Create a `Procfile` or `startup` script:
   ```bash
   web: python legal_assistant_mcp.py
   ```

2. Set environment variables on the platform

3. Deploy and get a permanent URL

4. Connect ChatGPT to `https://your-domain.com/mcp`

### Option 3: Hybrid (Recommended for Now)

**Keep Streamlit separate** (for direct UI access):
- Streamlit app on Streamlit Cloud: `your-app.streamlit.app`
- MCP server on Railway/Render: `your-api.railway.app/mcp`

Both share the same backend code (document_processor, workflow_engine, etc.)

---

## 🎯 Tool Descriptions

### 1. research_legal_question

**What it does:**
- Searches uploaded documents
- Retrieves top relevant chunks
- Uses Claude to generate cited answer
- Returns formatted answer with sources

**When to use:**
- Quick legal research questions
- Need cited answers fast
- Don't need full formal memo

**Example:**
```json
{
  "question": "What is the statute of limitations for breach of contract in California?",
  "num_sources": 10
}
```

### 2. run_litigation_workflow

**What it does:**
- Runs complete 11-phase workflow
- Extracts authorities, validates precedent
- Builds issue tree, applies rules to facts
- Generates formal research memo
- Runs 6 verification tests

**When to use:**
- Need formal research memo
- Want citation verification
- Require authority validation
- Need audit trail

**Example:**
```json
{
  "matter_id": "abc-123",
  "research_question": "Can plaintiff establish breach under CA law?",
  "jurisdictions": ["California", "9th Circuit"],
  "court_level": "trial",
  "matter_posture": "MTD"
}
```

### 3. create_matter

**What it does:**
- Creates new matter in system
- Returns matter_id for future use

**When to use:**
- Starting new legal work
- Need to organize documents

### 4. list_matters

**What it does:**
- Lists all available matters
- Shows document counts, history

**When to use:**
- User needs to find a matter_id
- Overview of current work

### 5. get_workflow_status

**What it does:**
- Shows workflow progress
- Phase-by-phase status
- Error messages if failed

**When to use:**
- Check on long-running workflow
- Debug failures

### 6. get_workflow_memo

**What it does:**
- Retrieves completed memo
- Includes authority table
- Shows verification results

**When to use:**
- Workflow completed successfully
- Need final deliverable

---

## 🐛 Troubleshooting

### "Cannot connect to server"

**Check:**
1. MCP server is running (`python legal_assistant_mcp.py`)
2. Ngrok tunnel is active
3. URL in ChatGPT matches ngrok URL
4. Environment variables set correctly

### "Tool call failed"

**Check:**
1. API key is set (`ANTHROPIC_API_KEY`)
2. Documents are uploaded in Streamlit app
3. Matter exists (for workflow tools)
4. Check MCP server logs for errors

### "No documents found"

**Solution:**
- Upload documents through Streamlit app first
- Documents are stored in local file system
- MCP server reads from same storage

### "Workflow timeout"

**Note:**
- Workflows take 2-5 minutes
- ChatGPT may show interim progress
- Use `get_workflow_status` to check

---

## 📈 Next Steps (Phase 2: Custom UI)

After Phase 1 works, you can add:

1. **Custom Widgets**: Render workflow progress in custom UI
2. **Interactive Forms**: Better input collection
3. **Rich Displays**: Format memos with styling
4. **Document Viewer**: Show source documents inline

**This requires:**
- Creating HTML/React components
- Registering resources in MCP server
- Adding `_meta["openai/outputTemplate"]` to tool responses

---

## 🔐 Security Considerations

### Current Setup (Development)

- **No authentication** - MCP server is open
- **Local-only** - Only accessible via tunnel
- **OK for testing** - Not production-ready

### Production Requirements

Will need to add:

1. **OAuth 2.1 with PKCE**: User authentication
2. **Per-user data isolation**: Each user sees only their matters
3. **Rate limiting**: Prevent abuse
4. **Secure storage**: Encrypt sensitive data
5. **Privacy policy**: Required for app submission

---

## 📝 File Structure

After integration, your project should have:

```
project/
├── app.py                      # Streamlit UI
├── legal_assistant_mcp.py      # MCP server (NEW)
├── document_processor.py
├── matter_manager.py
├── workflow_engine.py
├── litigation_workflow.py
├── workflow_verification.py
├── workflow_exports.py
├── requirements.txt            # Updated with MCP deps
├── .env                        # Environment variables
└── README.md
```

---

## ✅ Testing Checklist

- [ ] MCP server starts without errors
- [ ] MCP Inspector shows all 6 tools
- [ ] Ngrok tunnel is active
- [ ] ChatGPT connector added successfully
- [ ] `create_matter` tool works
- [ ] `list_matters` returns created matters
- [ ] `research_legal_question` returns cited answers
- [ ] `run_litigation_workflow` completes (or fails gracefully)
- [ ] `get_workflow_status` shows progress
- [ ] `get_workflow_memo` retrieves completed memos

---

## 🎯 Success Metrics

You'll know Phase 1 is successful when:

1. ✅ Users can create matters via ChatGPT
2. ✅ Users can run legal research via conversation
3. ✅ Workflows execute and return memos in chat
4. ✅ All tool calls work consistently
5. ✅ Error messages are clear and actionable

---

## 📞 Support

**MCP Protocol:**
- Docs: https://modelcontextprotocol.io/
- GitHub: https://github.com/modelcontextprotocol

**Apps SDK:**
- Docs: https://developers.openai.com/apps-sdk/
- Examples: https://github.com/openai/openai-apps-sdk-examples

**Your Legal Assistant:**
- Test locally before connecting to ChatGPT
- Check logs in both Streamlit app and MCP server
- Use MCP Inspector for debugging tool responses

---

## 🚀 Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY="your-key"

# 3. Start MCP server
python legal_assistant_mcp.py &

# 4. Start ngrok
ngrok http 8787

# 5. Copy ngrok URL and set environment
export MCP_ALLOWED_HOSTS="abc123.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://abc123.ngrok-free.app"

# 6. Restart MCP server
pkill -f legal_assistant_mcp
python legal_assistant_mcp.py &

# 7. Connect in ChatGPT
# Add connector: https://abc123.ngrok-free.app/mcp

# 8. Test!
# Ask ChatGPT: "Create a matter called Test Matter for client Test Client"
```

You're now ready to use your legal assistant directly in ChatGPT! 🎉
