from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

client = anthropic.Anthropic(api_key=config["api_key"])

class TextRequest(BaseModel):
    text: str
    prompt: str = ""

@app.post("/summarize")
async def summarize(request: TextRequest):
    try:
        message = client.messages.create(
            model=config["model"],
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"Summarize the following text concisely:\n\n{request.text}"
            }]
        )
        return {"result": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/draft")
async def draft(request: TextRequest):
    try:
        message = client.messages.create(
            model=config["model"],
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"Write a draft based on this prompt: {request.prompt}\n\nContext: {request.text}"
            }]
        )
        return {"result": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research")
async def research(request: TextRequest):
    try:
        message = client.messages.create(
            model=config["model"],
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"Research and provide detailed information about: {request.text}"
            }]
        )
        return {"result": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))