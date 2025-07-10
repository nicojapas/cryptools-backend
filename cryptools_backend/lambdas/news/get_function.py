from ..utils import layers, handle_http_errors, create_success_response
from ..services import NewsService
from ..config import S3_BUCKET, NEWS_CACHE_DURATION
from ..s3_utils import get_cached_or_fetch


@layers(["requests"])
@handle_http_errors
def lambda_handler(event, context):
    """
    Lambda handler for cryptocurrency news data with caching.
    Returns trending crypto news from CryptoPanic, cached for 1 hour.
    """
    # Get cached data or fetch new data
    news_data = get_cached_or_fetch(
        bucket_name=S3_BUCKET,
        cache_key="crypto_news.json",
        fetch_function=NewsService.get_trending_news,
        cache_duration=NEWS_CACHE_DURATION
    )

    return create_success_response(
        data=news_data,
        message="Cryptocurrency news retrieved successfully",
        count=len(news_data)
    )
    
    
    
