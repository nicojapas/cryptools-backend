from ..config import NEWS_CACHE_DURATION, S3_BUCKET
from ..s3_utils import get_cached_or_fetch
from ..services.news_service import NewsService
from ..utils import create_success_response, handle_http_errors


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
        cache_duration=NEWS_CACHE_DURATION,
    )

    return create_success_response(
        data=news_data,
        message="Cryptocurrency news retrieved successfully",
        count=len(news_data),
    )
