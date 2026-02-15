import sys
import os

from src.services.navigation_service import NavigationService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.logger_service import LoggerService
from src.services import job_service
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID, INFORM_CHAT_ID
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
    PROMOCODE_INPUT,
    QUESTIONS,
    SKIP,
    USER_BOOKING,
    GIFT_VALIDATE_USER,
    USER_BOOKING_VALIDATE_USER,
    INCOGNITO_WINE,
    INCOGNITO_TRANSFER,
    FEEDBACK_Q1,
    FEEDBACK_Q2,
    FEEDBACK_Q3,
    FEEDBACK_Q4,
    FEEDBACK_Q5,
    FEEDBACK_Q6,
    FEEDBACK_Q7,
    FEEDBACK_Q8,
    FEEDBACK_Q9,
)
from src.handlers import (
    admin_handler,
    booking_handler,
    change_booking_date_handler,
    cancel_booking_handler,
    question_handler,
    price_handler,
    gift_certificate_handler,
    available_dates_handler,
    user_booking,
    feedback_handler,
    booking_details_handler,
)

job = job_service.JobService()
navigation_service = NavigationService()


def get_handler() -> ConversationHandler:
    handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "start",
                show_menu,
                filters=~filters.Chat(chat_id=[ADMIN_CHAT_ID, INFORM_CHAT_ID])
            ),
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
            PROMOCODE_INPUT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    booking_handler.handle_promocode_input,
                ),
                CallbackQueryHandler(
                    booking_handler.skip_promocode,
                    pattern=f"^BOOKING-PROMO_({SKIP}|{END})$",
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
                CallbackQueryHandler(show_menu, pattern=f"^{MENU}$"),
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
                # Handle feedback button - start feedback conversation
                CallbackQueryHandler(
                    feedback_handler.start_feedback, pattern=r"^START_FEEDBACK_(\d+)$"
                ),
                # Handle booking details management callbacks
                CallbackQueryHandler(
                    booking_details_handler.show_booking_detail, pattern=r"^MBD_\d+$"
                ),
                CallbackQueryHandler(
                    admin_handler.back_to_booking_list, pattern=r"^MBL$"
                ),
            ],
            # Feedback conversation states
            FEEDBACK_Q1: [
                CallbackQueryHandler(feedback_handler.handle_q1_rating, pattern=r"^FBQ1_(\d+)$")
            ],
            FEEDBACK_Q2: [
                CallbackQueryHandler(feedback_handler.handle_q2_rating, pattern=r"^FBQ2_(\d+)$")
            ],
            FEEDBACK_Q3: [
                CallbackQueryHandler(feedback_handler.handle_q3_rating, pattern=r"^FBQ3_(\d+)$")
            ],
            FEEDBACK_Q4: [
                CallbackQueryHandler(feedback_handler.handle_q4_rating, pattern=r"^FBQ4_(\d+)$")
            ],
            FEEDBACK_Q5: [
                CallbackQueryHandler(feedback_handler.handle_q5_rating, pattern=r"^FBQ5_(\d+)$")
            ],
            FEEDBACK_Q6: [
                CallbackQueryHandler(feedback_handler.handle_q6_rating, pattern=r"^FBQ6_(\d+)$")
            ],
            FEEDBACK_Q7: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler.handle_text_response),
                CallbackQueryHandler(feedback_handler.back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
            FEEDBACK_Q8: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler.handle_text_response),
                CallbackQueryHandler(feedback_handler.back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
            FEEDBACK_Q9: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler.handle_text_response),
                CallbackQueryHandler(feedback_handler.back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
        },
        fallbacks=[
            CommandHandler(
                "start",
                show_menu,
                filters=~filters.Chat(chat_id=[ADMIN_CHAT_ID, INFORM_CHAT_ID])
            ),
            # Global fallback for menu callbacks when conversation state is lost
            CallbackQueryHandler(handle_menu_callback_fallback),
        ],
        name="main_menu_conversation",
        persistent=True,
    )
    return handler


