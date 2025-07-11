"""
Service layer for external API calls and data processing.
"""

import os
from typing import Any, Dict, List

import requests

from .config import (COINGECKO_DEFAULT_PARAMS, COINGECKO_TOP_COINS_ENDPOINT,
                     CRYPTOPANIC_NEWS_ENDPOINT, REQUEST_HEADERS,
                     REQUEST_TIMEOUT)
from .utils import format_coin_data


class CoinGeckoService:
    """Service for interacting with CoinGecko API."""

    @staticmethod
    def get_top_coins(per_page: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch top coins by market cap from CoinGecko API.

        Args:
            per_page: Number of coins to fetch (max 250)
            page: Page number for pagination

        Returns:
            List of formatted coin data
        """
        params = COINGECKO_DEFAULT_PARAMS.copy()
        params.update({"per_page": min(per_page, 250), "page": page})  # CoinGecko limit

        response = requests.get(
            COINGECKO_TOP_COINS_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        coins_data = response.json()

        # Format the data
        formatted_coins = [format_coin_data(coin) for coin in coins_data]

        return formatted_coins

    @staticmethod
    def get_coin_by_id(coin_id: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific coin.

        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin')

        Returns:
            Formatted coin data
        """
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"

        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        coin_data = response.json()

        # Extract market data
        market_data = coin_data.get("market_data", {})

        formatted_coin = {
            "symbol": coin_data.get("symbol", "").lower(),
            "name": coin_data.get("name", ""),
            "image": coin_data.get("image", {}).get("large", ""),
            "currentPrice": str(market_data.get("current_price", {}).get("usd", 0)),
            "marketCap": str(market_data.get("market_cap", {}).get("usd", 0)),
            "marketCapRank": market_data.get("market_cap_rank", 0),
            "priceChange24H": str(market_data.get("price_change_24h", 0)),
            "marketCapChange24H": str(market_data.get("market_cap_change_24h", 0)),
            "marketCapChangePercentage24H": str(
                market_data.get("market_cap_change_percentage_24h", 0)
            ),
            "circulatingSupply": str(market_data.get("circulating_supply", 0)),
            "sparkline7D": [],  # Would need separate call for sparkline
            "stable": market_data.get("price_change_percentage_24h", 0) < 1,
            "wrapped": "wrapped" in coin_data.get("name", "").lower()
            or "w" in coin_data.get("symbol", "").lower(),
            "description": coin_data.get("description", {}).get("en", ""),
            "categories": coin_data.get("categories", []),
            "links": coin_data.get("links", {}),
        }

        return formatted_coin


class NewsService:
    """Service for interacting with CryptoPanic API."""

    @staticmethod
    def get_trending_news(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch trending cryptocurrency news from CryptoPanic API.

        Args:
            limit: Number of news items to fetch (default: 20)

        Returns:
            List of formatted news data
        """
        # Get API token from environment variable
        api_token = os.environ.get("CRYPTOPANIC_API_TOKEN")

        if not api_token:
            raise ValueError("CRYPTOPANIC_API_TOKEN environment variable is not set")

        # Prepare request parameters
        params = {
            "auth_token": api_token,
            "filter": "hot",  # Get hot/trending news
            "public": "true",  # Only public posts
            "currencies": "BTC,ETH",  # Focus on major cryptocurrencies
            "limit": limit,
        }

        # Make request to CryptoPanic API
        response = requests.get(
            CRYPTOPANIC_NEWS_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        # Parse response
        data = response.json()

        # Extract and format news items
        news_items = []
        for result in data.get("results", []):
            news_item = {
                "id": result.get("id"),
                "title": result.get("title"),
                "summary": result.get("metadata", {}).get("description", ""),
                "source": result.get("source", {}).get("title", "Unknown"),
                "published_at": result.get("published_at"),
                "url": result.get("url"),
                "currencies": [
                    curr.get("code") for curr in result.get("currencies", [])
                ],
                "votes": result.get("votes", {}),
                "domain": result.get("domain"),
            }
            news_items.append(news_item)

        return news_items


class CacheService:
    """Service for handling data caching."""

    @staticmethod
    def is_cache_valid(last_modified: str, cache_duration: int = 60) -> bool:
        """
        Check if cached data is still valid.

        Args:
            last_modified: Last modified timestamp
            cache_duration: Cache duration in seconds

        Returns:
            True if cache is valid, False otherwise
        """
        from datetime import datetime

        try:
            last_modified_dt = datetime.fromisoformat(
                last_modified.replace("Z", "+00:00")
            )
            current_time = datetime.utcnow().replace(tzinfo=last_modified_dt.tzinfo)

            return (current_time - last_modified_dt).total_seconds() <= cache_duration
        except Exception:
            return False
