"""
Redis connection manager.
Provides a singleton Redis client for use across all Redis services.
"""
import redis
from singleton_decorator import singleton
from telegram_bot.config.config import REDIS_URL, REDIS_PORT, REDIS_SSL
from telegram_bot.services.logger_service import LoggerService


@singleton
class RedisConnection:
    """
    Singleton Redis connection manager.
    Ensures a single Redis client instance is shared across the application.
    """

    def __init__(self):
        """Initialize Redis client with configuration from environment."""
        try:
            self._client = redis.Redis(
                host=REDIS_URL,
                port=REDIS_PORT,
                decode_responses=True,
                ssl=REDIS_SSL,
                ssl_cert_reqs=None,
            )
            # Test connection
            self._client.ping()
            LoggerService.info(__name__, f"Redis connected to {REDIS_URL}:{REDIS_PORT}")
        except Exception as e:
            LoggerService.error(
                __name__,
                "Failed to connect to Redis",
                exception=e,
                kwargs={"host": REDIS_URL, "port": REDIS_PORT}
            )
            raise

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance."""
        return self._client

    def ping(self) -> bool:
        """Check if Redis connection is alive."""
        try:
            return self._client.ping()
        except Exception as e:
            LoggerService.error(__name__, "Redis ping failed", exception=e)
            return False

    def close(self):
        """Close the Redis connection."""
        try:
            self._client.close()
            LoggerService.info(__name__, "Redis connection closed")
        except Exception as e:
            LoggerService.error(__name__, "Failed to close Redis connection", exception=e)
