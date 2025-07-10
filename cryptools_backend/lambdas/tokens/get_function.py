from ..utils import layers, handle_http_errors, create_success_response
from ..services import CoinGeckoService
from ..config import S3_BUCKET, CACHE_DURATION
from ..s3_utils import get_cached_or_fetch


def fetch_tokens_data(per_page: int = 50, page: int = 1):
    """Fetch tokens data from CoinGecko API."""
    return CoinGeckoService.get_top_coins(per_page=per_page, page=page)


@layers(["requests"])
@handle_http_errors
def lambda_handler(event, context):
    """
    Lambda handler for fetching top cryptocurrency data from CoinGecko API.
    
    Query Parameters:
        per_page: Number of coins to fetch (default: 50, max: 250)
        page: Page number for pagination (default: 1)
    """
    # Parse query parameters
    query_params = event.get('queryStringParameters', {}) or {}
    per_page = int(query_params.get('per_page', 50))
    page = int(query_params.get('page', 1))
    
    # Create cache key based on parameters to avoid cache conflicts
    cache_key = f"tokens_data_p{per_page}_page{page}.json"
    
    # Get cached data or fetch new data
    coins_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=cache_key,
        fetch_function=lambda: fetch_tokens_data(per_page, page),
        cache_duration=CACHE_DURATION
    )
    
    return create_success_response(
        data=coins_data,
        message=f"Successfully fetched {len(coins_data)} top coins",
        count=len(coins_data),
        page=page,
        per_page=per_page
    )
