"""
session_memory.py — Persistent Session Storage using MongoDB.

Responsibilities:
  - Manages session lifecycle (Create, Load, Update, Delete).
  - Stores conversation history and emotional trend snapshots in MongoDB.
  - Ensures thread-safe access to persistent data.
"""

import time
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection

from app.config import config
from app.state import MentalHealthState
from utils.redactor import redact_message_history

# ── MongoDB Initialization ───────────────────────────────────────────────────

# Singleton MongoDB Client
_mongo_client: Optional[MongoClient] = None
_sessions_collection: Optional[Collection] = None

def get_collection() -> Collection:
    """Returns the MongoDB collection for sessions, initializing if needed."""
    global _mongo_client, _sessions_collection
    
    if _sessions_collection is None:
        if not config.MONGODB_URI:
            # Fallback to local dict for development if no URI provided
            # (Though in your case, we have the URI)
            print("[SessionMemory] ⚠️ MONGODB_URI not found. Persistence is DISABLED.")
            raise ValueError("MONGODB_URI is required for persistent memory.")
            
        _mongo_client = MongoClient(config.MONGODB_URI)
        db = _mongo_client[config.MONGODB_DB_NAME]
        _sessions_collection = db["sessions"]
        
        # Ensure index on session_id for fast lookups
        _sessions_collection.create_index("session_id", unique=True)
        print(f"[SessionMemory] ✅ Connected to MongoDB: {config.MONGODB_DB_NAME}.sessions")
        
    return _sessions_collection

# ── Memory Operations ────────────────────────────────────────────────────────

def create_session(session_id: str, **kwargs) -> Dict[str, Any]:
    """Initialize a new session entry in MongoDB with optional metadata."""
    coll = get_collection()
    
    new_session = {
        "session_id": session_id,
        "conversation_history": [],
        "emotion_history": [],
        "trend_warning": None,
        "last_updated": time.time()
    }
    
    # Merge any metadata (country, consent_given, etc.)
    new_session.update(kwargs)
    
    # Upsert to handle potential re-initialization
    coll.update_one(
        {"session_id": session_id},
        {"$set": new_session},
        upsert=True
    )
    return new_session

def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session data from MongoDB."""
    coll = get_collection()
    return coll.find_one({"session_id": session_id}, {"_id": 0})

def save_session(state: Dict[str, Any]):
    """
    Update an existing session in MongoDB using the current state dictionary.
    """
    session_id = state.get("session_id")
    if not session_id:
        return

    coll = get_collection()
    
    # Redact conversation history before storing
    history = state.get("conversation_history", [])
    redacted_history = redact_message_history(history)

    # We only want to persist key fields, not the entire transient state
    persist_payload = {
        "conversation_history": redacted_history,
        "emotion_history": state.get("emotion_history", []),
        "trend_warning": state.get("trend_warning"),
        "last_updated": time.time()
    }
    
    coll.update_one(
        {"session_id": session_id},
        {"$set": persist_payload},
        upsert=False
    )
    print(f"[SessionMemory] 💾 Saved session {session_id} to MongoDB (PII Redacted).")

def delete_session(session_id: str) -> bool:
    """Permanently delete a session (Privacy/GDPR)."""
    coll = get_collection()
    result = coll.delete_one({"session_id": session_id})
    return result.deleted_count > 0

# ── Emotion Tracking ───────────────────────────────────────────────────────

def record_emotion_snapshot(session_id: str, emotion: str, risk_level: str, confidence: float):
    """
    Append a new emotional snapshot to the session's history in MongoDB.
    Snapshots are used by the ResponseGenerator to detect trends.
    """
    coll = get_collection()
    
    snapshot = {
        "timestamp": time.time(),
        "emotion": emotion,
        "risk_level": risk_level,
        "confidence": confidence
    }
    
    coll.update_one(
        {"session_id": session_id},
        {"$push": {"emotion_history": snapshot}}
    )

def record_emotion(state: MentalHealthState) -> MentalHealthState:
    """
    Compatibility wrapper: extracts data from state and records an emotion snapshot.
    Only records if consent_given is True.
    """
    if not state.get("consent_given", False):
        return state

    session_id = state.get("session_id")
    emotion = state.get("emotion", "neutral")
    risk_level = state.get("risk_level", "low")
    confidence = state.get("confidence", 0.0)

    if session_id:
        record_emotion_snapshot(session_id, emotion, risk_level, confidence)
        
        # Also update the local state's emotion_history for current turn logic
        history = list(state.get("emotion_history", []))
        history.append({
            "timestamp": time.time(),
            "emotion": emotion,
            "risk_level": risk_level,
            "confidence": confidence
        })
        state["emotion_history"] = history
    
    return state

def get_emotion_history(session_id: str) -> List[Dict[str, Any]]:
    """Return the list of emotion snapshots for a session."""
    session = load_session(session_id)
    return session.get("emotion_history", []) if session else []
