# web-search-mcp

## Overview


Requires : (Conventional Commits)[https://github.com/conventional-changelog/commitlint/#what-is-commitlint]

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

## Deployment (AWS CDK → AWS Lambda)

This repo includes an optional Continuous Deployment (CD) workflow that deploys the project as an internal AWS Lambda function using AWS CDK (Python). The Lambda is named `web_search_mcp` and invokes the existing `web_search_impl` logic via `src/lambda_handler.py`.

What gets provisioned:
- AWS Lambda function: `web_search_mcp` (Python 3.11)
- No public API; for internal invocation only (e.g., via EventBridge, other Lambdas, or manual invocation)

### Event format (Lambda)
Invoke the function with a JSON payload like:

```
{
  "query": "chatgpt",
  "max_results": 5
}
```

The response mirrors the dict returned by `web_search_impl`:

```
{
  "query": "chatgpt",
  "results": [ {"title": "...", "url": "...", "snippet": "..."}, ... ],
  "errors": []
}
```

### CDK project layout
- `cdk/app.py` — CDK entrypoint
- `cdk/web_search_mcp_stack.py` — defines the Lambda (no API Gateway)
- `cdk/requirements.txt` — CDK Python dependencies
- `src/lambda_handler.py` — AWS Lambda entrypoint calling `web_search_impl`
- `src/requirements.txt` — minimal runtime deps bundled into the Lambda

### GitHub Actions CD (push to main)
- Workflow: `.github/workflows/cd.yml`
- Triggers: push to `main`
- Uses GitHub OIDC to assume an AWS IAM role
- Expects the following:
  - Repo secret: `GH_AWS_ROLE_ARN` — ARN of the IAM role to assume
  - Environment variables baked into the workflow: `AWS_ACCOUNT_ID` and `AWS_REGION`

Defaults in this repo:
- `AWS_ACCOUNT_ID=920096439137`
- `AWS_REGION=us-east-1`

You can change these by editing `.github/workflows/cd.yml`.

### One-time AWS setup (OIDC role)
You need an IAM role that GitHub Actions can assume via OpenID Connect. The simplest path is to create a role with trust policy for your GitHub repo and attach `AdministratorAccess` (tighten later).

1. Create an IAM role (e.g., `GitHubActionsDeployRole`) with the following trust policy, updating `repo: <owner>/<repo>` and branches as needed:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<OWNER>/<REPO>:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

2. Attach permissions (start broad, then tighten):
   - `AdministratorAccess` (for initial bootstrap and deployment)

3. In your GitHub repo settings, add a secret named `GH_AWS_ROLE_ARN` with the role's ARN.

### Deploy from CI
Push to `main`. The `deploy` workflow will:
1. Configure OIDC and assume the role (`GH_AWS_ROLE_ARN`).
2. Install CDK CLI and Python CDK deps.
3. `cdk bootstrap` your account/region (safe if already bootstrapped).
4. `cdk deploy` the `WebSearchMcpStack` without manual approval.

### Local synth/deploy (optional)

```
python -m pip install --upgrade pip
pip install -r cdk/requirements.txt

# Set your env (PowerShell example)
$env:AWS_ACCOUNT_ID="123456789"
$env:AWS_REGION="us-east-1"

# Use your configured AWS credentials locally
cdk synth
cdk deploy
```


Notes:
- CDK bundles the Lambda from `src/` and installs `src/requirements.txt` into the artifact. Tests and dev-only files are not included.
- The MCP server code remains unchanged and is not started in Lambda; only `web_search_impl` is used via the handler.
