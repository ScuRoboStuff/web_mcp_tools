
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


## Releases, Versioning, and Deployment

This repo uses Conventional Commits + Semantic Release to automatically version, create GitHub Releases, and deploy the Lambda via CDK.

### Commit message rules (Conventional Commits)

- Major release: add `!` after type or include a `BREAKING CHANGE:` footer
  - Example: `feat!: remove deprecated endpoint`
  - Or:
    ```
    fix: adjust auth flow

    BREAKING CHANGE: removed legacy token support
    ```
- Minor release: `feat: ...`
  - Example: `feat(search): add max_results option`
- Patch release: `fix: ...` or `perf: ...`
  - Example: `fix: handle empty query gracefully`
- Non-releasing by default: `docs:`, `chore:`, `ci:`, `build:`, `test:` (unless you add `!`)

Tip: To force a patch release without code changes, push an empty commit:
```
git checkout master
git pull --ff-only
git commit --allow-empty -m "fix: trigger release"
git push
```

### Pipeline flow

1. Push to `master` with Conventional Commit messages.
2. Workflow `tests` runs (lint commits + run tests). Must succeed.
3. Workflow `deploy (auto release + deploy)` triggers from the successful CI run and:
   - Calculates next semver and publishes a GitHub Release tag `vX.Y.Z` with notes.
   - Deploys that exact tag with CDK.
4. The Lambda is published as a new Lambda Version, with an Alias named like the tag (`v1-2-3`) and environment variable `APP_VERSION` set to the tag.

### Where to see results

- GitHub → Releases: new `vX.Y.Z` with notes and updated `CHANGELOG.md`.
- AWS Lambda → your function `web_search_mcp`:
  - Versions: one per release, description includes `Release vX.Y.Z`.
  - Aliases: `vX-Y-Z` pointing to its version.
  - Environment: `APP_VERSION` set to release tag.

### Formatting and validation

- CI validates `.releaserc.json` has no UTF-8 BOM and is valid JSON.
- The repository includes `.editorconfig` enforcing UTF-8 (no BOM) and LF endings.
