import os
import subprocess
import ast

from aws_cdk import (
    App, Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam,
    aws_s3
)

current_path = os.path.dirname(os.path.relpath(__file__))

class CryptoolsAPI(Stack):
    def __init__(self, scope: App, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Run the dependency installation script
        print("Installing dependencies...")
        subprocess.run(["python", "install_dependencies.py"], check=True)

        # Define the API Gateway with CORS enabled
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
                    "Access-Control-Allow-Headers"
                ]
            )
        )

        existing_bucket = aws_s3.Bucket.from_bucket_name(self, "CacheBucket", "cryptools-cache")

        bucket = existing_bucket if existing_bucket else aws_s3.Bucket(self, "CacheBucket",
                                                                       bucket_name="cryptools-cache")

        lambda_role = aws_iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        # Attach the S3 access policy to the role
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:HeadObject",
                ],
                resources=[f"{bucket.bucket_arn}/*"],
            )
        )

        # Create the Lambda layer from the 'layers/my-layer' directory
        layers_folder = os.path.join(current_path, 'layers')
        lambda_layers = {}
        if os.path.exists(layers_folder):
            for name in os.listdir(layers_folder):
                layer_path = os.path.join(layers_folder, name)
                if os.path.isdir(layer_path):
                    lambda_layers[name] = _lambda.LayerVersion(
                        self,
                        name,
                        code=_lambda.Code.from_asset(f"cryptools_backend/layers/{name}"),
                        compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
                    )

        def get_function_layers_from_ast(handler_path):
            """Get the required layers for a function by parsing the AST without importing."""
            try:
                with open(handler_path, 'r') as file:
                    tree = ast.parse(file.read())
                
                # Look for @layers decorator on lambda_handler function
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == 'lambda_handler':
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Call):
                                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'layers':
                                    # Extract the layers list from the decorator
                                    if decorator.args and isinstance(decorator.args[0], ast.List):
                                        return [elt.s if isinstance(elt, ast.Str) else elt.value for elt in decorator.args[0].elts]
                                elif isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'layers':
                                    # Handle @layers decorator from utils module
                                    if decorator.args and isinstance(decorator.args[0], ast.List):
                                        return [elt.s if isinstance(elt, ast.Str) else elt.value for elt in decorator.args[0].elts]
            except Exception as e:
                print(f"Warning: Could not parse layers for {handler_path}: {e}")
            return []

        # Define layer requirements for each function (fallback if AST parsing fails)
        function_layer_requirements = {
            'tokens': ['requests'],
            'banner': ['libs', 'requests'],
            'fetch_bsc_tokens': ['libs'],
            'news': ['requests'],
        }

        # Find all Lambda handlers in the `lambdas/` folder
        lambdas_folder = os.path.join(current_path, 'lambdas')
        for subdir in os.listdir(lambdas_folder):
            lambda_folder_path = os.path.join(lambdas_folder, subdir)

            if os.path.isdir(lambda_folder_path):
                for http_method in ["GET", "POST", "PUT", "DELETE"]:
                    handler_file = f"{http_method.lower()}_function.py"
                    handler_path = os.path.join(lambda_folder_path, handler_file)

                    if os.path.exists(handler_path):
                        # Try to get layers from AST parsing first, fallback to predefined requirements
                        required_layers = get_function_layers_from_ast(handler_path)
                        if not required_layers and subdir in function_layer_requirements:
                            required_layers = function_layer_requirements[subdir]
                        
                        # Create the layers list for this function
                        function_layers = []
                        for layer_name in required_layers:
                            if layer_name in lambda_layers:
                                function_layers.append(lambda_layers[layer_name])
                            else:
                                print(f"Warning: Layer '{layer_name}' not found for function {subdir}/{handler_file}")
                        
                        # Handler string for AWS Lambda
                        handler_str = f"lambdas.{subdir}.{http_method.lower()}_function.lambda_handler"
                        
                        # Define environment variables for specific functions
                        environment_vars = {}
                        if subdir == 'news':
                            # Get API token from environment or use a placeholder
                            # In production, this should be set via AWS Systems Manager Parameter Store
                            # or AWS Secrets Manager for better security
                            api_token = os.environ.get('CRYPTOPANIC_API_TOKEN', '')
                            if api_token:
                                environment_vars['CRYPTOPANIC_API_TOKEN'] = api_token
                            else:
                                print("Warning: CRYPTOPANIC_API_TOKEN not set in environment. News function may fail.")
                        
                        lambda_function = _lambda.Function(
                            self, f"cryptools_backend.lambdas.{subdir}{http_method}Lambda",
                            runtime=_lambda.Runtime.PYTHON_3_12,
                            handler=handler_str,
                            code=_lambda.Code.from_asset('cryptools_backend'),
                            layers=function_layers if function_layers else None,
                            role=lambda_role,
                            environment=environment_vars if environment_vars else None,
                        )
                        bucket.grant_read_write(lambda_function)
                        resource = api.root.get_resource(subdir) or api.root.add_resource(subdir)
                        resource.add_method(
                            http_method, apigateway.LambdaIntegration(lambda_function)
                        )

# App initialization
app = App()
CryptoolsAPI(app, "CryptoolsAPI")
app.synth()
