# ChatGPT Integration - Quick Reference

## 🎯 For End Users (Using in ChatGPT)

### Starting a Session

1. Open ChatGPT
2. Click "More" (•••) → "Connectors"
3. Select "Legal Assistant"
4. Start chatting!

### Example Conversations

#### Create a Matter
```
You: I need to work on a new case for ABC Corp
ChatGPT: I'll help you create a matter. What should we call it?
You: "ABC Corp v. XYZ Ltd - Breach of Contract"
ChatGPT: [creates matter] Matter created! ID: abc-123
```

#### Quick Research
```
You: What are the elements of fraud under California law?
ChatGPT: [searches documents, returns cited answer]

**Answer:**
Fraud requires five elements under California law [1][2]:
1. Misrepresentation of material fact [1]
2. Knowledge of falsity [1][2]
...

**Sources:**
[1] Lazar v. Superior Court - Page 45
...
```

#### Run Full Workflow
```
You: Run a litigation workflow for matter abc-123. Question: Can we establish breach of fiduciary duty?
Jurisdictions: California, 9th Circuit
Court level: trial
Posture: MTD

ChatGPT: [runs workflow - takes 2-5 minutes]
✅ Workflow completed!

**Research Memo:**
[Full memo with citations, authority table, analysis]
```

#### Check Status
```
You: What's the status of workflow run xyz-789?
ChatGPT: [shows phase-by-phase progress]
```

### Tips

- **Be specific**: Include jurisdiction, court level, and case posture for workflows
- **Upload first**: Make sure documents are uploaded in Streamlit before research
- **Use matter IDs**: Get from `list matters` command
- **Wait for workflows**: They take 2-5 minutes - ChatGPT will update you

---

## 🔧 For Developers (Deployment)

### Local Development Setup

```bash
# 1. Clone/setup project
cd your-legal-assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.template .env
# Edit .env with your ANTHROPIC_API_KEY

# 4. Start MCP server
python legal_assistant_mcp.py

# 5. In another terminal, start ngrok
ngrok http 8787

# 6. Update .env with ngrok URL
# (get URL from ngrok output)

# 7. Restart MCP server
pkill -f legal_assistant_mcp
python legal_assistant_mcp.py

# 8. Connect in ChatGPT
# Settings → Beta → Developer Mode
# More → Connectors → Add Connector
# URL: https://your-url.ngrok-free.app/mcp
```

### Production Deployment

#### Option 1: Railway.app

```bash
# 1. Create railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python legal_assistant_mcp.py"

# 2. Deploy
railway up
```

#### Option 2: Render.com

```bash
# 1. Create render.yaml
services:
  - type: web
    name: legal-assistant-mcp
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python legal_assistant_mcp.py"
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false

# 2. Deploy via Render dashboard
```

#### Option 3: Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8787
CMD ["python", "legal_assistant_mcp.py"]

# Build and run
docker build -t legal-assistant-mcp .
docker run -p 8787:8787 -e ANTHROPIC_API_KEY=your-key legal-assistant-mcp
```

### Testing Checklist

- [ ] `python legal_assistant_mcp.py` starts without errors
- [ ] Ngrok tunnel shows public URL
- [ ] MCP Inspector connects successfully
- [ ] All 6 tools appear in inspector
- [ ] Test tool: `create_matter` works
- [ ] Test tool: `research_legal_question` returns results
- [ ] ChatGPT connector added
- [ ] End-to-end test in ChatGPT succeeds

---

## 🐛 Common Issues

### "Server not responding"
**Fix:** Check MCP server is running, ngrok is active, URL matches

### "No documents found"
**Fix:** Upload documents through Streamlit app first

### "Matter not found"
**Fix:** Create matter first with `create_matter` tool

### "Workflow timeout"
**Note:** Normal - workflows take 2-5 minutes. Use `get_workflow_status` to check.

### "Tool call failed"
**Fix:** Check MCP server logs for detailed error message

---

## 📊 Tool Quick Reference

| Tool | Purpose | Required Args | Time |
|------|---------|---------------|------|
| `create_matter` | Create new matter | matter_name, client_name | <1s |
| `list_matters` | View all matters | none | <1s |
| `research_legal_question` | Quick research | question | 5-10s |
| `run_litigation_workflow` | Full memo | matter_id, question, jurisdictions, court_level, posture | 2-5min |
| `get_workflow_status` | Check progress | run_id | <1s |
| `get_workflow_memo` | Get final memo | run_id | <1s |

---

## 🎯 Best Practices

### For Users

1. **Create matter first**: Organize work properly
2. **Upload documents in Streamlit**: Before running research
3. **Be patient with workflows**: They're thorough (2-5 min)
4. **Save run IDs**: From workflow responses for later retrieval

### For Developers

1. **Test locally first**: Use MCP Inspector before ChatGPT
2. **Monitor logs**: MCP server shows all tool calls
3. **Handle errors gracefully**: Return clear error messages
4. **Keep Streamlit separate**: Two interfaces to same backend
5. **Version your MCP server**: Track changes as you iterate

---

## 📈 Metrics to Monitor

- **Tool call success rate**: % of successful vs failed calls
- **Workflow completion rate**: % that complete vs fail
- **Average response time**: Per tool
- **Most used tools**: Which get called most often
- **Error patterns**: Common failure reasons

---

## 🚀 What's Next

### Phase 2: Custom UI (Future)

After text-only integration works:

1. **Rich Workflow Display**: Show progress with custom UI
2. **Interactive Forms**: Better input collection
3. **Document Viewer**: Show sources inline
4. **Memo Formatting**: Styled memos in chat

### Features to Add

- **Document upload via ChatGPT**: Upload directly in conversation
- **Multi-matter search**: Search across all matters
- **Collaboration**: Share matters with team
- **Export to Drive**: Save memos to Google Drive

---

## 💡 Pro Tips

1. **Natural language works**: Don't need exact syntax
   - "Research fraud" works as well as formal tool calls

2. **ChatGPT handles context**: 
   - "Run a workflow for that matter" - it knows which one

3. **Follow-up questions**: 
   - After research, ask "What about California specifically?"

4. **Save important run IDs**: 
   - ChatGPT might lose them in long conversations

5. **Use Streamlit for management**: 
   - Upload docs, view detailed artifacts, manage matters

---

## 📞 Getting Help

**MCP Server Issues:**
- Check logs: `tail -f nohup.out` (if running in background)
- Test with Inspector: `npx @modelcontextprotocol/inspector@latest`

**ChatGPT Issues:**
- Verify connector is active (green checkmark)
- Check Developer Mode is enabled
- Try disconnecting and reconnecting

**App Logic Issues:**
- Test directly in Streamlit first
- Verify documents are uploaded
- Check workflow runs work in Streamlit

**Documentation:**
- Apps SDK: https://developers.openai.com/apps-sdk/
- MCP Protocol: https://modelcontextprotocol.io/
- Your Streamlit app logs

---

## ✅ Success Checklist

Setup Complete When:
- [ ] MCP server accessible via public URL
- [ ] ChatGPT connector added and active
- [ ] Can create matters via conversation
- [ ] Can run research and get cited answers
- [ ] Can execute workflows end-to-end
- [ ] Can retrieve completed memos
- [ ] Error messages are clear
- [ ] Response times acceptable (<10s for research, <5min for workflows)

You're ready to use your legal assistant in ChatGPT! 🎉
