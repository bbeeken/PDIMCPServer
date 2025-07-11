"""Analyze sentiment of a ticket."""

from typing import Dict, Any

from mcp.types import Tool
from textblob import TextBlob


async def ticket_sentiment_impl(text: str) -> Dict[str, Any]:
    """Return a basic sentiment score for the provided text."""
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    return {"score": score}


ticket_sentiment_tool = Tool(
    name="ticket_sentiment",
    description="Calculate sentiment polarity for a text string using TextBlob.",
    inputSchema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Ticket text to analyze"},
        },
        "required": ["text"],
        "additionalProperties": False,
    },
)

ticket_sentiment_tool._implementation = ticket_sentiment_impl
