import aws_cdk as core
import aws_cdk.assertions as assertions

from cryptools_backend.cryptools_backend_stack import CryptoolsBackendStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cryptools_backend/cryptools_backend_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CryptoolsBackendStack(app, "cryptools-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
