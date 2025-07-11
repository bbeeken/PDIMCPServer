"""Simple priority classifier for ticket text."""

from typing import Dict, Any

from mcp.types import Tool


async def ticket_priority_impl(text: str) -> Dict[str, Any]:
    """Return a priority level based on simple keyword matching."""
    text_lower = text.lower()
    if any(word in text_lower for word in ["urgent", "immediately", "asap", "critical"]):
        priority = "high"
    elif any(word in text_lower for word in ["soon", "whenever", "request"]):
        priority = "medium"
    else:
        priority = "low"
    return {"priority": priority}


ticket_priority_tool = Tool(
    name="ticket_priority",
    description="Classify ticket text into a priority level (high, medium, low).",
    inputSchema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Ticket text to classify"},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
)

ticket_priority_tool._implementation = ticket_priority_impl
