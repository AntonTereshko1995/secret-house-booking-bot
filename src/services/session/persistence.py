"""
Custom persistence for Telegram bot conversation states.
Replaces RedisPersistence using SessionStore.
"""
import json
from typing import Dict, Optional, Tuple
from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._utils.types import ConversationDict, CDCData

from src.services.session.session_store import SessionStore
from src.services.logger_service import LoggerService
from src.constants import SESSION_STORAGE_FILE, SESSION_TTL_DAYS, CLEANUP_INTERVAL_DAYS


class CustomPersistence(BasePersistence):
    """
    Stores Telegram conversation states.
    Drop-in replacement for RedisPersistence.
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
        self._store = SessionStore(
            storage_file=SESSION_STORAGE_FILE,
            cleanup_interval_days=CLEANUP_INTERVAL_DAYS
        )
        self._conversations: Dict[str, ConversationDict] = {}
        self._conversation_key_prefix = "conversation_state"
        self._ttl_seconds = SESSION_TTL_DAYS * 86400

    async def get_conversations(self, name: str) -> ConversationDict:
        """Retrieve conversation states"""
        try:
            key = f"{self._conversation_key_prefix}:{name}"
            data = await self._store.get(key)

            if data:
                raw_dict = json.loads(data)
                result = {}
                for key_str, state in raw_dict.items():
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

            existing_data = await self._store.get(redis_key)
            conversations = json.loads(existing_data) if existing_data else {}

            key_str = ",".join(map(str, key))

            if new_state is None:
                conversations.pop(key_str, None)
            else:
                conversations[key_str] = new_state

            await self._store.set(
                redis_key,
                json.dumps(conversations),
                self._ttl_seconds
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
