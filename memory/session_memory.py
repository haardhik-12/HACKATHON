"""
session_memory.py — In-memory session store with emotion trend analysis.

Stores conversation histories and emotion records per session_id.
In production, replace the in-memory dict with Redis or a database.
"""

import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.state import MentalHealthState, EmotionRecord


# Thread-safe in-memory session store
_store: Dict[str, MentalHealthState] = {}
_lock = threading.Lock()

# Risk level severity map for trend analysis
_RISK_SEVERITY: Dict[str, int] = {
    "low": 1,
    "moderate": 2,
    "high": 3,
    "critical": 4,
}


def load_session(session_id: str) -> Optional[MentalHealthState]:
    """
    Retrieve a session's state by session_id.
    Returns None if session doesn't exist.
    """
    with _lock:
        return _store.get(session_id)


def save_session(state: MentalHealthState) -> None:
    """Persist the current state back to memory."""
    with _lock:
        _store[state["session_id"]] = state


def create_session(session_id: str, country: str = "US", consent: bool = False) -> MentalHealthState:
    """
    Initialize a fresh session state.
    Called when a new session_id arrives for the first time.
    """
    initial_state: MentalHealthState = {
        "session_id": session_id,
        "consent_given": consent,
        "user_message": "",
        "country": country,
        "conversation_history": [],
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
    save_session(initial_state)
    return initial_state


def record_emotion(state: MentalHealthState) -> MentalHealthState:
    """
    Append the current emotion/risk snapshot to emotion_history (only if consent given).
    Then run trend detection and attach a warning if distress is worsening.
    """
    if not state.get("consent_given", False):
        return state

    record: EmotionRecord = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emotion": state["emotion"],
        "risk_level": state["risk_level"],
        "confidence": state["confidence"],
    }

    history = list(state.get("emotion_history", []))
    history.append(record)
    state["emotion_history"] = history

    # Run trend analysis
    state["trend_warning"] = detect_worsening_trend(history)

    return state


def detect_worsening_trend(history: List[EmotionRecord], window: int = 5) -> Optional[str]:
    """
    Analyze the last `window` emotion records for a worsening pattern.

    Returns a warning string if distress is escalating, otherwise None.

    Logic:
    - Take the most recent `window` entries (or all if fewer).
    - Compare average severity score of the first half vs second half.
    - If the second half average is meaningfully higher → worsening trend.
    """
    if len(history) < 3:
        return None  # Not enough data

    recent = history[-window:]
    scores = [_RISK_SEVERITY.get(r["risk_level"], 1) for r in recent]

    mid = len(scores) // 2
    first_half_avg = sum(scores[:mid]) / max(len(scores[:mid]), 1)
    second_half_avg = sum(scores[mid:]) / max(len(scores[mid:]), 1)

    # Worsening if the more recent half is significantly higher
    if second_half_avg - first_half_avg >= 1.0:
        return (
            "⚠️ I've noticed that your distress level has been increasing over our recent conversations. "
            "It may be a good time to reach out to a mental health professional for additional support."
        )

    # Also warn if sustained moderate/high risk
    if all(s >= 2 for s in scores[-3:]):
        return (
            "I've noticed you've been experiencing ongoing emotional difficulty. "
            "Speaking with a counselor or therapist could provide more personalized support."
        )

    return None


def delete_session(session_id: str) -> bool:
    """
    Remove a session from the store (user privacy / right to delete).
    Returns True if session existed, False otherwise.
    """
    with _lock:
        existed = session_id in _store
        _store.pop(session_id, None)
        return existed


def get_emotion_history(session_id: str) -> List[EmotionRecord]:
    """Return just the emotion history list for a given session."""
    session = load_session(session_id)
    if session is None:
        return []
    return session.get("emotion_history", [])


def list_sessions() -> List[str]:
    """Return all active session IDs (for admin/debug use)."""
    with _lock:
        return list(_store.keys())
