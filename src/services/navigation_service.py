from singleton_decorator import singleton
from telegram import CallbackQuery, Update
from telegram.error import BadRequest
from src.models.enum.booking_step import BookingStep
from src.models.enum.tariff import Tariff
from src.services.logger_service import LoggerService


@singleton
class NavigationService:
    TARIFF_FLOW = {
        Tariff.DAY: [
            BookingStep.TARIFF,
            BookingStep.SAUNA,
            BookingStep.PHOTOSHOOT,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
        Tariff.DAY_FOR_COUPLE: [
            BookingStep.TARIFF,
            BookingStep.SAUNA,
            BookingStep.PHOTOSHOOT,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
        Tariff.HOURS_12: [
            BookingStep.TARIFF,
            BookingStep.FIRST_BEDROOM,
            BookingStep.SECOND_BEDROOM,
            BookingStep.SECRET_ROOM,
            BookingStep.SAUNA,
            BookingStep.PHOTOSHOOT,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
        Tariff.INCOGNITA_DAY: [
            BookingStep.TARIFF,
            BookingStep.PHOTOSHOOT,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
        Tariff.INCOGNITA_HOURS: [
            BookingStep.TARIFF,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
        Tariff.WORKER: [
            BookingStep.TARIFF,
            BookingStep.FIRST_BEDROOM,
            BookingStep.SECOND_BEDROOM,
            BookingStep.SECRET_ROOM,
            BookingStep.SAUNA,
            BookingStep.PHOTOSHOOT,
            BookingStep.NUMBER_GUESTS,
            BookingStep.START_DATE,
            BookingStep.START_TIME,
            BookingStep.FINISH_DATE,
            BookingStep.FINISH_TIME,
            BookingStep.COMMENT,
            BookingStep.CONFIRM_BOOKING,
            BookingStep.CONTACT,
            BookingStep.PAY,
            BookingStep.FINISH,
        ],
    }

    async def safe_edit_message_text(
        self, callback_query: CallbackQuery, text, reply_markup=None
    ):
        """
        Safely edit message text, handling common errors gracefully.

        Handles:
        - Message is not modified (no-op edits)
        - Query expired or message deleted (after bot restart)
        """
        try:
            await callback_query.edit_message_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )
        except BadRequest as e:
            error_msg = str(e).lower()
            if "message is not modified" in error_msg:
                # Ignore no-op edits (existing behavior)
                pass
            elif "query is too old" in error_msg or "message to edit not found" in error_msg:
                # Query expired or message deleted - log and continue
                LoggerService.info(
                    __name__,
                    "Cannot edit message - query expired or message deleted",
                    kwargs={"error": str(e)}
                )
                # Don't raise - this is expected after bot restart
            else:
                raise

    async def safe_answer_callback_query(
        self,
        callback_query: CallbackQuery,
        text: str = None,
        show_alert: bool = False
    ) -> bool:
        """
        Safely answer a callback query, handling expired queries gracefully.

        Args:
            callback_query: The callback query to answer
            text: Optional text to show to the user
            show_alert: If True, show as an alert popup

        Returns:
            True if answered successfully, False if query expired
        """
        try:
            await callback_query.answer(text=text, show_alert=show_alert)
            return True
        except BadRequest as e:
            error_msg = str(e).lower()
            if "query is too old" in error_msg or "query id is invalid" in error_msg:
                LoggerService.info(
                    __name__,
                    "Callback query already expired - cannot answer",
                    kwargs={"error": str(e)}
                )
                return False
            else:
                # Re-raise other BadRequest errors
                raise

    async def next_booking_step(
        self, update: Update, tariff: Tariff, current_step: BookingStep
    ):
        pass

    async def back_booking_step(
        self, update: Update, tariff: Tariff, current_step: BookingStep
    ):
        pass

    def get_chat_id(self, update: Update) -> int:
        if update.message:
            chat_id = update.message.chat.id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat.id
        return chat_id
