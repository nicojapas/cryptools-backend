import os

from aws_cdk import App, BundlingOptions, Duration, Stack
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3
from cdk_klayers import Klayers

# === Constants and Config ===
REGION = "eu-west-1"
BUCKET_NAME = "cryptools-cache"
LAMBDA_RUNTIME = _lambda.Runtime.PYTHON_3_12
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]
KLAYER_DEPENDENCIES = {
    "requests": "requests",
    "pandas": "pandas",
}
FUNCTION_KLAYERS = {
    "tokens": ["requests"],
    "banner": ["requests", "pandas"],
    "fetch_bsc_tokens": ["web3"],
    "news": ["requests"],
}
KLAYER_POLICY_ARNS = [
    "arn:aws:lambda:eu-west-1:770693421928:layer:klayers-p312-web3:1",
    "arn:aws:lambda:eu-west-1:770693421928:layer:klayers-p312-numpy:1",
    "arn:aws:lambda:eu-west-1:770693421928:layer:klayers-p312-requests:1",
    "arn:aws:lambda:eu-west-1:770693421928:layer:klayers-p312-pandas:1",
]

current_path = os.path.dirname(os.path.relpath(__file__))


def get_environment_vars(subdir: str) -> dict:
    """Return environment variables for a given Lambda subdir."""
    env = {}
    if subdir == "news":
        api_token = os.environ.get("CRYPTOPANIC_API_TOKEN", "")
        if api_token:
            env["CRYPTOPANIC_API_TOKEN"] = api_token
        else:
            print(
                "Warning: CRYPTOPANIC_API_TOKEN not set in environment. News function may fail."
            )
    return env


def get_function_layers(self, subdir: str, klayers_map: dict) -> list:
    """Return the appropriate Lambda layers for a given subdir."""
    # Only attach the web3 layer to fetch_bsc_tokens
    if subdir == "fetch_bsc_tokens":
        layer_code = _lambda.Code.from_asset(
            "cryptools_backend/layers/web3",
            bundling=BundlingOptions(
                image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                command=["bash", "-c", "pip install web3 -t /asset-output/python"],
            ),
        )
        return [
            _lambda.LayerVersion(
                self,
                "Web3Layer",
                code=layer_code,
                compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
                description="Web3 layer built using bundling",
            )
        ]
    # For all other functions, do not include web3 in the layers
    non_web3_layers = [
        klayers_map[layer_name]
        for layer_name in FUNCTION_KLAYERS.get(subdir, [])
        if layer_name != "web3"
    ]
    return non_web3_layers


def create_lambda_function(
    self, subdir, http_method, handler_path, klayers_map, lambda_role, bucket
):
    """Create a Lambda function for the given subdir and HTTP method."""
    handler_str = f"lambdas.{subdir}.{http_method.lower()}_function.lambda_handler"
    environment_vars = get_environment_vars(subdir)
    function_layers = get_function_layers(self, subdir, klayers_map)
    lambda_function = _lambda.Function(
        self,
        f"cryptools_backend.lambdas.{subdir}{http_method}Lambda",
        runtime=LAMBDA_RUNTIME,
        handler=handler_str,
        code=_lambda.Code.from_asset("cryptools_backend"),
        layers=function_layers if function_layers else None,
        role=lambda_role,
        environment=environment_vars if environment_vars else None,
        timeout=Duration.seconds(10),
    )
    bucket.grant_read_write(lambda_function)
    return lambda_function


def attach_lambda_to_api(api, subdir, http_method, lambda_function):
    """Attach a Lambda function to the API Gateway resource/method."""
    resource = api.root.get_resource(subdir) or api.root.add_resource(subdir)
    resource.add_method(http_method, apigateway.LambdaIntegration(lambda_function))


class CryptoolsAPI(Stack):
    """
    CDK Stack for Cryptools API: sets up API Gateway, Lambda functions, S3 bucket, IAM roles, and Lambda layers.
    """

    def __init__(self, scope: App, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # API Gateway with CORS
        api = apigateway.RestApi(
            self,
            "CryptoolsAPI",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers",
                ],
            ),
        )

        # S3 Bucket (existing or new)
        existing_bucket = aws_s3.Bucket.from_bucket_name(
            self, "CacheBucket", BUCKET_NAME
        )
        bucket = (
            existing_bucket
            if existing_bucket
            else aws_s3.Bucket(self, "CacheBucket", bucket_name=BUCKET_NAME)
        )

        # Lambda Execution Role
        lambda_role = aws_iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject", "s3:HeadObject"],
                resources=[f"{bucket.bucket_arn}/*"],
            )
        )

        # Klayers for dependencies
        klayers = Klayers(self, python_version=LAMBDA_RUNTIME, region=REGION)
        klayers_map = {
            dep: klayers.layer_version(self, dep) for dep in KLAYER_DEPENDENCIES
        }

        # Discover and create Lambda functions
        lambdas_folder = os.path.join(current_path, "lambdas")
        for subdir in os.listdir(lambdas_folder):
            lambda_folder_path = os.path.join(lambdas_folder, subdir)
            if not os.path.isdir(lambda_folder_path):
                continue
            for http_method in HTTP_METHODS:
                handler_file = f"{http_method.lower()}_function.py"
                handler_path = os.path.join(lambda_folder_path, handler_file)
                if not os.path.exists(handler_path):
                    continue
                lambda_function = create_lambda_function(
                    self,
                    subdir,
                    http_method,
                    handler_path,
                    klayers_map,
                    lambda_role,
                    bucket,
                )
                attach_lambda_to_api(api, subdir, http_method, lambda_function)


# App initialization
app = App()
CryptoolsAPI(app, "CryptoolsAPI")
app.synth()
