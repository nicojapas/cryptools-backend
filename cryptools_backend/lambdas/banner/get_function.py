import requests
from typing import List, Dict, Any

from ..utils import layers, handle_http_errors, create_success_response
from ..config import S3_BUCKET, CACHE_DURATION
from ..s3_utils import get_cached_or_fetch


def fetch_banner_data() -> List[Dict[str, Any]]:
    """Fetch banner data from CoinGecko API."""
    from ..config import COINGECKO_TOP_COINS_ENDPOINT, COINGECKO_DEFAULT_PARAMS, REQUEST_TIMEOUT, REQUEST_HEADERS
    
    params = COINGECKO_DEFAULT_PARAMS.copy()
    params.update({
        "per_page": 20,  # Get top 20 for banner
        "page": 1
    })
    
    response = requests.get(
        COINGECKO_TOP_COINS_ENDPOINT,
        params=params,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    
    coins_data = response.json()
    
    # Format data for banner
    return [
        {
            "image": coin.get("image", ""),
            "name": coin.get("name", ""),
            "symbol": coin.get("symbol", "").upper(),
            "price": str(coin.get("current_price", 0)),
            "priceChangePercentage24H": coin.get("price_change_percentage_24h", 0),
            "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
            "id": coin.get("id", "")
        }
        for coin in coins_data
    ]


@layers(["libs", "requests"])
@handle_http_errors
def lambda_handler(event, context):
    """
    Lambda handler for banner data with caching.
    Returns top 20 coins by market cap, cached for 1 minute.
    """
    # Get cached data or fetch new data
    banner_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key="banner_data.json",
        fetch_function=fetch_banner_data,
        cache_duration=CACHE_DURATION
    )

    return create_success_response(
        data=banner_data,
        message="Banner data retrieved successfully",
        count=len(banner_data)
    )