"""
Service for handling data caching.
"""

from datetime import datetime


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
        try:
            last_modified_dt = datetime.fromisoformat(
                last_modified.replace("Z", "+00:00")
            )
            current_time = datetime.utcnow().replace(tzinfo=last_modified_dt.tzinfo)

            return (current_time - last_modified_dt).total_seconds() <= cache_duration
        except Exception:
            return False
