from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct


class WebSearchMcpStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Build the Lambda using aws-lambda-python bundling from the src directory.
        # This keeps packaging focused on the runtime code.
        project_root = Path(__file__).resolve().parents[1]
        entry_dir = str(project_root / "src")

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
            environment={},
        )
