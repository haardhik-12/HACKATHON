"""
distress_analysis_agent.py — Agent 2: Distress Analysis & Classification

Responsibilities:
  - Calls LLM with a strict JSON prompt to classify emotion and risk
  - Validates and parses the structured JSON output
  - Updates emotion_history and triggers trend detection
  - Returns updated state with emotion, risk_level, confidence
"""

import json
import re
from langchain_core.messages import SystemMessage, HumanMessage

from app.state import MentalHealthState
from utils.llm_factory import get_llm
from utils.prompt_templates import DISTRESS_ANALYSIS_PROMPT
from memory.session_memory import record_emotion


# Fallback if LLM returns malformed JSON
_FALLBACK_ANALYSIS = {
    "emotion": "neutral",
    "risk_level": "low",
    "confidence": 0.5,
}

# Valid values for schema validation
_VALID_EMOTIONS = {
    "anxiety", "sadness", "hopelessness", "anger", "stress",
    "loneliness", "grief", "fear", "numbness", "frustration",
    "shame", "panic", "neutral", "other"
}
_VALID_RISK_LEVELS = {"low", "moderate", "high", "critical"}


def _format_history(history: list, max_turns: int = 5) -> str:
    """Format last N conversation turns for inclusion in the prompt."""
    recent = history[-max_turns * 2:] if len(history) > max_turns * 2 else history
    lines = []
    for turn in recent:
        role = turn.get("role", "user").capitalize()
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No prior conversation."


def _parse_llm_output(raw: str) -> dict:
    """
    Extract and validate JSON from LLM response.
    Handles cases where LLM wraps JSON in markdown code blocks.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    # Find the first JSON object in the output
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return _FALLBACK_ANALYSIS.copy()

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return _FALLBACK_ANALYSIS.copy()

    # Validate and normalize fields
    emotion = str(data.get("emotion", "neutral")).lower()
    risk_level = str(data.get("risk_level", "low")).lower()
    confidence = float(data.get("confidence", 0.5))

    if emotion not in _VALID_EMOTIONS:
        emotion = "other"
    if risk_level not in _VALID_RISK_LEVELS:
        risk_level = "low"
    confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

    return {
        "emotion": emotion,
        "risk_level": risk_level,
        "confidence": confidence,
    }


def distress_analysis_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Distress Analysis Agent.

    Sends user message + conversation history to LLM for risk classification.
    Parses strict JSON output and updates state with emotion/risk data.
    Also records the snapshot in emotion_history for trend tracking.
    """
    llm = get_llm(temperature=0.1)  # Low temperature for consistent classification

    # Build the analysis prompt
    history_text = _format_history(state.get("conversation_history", []))
    prompt = DISTRESS_ANALYSIS_PROMPT.format(
        history=history_text,
        user_message=state["user_message"],
    )

    # Call LLM
    try:
        messages = [
            SystemMessage(content="You are a mental health distress analysis assistant. Always respond with valid JSON only."),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        raw_output = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"[DistressAnalysisAgent] LLM error: {e}. Using fallback.")
        raw_output = json.dumps(_FALLBACK_ANALYSIS)

    # Parse and validate
    analysis = _parse_llm_output(raw_output)

    print(f"[DistressAnalysisAgent] → emotion={analysis['emotion']}, "
          f"risk={analysis['risk_level']}, confidence={analysis['confidence']:.2f}")

    # Update state
    state["emotion"] = analysis["emotion"]
    state["risk_level"] = analysis["risk_level"]
    state["confidence"] = analysis["confidence"]

    # Record emotion snapshot (only if consent given)
    state = record_emotion(state)

    return state
