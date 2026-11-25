import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.constants import (
    END,
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
from src.decorators.callback_error_handler import safe_callback_query
from src.services.database_service import DatabaseService
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigationService
from src.services.redis import RedisSessionService
from src.services.review_api_service import ReviewApiService
from src.services.review_window import review_eligibility

redis_service = RedisSessionService()
navigation_service = NavigationService()
review_api_service = ReviewApiService()
database_service = DatabaseService()


def get_handler():
    """Return ConversationHandler for feedback"""
    handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_feedback, pattern=r"^START_FEEDBACK_(\d+)$")
        ],
        states={
            FEEDBACK_Q1: [
                CallbackQueryHandler(handle_q1_rating, pattern=r"^FBQ1_(\d+)$")
            ],
            FEEDBACK_Q2: [
                CallbackQueryHandler(handle_q2_rating, pattern=r"^FBQ2_(\d+)$")
            ],
            FEEDBACK_Q3: [
                CallbackQueryHandler(handle_q3_rating, pattern=r"^FBQ3_(\d+)$")
            ],
            FEEDBACK_Q4: [
                CallbackQueryHandler(handle_q4_rating, pattern=r"^FBQ4_(\d+)$")
            ],
            FEEDBACK_Q5: [
                CallbackQueryHandler(handle_q5_rating, pattern=r"^FBQ5_(\d+)$")
            ],
            FEEDBACK_Q6: [
                CallbackQueryHandler(handle_q6_rating, pattern=r"^FBQ6_(\d+)$")
            ],
            FEEDBACK_Q7: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response),
                CallbackQueryHandler(back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
            FEEDBACK_Q8: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response),
                CallbackQueryHandler(back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
            FEEDBACK_Q9: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response),
                CallbackQueryHandler(back_to_menu, pattern=f"^FEEDBACK_{END}$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(back_to_menu, pattern=f"^FEEDBACK_{END}$")],
    )
    return handler


@safe_callback_query()
async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Initialize feedback and show Q1"""
    await update.callback_query.answer()

    # Extract booking_id from callback_data
    booking_id = int(update.callback_query.data.split("_")[-1])

    # Early refusal: do not ask nine questions if the booking is not eligible.
    # The API remains the source of truth and re-checks everything on submit.
    booking = database_service.get_booking_by_id(booking_id)
    can_review, _ = review_eligibility(booking)
    if not can_review:
        if booking is None:
            message = "Бронирование не найдено."
        elif booking.feedback_submitted:
            message = "Вы уже оставили отзыв для этого бронирования."
        elif booking.is_canceled or not booking.is_prepaymented:
            message = "Отзыв для этого бронирования недоступен."
        else:
            message = "Период для отзыва об этом бронировании истёк."
        await navigation_service.safe_edit_message_text(
            callback_query=update.callback_query,
            text=message,
        )
        LoggerService.info(
            __name__,
            "Feedback not available",
            update,
            booking_id=booking_id, reason=message,
        )
        return ConversationHandler.END

    # Initialize Redis with booking_id and chat_id
    chat_id = update.effective_chat.id
    redis_service.init_feedback(update)
    redis_service.update_feedback_field(update, "booking_id", booking_id)
    redis_service.update_feedback_field(update, "chat_id", chat_id)

    LoggerService.info(
        __name__,
        "Feedback conversation started",
        update,
        booking_id=booking_id,
    )

    # Show Q1
    await show_question_1(update, context)
    return FEEDBACK_Q1


async def show_question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q1: Оправдались ли ваши ожидания от отдыха в нашем доме?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ1_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ1_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 1 из 9</b>\n\n"
        "Оправдались ли ваши ожидания от отдыха в нашем доме?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q1_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q1 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "expectations_rating", rating)

    LoggerService.info(
        __name__, "Q1 rating received", update, rating=rating
    )

    await show_question_2(update, context)
    return FEEDBACK_Q2


async def show_question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q2: Как бы вы оценили уровень комфорта и удобства пребывания в доме?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ2_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ2_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 2 из 9</b>\n\n"
        "Как бы вы оценили уровень комфорта и удобства пребывания в доме?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q2_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q2 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "comfort_rating", rating)

    LoggerService.info(
        __name__, "Q2 rating received", update, rating=rating
    )

    await show_question_3(update, context)
    return FEEDBACK_Q3


async def show_question_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q3: Как бы вы оценили чистоту и общую уборку в доме?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ3_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ3_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 3 из 9</b>\n\n"
        "Как бы вы оценили чистоту и общую уборку в доме?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q3_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q3 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "cleanliness_rating", rating)

    LoggerService.info(
        __name__, "Q3 rating received", update, rating=rating
    )

    await show_question_4(update, context)
    return FEEDBACK_Q4


async def show_question_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q4: Как бы вы оценили общение и поддержку от нас как хозяев?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ4_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ4_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 4 из 9</b>\n\n"
        "Как бы вы оценили общение и поддержку от нас как хозяев?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q4_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q4 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "host_support_rating", rating)

    LoggerService.info(
        __name__, "Q4 rating received", update, rating=rating
    )

    await show_question_5(update, context)
    return FEEDBACK_Q5


async def show_question_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q5: Как бы вы оценили расположение дома и его окружающую территорию?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ5_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ5_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 5 из 9</b>\n\n"
        "Как бы вы оценили расположение дома и его окружающую территорию "
        "(удобство добираться, близость к лесу, озеру, состояние территории вокруг дома и т.д.)?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q5_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q5 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "location_rating", rating)

    LoggerService.info(
        __name__, "Q5 rating received", update, rating=rating
    )

    await show_question_6(update, context)
    return FEEDBACK_Q6


async def show_question_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q6: Рекомендовали бы вы наш дом своим друзьям?"""
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"FBQ6_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"FBQ6_{i}") for i in range(6, 11)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="<b>Вопрос 6 из 9</b>\n\n"
        "Рекомендовали бы вы наш дом своим друзьям?\n\n"
        "Оцените от 1 до 10:",
        reply_markup=reply_markup,
    )


