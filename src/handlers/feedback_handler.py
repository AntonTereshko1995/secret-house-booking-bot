import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
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
from src.services.redis_service import RedisService
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigatonService
from src.services.database_service import DatabaseService
from src.config.config import ADMIN_CHAT_ID

redis_service = RedisService()
navigation_service = NavigatonService()


def get_handler():
    """Return list of handlers for feedback conversation"""
    return [
        # Entry point - start feedback
        CallbackQueryHandler(start_feedback, pattern=r"^START_FEEDBACK_(\d+)$"),
        # Q1-Q6: Rating questions (1-10 buttons)
        CallbackQueryHandler(handle_q1_rating, pattern=r"^FBQ1_(\d+)$"),
        CallbackQueryHandler(handle_q2_rating, pattern=r"^FBQ2_(\d+)$"),
        CallbackQueryHandler(handle_q3_rating, pattern=r"^FBQ3_(\d+)$"),
        CallbackQueryHandler(handle_q4_rating, pattern=r"^FBQ4_(\d+)$"),
        CallbackQueryHandler(handle_q5_rating, pattern=r"^FBQ5_(\d+)$"),
        CallbackQueryHandler(handle_q6_rating, pattern=r"^FBQ6_(\d+)$"),
        # Q7-Q9: Text input questions
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response),
        # Cancel button
        CallbackQueryHandler(cancel_feedback, pattern="^CANCEL_FEEDBACK$"),
        # Back to menu button
        CallbackQueryHandler(back_to_menu, pattern=f"^{END}$"),
    ]


async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Initialize feedback and show Q1"""
    await update.callback_query.answer()

    # Extract booking_id from callback_data
    booking_id = int(update.callback_query.data.split("_")[-1])
    chat_id = update.effective_chat.id

    # Initialize Redis with booking_id and chat_id
    redis_service.init_feedback(update)
    redis_service.update_feedback_field(update, "booking_id", booking_id)
    redis_service.update_feedback_field(update, "chat_id", chat_id)

    LoggerService.info(
        __name__,
        "Feedback conversation started",
        update,
        kwargs={"booking_id": booking_id},
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


async def handle_q1_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q1 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "expectations_rating", rating)

    LoggerService.info(
        __name__, "Q1 rating received", update, kwargs={"rating": rating}
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


async def handle_q2_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q2 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "comfort_rating", rating)

    LoggerService.info(
        __name__, "Q2 rating received", update, kwargs={"rating": rating}
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


async def handle_q3_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q3 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "cleanliness_rating", rating)

    LoggerService.info(
        __name__, "Q3 rating received", update, kwargs={"rating": rating}
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


async def handle_q4_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q4 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "host_support_rating", rating)

    LoggerService.info(
        __name__, "Q4 rating received", update, kwargs={"rating": rating}
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


async def handle_q5_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q5 rating button click"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "location_rating", rating)

    LoggerService.info(
        __name__, "Q5 rating received", update, kwargs={"rating": rating}
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


async def handle_q6_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Q6 rating (last rating question)"""
    await update.callback_query.answer()

    rating = int(update.callback_query.data.split("_")[-1])
    redis_service.update_feedback_field(update, "recommendation_rating", rating)

    LoggerService.info(
        __name__, "Q6 rating received", update, kwargs={"rating": rating}
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
        return END

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

        # Send to admin
        await send_feedback_to_admin(update, context)

        # Thank user and show menu button
        keyboard = [[InlineKeyboardButton("Главное меню 🏠", callback_data=END)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Спасибо за ваш отзыв! 🌟\n"
            "Ваше мнение очень важно для нас.\n\n"
            "После получения фидбека мы дарим Вам <b>10% скидки</b> для следующей поездки.",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

        # Clean up Redis
        redis_service.clear_feedback(update)

        return END

    # Fallback
    return END


async def send_feedback_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send complete feedback to ADMIN_CHAT_ID (NO database storage)"""
    feedback_data = redis_service.get_feedback(update)

    if not feedback_data:
        LoggerService.error(__name__, "No feedback data to send", update)
        return

    # Get user contact from database
    database_service = DatabaseService()
    booking = database_service.get_booking_by_id(feedback_data.booking_id)
    user = database_service.get_user_by_id(booking.user_id)
    user_contact = user.contact

    # Format message for admin
    message = (
        "📊 <b>Новый отзыв клиента</b>\n\n"
        f"<b>Пользователь:</b> {user_contact}\n\n"
        f"<b>1. Ожидания от отдыха:</b> {feedback_data.expectations_rating}/10\n"
        f"<b>2. Уровень комфорта:</b> {feedback_data.comfort_rating}/10\n"
        f"<b>3. Чистота и уборка:</b> {feedback_data.cleanliness_rating}/10\n"
        f"<b>4. Общение и поддержка:</b> {feedback_data.host_support_rating}/10\n"
        f"<b>5. Расположение дома:</b> {feedback_data.location_rating}/10\n"
        f"<b>6. Рекомендация друзьям:</b> {feedback_data.recommendation_rating}/10\n\n"
        f"<b>7. Что понравилось:</b>\n{feedback_data.liked_most}\n\n"
        f"<b>8. Что улучшить:</b>\n{feedback_data.improvements}\n\n"
        f"<b>9. Публичный отзыв:</b>\n{feedback_data.public_review}"
    )

    # Send to ADMIN_CHAT_ID
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID, text=message, parse_mode="HTML"
    )

    # Mark feedback as submitted in database
    if booking:
        booking.feedback_submitted = True
        database_service.update_booking(booking)
        LoggerService.info(
            __name__,
            "Booking marked as feedback submitted",
            update,
            kwargs={"booking_id": feedback_data.booking_id},
        )

    LoggerService.info(
        __name__,
        "Feedback sent to admin",
        update,
        kwargs={"booking_id": feedback_data.booking_id, "user_contact": user_contact},
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu after feedback completion"""
    await update.callback_query.answer()
    redis_service.clear_feedback(update)

    LoggerService.info(__name__, "User returned to menu after feedback", update)

    # Import here to avoid circular import
    from src.handlers import menu_handler

    return await menu_handler.show_menu(update, context)


async def cancel_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel feedback conversation"""
    await update.callback_query.answer()
    redis_service.clear_feedback(update)

    await update.callback_query.edit_message_text(
        "Отзыв отменен. Спасибо за ваше время!"
    )

    LoggerService.info(__name__, "Feedback canceled by user", update)

    return END
