"""
AWS Lambda handler that reuses the existing web_search_impl from src.server.

Expected event JSON:
{
  "query": "<string>",
  "max_results": 10  # optional
}

Returns the dict produced by web_search_impl.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import server


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:  # AWS Lambda entrypoint
    query = ""
    max_results = 10

    if isinstance(event, dict):
        query = event.get("query", "")
        if "max_results" in event:
            max_results = _coerce_int(event.get("max_results", 10), 10)

    # Run the async implementation
    return asyncio.run(server.web_search_impl(query=query, max_results=max_results))
