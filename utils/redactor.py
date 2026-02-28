"""
redactor.py — Simple PII Redaction Utility.

Redacts names, emails, and phone numbers from text using regex patterns
to ensure user privacy before data is stored in the database.
"""

import re

# Regex for common PII patterns
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_PATTERN = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

# Common name introduction patterns (best effort without NER)
# Matches: "My name is Sarah", "I am Sarah", "I'm Sarah", "Call me Sarah"
NAME_INTRO_PATTERNS = [
    r'(?i)(?:my name is|i am|i\'m|call me)\s+([A-Z][a-z]+)',
    r'(?i)(?:this is)\s+([A-Z][a-z]+)',
]

def redact_pii(text: str) -> str:
    """
    Redacts basic PII (emails, phone numbers, and some names) from the input text.
    """
    if not text:
        return text

    # 1. Redact Emails
    text = re.sub(EMAIL_PATTERN, '[EMAIL_REDACTED]', text)

    # 2. Redact Phone Numbers
    text = re.sub(PHONE_PATTERN, '[PHONE_REDACTED]', text)

    # 3. Redact Names (Best Effort)
    # We look for patterns like "My name is [Name]" and redact the captured group
    for pattern in NAME_INTRO_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            name = match.group(1)
            # Only redact if it starts with a capital letter (likely a name)
            if name and name[0].isupper():
                text = text.replace(name, '[NAME_REDACTED]')

    return text

def redact_message_history(history: list) -> list:
    """
    Redacts PII from a list of conversation turns.
    Each turn is a dict with 'role' and 'content'.
    """
    redacted_history = []
    for turn in history:
        new_turn = turn.copy()
        if 'content' in new_turn:
            new_turn['content'] = redact_pii(new_turn['content'])
        redacted_history.append(new_turn)
    return redacted_history
