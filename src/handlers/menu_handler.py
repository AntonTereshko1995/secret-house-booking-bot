import sys
import os

from src.services.navigation_service import NavigatonService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.services import job_service
from src.services.database_service import DatabaseService
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
from src.constants import (
    AVAILABLE_DATES,
    BOOKING,
    BOOKING_COMMENT,
    BOOKING_PHOTO_UPLOAD,
    BOOKING_VALIDATE_USER,
    BOOKING_WRITE_CODE,
    CANCEL_BOOKING,
    CANCEL_BOOKING_VALIDATE_USER,
    CASH_PAY,
    CHANGE_BOOKING_DATE,
    CHANGE_BOOKING_DATE_VALIDATE_USER,
    GIFT_PHOTO_UPLOAD,
    END,
    GIFT_CERTIFICATE,
    MENU,
    PRICE,
    QUESTIONS,
    SKIP,
    USER_BOOKING,
    GIFT_VALIDATE_USER,
    USER_BOOKING_VALIDATE_USER,
    INCOGNITO_WINE,
    INCOGNITO_TRANSFER,
)
from src.handlers import (
    booking_handler,
    change_booking_date_handler,
    cancel_booking_handler,
    question_handler,
    price_handler,
    gift_certificate_handler,
    available_dates_handler,
    user_booking,
)

job = job_service.JobService()
navigation_service = NavigatonService()


def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", show_menu),
        ],
        states={
            # GIFT navigation flow
            GIFT_CERTIFICATE: gift_certificate_handler.get_handler(),
            GIFT_VALIDATE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    gift_certificate_handler.check_user_contact,
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            GIFT_PHOTO_UPLOAD: [
                MessageHandler(
                    filters.PHOTO | filters.Document.PDF & filters.Document.PDF,
                    gift_certificate_handler.handle_photo,
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            # CANCEL_BOOKING navigation flow
            CANCEL_BOOKING: cancel_booking_handler.get_handler(),
            CANCEL_BOOKING_VALIDATE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    cancel_booking_handler.check_user_contact,
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            # CHANGE_BOOKING_DATE navigation flow
            CHANGE_BOOKING_DATE: change_booking_date_handler.get_handler(),
            CHANGE_BOOKING_DATE_VALIDATE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    change_booking_date_handler.check_user_contact,
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            # AVAILABLE_DATES navigation flow
            AVAILABLE_DATES: available_dates_handler.get_handler(),
            # PRICE navigation flow
            PRICE: price_handler.get_handler(),
            # QUESTIONS navigation flow
            QUESTIONS: question_handler.get_handler(),
            # QUESTIONS navigation flow
            USER_BOOKING: user_booking.get_handler(),
            USER_BOOKING_VALIDATE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, user_booking.check_user_contact
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            # BOOKING navigation flow
            BOOKING: booking_handler.get_handler(),
            BOOKING_VALIDATE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, booking_handler.check_user_contact
                ),
                CallbackQueryHandler(show_menu, pattern=f"^{END}$"),
            ],
            BOOKING_PHOTO_UPLOAD: [
                MessageHandler(
                    filters.PHOTO | filters.Document.PDF, booking_handler.handle_photo
                ),
                CallbackQueryHandler(
                    booking_handler.cash_pay_booking,
                    pattern=f"^BOOKING-PAY_({CASH_PAY})$",
                ),
            ],
            BOOKING_WRITE_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, booking_handler.write_secret_code
                ),
                CallbackQueryHandler(show_menu, pattern=f"^BOOKING-CODE_({END})$"),
            ],
            BOOKING_COMMENT: [
                CallbackQueryHandler(
                    booking_handler.write_comment, pattern=f"^BOOKING-COMMENT_{SKIP}$"
                ),
                CallbackQueryHandler(show_menu, pattern=f"^BOOKING-COMMENT_{END}$"),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, booking_handler.write_comment
                ),
            ],
            INCOGNITO_WINE: [
                CallbackQueryHandler(
                    booking_handler.handle_wine_preference,
                    pattern="^BOOKING-WINE_(.+)$",
                ),
                CallbackQueryHandler(show_menu, pattern=f"^BOOKING-WINE_{END}$"),
            ],
            INCOGNITO_TRANSFER: [
                CallbackQueryHandler(
                    booking_handler.handle_transfer_skip,
                    pattern=f"^BOOKING-TRANSFER_({SKIP}|{END})$",
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    booking_handler.handle_transfer_input,
                ),
            ],
            # MENU navigation flow
            MENU: [
                CallbackQueryHandler(
                    booking_handler.generate_tariff_menu, pattern=f"^{BOOKING}$"
                ),
                CallbackQueryHandler(
                    cancel_booking_handler.enter_user_contact,
                    pattern=f"^{CANCEL_BOOKING}$",
                ),
                CallbackQueryHandler(
                    change_booking_date_handler.enter_user_contact,
                    pattern=f"^{CHANGE_BOOKING_DATE}$",
                ),
                CallbackQueryHandler(
                    available_dates_handler.select_month, pattern=f"^{AVAILABLE_DATES}$"
                ),
                CallbackQueryHandler(price_handler.send_prices, pattern=f"^{PRICE}$"),
                CallbackQueryHandler(
                    gift_certificate_handler.generate_tariff_menu,
                    pattern=f"^{GIFT_CERTIFICATE}$",
                ),
                CallbackQueryHandler(
                    question_handler.start_conversation, pattern=f"^{QUESTIONS}$"
                ),
                CallbackQueryHandler(
                    user_booking.enter_user_contact, pattern=f"^{USER_BOOKING}$"
                ),
            ],
        },
        fallbacks=[CommandHandler("start", show_menu)],
    )
    return handler


