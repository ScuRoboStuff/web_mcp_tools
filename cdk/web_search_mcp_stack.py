from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Runtime, Version, Alias
from aws_cdk import CfnOutput
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct


class WebSearchMcpStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Build the Lambda using aws-lambda-python bundling from the src directory.
        # This keeps packaging focused on the runtime code.
        project_root = Path(__file__).resolve().parents[1]
        entry_dir = str(project_root / "src")

        # Optionally read the app version from CDK context (passed by the deploy workflow)
        app_version: str | None = self.node.try_get_context("appVersion")

        self.fn = PythonFunction(
            self,
            "WebSearchMcpFunction",
            function_name="web_search_mcp",
            entry=entry_dir,
            index="lambda_handler.py",
            handler="lambda_handler",
            runtime=Runtime.PYTHON_3_11,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                # Surface the version at runtime if provided
                **({"APP_VERSION": app_version} if app_version else {})
            },
        )

        # Always publish a new Lambda Version on deploy. If app_version is provided,
        # record it in the version description and create an alias that maps to it.
        lambda_version = Version(
            self,
            "WebSearchMcpVersion",
            lambda_=self.fn,
            description=(f"Release {app_version}" if app_version else None),
        )

        # Lambda alias names cannot contain dots, so convert e.g. v1.2.3 -> v1-2-3
        alias_name = None
        if app_version:
            alias_name = app_version.replace(".", "-")
            alias = Alias(
                self,
                "WebSearchMcpAlias",
                alias_name=alias_name,
                version=lambda_version,
            )

            CfnOutput(self, "LambdaAliasName", value=alias.alias_name)
            CfnOutput(self, "LambdaAliasArn", value=alias.alias_arn)

        CfnOutput(self, "LambdaVersion", value=lambda_version.version)
