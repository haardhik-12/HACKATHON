"""
prompts/__init__.py — Centralized system prompts for all agents

This module imports and provides access to all agent system prompts.
Each prompt is carefully designed for the specific agent's role and responsibilities.
"""

# Import all agent system prompts
from .conversation_agent_prompt import CONVERSATION_AGENT_SYSTEM_PROMPT
from .distress_analysis_agent_prompt import DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT
from .support_strategy_agent_prompt import SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT
from .crisis_escalation_agent_prompt import CRISIS_ESCALATION_AGENT_SYSTEM_PROMPT
from .response_generator_agent_prompt import RESPONSE_GENERATOR_AGENT_SYSTEM_PROMPT

# Prompt registry for easy access
AGENT_PROMPTS = {
    "conversation_agent": CONVERSATION_AGENT_SYSTEM_PROMPT,
    "distress_analysis_agent": DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT,
    "support_strategy_agent": SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT,
    "crisis_escalation_agent": CRISIS_ESCALATION_AGENT_SYSTEM_PROMPT,
    "response_generator_agent": RESPONSE_GENERATOR_AGENT_SYSTEM_PROMPT,
}

def get_agent_prompt(agent_name: str) -> str:
    """
    Get the system prompt for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        System prompt string for the agent
        
    Raises:
        KeyError: If agent_name is not found
    """
    return AGENT_PROMPTS[agent_name]

def list_all_prompts() -> dict:
    """Return all available agent prompts."""
    return AGENT_PROMPTS.copy()

# Export all prompts for direct import
__all__ = [
    'CONVERSATION_AGENT_SYSTEM_PROMPT',
    'DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT', 
    'SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT',
    'CRISIS_ESCALATION_AGENT_SYSTEM_PROMPT',
    'RESPONSE_GENERATOR_AGENT_SYSTEM_PROMPT',
    'AGENT_PROMPTS',
    'get_agent_prompt',
    'list_all_prompts'
]
