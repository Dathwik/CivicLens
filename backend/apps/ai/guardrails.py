import re

BLOCKED_PATTERNS = [
    r"\b(ssn|social security|password|credit card|cvv)\b",
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN format
]

MAX_QUERY_LENGTH = 500
MAX_MESSAGES_PER_REQUEST = 20


def validate_message(message: str) -> tuple[bool, str]:
    if not message or not message.strip():
        return False, "Message cannot be empty."
    if len(message) > MAX_QUERY_LENGTH:
        return False, f"Message too long (max {MAX_QUERY_LENGTH} chars)."
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return False, "Message contains sensitive information that cannot be processed."
    return True, ""


def sanitize_tool_input(tool_input: dict) -> dict:
    """Strip any string values that exceed reasonable limits."""
    sanitized = {}
    for k, v in tool_input.items():
        if isinstance(v, str):
            sanitized[k] = v[:200]
        else:
            sanitized[k] = v
    return sanitized
