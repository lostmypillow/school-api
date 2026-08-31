
from aws_cdk import Duration, Stack, aws_lambda
from aws_cdk.aws_lambda_python_alpha import BundlingOptions, PythonLayerVersion
from constructs import Construct


class SearchStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        dependency_layer = PythonLayerVersion(
            self,
            "SearchApiDepLayer",
            entry=".",
            bundling=BundlingOptions(
                asset_excludes=[
                    ".venv",
                    "cdk.out",
                    "__pycache__",
                    "*.pyc",
                    ".git",
                ]
            ),
            layer_version_name="dependencies-layer",
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_14],
            compatible_architectures=[aws_lambda.Architecture.ARM_64],
        )


        search_function = aws_lambda.Function(
            self,
            id="SearchApi",
            runtime=aws_lambda.Runtime.PYTHON_3_14,
            architecture=aws_lambda.Architecture.ARM_64,
            memory_size=128,
            timeout=Duration.seconds(10),
            handler="main.handler",
            code=aws_lambda.Code.from_asset("app"),
            environment={},
            layers=[dependency_layer],
        )
        search_function.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,
            cors=aws_lambda.FunctionUrlCorsOptions(
                allow_credentials=True,
                allowed_origins=[
                    "http://localhost:5173",
                    "https://jsearch.lostmypillow.com",
                ],
                allowed_methods=[aws_lambda.HttpMethod.GET],
                allowed_headers=["Content-Type", "Authorization"],
                max_age=Duration.hours(1),
            ),
        )
