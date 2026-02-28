"""
state.py — Shared LangGraph state schema (TypedDict).

This TypedDict is the single source of truth passed between all agents in the graph.
Each agent reads from and writes to this state object.
"""

from typing import TypedDict, List, Optional, Any


class EmotionRecord(TypedDict):
    """A single emotion snapshot stored in emotional history."""
    timestamp: str          # ISO 8601 datetime string
    emotion: str            # e.g., "anxiety", "sadness", "hopelessness"
    risk_level: str         # low | moderate | high | critical
    confidence: float       # 0.0–1.0


class MentalHealthState(TypedDict):
    """
    The complete shared state passed between all LangGraph agents.

    Flow:
      conversation_agent → distress_analysis_agent → risk_router
        ├─ (high/critical) → crisis_escalation_agent → response_generator_agent
        └─ (low/moderate)  → support_strategy_agent  → response_generator_agent
    """

    # ── Session identity ────────────────────────────────────────────────────
    session_id: str                         # Unique session identifier
    consent_given: bool                     # User consented to emotional history storage

    # ── Current input ───────────────────────────────────────────────────────
    user_message: str                       # Latest message from the user
    country: str                            # Country code for crisis resources (US, UK, IN…)

    # ── Conversation history ─────────────────────────────────────────────────
    conversation_history: List[dict]        # List of {"role": "user"|"assistant", "content": str}

    # ── Distress analysis output (from distress_analysis_agent) ─────────────
    emotion: str                            # Detected primary emotion
    risk_level: str                         # low | moderate | high | critical
    confidence: float                       # Classifier confidence score 0.0–1.0

    # ── Routing ─────────────────────────────────────────────────────────────
    routing_path: str                       # "support" | "crisis" — set by risk_router

    # ── Support agent output ─────────────────────────────────────────────────
    selected_tools: List[str]               # Tool IDs selected from support_library.json
    support_response: str                   # Formatted support message
    general_response: str                   # Formatted general/conversational response
    retrieved_context: Optional[str]        # Context fetched from knowledge base (RAG)

    # ── Crisis agent output ──────────────────────────────────────────────────
    crisis_response: str                    # Crisis escalation message with hotlines

    # ── Final response ───────────────────────────────────────────────────────
    final_response: str                     # Safe, formatted, disclaimered final response

    # ── Emotional trend tracking ─────────────────────────────────────────────
    emotion_history: List[EmotionRecord]    # Historical emotion snapshots
    trend_warning: Optional[str]            # Set if worsening trend detected