@safe_callback_query()
async def handle_q6_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q6 rating (last rating question)"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "recommendation_rating", rating)

    LoggerService.info(
        __name__, "Q6 rating received", update, rating=rating
    )

    # Transition to text questions
    await show_question_7(update, context)
    return FEEDBACK_Q7


async def show_question_7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q7: Что вам больше всего понравилось в доме и на его территории?"""
    redis_service.update_feedback_field(update, "current_question", 7)

    await update.callback_query.edit_message_text(
        text="<b>Вопрос 7 из 9</b>\n\n"
        "Что вам больше всего понравилось в доме и на его территории?\n\n"
        "Напишите ваш ответ:",
        parse_mode="HTML",
    )


async def show_question_8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q8: Что следует улучшить?"""
    redis_service.update_feedback_field(update, "current_question", 8)

    await update.message.reply_text(
        text="<b>Вопрос 8 из 9</b>\n\n"
        "Есть ли что-то, что, по вашему мнению, следует улучшить в доме или его окружающей территории?\n\n"
        "Напишите ваш ответ:",
        parse_mode="HTML",
    )


async def show_question_9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Q9: Публичный отзыв"""
    redis_service.update_feedback_field(update, "current_question", 9)

    await update.message.reply_text(
        text="<b>Вопрос 9 из 9</b>\n\n"
        "Напишите пожалуйста ваш отзыв, которым мы поделимся с другими гостями:\n\n"
        "Напишите ваш ответ:",
        parse_mode="HTML",
    )


async def handle_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text responses for Q7, Q8, Q9"""
    feedback_data = redis_service.get_feedback(update)
    if not feedback_data:
        LoggerService.warning(__name__, "No feedback data found in Redis", update)
        return ConversationHandler.END

    current_q = feedback_data.current_question
    text = update.message.text

    # Validate text length (max 1000 characters)
    if len(text) > 1000:
        await update.message.reply_text(
            "⚠️ Ваш ответ слишком длинный. Пожалуйста, ограничьтесь 1000 символами."
        )
        return current_q  # Stay in same state

    if current_q == 7:
        # Store Q7 answer
        redis_service.update_feedback_field(update, "liked_most", text)
        LoggerService.info(__name__, "Q7 answer received", update)
        await show_question_8(update, context)
        return FEEDBACK_Q8

    elif current_q == 8:
        # Store Q8 answer
        redis_service.update_feedback_field(update, "improvements", text)
        LoggerService.info(__name__, "Q8 answer received", update)
        await show_question_9(update, context)
        return FEEDBACK_Q9

    elif current_q == 9:
        # Store Q9 answer (final question)
        redis_service.update_feedback_field(update, "public_review", text)
        LoggerService.info(__name__, "Q9 answer received", update)

        # Submit the review to the API: it stores the review, mints the
        # personal single-use promo code and notifies the admin chat.
        result = await submit_review_to_api(update)

        # Thank user and show menu button
        keyboard = [
            [InlineKeyboardButton("Главное меню 🏠", callback_data=f"FEEDBACK_{END}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if result is not None:
            promo_code = result.get("rewardPromoCode")
            valid_until = result.get("validUntil")
            valid_until_text = "3 месяца"
            if valid_until:
                try:
                    valid_until_text = datetime.strptime(
                        valid_until, "%Y-%m-%d"
                    ).strftime("%d.%m.%Y")
                except ValueError:
                    valid_until_text = str(valid_until)

            thank_you_message = (
                "Спасибо за ваш отзыв! 🌟\n"
                "Ваше мнение очень важно для нас.\n\n"
                f"🎁 <b>Ваш промокод на 10% скидку:</b> <code>{promo_code}</code>\n\n"
                f"Промокод действителен до <b>{valid_until_text}</b> и применим "
                "ко всем тарифам.\n"
                "Используйте его при следующем бронировании! 🏡"
            )
            # Answers are no longer needed once the review is saved.
            redis_service.clear_feedback(update)
        else:
            thank_you_message = (
                "Не удалось отправить ваш отзыв. Попробуйте позже — "
                "ваши ответы сохранены."
            )
            # On an API error the answers stay in Redis so nothing is lost.

        await update.message.reply_text(
            thank_you_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        return f"FEEDBACK_{END}"

    # Fallback
    return f"FEEDBACK_{END}"


async def submit_review_to_api(update: Update) -> dict | None:
    """Submit the collected review to the backend API.

    The bot no longer creates the promo code itself and no longer sends the
    review text to the admin chat: the API stores the review, mints the
    personal single-use promo code and notifies the admin chat.
    """
    feedback_data = redis_service.get_feedback(update)
    if not feedback_data:
        LoggerService.error(__name__, "No feedback data to send", update)
        return None

    booking = database_service.get_booking_by_id(feedback_data.booking_id)
    if not booking:
        LoggerService.error(
            __name__,
            "Booking not found for review submission",
            update,
            booking_id=feedback_data.booking_id,
        )
        return None

    payload = {
        "bookingPublicId": str(booking.public_id),
        "ratingExpectations": feedback_data.expectations_rating,
        "ratingComfort": feedback_data.comfort_rating,
        "ratingCleanliness": feedback_data.cleanliness_rating,
        "ratingCommunication": feedback_data.host_support_rating,
        "ratingLocation": feedback_data.location_rating,
        "ratingRecommendation": feedback_data.recommendation_rating,
        "likedMost": feedback_data.liked_most,
        "improvement": feedback_data.improvements,
        "publicReview": feedback_data.public_review,
    }

    # submit_review uses blocking `requests`: run it off the event loop.
    result = await asyncio.to_thread(review_api_service.submit_review, payload)
    if result is None:
        LoggerService.error(
            __name__,
            "API rejected review submission",
            update,
            booking_id=feedback_data.booking_id,
        )
        return None

    LoggerService.info(
        __name__,
        "Review submitted to API",
        update,
        booking_id=feedback_data.booking_id, promocode=result.get("rewardPromoCode"),
    )
    return result


@safe_callback_query()
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu after feedback completion"""
    await update.callback_query.answer()
    redis_service.clear_feedback(update)

    LoggerService.info(__name__, "User returned to menu after feedback", update)

    # Import here to avoid circular import
    from src.handlers import menu_handler

    return await menu_handler.show_menu(update, context)
