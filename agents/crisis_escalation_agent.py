"""
crisis_escalation_agent.py — Agent 4: Crisis Escalation (High/Critical Risk)

Responsibilities:
  - Activated ONLY for high or critical risk levels (via LangGraph conditional routing)
  - Loads country-appropriate crisis hotline resources
  - Calls LLM to generate a calm, empathetic crisis response
  - Always provides hotlines, trusted-person encouragement, and emergency services info
  - Enforces tone: calm, supportive, non-judgmental, non-harmful

This agent OVERRIDES all support responses when activated.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage

from app.state import MentalHealthState
from app.config import config
from utils.llm_factory import get_llm
from utils.prompt_templates import CRISIS_ESCALATION_PROMPT
from utils.safety_filter import sanitize_response, contains_harmful_content


def _load_crisis_resources() -> dict:
    """Load crisis resources from JSON file."""
    try:
        with open(config.CRISIS_RESOURCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[CrisisEscalationAgent] Error loading crisis resources: {e}")
        return {}


def _format_crisis_resources(country_code: str, resources: dict) -> tuple[str, str]:
    """
    Format crisis resources for the given country into a readable string.
    Returns (formatted_resources_text, emergency_number).
    Falls back to GLOBAL if country not found.
    """
    country_data = resources.get("resources", {}).get(country_code.upper())
    if not country_data:
        country_data = resources.get("resources", {}).get("GLOBAL", {})

    emergency = country_data.get("emergency", "your local emergency number")
    hotlines = country_data.get("hotlines", [])

    lines = []
    for h in hotlines:
        name = h.get("name", "Crisis Line")
        phone = h.get("phone")
        details = h.get("details", "")
        chat = h.get("chat", "")

        line = f"• **{name}**"
        if phone:
            line += f" — 📞 {phone}"
        if details:
            line += f" ({details})"
        if chat:
            line += f" | 💬 {chat}"
        lines.append(line)

    return "\n".join(lines), emergency


def _hardcoded_crisis_fallback(country_code: str, emergency: str) -> str:
    """
    Emergency fallback in case LLM fails completely.
    Always safe, always has hotline information.
    """
    return (
        f"I hear you, and what you've shared matters deeply. You are not alone right now.\n\n"
        f"Please reach out to a crisis support line — they are available 24/7 and trained to help:\n\n"
        f"For your country, contact a crisis line or call emergency services ({emergency}) if you are in immediate danger.\n\n"
        f"Please also consider reaching out to someone you trust — a friend, family member, or counselor.\n\n"
        f"I'm here with you. You don't have to face this alone."
    )


def crisis_escalation_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Crisis Escalation Agent.

    Generates an immediate, empathetic crisis response with crisis resources.
    This node is only activated when risk_level is 'high' or 'critical'.
    """
    print(f"[CrisisEscalationAgent] ⚠️  CRISIS ACTIVATED — risk_level={state.get('risk_level')}")

    country = state.get("country", config.DEFAULT_CRISIS_COUNTRY).upper()
    crisis_resources = _load_crisis_resources()
    crisis_text, emergency_number = _format_crisis_resources(country, crisis_resources)

    llm = get_llm(temperature=0.3)  # Low temp for consistent, safe crisis responses

    # Build the crisis escalation prompt
    prompt = CRISIS_ESCALATION_PROMPT.format(
        user_message=state.get("user_message", ""),
        risk_level=state.get("risk_level", "high"),
        country=country,
        crisis_resources=crisis_text,
        emergency_number=emergency_number,
    )

    # Call LLM
    try:
        messages = [
            SystemMessage(content=(
                "You are a compassionate crisis support assistant. "
                "Your ONLY goal is to keep the person safe and connect them with professional help. "
                "You will NEVER provide information about methods of self-harm. "
                "Tone: calm, caring, present, non-judgmental."
            )),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        raw_response = response.content if hasattr(response, "content") else str(response)

        # Critical safety check — if LLM somehow returns harmful content, use fallback
        if contains_harmful_content(raw_response):
            print("[CrisisEscalationAgent] ⛔ Harmful content detected in LLM output. Using hardcoded fallback.")
            raw_response = _hardcoded_crisis_fallback(country, emergency_number)

    except Exception as e:
        print(f"[CrisisEscalationAgent] LLM error: {e}. Using hardcoded fallback.")
        raw_response = _hardcoded_crisis_fallback(country, emergency_number)

    # Final safety sanitization pass
    safe_response = sanitize_response(raw_response)

    state["crisis_response"] = safe_response
    state["routing_path"] = "crisis"

    return state