async def handle_menu_callback_fallback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Fallback handler for menu callbacks when conversation state is lost.
    This handles cases when bot restarts and users try to use old buttons.
    """
    LoggerService.info(__name__, "Menu callback fallback triggered", update)

    if not update.callback_query:
        return ConversationHandler.END

    callback_data = update.callback_query.data

    # Map callback data to appropriate handlers
    if callback_data == BOOKING:
        return await booking_handler.generate_tariff_menu(update, context)
    elif callback_data == CANCEL_BOOKING:
        return await cancel_booking_handler.enter_user_contact(update, context)
    elif callback_data == CHANGE_BOOKING_DATE:
        return await change_booking_date_handler.enter_user_contact(update, context)
    elif callback_data == AVAILABLE_DATES:
        return await available_dates_handler.select_month(update, context)
    elif callback_data == PRICE:
        return await price_handler.send_prices(update, context)
    elif callback_data == GIFT_CERTIFICATE:
        return await gift_certificate_handler.generate_tariff_menu(update, context)
    elif callback_data == QUESTIONS:
        return await question_handler.start_conversation(update, context)
    elif callback_data == USER_BOOKING:
        return await user_booking.enter_user_contact(update, context)
    elif callback_data == MENU:
        return await show_menu(update, context)
    elif callback_data.startswith("START_FEEDBACK_"):
        # Handle feedback start button
        return await feedback_handler.start_feedback(update, context)
    elif callback_data.startswith("MBD_"):
        # Booking details management callbacks - delegate to booking_details_handler
        LoggerService.info(
            __name__,
            f"Delegating to booking_details_handler for callback: {callback_data}",
            update
        )
        return await booking_details_handler.show_booking_detail(update, context)
    elif callback_data == "MBL":
        # Back to booking list - delegate to admin_handler
        LoggerService.info(
            __name__,
            f"Delegating to admin_handler for callback: {callback_data}",
            update
        )
        return await admin_handler.back_to_booking_list(update, context)
    elif callback_data.startswith("booking_") or callback_data.startswith("gift_"):
        # Admin booking/gift management callbacks - delegate to admin_handler
        LoggerService.info(
            __name__,
            f"Delegating booking/gift callback to admin_handler: {callback_data}",
            update
        )
        if callback_data.startswith("booking_"):
            return await admin_handler.booking_callback(update, context)
        else:
            return await admin_handler.gift_callback(update, context)
    else:
        # Unknown callback - show menu
        LoggerService.warning(
            __name__,
            f"Unknown callback in fallback: {callback_data}",
            update
        )
        return await show_menu(update, context)


def _capture_and_store_user_chat_id(update: Update) -> None:
    """Capture and store user's chat_id in the database."""
    navigation_service = NavigationService()
    chat_id = navigation_service.get_chat_id(update)
    user_name = update.effective_user.username

    try:
        database_service = DatabaseService()
        database_service.update_user_chat_id(user_name, chat_id)
    except Exception as e:
        LoggerService.error(
            __name__,
            "Failed to store chat_id",
            exception=e,
            kwargs={"chat_id": chat_id},
        )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    LoggerService.info(__name__, "show menu", update)
    await job.init_job(update, context)

    # Capture and store user's chat_id
    _capture_and_store_user_chat_id(update)

    # Testing code - commented out
    # service = DatabaseService()
    # booking = service.get_booking_by_id(234)
    # await admin_handler.send_feedback(context, booking)

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
        # [InlineKeyboardButton("Задать вопрос ❓", callback_data=QUESTIONS)],
        [
            InlineKeyboardButton(
                "Связаться с администратором 📞", url="https://t.me/the_secret_house"
            )
        ],
    ]

    text = (
        "<b>Добро пожаловать в The Secret House!</b>\n"
        "🏡 <b>Уют, искусство и тайны — всё для вашего идеального отдыха.</b>\n\n"
        "📱 <b>Мы в соцсетях:</b>\n"
        "• <a href=\"https://www.instagram.com/sekret_blr/\">Instagram (публичный)</a>\n"
        "• <a href=\"https://www.instagram.com/sekret_belarus\">Instagram (закрытый)</a>\n"
        "• <a href=\"https://t.me/sekret_blr\">Telegram канал</a>\n\n"
        "Выберите нужный пункт:\n\n"
    )

    if update.message:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    elif update.callback_query:
        try:
            context.drop_callback_data(update.callback_query)
        except:
            pass
        # Use safe method to handle expired queries
        await navigation_service.safe_answer_callback_query(update.callback_query)
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    return MENU
