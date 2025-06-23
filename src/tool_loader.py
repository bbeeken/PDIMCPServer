import logging
import os
from typing import Any, List, Optional

import httpx

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10"))

logger = logging.getLogger(__name__)


def load_tools(url: str) -> Optional[List[Any]]:
    """Fetch a list of tools from ``url``.

    Returns the JSON-decoded response on success, otherwise ``None`` and logs
    an error message.
    """
    try:
        resp = httpx.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # pragma: no cover - network failure path
        logger.error("Error loading tools: %s", exc)
        return None
