from singleton_decorator import singleton
from telegram import CallbackQuery, Update
from telegram.error import BadRequest
from src.models.enum.booking_step import BookingStep
from src.models.enum.tariff import Tariff

@singleton
class NavigatonService:

    TARIFF_FLOW = {
        Tariff.DAY: [BookingStep.TARIFF, BookingStep.SAUNA, BookingStep.PHOTOSHOOT, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
        Tariff.DAY_FOR_COUPLE: [BookingStep.TARIFF, BookingStep.SAUNA, BookingStep.PHOTOSHOOT, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
        Tariff.HOURS_12: [BookingStep.TARIFF, BookingStep.FIRST_BEDROOM, BookingStep.SECOND_BEDROOM, BookingStep.SECRET_ROOM, BookingStep.SAUNA, BookingStep.PHOTOSHOOT, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
        Tariff.INCOGNITA_DAY: [BookingStep.TARIFF, BookingStep.PHOTOSHOOT, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
        Tariff.INCOGNITA_HOURS: [BookingStep.TARIFF, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
        Tariff.WORKER: [BookingStep.TARIFF, BookingStep.FIRST_BEDROOM, BookingStep.SECOND_BEDROOM, BookingStep.SECRET_ROOM, BookingStep.SAUNA, BookingStep.PHOTOSHOOT, BookingStep.NUMBER_GUESTS, BookingStep.START_DATE, BookingStep.START_TIME, BookingStep.FINISH_DATE, BookingStep.FINISH_TIME, BookingStep.COMMENT, BookingStep.CONFIRM_BOOKING, BookingStep.CONTACT, BookingStep.PAY, BookingStep.FINISH],
    }

    async def safe_edit_message_text(self, callback_query: CallbackQuery, text, reply_markup=None):
        try:
            await callback_query.edit_message_text(
                text=text,
                parse_mode='HTML',
                reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                # Ignore no-op edits
                pass
            else:
                raise

    async def next_booking_step(self, update: Update, tariff: Tariff, current_step: BookingStep):
        pass

    async def back_booking_step(self, update: Update, tariff: Tariff, current_step: BookingStep):
        pass

    def get_chat_id(self, update: Update) -> int:
        if update.message:
            chat_id = update.message.chat.id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat.id
        return chat_id