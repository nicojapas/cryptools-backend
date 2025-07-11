from typing import Any, Dict, List

import requests

from ..config import CACHE_DURATION, S3_BUCKET
from ..s3_utils import get_cached_or_fetch
from ..utils import create_success_response, handle_http_errors


def fetch_banner_data() -> List[Dict[str, Any]]:
    """Fetch banner data from CoinGecko API."""
    from ..config import (COINGECKO_DEFAULT_PARAMS,
                          COINGECKO_TOP_COINS_ENDPOINT, REQUEST_HEADERS,
                          REQUEST_TIMEOUT)

    params = COINGECKO_DEFAULT_PARAMS.copy()
    params.update({"per_page": 20, "page": 1})  # Get top 20 for banner

    response = requests.get(
        COINGECKO_TOP_COINS_ENDPOINT,
        params=params,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
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
            "id": coin.get("id", ""),
        }
        for coin in coins_data
    ]


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
        cache_duration=CACHE_DURATION,
    )

    return create_success_response(
        data=banner_data,
        message="Banner data retrieved successfully",
        count=len(banner_data),
    )
