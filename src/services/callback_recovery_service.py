from singleton_decorator import singleton
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigationService
from src.services.redis_service import RedisService
from src.constants import MENU


@singleton
class CallbackRecoveryService:
    """
    Service to handle recovery from stale callback queries.
    Detects expired sessions and provides auto-recovery.
    """

    def __init__(self):
        self.navigation_service = NavigationService()
        self.redis_service = RedisService()

    async def handle_stale_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message: str = None
    ):
        """
        Handle a stale callback query by showing recovery options.

        Args:
            update: Telegram Update object
            context: Callback context
            message: Optional custom message to show user
        """
        LoggerService.info(
            __name__,
            "Handling stale callback query",
            update
        )

        # Default message
        if not message:
            message = (
                "⚠️ <b>Бот был обновлен</b>\n\n"
                "Кнопки из предыдущей сессии больше не работают.\n"
                "Обновляем главное меню..."
            )

        # Try to send new message with menu (if callback_query exists)
        if update.callback_query and update.callback_query.message:
            try:
                # Try to edit the existing message
                keyboard = [
                    [InlineKeyboardButton(
                        "🏠 Главное меню",
                        callback_data=f"{MENU}"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await self.navigation_service.safe_edit_message_text(
                    callback_query=update.callback_query,
                    text=message,
                    reply_markup=reply_markup
                )
            except:
                # If edit fails, send new message
                try:
                    await update.callback_query.message.reply_text(
                        text=message,
                        parse_mode="HTML"
                    )
                except:
                    pass

        # Clear any stale Redis state
        try:
            self.redis_service.clear_booking(update)
            self.redis_service.clear_feedback(update)
        except:
            pass

        # Auto-redirect to main menu
        from src.handlers import menu_handler
        return await menu_handler.show_menu(update, context)

    def is_callback_stale(self, update: Update) -> bool:
        """
        Detect if a callback query is likely stale.

        Heuristics:
        - Callback data exists but Redis session is empty/expired
        - (Future) Check bot start time vs callback timestamp
        """
        if not update.callback_query:
            return False

        # Check if user has active booking session
        # If callback is for booking but no session exists, it's stale
        callback_data = update.callback_query.data or ""

        if callback_data.startswith("BOOKING-"):
            booking = self.redis_service.get_booking(update)
            if not booking:
                LoggerService.info(
                    __name__,
                    "Callback query appears stale - no active booking session",
                    update
                )
                return True

        return False
