from functools import wraps


def add_cors_headers(lambda_handler):
    @wraps(lambda_handler)
    def wrapper(event, context):
        # Call the original lambda handler
        response = lambda_handler(event, context)

        # Add CORS headers to the response
        if isinstance(response, dict):
            response["headers"] = {
                "Access-Control-Allow-Origin": "*",  # Allow all origins
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",  # Allowed HTTP methods
                "Access-Control-Allow-Headers": "Content-Type, Authorization",  # Allowed headers
            }

        return response

    return wrapper
