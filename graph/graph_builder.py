"""
graph_builder.py — LangGraph Multi-Agent Graph Definition

This module constructs and compiles the LangGraph StateGraph that
orchestrates all 5 agents with conditional routing based on risk level.

Graph Flow:
  START
    → conversation_agent          [Loads/updates session & history]
    → distress_analysis_agent     [Classifies emotion, risk_level, confidence]
    → risk_router (conditional)   [Pure function — no LLM call]
         ├─ "crisis"  → crisis_escalation_agent  → response_generator_agent → END
         └─ "support" → support_strategy_agent   → response_generator_agent → END
"""

from langgraph.graph import StateGraph, START, END

from app.state import MentalHealthState
from agents.conversation_agent import conversation_agent
from agents.distress_analysis_agent import distress_analysis_agent
from agents.support_strategy_agent import support_strategy_agent
from agents.crisis_escalation_agent import crisis_escalation_agent
from agents.general_conversation_agent import general_conversation_agent
from agents.retrieval_agent import retrieval_agent
from agents.response_generator_agent import response_generator_agent


# ─────────────────────────────────────────────────────────────────────────────
# Risk Router — Conditional Edge Function (No LLM)
# ─────────────────────────────────────────────────────────────────────────────
def risk_router(state: MentalHealthState) -> str:
    """
    LangGraph conditional routing function.

    Reads risk_level from state and returns the name of the next node.
    This is a pure function — no LLM call, no side effects.

    Returns:
      "crisis"  — for risk_level == "high" or "critical"
      "support" — for risk_level == "low" or "moderate"
    """
    risk_level = state.get("risk_level", "low").lower()
    emotion = state.get("emotion", "neutral").lower()

    if risk_level in ("high", "critical"):
        print(f"[RiskRouter] ⚠️  Routing to CRISIS AGENT (risk_level={risk_level})")
        return "crisis"

    # If risk is low AND emotion is neutral, route to general chat
    if risk_level == "low" and emotion == "neutral":
        print(f"[RiskRouter] 👋 Routing to GENERAL CONVERSATION (emotion=neutral)")
        return "normal_chat"

    print(f"[RiskRouter] ✅ Routing to SUPPORT AGENT (risk_level={risk_level}, emotion={emotion})")
    return "support"


# ─────────────────────────────────────────────────────────────────────────────
# Graph Builder
# ─────────────────────────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph.

    Returns a compiled graph ready to be invoked with a MentalHealthState dict.
    """
    # Create the graph with our shared state type
    graph = StateGraph(MentalHealthState)

    # ── Add agent nodes ───────────────────────────────────────────────────────
    graph.add_node("conversation_agent", conversation_agent)
    graph.add_node("distress_analysis_agent", distress_analysis_agent)
    graph.add_node("general_conversation_agent", general_conversation_agent)
    graph.add_node("retrieval_agent", retrieval_agent)
    graph.add_node("support_strategy_agent", support_strategy_agent)
    graph.add_node("crisis_escalation_agent", crisis_escalation_agent)
    graph.add_node("response_generator_agent", response_generator_agent)

    # ── Define edges ──────────────────────────────────────────────────────────

    # Entry: START → conversation_agent
    graph.add_edge(START, "conversation_agent")

    # conversation_agent → distress_analysis_agent (always)
    graph.add_edge("conversation_agent", "distress_analysis_agent")

    # distress_analysis_agent → risk_router (conditional fork)
    graph.add_conditional_edges(
        "distress_analysis_agent",
        risk_router,
        {
            "crisis": "crisis_escalation_agent",
            "support": "retrieval_agent",
            "normal_chat": "general_conversation_agent",
        }
    )

    # Route retrieval_agent to support_strategy_agent
    graph.add_edge("retrieval_agent", "support_strategy_agent")

    # All paths converge at response_generator_agent
    graph.add_edge("crisis_escalation_agent", "response_generator_agent")
    graph.add_edge("support_strategy_agent", "response_generator_agent")
    graph.add_edge("general_conversation_agent", "response_generator_agent")

    # Final node → END
    graph.add_edge("response_generator_agent", END)

    # ── Compile ───────────────────────────────────────────────────────────────
    compiled = graph.compile()

    print("[GraphBuilder] ✅ LangGraph compiled successfully.")
    print("[GraphBuilder] Flow: START → conversation → distress_analysis → [risk_router]")
    print("[GraphBuilder]         ├── crisis → crisis_escalation → response_generator → END")
    print("[GraphBuilder]         ├── normal_chat → general_conversation → response_generator → END")
    print("[GraphBuilder]         └── support → retrieval → support_strategy → response_generator → END")

    return compiled


# Singleton compiled graph instance — imported by FastAPI and demo scripts
mental_health_graph = build_graph()
