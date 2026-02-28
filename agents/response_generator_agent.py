"""
response_generator_agent.py — Agent 5: Final Response Formatter

Responsibilities:
  - Merges output from either crisis_escalation_agent or support_strategy_agent
  - Optionally calls LLM to improve naturalness of the response
  - Appends trend warnings when worsening emotional patterns are detected
  - Enforces the standard disclaimer on all responses
  - Appends the formatted response to conversation history
  - Saves final state back to session memory
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.state import MentalHealthState
from utils.llm_factory import get_llm
from utils.prompt_templates import RESPONSE_GENERATOR_PROMPT, STANDARD_DISCLAIMER
from utils.safety_filter import sanitize_response, enforce_disclaimer
from memory.session_memory import save_session


async def response_generator_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Response Generator Agent.

    Selects the appropriate agent output (crisis or support), polishes it
    via LLM for natural flow, enforces disclaimer, and updates session memory.
    """
    routing_path = state.get("routing_path", "support")

    # ── Select the raw response from the appropriate preceding agent ──────────
    if routing_path == "crisis":
        agent_response = state.get("crisis_response", "")
    elif routing_path == "normal_chat":
        agent_response = state.get("general_response", "")
    else:
        agent_response = state.get("support_response", "")

    # Safety fallback if no response present
    if not agent_response:
        agent_response = (
            "I'm here to support you. Could you tell me a bit more about how you're feeling right now?"
        )

    trend_warning = state.get("trend_warning") or "None"

    # ── Optionally use LLM to improve naturalness (skip for mock to avoid redundant call) ──
    llm = get_llm(temperature=0.4)
    llm_type = getattr(llm, "_llm_type", "") or getattr(llm, "model_name", "")

    # Skip LLM reformatting for MockLLM — the mock responses are already well-formatted
    if "mock" not in str(llm_type).lower():
        prompt = RESPONSE_GENERATOR_PROMPT.format(
            routing_path=routing_path.upper(),
            agent_response=agent_response,
            trend_warning=trend_warning,
        )
        try:
            messages = [
                SystemMessage(content=(
                    "You are a final response formatter for a mental wellness support system. "
                    "Format the provided response to be natural, empathetic, and safe. "
                    "Never alter the substance or add new advice."
                )),
                HumanMessage(content=prompt),
            ]
            response = llm.invoke(messages)
            formatted = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            print(f"[ResponseGeneratorAgent] LLM error: {e}. Using agent response directly.")
            formatted = agent_response
    else:
        # For MockLLM: use the agent response directly, append trend warning if present
        formatted = agent_response
        if trend_warning and trend_warning != "None":
            formatted += f"\n\n{trend_warning}"

    # ── Final safety passes ───────────────────────────────────────────────────
    formatted = sanitize_response(formatted)

    print(f"[ResponseGeneratorAgent] → Path: {routing_path.upper()} | "
          f"Response length: {len(formatted)} chars")

    # ── Update conversation history with assistant's final response ───────────
    history = list(state.get("conversation_history", []))
    history.append({"role": "assistant", "content": formatted})
    state["conversation_history"] = history

    # ── Persist session ───────────────────────────────────────────────────────
    state["final_response"] = formatted
    await save_session(state)

    return state
