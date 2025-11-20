# web-search-mcp

## Overview

`web-search-mcp` is a minimal Model Context Protocol (MCP) server built with `fastmcp`. It exposes a single tool today — `web_search` — that performs DuckDuckGo web searches via the `ddgs` library and returns up to the top 10 results.

Key points (from `src/server.py`):
- Uses `FastMCP` to run a streamable HTTP MCP server.
- Tool: `web_search(query: str, max_results: int = 10)` delegates to `web_search_impl`.
- Input validation ensures `query` is a non-empty string; `max_results` is capped to 10.
- Each result item contains: `title`, `url`, and `snippet`.
- Structured logging is enabled; adjust with `LOG_LEVEL` environment variable (e.g., `DEBUG`, `INFO`).

The server is started with `mcp.run("streamable-http")` when invoked as a script.

## MCP Tools

MCP Server will have various tools to help when interacting with Search and Web Crawling. Below is an initial list we will enhance over time as more tools are added.

| Tool name   | Description |
|-------------|-------------|
| `web_search` | Search DuckDuckGo and return up to 10 results with `title`, `url`, and `snippet`. Parameters: `query` (str), `max_results` (int, optional, capped at 10). |
| `web_crawl` (planned) | Crawl a given URL and extract readable text, metadata, and links. |
| `fetch_page_text` (planned) | Fetch a single page and return cleaned text for summarization/RAG. |

We will refine and expand these descriptions as additional tools are implemented.

## Setup

Prerequisites:
- Python 3.11+

Steps:
1. Clone the repository and switch into the project directory.
2. (Recommended) Create a virtual environment:
   - Windows PowerShell:
     ```
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```
     python -m venv .venv
     source .venv/bin/activate
     ```
3. Upgrade pip and install dependencies:
   ```
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Running the MCP server

Set the desired log level (optional) and start the server:

```
set LOG_LEVEL=INFO   # Windows PowerShell
python -m src.server
```

On macOS/Linux:

```
export LOG_LEVEL=INFO
python -m src.server
```

By default, the server starts using the `streamable-http` transport provided by `fastmcp`. Integrate it with your MCP-compatible client by pointing the client to the running server as per your client's documentation.

### Using the `web_search` tool

Input parameters:
- `query` (string, required): the search query.
- `max_results` (integer, optional): maximum number of results to return (1–10, defaults to 10).

Example output item:

```
{
  "title": "Example Result Title",
  "url": "https://example.com",
  "snippet": "Short preview text from the result"
}
``;

### Testing

This project uses `pytest` and `pytest-asyncio`.

Run the test suite:

```
pytest -q
```

Continuous Integration is configured via GitHub Actions to run tests on every push and pull request.

### Configuration

- `LOG_LEVEL` — controls verbosity (e.g., `DEBUG`, `INFO`, `WARNING`).

### CI

A GitHub Actions workflow (`.github/workflows/ci.yml`) installs dependencies and runs the tests on `push` and `pull_request`. To require passing tests before merging, enable branch protection rules in your repository settings and require the workflow to succeed.

### License

MIT or your preferred license. Update this section as needed.
