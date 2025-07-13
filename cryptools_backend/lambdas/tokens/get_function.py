from ..config import CACHE_DURATION, S3_BUCKET
from ..s3_utils import get_cached_or_fetch
from ..services.coin_gecko_service import CoinGeckoService
from ..utils import create_success_response, handle_http_errors


def fetch_tokens_data(per_page: int = 50, page: int = 1):
    """Fetch tokens data from CoinGecko API."""
    return CoinGeckoService.get_top_coins(per_page=per_page, page=page)


def fetch_top_gainers_data(limit: int = 20):
    """Fetch top gainers data from CoinGecko API."""
    return CoinGeckoService.get_top_gainers(limit=limit)


def fetch_trending_coins_data():
    """Fetch trending coins data from CoinGecko API."""
    return CoinGeckoService.get_trending_coins()


def fetch_worst_losers_data(limit: int = 20):
    """Fetch worst losers data from CoinGecko API."""
    return CoinGeckoService.get_worst_losers(limit=limit)


def fetch_banner_data():
    """Fetch banner data from CoinGecko API."""
    return CoinGeckoService.get_banner_data()


def calculate_market_sentiment(coins_data):
    """
    Calculate market sentiment based on Bitcoin's 24h price change.
    
    Args:
        coins_data: List of coin data from CoinGecko API
        
    Returns:
        str: "bullish", "bearish", or "neutral"
    """
    # Find Bitcoin in the coins data
    bitcoin = None
    for coin in coins_data:
        if coin.get("symbol", "").lower() == "btc" or coin.get("name", "").lower() == "bitcoin":
            bitcoin = coin
            break
    
    if not bitcoin:
        # If Bitcoin not found, return neutral
        return "neutral"
    
    # Get Bitcoin's 24h price change percentage
    btc_24h_change = bitcoin.get("price_change_percentage_24h", 0)
    
    # Determine sentiment based on 24h change
    if btc_24h_change > 1:
        return "bullish"
    elif btc_24h_change < -1:
        return "bearish"
    else:
        return "neutral"


@handle_http_errors
def lambda_handler(event, context):
    """
    Lambda handler for fetching top cryptocurrency data from CoinGecko API.

    Query Parameters:
        per_page: Number of coins to fetch (default: 50, max: 250)
        page: Page number for pagination (default: 1)
    """
    # Parse query parameters
    query_params = event.get("queryStringParameters", {}) or {}
    per_page = int(query_params.get("per_page", 50))
    page = int(query_params.get("page", 1))

    # Create cache key based on parameters to avoid cache conflicts
    cache_key = f"tokens_data_p{per_page}_page{page}.json"
    gainers_cache_key = "top_gainers_data.json"
    trending_coins_cache_key = "trending_coins_data.json"
    losers_cache_key = "worst_losers_data.json"
    banner_cache_key = "banner_data.json"

    # Get cached data or fetch new data for regular tokens
    coins_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=cache_key,
        fetch_function=lambda: fetch_tokens_data(per_page, page),
        cache_duration=CACHE_DURATION,
    )

    # Get cached data or fetch new data for top gainers
    top_gainers_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=gainers_cache_key,
        fetch_function=lambda: fetch_top_gainers_data(20),
        cache_duration=CACHE_DURATION,
    )

    # Get cached data or fetch new data for trending coins
    trending_coins_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=trending_coins_cache_key,
        fetch_function=fetch_trending_coins_data,
        cache_duration=CACHE_DURATION,
    )

    # Get cached data or fetch new data for worst losers
    worst_losers_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=losers_cache_key,
        fetch_function=lambda: fetch_worst_losers_data(20),
        cache_duration=CACHE_DURATION,
    )

    # Get cached data or fetch new data for banner
    banner_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key=banner_cache_key,
        fetch_function=fetch_banner_data,
        cache_duration=CACHE_DURATION,
    )

    # Calculate market sentiment based on Bitcoin's 24h price change
    sentiment = calculate_market_sentiment(coins_data)

    # Combine both datasets in the response
    response_data = {
        "biggestCoins": coins_data,
        "topGainers": top_gainers_data,
        "trendingCoins": trending_coins_data,
        "worstLosers": worst_losers_data,
        "banner": banner_data,
        "sentiment": sentiment
    }

    return create_success_response(
        data=response_data,
        message=f"Successfully fetched {len(coins_data)} top coins and {len(top_gainers_data)} top gainers",
        count=len(coins_data),
        page=page,
        per_page=per_page,
    )
