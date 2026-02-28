"""
retrieval_agent.py — Agent 2.7: Knowledge Retrieval Assistant (RAG)

Responsibilities:
  - Queries the FAISS vector store for clinically relevant context.
  - Searches based on the current user message and detected distress.
  - Enriches the state with retrieved knowledge for the SupportStrategyAgent.
"""

from app.state import MentalHealthState
from utils.vector_store import query_knowledge_base

def retrieval_agent(state: MentalHealthState) -> MentalHealthState:
    """
    LangGraph node: Retrieval Agent.

    Queries the vector store and adds context to the shared state.
    This node is only triggered for 'moderate' risk levels.
    """
    query = f"emotion: {state.get('emotion', 'distress')} user_message: {state.get('user_message', '')}"
    
    print(f"[RetrievalAgent] 🔍 Searching knowledge base for: '{state.get('emotion')}' context...")
    
    # Query the local FAISS index
    context = query_knowledge_base(query, k=2)
    
    if context:
        print(f"[RetrievalAgent] ✅ Found relevant context ({len(context)} chars).")
        # Store context in state for the support agent to use
        state["retrieved_context"] = context
    else:
        print("[RetrievalAgent] ⚠️ No specific knowledge found. Using general support.")
        state["retrieved_context"] = ""

    return state
