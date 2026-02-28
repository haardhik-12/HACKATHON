"""
conversation_agent.py — Agent 1: Conversation & Memory Manager

Responsibilities:
  - Loads existing session state (or creates a new one)
  - Appends the user's latest message to conversation history
  - Maintains a rolling context window (last 10 turns)
  - Returns enriched state for downstream agents
"""

from typing import Any
from memory.session_memory import load_session, create_session, save_session
from app.state import MentalHealthState


def conversation_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Conversation Agent.

    Reads the current session from memory, updates conversation history
    with the user's latest message, and returns the merged state.
    """
    session_id = state["session_id"]
    user_message = state["user_message"]
    country = state.get("country", "US")
    consent = state.get("consent_given", False)

    # ── Load or create session ────────────────────────────────────────────────
    existing_session = load_session(session_id)

    if existing_session is None:
        # First time this session — initialize fresh state
        session_state = create_session(
            session_id=session_id,
            country=country,
            consent=consent,
        )
    else:
        # Resume existing session — merge with incoming state
        session_state = existing_session
        # Update consent if newly provided
        if consent and not session_state.get("consent_given"):
            session_state["consent_given"] = True

    # ── Append user message to conversation history ───────────────────────────
    history = list(session_state.get("conversation_history", []))
    history.append({"role": "user", "content": user_message})

    # Keep a rolling window of the last 20 turns (10 exchanges)
    if len(history) > 20:
        history = history[-20:]

    session_state["conversation_history"] = history
    session_state["user_message"] = user_message
    session_state["country"] = country

    # ── Persist updated session ──────────────────────────────────────────────
    save_session(session_state)

    # ── Return merged state for next agent ────────────────────────────────────
    return session_state
