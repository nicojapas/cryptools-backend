"""
S3 utilities for Lambda functions to cache data.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3


class S3CacheService:
    """Service for caching data in S3 with expiration."""

    def __init__(self, bucket_name: str, cache_duration: int = 60):
        """
        Initialize S3 cache service.

        Args:
            bucket_name: S3 bucket name for caching
            cache_duration: Cache duration in seconds (default: 60)
        """
        self.bucket_name = bucket_name
        self.cache_duration = cache_duration
        self.s3_client = boto3.client("s3")

    def get_cached_data(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached data from S3 if it exists and is not expired.

        Args:
            key: S3 object key

        Returns:
            Cached data as list of dictionaries, or None if not found/expired
        """
        try:
            # Get the object's metadata to check the last modified timestamp
            metadata = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            last_modified = metadata["LastModified"].isoformat()

            # Check if the cached data is still valid
            if self._is_cache_valid(last_modified):
                # Fetch the cached data
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                cached_json = response["Body"].read().decode("utf-8")
                return json.loads(cached_json)
        except self.s3_client.exceptions.NoSuchKey:
            # File does not exist
            pass
        except Exception as e:
            print(f"Error retrieving cached data: {e}")
        return None

    def save_data(self, key: str, data: List[Dict[str, Any]]) -> None:
        """
        Save data to S3 cache.

        Args:
            key: S3 object key
            data: Data to cache
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data),
                ContentType="application/json",
            )
        except Exception as e:
            print(f"Error saving data to S3: {e}")

    def _is_cache_valid(self, last_modified: str) -> bool:
        """
        Check if cached data is still valid.

        Args:
            last_modified: Last modified timestamp

        Returns:
            True if cache is valid, False otherwise
        """
        try:
            last_modified_dt = datetime.fromisoformat(
                last_modified.replace("Z", "+00:00")
            )
            current_time = datetime.utcnow().replace(tzinfo=last_modified_dt.tzinfo)

            return (
                current_time - last_modified_dt
            ).total_seconds() <= self.cache_duration
        except Exception:
            return False


# Convenience function for quick cache operations
def get_cached_or_fetch(
    bucket_name: str, cache_key: str, fetch_function, cache_duration: int = 60
) -> List[Dict[str, Any]]:
    """
    Get cached data or fetch new data if cache is expired/missing.

    Args:
        bucket_name: S3 bucket name
        cache_key: S3 object key for caching
        fetch_function: Function to call for fetching new data
        cache_duration: Cache duration in seconds

    Returns:
        Data (either from cache or freshly fetched)
    """
    cache_service = S3CacheService(bucket_name, cache_duration)

    # Try to get cached data
    cached_data = cache_service.get_cached_data(cache_key)
    if cached_data:
        print(f"Returning cached data for key: {cache_key}")
        return cached_data

    # Fetch new data
    print(f"Fetching new data for key: {cache_key}")
    new_data = fetch_function()

    # Cache the new data
    cache_service.save_data(cache_key, new_data)

    return new_data
