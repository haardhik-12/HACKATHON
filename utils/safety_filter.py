"""
safety_filter.py — Output safety layer for all LLM responses.

This module provides:
  - Harmful content detection (keyword + pattern scanning)
  - Diagnosis language removal
  - Disclaimer enforcement
  - Response sanitization

Applied as a final gate before any response reaches the user.
"""

import re
from utils.prompt_templates import STANDARD_DISCLAIMER


# ─────────────────────────────────────────────────────────────────────────────
# Patterns that indicate dangerous or inappropriate content in LLM output
# ─────────────────────────────────────────────────────────────────────────────
_HARMFUL_PATTERNS = [
    # Method information — never acceptable
    r"\bhow to (kill|hang|overdose|cut|poison)\b",
    r"\bstep[s]? (to|for) (suicide|self.harm)\b",
    r"\blethal dose\b",
    r"\bbest way to die\b",
    r"\bpainless (way|method)\b",
    # Encouraging self-harm
    r"\byou should (hurt|harm|kill|end)\b",
    r"\bit('s| is) (okay|fine|understandable) to (hurt|harm|end)\b",
]

# Patterns indicating diagnosis claims
_DIAGNOSIS_PATTERNS = [
    r"\byou have (depression|anxiety disorder|bipolar|schizophrenia|ptsd|ocd|bpd|adhd)\b",
    r"\byou('re| are) (depressed|bipolar|schizophrenic|psychotic)\b",
    r"\bdiagnos(is|ed|e) (you |with )?(with )?(depression|anxiety|bipolar|schizophrenia|ptsd|ocd)\b",
    r"\byou('re| are) suffering from\b",
    r"\byou (have|show|exhibit) symptoms of\b",
]

# Patterns indicating medical/medication advice
_MEDICAL_ADVICE_PATTERNS = [
    r"\btake (medication|antidepressants|pills|prozac|zoloft|xanax|lithium)\b",
    r"\bprescri(be|ption)\b",
    r"\bdosage\b",
    r"\bmedical treatment\b",
    r"\btherapy (for your|to treat your)\b",
]

# Compile all harmful patterns for efficiency
_COMPILED_HARMFUL = [re.compile(p, re.IGNORECASE) for p in _HARMFUL_PATTERNS]
_COMPILED_DIAGNOSIS = [re.compile(p, re.IGNORECASE) for p in _DIAGNOSIS_PATTERNS]
_COMPILED_MEDICAL = [re.compile(p, re.IGNORECASE) for p in _MEDICAL_ADVICE_PATTERNS]


def contains_harmful_content(text: str) -> bool:
    """
    Returns True if the text contains any patterns that should never
    appear in a response (self-harm instructions, method information, etc.).
    """
    return any(pattern.search(text) for pattern in _COMPILED_HARMFUL)


def remove_diagnosis_language(text: str) -> str:
    """
    Removes or softens any diagnosis claims from LLM output.
    Replaces with appropriately cautious phrasing.
    """
    for pattern in _COMPILED_DIAGNOSIS:
        # Replace diagnosis claims with supportive alternatives
        text = pattern.sub(
            "you're going through something that sounds difficult",
            text
        )
    for pattern in _COMPILED_MEDICAL:
        text = pattern.sub(
            "professional support may help",
            text
        )
    return text


def enforce_disclaimer(text: str) -> str:
    """
    Ensures the standard disclaimer is present at the end of the response.
    If already present (case-insensitive), returns text unchanged.
    If missing, appends it.
    """
    disclaimer_marker = "not a substitute for professional medical care"
    if disclaimer_marker.lower() in text.lower():
        return text
    return text + STANDARD_DISCLAIMER


def sanitize_response(text: str) -> str:
    """
    Full sanitization pipeline:
      1. Check for harmful content → replace with safe fallback if found
      2. Remove diagnosis language
      3. Ensure disclaimer is present

    This should be called on ALL LLM outputs before returning to the user.
    """
    if contains_harmful_content(text):
        # Hard override — never pass harmful content through
        text = (
            "I'm really concerned about your safety right now. "
            "Please reach out to a crisis support line immediately — they are there for you 24/7.\n\n"
            "📞 **US**: Call or text **988** (Suicide & Crisis Lifeline)\n"
            "🌍 **International**: Visit https://www.befrienders.org to find your local crisis centre.\n\n"
            "If you are in immediate danger, please call **911** (or your local emergency number)."
        )

    text = remove_diagnosis_language(text)
    text = enforce_disclaimer(text)
    return text


def is_safe_to_send(text: str) -> bool:
    """
    Quick gate check — returns True if the response passes basic safety filters.
    Used before sending to the response generator.
    """
    return not contains_harmful_content(text)
