import asyncio

from telegram.error import Forbidden, BadRequest, TelegramError
from singleton_decorator import singleton
from services.logger_service import LoggerService


@singleton
class ChatValidationService:
    """Service for validating chat IDs and detecting blocked users"""

    async def is_chat_valid(self, bot, chat_id: int) -> bool:
        """
        Check if chat_id is valid and bot is not blocked.

        Uses sendChatAction to avoid cache issues.
        Returns True if chat is accessible, False otherwise.

        CRITICAL: Don't use getChat() - it caches results for weeks!
        Use sendChatAction("typing") instead - returns 403 immediately if blocked.
        """
        try:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
            return True
        except Forbidden as e:
            # User blocked the bot
            LoggerService.info(
                __name__,
                f"Chat {chat_id} blocked bot",
                kwargs={"chat_id": chat_id, "error": str(e)},
            )
            return False
        except BadRequest as e:
            # Chat doesn't exist
            LoggerService.info(
                __name__,
                f"Chat {chat_id} not found",
                kwargs={"chat_id": chat_id, "error": str(e)},
            )
            return False
        except TelegramError as e:
            # Other errors - treat as invalid to be safe
            LoggerService.error(
                __name__,
                f"Error validating chat {chat_id}",
                exception=e,
                kwargs={"chat_id": chat_id},
            )
            return False

    async def validate_all_chat_ids(self, bot, chat_ids: list[int]) -> dict:
        """
        Validate list of chat IDs and return results.

        Returns dict with:
        - total_checked: int
        - valid: int
        - invalid: int
        - invalid_ids: list[int]
        """
        valid_count = 0
        invalid_count = 0
        invalid_ids = []

        for chat_id in chat_ids:
            is_valid = await self.is_chat_valid(bot, chat_id)

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_ids.append(chat_id)

            # Sleep to avoid rate limiting
            await asyncio.sleep(0.1)

        return {
            "total_checked": len(chat_ids),
            "valid": valid_count,
            "invalid": invalid_count,
            "invalid_ids": invalid_ids,
        }
