# Agent System Prompts Documentation

## Overview
This directory contains individual system prompts for each agent in the mental health support multi-agent system. Each prompt is carefully designed to define the agent's role, responsibilities, and behavioral guidelines.

## Prompt Structure

### 1. Conversation Agent (`conversation_agent_prompt.py`)
- **Purpose**: Session management and conversation history
- **LLM Usage**: None (pure state management)
- **Key Features**: 
  - Session persistence
  - Rolling context window maintenance
  - Data integrity

### 2. Distress Analysis Agent (`distress_analysis_agent_prompt.py`)
- **Purpose**: Emotion classification and risk assessment
- **LLM Temperature**: 0.1 (low for consistency)
- **Key Features**:
  - Structured JSON output
  - Risk level definitions
  - Safety-critical keyword detection
  - Conservative escalation principles

### 3. Support Strategy Agent (`support_strategy_agent_prompt.py`)
- **Purpose**: Coping tools selection and emotional support
- **LLM Temperature**: 0.6 (higher for natural responses)
- **Key Features**:
  - Tool matching to emotional states
  - Brief, actionable responses
  - Strict medical advice prohibition
  - Evidence-based coping techniques

### 4. Crisis Escalation Agent (`crisis_escalation_agent_prompt.py`)
- **Purpose**: Emergency response and safety protocols
- **LLM Temperature**: 0.3 (low for safety)
- **Key Features**:
  - Country-specific resource integration
  - Immediate safety prioritization
  - Multiple safety layers
  - Calm, urgent communication style

### 5. Response Generator Agent (`response_generator_agent_prompt.py`)
- **Purpose**: Final response formatting and quality control
- **LLM Temperature**: 0.4 (balanced)
- **Key Features**:
  - Natural language enhancement
  - Disclaimer enforcement
  - Trend warning integration
  - Final safety validation

## Import Structure

All prompts are centrally imported through `__init__.py`:

```python
from prompts import (
    CONVERSATION_AGENT_SYSTEM_PROMPT,
    DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT,
    SUPPORT_STRATEGY_AGENT_SYSTEM_PROMPT,
    CRISIS_ESCALATION_AGENT_SYSTEM_PROMPT,
    RESPONSE_GENERATOR_AGENT_SYSTEM_PROMPT,
)
```

## Usage in Agents

Each agent imports and uses its specific system prompt:

```python
from prompts import DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT

messages = [
    SystemMessage(content=DISTRESS_ANALYSIS_AGENT_SYSTEM_PROMPT),
    HumanMessage(content=user_prompt),
]
```

## Prompt Design Principles

1. **Safety First**: All prompts prioritize user safety and appropriate boundaries
2. **Role Clarity**: Each prompt clearly defines the agent's specific responsibilities
3. **Behavioral Guidelines**: Explicit rules for what the agent should and should not do
4. **Output Specifications**: Clear requirements for response format and content
5. **Context Awareness**: Prompts include relevant context for decision-making

## Maintenance

- Prompts are version-controlled and easily auditable
- Each prompt is in a separate file for focused editing
- Centralized import structure simplifies updates
- Documentation provides clear understanding of each agent's role

## Safety Features

- Multiple content filtering layers
- Fallback responses for LLM failures
- Explicit prohibition of harmful content
- Crisis escalation protocols
- Medical disclaimer enforcement

This modular prompt system allows for easy maintenance, testing, and improvement of individual agent behaviors while maintaining system coherence and safety.
