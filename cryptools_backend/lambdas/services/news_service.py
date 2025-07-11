"""
Service for interacting with CryptoPanic API.
"""

import os
from typing import Any, Dict, List

import requests

from ..config import (CRYPTOPANIC_NEWS_ENDPOINT, REQUEST_HEADERS,
                      REQUEST_TIMEOUT)


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
