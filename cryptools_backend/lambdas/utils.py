from functools import wraps
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union


def layers(_layers: list):
    def decorator(func):
        func.layers = _layers
        return func
    return decorator


# CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token',
}


def create_response(
    status_code: int = 200,
    body: Union[Dict, str] = None,
    message: str = "success",
    data: Any = None,
    error: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized API response with CORS headers.
    
    Args:
        status_code: HTTP status code
        body: Response body (if provided, overrides message/data)
        message: Success/error message
        data: Response data
        error: Error message (if any)
        **kwargs: Additional fields to include in response
    
    Returns:
        Dict with statusCode, headers, and body
    """
    if body is None:
        response_body = {
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response_body['data'] = data
            
        if error is not None:
            response_body['error'] = error
            
        # Add any additional fields
        response_body.update(kwargs)
        
        body = json.dumps(response_body)
    
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': body if isinstance(body, str) else json.dumps(body)
    }


def create_success_response(data: Any = None, message: str = "success", **kwargs) -> Dict[str, Any]:
    """Create a success response (200 status code)."""
    return create_response(
        status_code=200,
        message=message,
        data=data,
        **kwargs
    )


def create_error_response(
    error: str,
    status_code: int = 500,
    message: str = "Internal server error"
) -> Dict[str, Any]:
    """Create an error response."""
    return create_response(
        status_code=status_code,
        message=message,
        error=error
    )


def handle_api_errors(func):
    """
    Decorator to handle common API errors and provide standardized error responses.
    """
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            return create_error_response(
                error=str(e),
                message="Internal server error"
            )
    return wrapper


def handle_http_errors(func):
    """
    Decorator to handle HTTP request errors specifically.
    """
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            error_message = "Internal server error"
            if "requests" in str(type(e).__module__):
                error_message = "Failed to fetch data from external API"
            
            return create_error_response(
                error=str(e),
                message=error_message
            )
    return wrapper


def format_coin_data(coin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format CoinGecko coin data to match the required format.
    
    Args:
        coin: Raw coin data from CoinGecko API
        
    Returns:
        Formatted coin data
    """
    return {
        "symbol": coin.get("symbol", "").lower(),
        "name": coin.get("name", ""),
        "image": coin.get("image", ""),
        "currentPrice": str(coin.get("current_price", 0)),
        "marketCap": str(coin.get("market_cap", 0)),
        "marketCapRank": coin.get("market_cap_rank", 0),
        "priceChange24H": str(coin.get("price_change_24h", 0)),
        "marketCapChange24H": str(coin.get("market_cap_change_24h", 0)),
        "marketCapChangePercentage24H": str(coin.get("market_cap_change_percentage_24h", 0)),
        "circulatingSupply": str(coin.get("circulating_supply", 0)),
        "sparkline7D": coin.get("sparkline_in_7d", {}).get("price", []) if coin.get("sparkline_in_7d") else [],
        "stable": coin.get("price_change_percentage_24h", 0) < 1,  # Consider stable if 24h change < 1%
        "wrapped": "wrapped" in coin.get("name", "").lower() or "w" in coin.get("symbol", "").lower()
    }


