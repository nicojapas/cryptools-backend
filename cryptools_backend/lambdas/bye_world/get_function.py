import json


def generate_bye_message(name):
    return f"Bye, {name}!"


def lambda_handler(event, context):
    name = event.get("name", "World")  # Default to 'World' if name not provided
    message = generate_bye_message(name)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }

@http_method("POST")
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
