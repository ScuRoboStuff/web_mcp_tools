import asyncio
import types
import unittest
from typing import Dict, List

from unittest.mock import AsyncMock, patch


class FakeDDGS:
    """Minimal fake of ddgs.DDGS used by src.server.web_search.

    The real API is an object with a .text(query, max_results=...) method that
    yields dicts with keys: 'title', 'href', 'body'.
    """

    def __init__(self, items: List[Dict[str, str]] | None = None) -> None:
        self._items = items or []

    def text(self, query: str, max_results: int = 10):  # returns an iterator
        # Return at most max_results items as an iterator of dicts
        return iter(self._items[:max_results])


class WebSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_query_returns_error(self):
        from src import server  # import inside test to allow patches per test

        result = await server.web_search_impl("")
        self.assertIn("Query must be a non-empty string.", result["errors"])  # top-level error
        self.assertEqual(result["results"], [])

    async def test_success_with_two_results(self):
        from src import server

        items = [
            {"title": "Example 1", "href": "https://example.com/1", "body": "snippet 1"},
            {"title": "Example 2", "href": "https://example.com/2", "body": "snippet 2"},
        ]

        fake_ddgs = FakeDDGS(items)

        async def fake_fetch(_client, url: str):
            return f"<html><body><main>{url} content</main></body></html>"

        with patch("src.server.DDGS", return_value=fake_ddgs), \
             patch("src.server._fetch_url", new=AsyncMock(side_effect=fake_fetch)):
            result = await server.web_search_impl("test query", max_results=10)

        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["results"]), 2)
        # Verify fields present and text extracted
        for i, item in enumerate(result["results"]):
            self.assertEqual(item["title"], items[i]["title"])
            self.assertEqual(item["url"], items[i]["href"])
            self.assertEqual(item["snippet"], items[i]["body"])
            self.assertIn("content", item.get("text", ""))
            self.assertNotIn("error", item)

    async def test_partial_failure_fetch_error(self):
        from src import server

        items = [
            {"title": "OK", "href": "https://ok.example/", "body": "ok"},
            {"title": "Bad", "href": "https://bad.example/", "body": "bad"},
        ]
        fake_ddgs = FakeDDGS(items)

        async def fake_fetch(_client, url: str):
            if "bad" in url:
                raise RuntimeError("network fail")
            return "<html><body>hello</body></html>"

        with patch("src.server.DDGS", return_value=fake_ddgs), \
             patch("src.server._fetch_url", new=AsyncMock(side_effect=fake_fetch)):
            result = await server.web_search_impl("whatever")

        self.assertEqual(result["errors"], [])  # top-level still OK
        self.assertEqual(len(result["results"]), 2)
        # First should have text, second should have per-item error
        self.assertIn("text", result["results"][0])
        self.assertNotIn("error", result["results"][0])
        self.assertIn("error", result["results"][1])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
