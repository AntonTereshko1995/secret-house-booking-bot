"""
Redis-based persistence for Telegram bot conversation states.
This allows the bot to maintain user sessions across restarts.
"""
import json
from typing import Dict, Optional, Tuple
from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._utils.types import ConversationDict, CDCData
from telegram_bot.services.redis.redis_connection import RedisConnection
from telegram_bot.services.logger_service import LoggerService


class RedisPersistence(BasePersistence):
    """
    Custom persistence implementation using Redis.
    Stores conversation states to allow seamless bot restarts.
    """

    def __init__(self):
        super().__init__(
            store_data=PersistenceInput(
                user_data=False,
                chat_data=False,
                bot_data=False,
                callback_data=False,
            ),
            update_interval=1.0,
        )
        self._redis = RedisConnection()
        self._conversations: Dict[str, ConversationDict] = {}
        self._conversation_key_prefix = "conversation_state"
        self._ttl = 259200  # 3 dayes

    async def get_conversations(self, name: str) -> ConversationDict:
        """Retrieve conversation states from Redis"""
        try:
            key = f"{self._conversation_key_prefix}:{name}"
            data = self._redis.client.get(key)

            if data:
                # Parse JSON and convert keys back to tuples
                raw_dict = json.loads(data)
                result = {}
                for key_str, state in raw_dict.items():
                    # Convert "chat_id,user_id" back to (chat_id, user_id) tuple
                    parts = key_str.split(",")
                    if len(parts) == 2:
                        conversation_key = (int(parts[0]), int(parts[1]))
                        result[conversation_key] = state
                        LoggerService.info(
                            __name__,
                            f"Restored conversation state: key={conversation_key}, state={state}, name='{name}'"
                        )

                LoggerService.info(
                    __name__,
                    f"Loaded {len(result)} conversation states for '{name}'"
                )
                return result
            else:
                LoggerService.info(
                    __name__,
                    f"No conversation states found for '{name}'"
                )

            return {}
        except Exception as e:
            LoggerService.error(
                __name__,
                f"Failed to load conversations for '{name}'",
                exception=e
            )
            return {}

    async def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        """Update conversation state in Redis"""
        try:
            redis_key = f"{self._conversation_key_prefix}:{name}"

            # Get existing conversations
            existing_data = self._redis.client.get(redis_key)
            conversations = json.loads(existing_data) if existing_data else {}

            # Convert tuple key to string for JSON serialization
            key_str = ",".join(map(str, key))

            if new_state is None:
                # Remove conversation
                conversations.pop(key_str, None)
            else:
                # Update conversation state
                conversations[key_str] = new_state

            # Save back to Redis with TTL
            self._redis.client.setex(
                redis_key,
                self._ttl,
                json.dumps(conversations)
            )

        except Exception as e:
            LoggerService.error(
                __name__,
                f"Failed to update conversation '{name}'",
                exception=e,
                kwargs={"key": key, "new_state": new_state}
            )

    async def get_user_data(self) -> Dict:
        """Not implemented - user data not stored"""
        return {}

    async def get_chat_data(self) -> Dict:
        """Not implemented - chat data not stored"""
        return {}

    async def get_bot_data(self) -> Dict:
        """Not implemented - bot data not stored"""
        return {}

    async def get_callback_data(self) -> Optional[CDCData]:
        """Not implemented - callback data not stored"""
        return None

    async def update_user_data(self, user_id: int, data: Dict) -> None:
        """Not implemented - user data not stored"""
        pass

    async def update_chat_data(self, chat_id: int, data: Dict) -> None:
        """Not implemented - chat data not stored"""
        pass

    async def update_bot_data(self, data: Dict) -> None:
        """Not implemented - bot data not stored"""
        pass

    async def update_callback_data(self, data: CDCData) -> None:
        """Not implemented - callback data not stored"""
        pass

    async def drop_chat_data(self, chat_id: int) -> None:
        """Not implemented - chat data not stored"""
        pass

    async def drop_user_data(self, user_id: int) -> None:
        """Not implemented - user data not stored"""
        pass

    async def refresh_user_data(self, user_id: int, user_data: Dict) -> None:
        """Not implemented - user data not stored"""
        pass

    async def refresh_chat_data(self, chat_id: int, chat_data: Dict) -> None:
        """Not implemented - chat data not stored"""
        pass

    async def refresh_bot_data(self, bot_data: Dict) -> None:
        """Not implemented - bot data not stored"""
        pass

    async def flush(self) -> None:
        """Flush any pending writes - no-op for immediate writes"""
        pass
