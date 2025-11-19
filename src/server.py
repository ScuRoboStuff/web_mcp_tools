
import logging
import os
from typing import Any, Dict, List
import httpx
from ddgs import DDGS

try:
    # fastmcp >= 0.4 API
    from fastmcp import FastMCP
except Exception as e:  # pragma: no cover - import guard for clarity
    raise


def setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    class _Formatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:  # noqa: D401
            parts = [
                f"ts={self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S')}",
                f"lvl={record.levelname}",
                f"logger={record.name}",
                f"msg={record.getMessage()}",
            ]
            if record.exc_info:
                parts.append(f"exc={self.formatException(record.exc_info)}")
            return " ".join(parts)

    handler = logging.StreamHandler()
    handler.setFormatter(_Formatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


setup_logging()
log = logging.getLogger("web_search_mcp")


# HTTP client shared across calls
_DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=10.0, read=20.0)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

class FetchError(Exception):
    pass

mcp = FastMCP(
    name="web-search-mcp",
    version="0.1.0",
)


async def web_search_impl(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for the query and return results with fetched text.

    Parameters:
      - query: The search string to use.
      - max_results: Maximum results to retrieve from DuckDuckGo (default 10, capped at 10).

    Returns a dict with keys:
      - query: original query
      - results: list of objects {title, url, snippet, text, error?}
      - errors: list of top-level errors (if search failed)
    """
    log.info(f"web_search called query='{query}' max_results={max_results}")
    result: Dict[str, Any] = {"query": query, "results": [], "errors": []}
    if not isinstance(query, str) or not query.strip():
        msg = "Query must be a non-empty string."
        log.error(msg)
        result["errors"].append(msg)
        return result

    try:
        cap = min(max(int(max_results), 1), 10)
    except Exception:
        cap = 10

    # Perform the search
    try:
        ddgs = DDGS()
        search_hits: List[Dict[str, Any]] = []
        for item in ddgs.text(query, max_results=cap):
            # item typically contains 'title', 'href', 'body'
            result["results"].append(
                {
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                }
            )
        log.info(f"DuckDuckGo returned {len(search_hits)} results for query='{query}'")
    except Exception as e:
        msg = f"Search failed: {e}"
        log.exception(msg)
        result["errors"].append(msg)
        return result


    return result


@mcp.tool(
    name="web_search",
    description=(
        "Search DuckDuckGo and return up to the top 10 results along with fetched "
        "page text. Input is a search string."
    ),
)
async def web_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """MCP-exposed wrapper that delegates to web_search_impl."""
    return await web_search_impl(query, max_results)


if __name__ == "__main__":
    # Run the MCP server
    # You can control logging with LOG_LEVEL env var, e.g., LOG_LEVEL=DEBUG
    log.info("Starting web-search-mcp server")
    mcp.run("streamable-http")
