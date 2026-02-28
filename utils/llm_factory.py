"""
llm_factory.py — LLM backend factory.

Returns the configured LangChain LLM based on the LLM_PROVIDER env var.
Supports: Ollama (local), Groq (cloud), OpenAI-compatible, MockLLM (demo).
"""

import json
import re
from typing import Any, Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from app.config import config


# ─────────────────────────────────────────────────────────────────────────────
# Mock LLM — deterministic responses for demo/testing without any API keys
# ─────────────────────────────────────────────────────────────────────────────
class MockLLM(BaseChatModel):
    """
    A deterministic mock LLM for demo and testing purposes.
    Detects context from system/human messages and returns appropriate mock responses.
    Does NOT require any API key or external service.
    """

    model_name: str = "mock-llm-v1"

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        combined = " ".join(m.content for m in messages if hasattr(m, "content")).lower()

        # Route based on context clues in the prompt
        if '"emotion"' in combined and '"risk_level"' in combined:
            # Distress analysis context — detect risk from keywords
            response_text = self._mock_distress_analysis(combined)
        elif "crisis" in combined and ("hotline" in combined or "resources" in combined or "emergency" in combined):
            response_text = self._mock_crisis_response()
        elif "coping" in combined or "support tool" in combined or "grounding" in combined or "breathing" in combined:
            response_text = self._mock_support_response(combined)
        elif "disclaimer" in combined or "format" in combined or "routing path" in combined:
            response_text = self._mock_format_response(combined)
        else:
            response_text = self._mock_generic_response()

        generation = ChatGeneration(message=AIMessage(content=response_text))
        return ChatResult(generations=[generation])

    def _mock_distress_analysis(self, context: str) -> str:
        """Return structured JSON matching distress level from context keywords."""
        # Critical / high risk
        if any(kw in context for kw in [
            "end it all", "kill myself", "suicide", "suicidal", "don't want to live",
            "i have a plan", "ending my life", "want to die", "no reason to live"
        ]):
            return json.dumps({"emotion": "hopelessness", "risk_level": "critical", "confidence": 0.96})

        if any(kw in context for kw in [
            "hurt myself", "self-harm", "meaningless", "worthless and disappear",
            "no one would miss", "no point", "give up on everything"
        ]):
            return json.dumps({"emotion": "hopelessness", "risk_level": "high", "confidence": 0.89})

        # Moderate
        if any(kw in context for kw in [
            "worthless", "nobody cares", "i'm a failure", "hopeless", "can't go on",
            "everything is pointless", "lost", "nothing matters"
        ]):
            return json.dumps({"emotion": "sadness", "risk_level": "moderate", "confidence": 0.82})

        # Low risk
        if any(kw in context for kw in [
            "stressed", "anxious", "nervous", "overwhelmed", "worried", "exhausted",
            "tired", "deadline", "work", "pressure", "busy"
        ]):
            return json.dumps({"emotion": "stress", "risk_level": "low", "confidence": 0.91})

        # Default
        return json.dumps({"emotion": "neutral", "risk_level": "low", "confidence": 0.70})

    def _mock_crisis_response(self) -> str:
        return (
            "I hear you, and I want you to know that what you're feeling right now matters deeply. "
            "You are not alone in this moment.\n\n"
            "Please reach out to a crisis line right now — they're available 24/7 and are trained "
            "to support people going through exactly what you're experiencing:\n\n"
            "📞 **988 Suicide & Crisis Lifeline** — Call or text **988** (US, available 24/7)\n"
            "💬 **Crisis Text Line** — Text HOME to **741741**\n\n"
            "If you are in immediate danger, please call **911** or go to your nearest emergency room.\n\n"
            "Is there someone you trust — a friend, family member, or counselor — you could reach out "
            "to right now? You don't have to face this alone.\n\n"
            "I care about what happens to you. Please make that call."
        )

    def _mock_support_response(self, context: str) -> str:
        if "stress" in context or "overwhelm" in context or "deadline" in context:
            return (
                "It sounds like you're carrying a lot right now, and it makes complete sense that you're "
                "feeling the pressure. That kind of stress is real and valid.\n\n"
                "Here are a couple of things that might help right now:\n\n"
                "**🔲 Box Breathing** — When stress spikes, your nervous system needs a signal that you're safe. "
                "Try breathing in for 4 counts, holding for 4, out for 4, hold for 4. Do this 4-6 times. "
                "Even one round can take the edge off.\n\n"
                "**📝 Worry Time** — Set aside 15 minutes today as your dedicated 'worry slot.' "
                "When anxious thoughts surface before then, gently note them and save them for that window. "
                "This keeps stress from spreading across your whole day.\n\n"
                "**🚶 Mindful Walk** — Even 10 minutes outside, phone in pocket, focusing on your senses "
                "can meaningfully reset your nervous system.\n\n"
                "You're doing better than you think. One thing at a time."
            )
        elif "sad" in context or "hopeless" in context or "worth" in context:
            return (
                "I'm really glad you reached out. What you're feeling sounds incredibly heavy, "
                "and it takes courage to put it into words.\n\n"
                "**💭 The Friend Test** — Try this: imagine your closest friend told you exactly what "
                "you just told me. What would you say to them? Chances are, you'd be kinder to them "
                "than you're being to yourself right now. You deserve that same compassion.\n\n"
                "**📓 Emotion Dump** — Set a timer for 10 minutes and write everything you're feeling — "
                "no filter, no judgment. Getting it out of your head and onto a page can bring surprising relief.\n\n"
                "**🌬️ 4-7-8 Breathing** — Breathe in for 4, hold for 7, exhale for 8. It activates "
                "your body's calming response almost immediately.\n\n"
                "You matter. This feeling is not permanent, even when it feels like it is."
            )
        return (
            "Thank you for sharing what you're going through. Let's try something grounding.\n\n"
            "**👁️ 5-4-3-2-1 Grounding** — Notice 5 things you can see, 4 you can touch, "
            "3 you can hear, 2 you can smell, 1 you can taste. This brings you back to the present moment.\n\n"
            "**🔲 Box Breathing** — In for 4, hold for 4, out for 4, hold for 4. Repeat a few times.\n\n"
            "You're not alone in this. Small steps matter."
        )

    def _mock_format_response(self, context: str) -> str:
        # Extract the agent response section if present
        if "agent response to format:" in context:
            parts = context.split("agent response to format:")
            if len(parts) > 1:
                core = parts[1].split("---")[0].strip()
                return core[:1500]  # Return trimmed version
        return "I'm here with you. Please take a moment to breathe."

    def _mock_generic_response(self) -> str:
        return "I'm here to support you. Could you tell me a bit more about how you're feeling?"

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        return self._generate(messages, stop, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Factory
# ─────────────────────────────────────────────────────────────────────────────
def get_llm(temperature: float = 0.3) -> BaseChatModel:
    """
    Return the configured LLM instance based on LLM_PROVIDER env var.

    Providers:
      - "mock"   → MockLLM (no API key, deterministic demo responses)
      - "ollama" → Ollama running locally (requires `ollama serve`)
      - "groq"   → Groq cloud API (requires GROQ_API_KEY)
      - "openai" → OpenAI or compatible API (requires OPENAI_API_KEY)
    """
    provider = config.LLM_PROVIDER.lower()

    if provider == "mock":
        return MockLLM()

    elif provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=config.MODEL_NAME,
                base_url=config.OLLAMA_BASE_URL,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError(
                "langchain-community is required for Ollama. Run: pip install langchain-community"
            )

    elif provider == "groq":
        try:
            from langchain_groq import ChatGroq
            if not config.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY must be set in .env when using LLM_PROVIDER=groq")
            return ChatGroq(
                api_key=config.GROQ_API_KEY,
                model=config.MODEL_NAME,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError(
                "langchain-groq is required for Groq. Run: pip install langchain-groq"
            )

    elif provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if not config.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY must be set in .env when using LLM_PROVIDER=gemini")
            
            # Default to gemini-1.5-flash if not specified or for better hackathon speed
            model = config.MODEL_NAME if config.MODEL_NAME else "gemini-1.5-flash"
            
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=config.GOOGLE_API_KEY,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai is required for Gemini. Run: pip install langchain-google-genai"
            )

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY must be set in .env when using LLM_PROVIDER=openai")
            return ChatOpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL,
                model=config.MODEL_NAME,
                temperature=temperature,
            )
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI. Run: pip install langchain-openai"
            )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. Must be one of: mock, ollama, groq, openai"
        )
