"""FastAPI backend for the Multi-Agent Business Assistant."""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

# We import the handle_message orchestrator function
from agents.orchestrator_agent import handle_message

app = FastAPI(title="Multi-Agent Business Assistant API")

# Ensure the static directory exists before mounting
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    error: str | None = None


@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the main HTML page."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Handle chat messages from the UI."""
    try:
        # If Azure credentials are missing, provide a friendly fallback for the demo UI
        if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
            # Simple mock response for UI testing
            import time
            time.sleep(1) # simulate thinking
            
            mock_text = req.message.lower()
            if "invoice" in mock_text:
                return ChatResponse(response="I checked with the Finance agent. The invoice is currently marked as **Paid** in our mock system.\n\n*(Note: Azure credentials not configured, this is a UI preview).*")
            elif "quote" in mock_text or "deal" in mock_text:
                 return ChatResponse(response="The Sales agent found the quote. It's in the draft stage.\n\n*(Note: Azure credentials not configured, this is a UI preview).*")
            else:
                return ChatResponse(response="I'm running in UI Preview mode because Azure credentials weren't found in the `.env` file. To connect me to the real agents, please add your Azure AI Foundry connection string!\n\nYou can test the UI by asking about an 'invoice' or a 'quote'.")

        
        # Real Orchestration
        response = handle_message(req.session_id, req.message)
        return ChatResponse(response=response)
        
    except Exception as e:
        return ChatResponse(response=f"An error occurred: {str(e)}", error=str(e))
