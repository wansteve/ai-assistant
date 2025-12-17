# AI Assistant App

A minimal FastAPI + Streamlit application with three AI-powered features: summarization, drafting, and research.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure API key:**
Edit `config.yaml` and add your Anthropic API key:
```yaml
api_key: "sk-ant-your-actual-key-here"
model: "claude-sonnet-4-20250514"
```

3. **Run the FastAPI backend:**
```bash
uvicorn main:app --reload
```

4. **Run the Streamlit frontend (in a new terminal):**
```bash
streamlit run app.py
```

## Usage

- **Summarize Tab**: Enter text to get a concise summary
- **Draft Tab**: Provide a prompt and optional context to generate content
- **Research Tab**: Enter a topic to get detailed research information

The app will be available at:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:8501

## Files

- `main.py` - FastAPI backend with three endpoints
- `app.py` - Streamlit frontend with three tabs
- `config.yaml` - Configuration for API key and model
- `requirements.txt` - Python dependencies