def __capture_and_store_user_chat_id(update: Update) -> None:
    """Capture and store user's chat_id in the database."""
    navigation_service = NavigatonService()
    chat_id = navigation_service.get_chat_id(update)
    user_contact = update.effective_user.username or str(chat_id)

    try:
        database_service = DatabaseService()
        database_service.update_user_chat_id(user_contact, chat_id)
        LoggerService.info(
            __name__,
            "Chat ID stored for user",
            kwargs={"chat_id": chat_id, "contact": user_contact}
        )
    except Exception as e:
        LoggerService.error(
            __name__,
            "Failed to store chat_id",
            exception=e,
            kwargs={"chat_id": chat_id}
        )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    LoggerService.info(__name__, "show menu", update)
    await job.init_job(update, context)

    # Capture and store user's chat_id
    __capture_and_store_user_chat_id(update)

    buttons = [
        [InlineKeyboardButton("Забронировать дом 🏠", callback_data=BOOKING)],
        [
            InlineKeyboardButton(
                "Купить подарочный сертификат 🎁", callback_data=GIFT_CERTIFICATE
            )
        ],
        [InlineKeyboardButton("Мои бронирования 👁️‍🗨️", callback_data=USER_BOOKING)],
        [
            InlineKeyboardButton(
                "Отменить бронирование ❌", callback_data=CANCEL_BOOKING
            )
        ],
        [
            InlineKeyboardButton(
                "Перенести бронирование 🔄", callback_data=CHANGE_BOOKING_DATE
            )
        ],
        [
            InlineKeyboardButton(
                "Проверить свободные даты 📅", callback_data=AVAILABLE_DATES
            )
        ],
        [InlineKeyboardButton("Узнать стоимость аренды 💰", callback_data=PRICE)],
        [InlineKeyboardButton("Задать вопрос ❓", callback_data=QUESTIONS)],
        [
            InlineKeyboardButton(
                "Связаться с администратором 📞", url="https://t.me/the_secret_house"
            )
        ],
    ]

    text = (
        "<b>Добро пожаловать в The Secret House!</b>\n"
        "🏡 <b>Уют, искусство и тайны — всё для вашего идеального отдыха.</b>\n\n"
        "Выберите нужный пункт:\n\n"
    )

    if update.message:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif update.callback_query:
        try:
            context.drop_callback_data(update.callback_query)
            await update.callback_query.answer()
        except:
            pass
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    return MENU
