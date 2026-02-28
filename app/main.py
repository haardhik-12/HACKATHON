"""
main.py — FastAPI Web Server for Mental Health Support System.

Provides endpoints for:
  - POST /chat: Send a message to the LangGraph multi-agent system.
  - GET /session/{session_id}/history: Retrieve emotional history & trends.
  - DELETE /session/{session_id}: Remove all session data (GDPR/Privacy).
  - GET /health: Simple health check.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid

from app.config import config
from app.schemas import (
    ChatRequest, ChatResponse, HealthResponse,
    EmotionHistoryResponse, SessionDeleteResponse, DistressAnalysis
)
from app.state import MentalHealthState
from graph.graph_builder import mental_health_graph
from memory.session_memory import (
    load_session, delete_session, get_emotion_history
)

# ── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="AI Mental Health Support & Crisis Coordination System",
    description="A multi-agent production-ready system for empathetic support and crisis escalation.",
    version="1.0.0",
)

# Enable CORS for hackathon frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "llm_provider": config.LLM_PROVIDER
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Primary endpoint for user interaction.
    Runs the multi-agent LangGraph and returns the safe, formatted response.
    """
    try:
        # Initialize input state
        initial_input: MentalHealthState = {
            "session_id": request.session_id,
            "user_message": request.message,
            "country": request.country,
            "consent_given": request.consent,
            "conversation_history": [],  # Filled by conversation_agent
            "emotion": "neutral",
            "risk_level": "low",
            "confidence": 0.0,
            "routing_path": "support",
            "selected_tools": [],
            "support_response": "",
            "crisis_response": "",
            "final_response": "",
            "emotion_history": [],
            "trend_warning": None,
        }

        # Invoke the LangGraph
        # The graph handles loading existing session state, analysis, routing, and response generation
        final_state = mental_health_graph.invoke(initial_input)

        # Build response
        return {
            "session_id": final_state["session_id"],
            "response": final_state["final_response"],
            "analysis": {
                "emotion": final_state["emotion"],
                "risk_level": final_state["risk_level"],
                "confidence": final_state["confidence"],
                "routing_path": final_state["routing_path"]
            },
            "selected_tools": final_state.get("selected_tools", []),
            "trend_warning": final_state.get("trend_warning")
        }

    except Exception as e:
        print(f"[API Error] Details: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request.")


@app.get("/session/{session_id}/history", response_model=EmotionHistoryResponse)
async def get_history(session_id: str):
    """
    Retrieve the emotional history and detected trends for a specific session.
    """
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    history = get_emotion_history(session_id)
    
    return {
        "session_id": session_id,
        "emotion_history": history,
        "trend_warning": session.get("trend_warning"),
        "total_records": len(history)
    }


@app.delete("/session/{session_id}", response_model=SessionDeleteResponse)
async def clear_session(session_id: str):
    """
    Permanently delete all data associated with a session ID.
    Enables user privacy controls.
    """
    deleted = delete_session(session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "session_id": session_id,
        "deleted": True,
        "message": "Session data has been permanently cleared."
    }

# ── Main Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # In development: uvicorn app.main:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
