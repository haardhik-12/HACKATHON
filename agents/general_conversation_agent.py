"""
general_conversation_agent.py — Agent 2.5: General Conversation & Chit-Chat

Responsibilities:
  - Handles non-clinical greetings, introductions, and general conversation.
  - Provides short, warm, and friendly responses.
  - Does NOT suggest coping tools or medical advice.
  - Aimed at keeping the interaction natural and low-friction for simple messages.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from app.state import MentalHealthState
from utils.llm_factory import get_llm
from utils.prompt_templates import GENERAL_CONVERSATION_PROMPT
from utils.safety_filter import sanitize_response


def general_conversation_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: General Conversation Agent.

    Provides a friendly, non-clinical response for greetings and introductions.
    """
    llm = get_llm(temperature=0.7)

    # Build the prompt
    prompt = GENERAL_CONVERSATION_PROMPT.format(
        user_message=state.get("user_message", "")
    )

    # Call LLM
    try:
        messages = [
            SystemMessage(content=(
                "You are a friendly, warm mental wellness companion. "
                "Keep your responses very short and natural. "
                "Do not provide medical advice or suggest coping tools."
            )),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        raw_response = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"[GeneralConvAgent] LLM error: {e}. Using fallback.")
        raw_response = "Hi there! It's good to hear from you. How are you doing today?"

    # Safety pass (though highly unlikely to trigger for general chat)
    safe_response = sanitize_response(raw_response)

    print(f"[GeneralConvAgent] → Response length: {len(safe_response)} chars")

    state["general_response"] = safe_response
    state["routing_path"] = "normal_chat"

    return state
