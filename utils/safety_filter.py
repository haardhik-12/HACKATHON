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


def add_contextual_disclaimer(text: str, context: dict = None) -> str:
    """
    Adds natural, contextual disclaimers based on conversation context.
    
    Args:
        text: The response text
        context: Dictionary with context information like:
                - is_first_message: bool
                - mentions_medical: bool
                - is_crisis: bool
                - routing_path: str
    
    Returns:
        Text with appropriate contextual disclaimer added
    """
    if not context:
        return text
    
    # Don't add disclaimer if it's already present
    disclaimer_marker = "not a substitute for professional medical care"
    if disclaimer_marker.lower() in text.lower():
        return text
    
    # Session start disclaimer
    if context.get('is_first_message', False):
        intro = ("I'm your AI support companion - I'm here to listen and help with coping strategies, "
                "but I'm not a substitute for professional medical care.")
        return f"{intro}\n\n{text}"
    
    # Medical topics disclaimer
    if context.get('mentions_medical', False):
        medical_note = ("While I can offer emotional support and coping tools, I can't provide medical advice "
                       "or prescribe treatments. For that, you'd want to speak with a healthcare professional.")
        return f"{text}\n\n{medical_note}"
    
    # Crisis responses focus on resources, not limitations
    if context.get('is_crisis', False) or context.get('routing_path') == 'crisis':
        # No disclaimer needed for crisis - focus on immediate help
        return text
    
    # General support - no disclaimer needed
    return text


def enforce_disclaimer(text: str, context: dict = None) -> str:
    """
    Ensures appropriate disclaimer is present based on context.
    If context is provided, uses contextual approach.
    If not, falls back to standard disclaimer.
    """
    if context:
        return add_contextual_disclaimer(text, context)
    
    # Fallback to standard disclaimer
    disclaimer_marker = "not a substitute for professional medical care"
    if disclaimer_marker.lower() in text.lower():
        return text
    return text + STANDARD_DISCLAIMER


def remove_emojis_and_special_chars(text: str) -> str:
    """
    Removes emojis and special characters from text to keep responses clean and professional.
    """
    # Remove emojis (Unicode ranges for common emojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE
    )
    
    # Remove special characters except basic punctuation
    text = emoji_pattern.sub('', text)
    
    # Remove any remaining unusual Unicode characters that might cause display issues
    text = re.sub(r'[^\w\s\.,!?;:\-\'"()]', ' ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def sanitize_response(text: str) -> str:
    """
    Full sanitization pipeline:
      1. Check for harmful content → replace with safe fallback if found
      2. Remove diagnosis language
      3. Remove emojis and special characters

    This should be called on ALL LLM outputs before returning to user.
    """
    if contains_harmful_content(text):
        # Hard override — never pass harmful content through
        text = (
            "I'm really concerned about your safety right now. "
            "Please reach out to a crisis support line immediately — they are there for you 24/7.\n\n"
            "Please call or text 988 (Suicide & Crisis Lifeline) or visit https://www.befrienders.org to find your local crisis centre.\n\n"
            "If you are in immediate danger, please call 911 (or your local emergency number)."
        )

    text = remove_diagnosis_language(text)
    text = remove_emojis_and_special_chars(text)
    # No automatic disclaimer enforcement - agents handle it contextually
    return text


def is_safe_to_send(text: str) -> bool:
    """
    Quick gate check — returns True if the response passes basic safety filters.
    Used before sending to the response generator.
    """
    return not contains_harmful_content(text)
