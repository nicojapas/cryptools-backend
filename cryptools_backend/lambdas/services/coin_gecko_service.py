"""
Service for interacting with CoinGecko API.
"""

from typing import Any, Dict, List

import requests
import os

from ..config import (COINGECKO_DEFAULT_PARAMS, COINGECKO_TOP_COINS_ENDPOINT,
                      REQUEST_HEADERS, REQUEST_TIMEOUT)
from ..utils import format_coin_data


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

    @staticmethod
    def get_top_gainers(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch top gaining coins by fetching 250 coins and sorting by price change percentage.

        Args:
            limit: Number of coins to fetch (default: 20)

        Returns:
            List of formatted coin data for top gainers
        """
        # Fetch 250 coins to get a good sample for sorting
        params = COINGECKO_DEFAULT_PARAMS.copy()
        params.update({"per_page": 250, "page": 1})
        
        response = requests.get(
            COINGECKO_TOP_COINS_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        
        coins_data = response.json()
        
        # Sort by price change percentage (descending for gainers)
        sorted_coins = sorted(
            coins_data,
            key=lambda x: x.get("price_change_percentage_24h", 0),
            reverse=True
        )
        
        # Take top gainers and format them
        formatted_gainers = []
        for coin in sorted_coins[:limit]:
            formatted_coin = {
                "id": coin.get("id", ""),
                "symbol": coin.get("symbol", "").lower(),
                "name": coin.get("name", ""),
                "image": coin.get("image", ""),
                "price": coin.get("current_price", 0),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
            }
            formatted_gainers.append(formatted_coin)

        return formatted_gainers

    @staticmethod
    def get_worst_losers(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch worst losing coins by fetching 250 coins and sorting by price change percentage.

        Args:
            limit: Number of coins to fetch (default: 20)

        Returns:
            List of formatted coin data for worst losers
        """
        # Fetch 250 coins to get a good sample for sorting
        params = COINGECKO_DEFAULT_PARAMS.copy()
        params.update({"per_page": 250, "page": 1})
        
        response = requests.get(
            COINGECKO_TOP_COINS_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        
        coins_data = response.json()
        
        # Sort by price change percentage (ascending for losers)
        sorted_coins = sorted(
            coins_data,
            key=lambda x: x.get("price_change_percentage_24h", 0),
            reverse=False
        )
        
        # Take worst losers and format them
        formatted_losers = []
        for coin in sorted_coins[:limit]:
            formatted_coin = {
                "id": coin.get("id", ""),
                "symbol": coin.get("symbol", "").lower(),
                "name": coin.get("name", ""),
                "image": coin.get("image", ""),
                "price": coin.get("current_price", 0),
                "price_change_percentage_24h": coin.get("price_change_percentage_24h", 0),
            }
            formatted_losers.append(formatted_coin)

        return formatted_losers

    @staticmethod
    def get_trending_coins() -> List[Dict[str, Any]]:
        """
        Fetch trending coins from CoinGecko API.
        Returns:
            List of trending coins with id, name, symbol, score, and large image url
        """
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        trending = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            trending.append({
                "id": coin.get("id", ""),
                "name": coin.get("name", ""),
                "symbol": coin.get("symbol", ""),
                "score": coin.get("score", 0),
                "large": coin.get("large", ""),
            })
        return trending

    @staticmethod
    def get_banner_data() -> List[Dict[str, Any]]:
        """
        Fetch banner data (top 20 coins by market cap) from CoinGecko API.

        Returns:
            List of formatted coin data for banner
        """
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
