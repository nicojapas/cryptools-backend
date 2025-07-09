import os
import subprocess
import importlib.util

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

        # Define the API Gateway
        api = apigateway.RestApi(self, "CryptoolsAPI")

        existing_bucket = aws_s3.Bucket.from_bucket_name(self, "BannerBucket", "banner-s3-bucket")

        bucket = existing_bucket if existing_bucket else aws_s3.Bucket(self, "BannerBucket",
                                                                       bucket_name="banner-s3-bucket")

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

        def get_function_layers(handler_path):
            """Get the required layers for a function by reading the decorator."""
            try:
                # Import the module to read the decorator
                spec = importlib.util.spec_from_file_location("handler_module", handler_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for lambda_handler function and check if it has layers attribute
                if hasattr(module, 'lambda_handler'):
                    handler_func = module.lambda_handler
                    if hasattr(handler_func, 'layers'):
                        return handler_func.layers
            except Exception as e:
                print(f"Warning: Could not read layers for {handler_path}: {e}")
            return []

        # Find all Lambda handlers in the `lambdas/` folder
        lambdas_folder = os.path.join(current_path, 'lambdas')
        for subdir in os.listdir(lambdas_folder):
            lambda_folder_path = os.path.join(lambdas_folder, subdir)

            if os.path.isdir(lambda_folder_path):
                for http_method in ["GET", "POST", "PUT", "DELETE"]:
                    handler_file = f"{http_method.lower()}_function.py"
                    handler_path = os.path.join(lambda_folder_path, handler_file)

                    if os.path.exists(handler_path):
                        # Get the required layers for this function
                        required_layers = get_function_layers(handler_path)
                        
                        # Create the layers list for this function
                        function_layers = []
                        for layer_name in required_layers:
                            if layer_name in lambda_layers:
                                function_layers.append(lambda_layers[layer_name])
                            else:
                                print(f"Warning: Layer '{layer_name}' not found for function {subdir}/{handler_file}")
                        
                        # Handler string for AWS Lambda
                        handler_str = f"lambdas.{subdir}.{http_method.lower()}_function.lambda_handler"
                        
                        lambda_function = _lambda.Function(
                            self, f"cryptools_backend.lambdas.{subdir}{http_method}Lambda",
                            runtime=_lambda.Runtime.PYTHON_3_12,
                            handler=handler_str,
                            code=_lambda.Code.from_asset('cryptools_backend'),
                            layers=function_layers if function_layers else None,
                            role=lambda_role,
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
