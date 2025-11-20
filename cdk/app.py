import os
import aws_cdk as cdk

from web_search_mcp_stack import WebSearchMcpStack


def _env_from_os() -> cdk.Environment | None:
    account = os.getenv("AWS_ACCOUNT_ID") or os.getenv("CDK_DEFAULT_ACCOUNT")
    region = os.getenv("AWS_REGION") or os.getenv("CDK_DEFAULT_REGION")
    if account and region:
        return cdk.Environment(account=account, region=region)
    return None


app = cdk.App()

WebSearchMcpStack(
    app,
    "WebSearchMcpStack",
    env=_env_from_os(),
)

app.synth()
