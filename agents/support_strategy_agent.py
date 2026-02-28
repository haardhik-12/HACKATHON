"""
support_strategy_agent.py — Agent 3: Support & Coping Tools Selector

Responsibilities:
  - Loads the support_library.json
  - Calls LLM to select the most relevant coping tools for the user's state
  - Formats a structured, empathetic support response
  - Enforces: NO diagnosis, NO medical treatment advice
"""

import json
import os
from langchain_core.messages import SystemMessage, HumanMessage

from app.state import MentalHealthState
from app.config import config
from utils.llm_factory import get_llm
from utils.prompt_templates import SUPPORT_STRATEGY_PROMPT
from prompts import SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT
from utils.safety_filter import sanitize_response


def _load_support_library() -> dict:
    """Load and return the support tools library from JSON."""
    try:
        with open(config.SUPPORT_LIBRARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[SupportStrategyAgent] Error loading support library: {e}")
        return {"tools": {}}


def _build_tools_summary(library: dict) -> str:
    """
    Build a concise summary of available tools to include in the LLM prompt.
    Lists tool names, descriptions, and best-for conditions.
    """
    tools = library.get("tools", {})
    lines = []
    for tool_id, tool_data in tools.items():
        name = tool_data.get("name", tool_id)
        description = tool_data.get("description", "")
        best_for = ", ".join(tool_data.get("best_for", []))
        lines.append(f"• [{tool_id}] {name}: {description} (Best for: {best_for})")
    return "\n".join(lines)


def _extract_tool_ids(response: str, library: dict) -> list:
    """
    Extract tool IDs mentioned in the LLM response by matching against
    the known tool keys in the library.
    """
    known_tools = list(library.get("tools", {}).keys())
    mentioned = []
    for tool_id in known_tools:
        if tool_id in response.lower():
            mentioned.append(tool_id)
    return mentioned if mentioned else ["grounding"]  # Default fallback


def support_strategy_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Support Strategy Agent.

    Selects relevant coping tools based on the user's emotional state
    and formats a warm, practical support response.
    """
    library = _load_support_library()
    tools_summary = _build_tools_summary(library)

    llm = get_llm(temperature=0.6)  # Higher temp for more natural, varied responses

    # Build prompt with current emotional context
    prompt = SUPPORT_STRATEGY_PROMPT.format(
        emotion=state.get("emotion", "neutral"),
        risk_level=state.get("risk_level", "low"),
        user_message=state.get("user_message", ""),
        support_tools_summary=tools_summary,
    )

    # Call LLM
    try:
        messages = [
            SystemMessage(content=SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        raw_response = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"[SupportStrategyAgent] LLM error: {e}. Using fallback response.")
        raw_response = (
            "I'm here with you. Let's try something simple together — "
            "take three slow, deep breaths right now. In for 4 counts, out for 4 counts. "
            "You're not alone in this."
        )

    # Safety sanitization
    safe_response = sanitize_response(raw_response)

    # Extract which tool IDs were used
    selected_tools = _extract_tool_ids(raw_response, library)

    print(f"[SupportStrategyAgent] → Selected tools: {selected_tools}")

    state["selected_tools"] = selected_tools
    state["support_response"] = safe_response
    state["routing_path"] = "support"

    return state
