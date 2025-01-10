import json

from lib.utils import generate_hello_message


def lambda_handler(event, context):
    name = event.get("name", "World")  # Default to 'World' if name not provided
    message = generate_hello_message(name)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }
