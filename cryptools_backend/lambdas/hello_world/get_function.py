import json

from cryptools_backend.lib.utils import http_method


def generate_hello_message(name):
    return f"Hello, {name}!"


@http_method("GET")
def lambda_handler(event, context):
    name = event.get("name", "World")  # Default to 'World' if name not provided
    message = generate_hello_message(name)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }
