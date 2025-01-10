from aws_cdk import (
    App, Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    Environment
)


class CryptoolsBackendStack(Stack):
    def __init__(self, scope: App, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define the hello world Lambda
        hello_world_lambda = _lambda.Function(
            self, "HelloWorldLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="hello_world.lambda_function.lambda_handler",  # Path to the hello world handler
            code=_lambda.Code.from_asset('cryptools_backend/lambdas'),
        )

        # Define the bye world Lambda
        bye_world_lambda = _lambda.Function(
            self, "ByeWorldLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="bye_world.lambda_function.lambda_handler",  # Path to the bye world handler
            code=_lambda.Code.from_asset('cryptools_backend/lambdas'),
        )

        # Create the API Gateway to trigger both Lambda functions
        api = apigateway.RestApi(self, "CryptoolsApi")

        # Add /hello-world endpoint to the API Gateway, triggering the HelloWorld Lambda
        api.root.add_resource("hello-world").add_method(
            "GET", apigateway.LambdaIntegration(hello_world_lambda)
        )

        # Add /bye-world endpoint to the API Gateway, triggering the ByeWorld Lambda
        api.root.add_resource("bye-world").add_method(
            "GET", apigateway.LambdaIntegration(bye_world_lambda)
        )


# App initialization
app = App()
CryptoolsBackendStack(app, "CryptoolsBackendStack")
app.synth()
