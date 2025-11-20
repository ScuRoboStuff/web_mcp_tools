import types
import pytest


# We will test the async function `web_search_impl` in src/server.py
from src import server


class _FakeDDGS:
    """A fake DDGS replacement to control search results and capture args."""

    def __init__(self, items=None, raise_exc: Exception | None = None):
        self.items = items or []
        self.raise_exc = raise_exc
        self.last_query = None
        self.last_max_results = None

    def text(self, query: str, max_results: int = 10):
        # Capture the incoming parameters for assertions
        self.last_query = query
        self.last_max_results = max_results
        if self.raise_exc:
            raise self.raise_exc
        # Return an iterator over the configured items
        return iter(self.items)


@pytest.mark.asyncio
async def test_web_search_impl_empty_query_returns_error(monkeypatch):
    result = await server.web_search_impl("")
    assert result["query"] == ""
    assert result["results"] == []
    assert any("non-empty" in err for err in result["errors"])  # validation message


@pytest.mark.asyncio
async def test_web_search_impl_success_maps_fields(monkeypatch):
    items = [
        {"title": "Result A", "href": "https://a.example", "body": "Snippet A"},
        {"title": "Result B", "href": "https://b.example", "body": "Snippet B"},
    ]
    fake = _FakeDDGS(items=items)

    # Patch the DDGS symbol used inside server to return our fake instance
    monkeypatch.setattr(server, "DDGS", lambda: fake)

    out = await server.web_search_impl("alpha beta", max_results=5)

    assert out["errors"] == []
    assert out["query"] == "alpha beta"
    assert len(out["results"]) == 2
    # Verify field mapping
    assert out["results"][0] == {
        "title": "Result A",
        "url": "https://a.example",
        "snippet": "Snippet A",
    }
    assert out["results"][1]["url"] == "https://b.example"

    # Verify that DDGS.text was called with our query and max_results as given
    assert fake.last_query == "alpha beta"
    assert fake.last_max_results == 5


@pytest.mark.asyncio
async def test_web_search_impl_caps_max_results_to_10(monkeypatch):
    # Provide more than 10 as requested; function should cap to 10 when calling DDGS
    items = [{"title": "T", "href": "U", "body": "B"}]
    fake = _FakeDDGS(items=items)
    monkeypatch.setattr(server, "DDGS", lambda: fake)

    await server.web_search_impl("cap test", max_results=50)
    assert fake.last_max_results == 10  # capped


@pytest.mark.asyncio
async def test_web_search_impl_handles_search_exception(monkeypatch):
    fake = _FakeDDGS(raise_exc=RuntimeError("boom"))
    monkeypatch.setattr(server, "DDGS", lambda: fake)

    out = await server.web_search_impl("will fail")
    assert out["results"] == []
    assert out["errors"] and any("Search failed" in e for e in out["errors"])
