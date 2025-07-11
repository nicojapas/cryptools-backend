"""
Configuration file for API endpoints and constants.
"""

# CoinGecko API configuration
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_TOP_COINS_ENDPOINT = f"{COINGECKO_API_BASE}/coins/markets"

# CoinGecko API parameters
COINGECKO_DEFAULT_PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": "true",
    "price_change_percentage": "24h",
    "locale": "en",
}

# CryptoPanic API configuration
CRYPTOPANIC_API_BASE = "https://cryptopanic.com/api/developer/v2"
CRYPTOPANIC_NEWS_ENDPOINT = f"{CRYPTOPANIC_API_BASE}/posts/"

# HTTP request configuration
REQUEST_TIMEOUT = 10
REQUEST_HEADERS = {"User-Agent": "CryptoTools-Backend/1.0"}

# S3 configuration
S3_BUCKET = "cryptools-cache"
CACHE_DURATION = 60  # seconds (for banner/tokens)
NEWS_CACHE_DURATION = 3600  # 1 hour for news

# BSC configuration
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"
MAX_STORED_TOKENS = 200

# API limits and pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 250
