import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import date, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.client.backend_api import BackendAPIClient, APIError
from src.services.logger_service import LoggerService
from src.decorators.callback_error_handler import safe_callback_query
from src.models.enum.tariff import Tariff
from src.config.config import ADMIN_CHAT_ID
from src.constants import (
    END,
    CREATE_PROMO_NAME,
    CREATE_PROMO_TYPE,
    CREATE_PROMO_DATE_FROM,
    CREATE_PROMO_DATE_TO,
    CREATE_PROMO_DISCOUNT,
    CREATE_PROMO_TARIFF,
)
from src.models.enum.promocode_type import PromocodeType
import logging

logger = logging.getLogger(__name__)


async def create_promocode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start promo code creation flow (admin only)"""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return END

    context.user_data["creating_promocode"] = {}

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📝 <b>Создание промокода</b>\n\n"
        "Шаг 1 из 6: Введите название промокода\n"
        "(буквы, цифры, дефис, подчеркивание, пробел; макс. 50 символов)\n\n"
        "Примеры: SUMMER2024, Новый год, Скидка_10"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(__name__, "Promocode creation started", update)
    return CREATE_PROMO_NAME


async def handle_promo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle promo code name input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_NAME

    promo_name = update.message.text.strip().lower()  # Convert to lowercase

    # Validate format - allow cyrillic, latin, digits, dash, underscore, space
    import re

    if not re.match(r"^[А-ЯЁа-яёA-Za-z0-9\-_\s]{1,50}$", promo_name):
        await update.message.reply_text(
            "❌ Неверный формат! Используйте только буквы (русские или латинские), цифры, дефис, подчеркивание и пробел (макс. 50 символов).\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_NAME

    # Check if already exists via API
    api_client = BackendAPIClient()
    try:
        result = await api_client.validate_promocode(promo_name)
        if result.get("valid"):
            await update.message.reply_text(
                f"❌ Промокод <b>{promo_name}</b> уже существует!\n\n"
                "Введите другое название:",
                parse_mode="HTML",
            )
            return CREATE_PROMO_NAME
    except APIError:
        # Promocode doesn't exist, which is good for creation
        pass

    context.user_data["creating_promocode"]["name"] = promo_name

    # Show promocode type selection
    keyboard = [
        [InlineKeyboardButton(
            "📅 Бронирование на конкретные даты",
            callback_data=f"promo_type_{PromocodeType.BOOKING_DATES.value}"
        )],
        [InlineKeyboardButton(
            "⏰ Действие в период (бронь на любые даты)",
            callback_data=f"promo_type_{PromocodeType.USAGE_PERIOD.value}"
        )],
        [InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Название: <b>{promo_name}</b>\n\n"
        "Шаг 2 из 6: Выберите тип промокода\n\n"
        "📅 <b>Бронирование на конкретные даты</b>\n"
        "   Клиент может забронировать ТОЛЬКО на указанные даты промокода\n\n"
        "⏰ <b>Действие в период</b>\n"
        "   Клиент может использовать промокод только в указанный период,\n"
        "   но бронировать на любую дату в будущем"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo name set", update, kwargs={"promo_name": promo_name}
    )
    return CREATE_PROMO_TYPE


async def handle_promo_type_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle promocode type selection"""
    await update.callback_query.answer()

    promo_type_value = int(update.callback_query.data.replace("promo_type_", ""))
    promo_type = PromocodeType(promo_type_value)

    context.user_data["creating_promocode"]["type"] = promo_type.value

    # Generate 10 dates starting from today
    from datetime import timedelta
    keyboard = []
    today = date.today()

    for i in range(10):
        future_date = today + timedelta(days=i)
        date_str = future_date.strftime('%d.%m.%Y')
        day_name = future_date.strftime('%a')  # Mon, Tue, etc.
        button_text = f"📅 {date_str} ({day_name})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"promo_date_from_{date_str}")])

    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    type_text = "📅 Бронирование на конкретные даты" if promo_type == PromocodeType.BOOKING_DATES else "⏰ Действие в период"

    message = (
        f"✅ Тип: <b>{type_text}</b>\n\n"
        "Шаг 3 из 6: Выберите дату начала действия\n"
        "или введите вручную в формате ДД.ММ.ГГГГ"
    )

    await update.callback_query.edit_message_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo type set", update, kwargs={"promo_type": promo_type.name}
    )
    return CREATE_PROMO_DATE_FROM


async def handle_promo_date_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start date input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DATE_FROM

    date_str = update.message.text.strip()
    today_str = date.today().strftime('%d.%m.%Y')

    # Parse date
    try:
        date_from = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\n"
            f"Используйте формат ДД.ММ.ГГГГ, например: {today_str}\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_FROM

    # Validate date is not in the past
    if date_from < date.today():
        await update.message.reply_text(
            "❌ Дата начала не может быть в прошлом!\n\n"
            "Введите дату сегодня или в будущем:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_FROM

    context.user_data["creating_promocode"]["date_from"] = date_from

    # Generate 10 dates starting from date_from
    from datetime import timedelta
    keyboard = []

    for i in range(10):
        future_date = date_from + timedelta(days=i)
        date_str_future = future_date.strftime('%d.%m.%Y')
        day_name = future_date.strftime('%a')
        button_text = f"📅 {date_str_future} ({day_name})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"promo_date_to_{date_str_future}")])

    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата начала: <b>{date_from.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 4 из 6: Выберите дату окончания действия\n"
        "или введите вручную в формате ДД.ММ.ГГГГ"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_from set", update, kwargs={"date_from": date_from}
    )
    return CREATE_PROMO_DATE_TO


async def handle_promo_date_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end date input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DATE_TO

    date_str = update.message.text.strip()
    today_str = date.today().strftime('%d.%m.%Y')

    # Parse date
    try:
        date_to = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\n"
            f"Используйте формат ДД.ММ.ГГГГ, например: {today_str}\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_TO

    date_from = context.user_data["creating_promocode"]["date_from"]

    # Validate date_to >= date_from
    if date_to < date_from:
        await update.message.reply_text(
            f"❌ Дата окончания не может быть раньше даты начала "
            f"(<b>{date_from.strftime('%d.%m.%Y')}</b>)!\n\n"
            f"Пример: {today_str}"
            "Введите дату окончания:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DATE_TO

    context.user_data["creating_promocode"]["date_to"] = date_to

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата окончания: <b>{date_to.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 5 из 6: Введите размер скидки в процентах\n"
        "Пример: 10 (для скидки 10%)\n\n"
        "Диапазон: 1-100"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_to set", update, kwargs={"date_to": date_to}
    )
    return CREATE_PROMO_DISCOUNT


async def handle_promo_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle discount percentage input"""
    if not update.message or not update.message.text:
        return CREATE_PROMO_DISCOUNT

    discount_str = update.message.text.strip()

    # Parse discount
    try:
        discount = float(discount_str)
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Введите число от 1 до 100, например: 15\n\n"
            "Попробуйте снова:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DISCOUNT

    # Validate range
    if not (1 <= discount <= 100):
        await update.message.reply_text(
            "❌ Скидка должна быть от 1% до 100%!\n\nВведите корректное значение:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_DISCOUNT

    context.user_data["creating_promocode"]["discount"] = discount

    # Show tariff selection
    keyboard = []
    keyboard.append(
        [InlineKeyboardButton("✅ ВСЕ ТАРИФЫ", callback_data="promo_tariff_ALL")]
    )

    # Add individual tariffs
    for tariff in Tariff:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"📋 {tariff.name}", callback_data=f"promo_tariff_{tariff.value}"
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Скидка: <b>{discount}%</b>\n\n"
        "Шаг 6 из 6: Выберите тарифы, к которым применим промокод\n\n"
        "Нажмите <b>ВСЕ ТАРИФЫ</b> для применения ко всем тарифам,\n"
        "или выберите конкретный тариф:"
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo discount set", update, kwargs={"discount": discount}
    )
    return CREATE_PROMO_TARIFF


async def handle_promo_date_from_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle date_from selection via button"""
    await update.callback_query.answer()

    date_str = update.callback_query.data.replace("promo_date_from_", "")
    date_from = datetime.strptime(date_str, "%d.%m.%Y").date()
    context.user_data["creating_promocode"]["date_from"] = date_from

    # Generate 10 dates starting from date_from
    from datetime import timedelta
    keyboard = []

    for i in range(10):
        future_date = date_from + timedelta(days=i)
        date_str_future = future_date.strftime('%d.%m.%Y')
        day_name = future_date.strftime('%a')
        button_text = f"📅 {date_str_future} ({day_name})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"promo_date_to_{date_str_future}")])

    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата начала: <b>{date_from.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 4 из 6: Выберите дату окончания действия\n"
        "или введите вручную в формате ДД.ММ.ГГГГ"
    )

    await update.callback_query.edit_message_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_from set via button", update, kwargs={"date_from": date_from}
    )
    return CREATE_PROMO_DATE_TO


async def handle_promo_date_to_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle date_to selection via button"""
    await update.callback_query.answer()

    date_str = update.callback_query.data.replace("promo_date_to_", "")
    date_to = datetime.strptime(date_str, "%d.%m.%Y").date()
    date_from = context.user_data["creating_promocode"]["date_from"]

    # Validate date_to >= date_from
    if date_to < date_from:
        await update.callback_query.answer(
            f"❌ Дата окончания не может быть раньше даты начала!",
            show_alert=True
        )
        return CREATE_PROMO_DATE_TO

    context.user_data["creating_promocode"]["date_to"] = date_to

    keyboard = [[InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"✅ Дата окончания: <b>{date_to.strftime('%d.%m.%Y')}</b>\n\n"
        "Шаг 5 из 6: Введите размер скидки в процентах\n"
        "Пример: 10 (для скидки 10%)\n\n"
        "Диапазон: 1-100"
    )

    await update.callback_query.edit_message_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo date_to set via button", update, kwargs={"date_to": date_to}
    )
    return CREATE_PROMO_DISCOUNT


async def handle_promo_tariff_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle tariff selection"""
    await update.callback_query.answer()

    data = update.callback_query.data

    if data == "cancel_promo_create":
        return await cancel_promo_creation(update, context)

    # Parse tariff selection
    tariff_selection = data.replace("promo_tariff_", "")

    promo_data = context.user_data["creating_promocode"]

    # Determine applicable tariffs
    if tariff_selection == "ALL":
        applicable_tariffs = None  # None = all tariffs
        tariff_text = "ВСЕ ТАРИФЫ"
    else:
        applicable_tariffs = [int(tariff_selection)]
        tariff_name = Tariff(int(tariff_selection)).name
        tariff_text = tariff_name

    # Create promocode via API
    api_client = BackendAPIClient()
    try:
        promocode = await api_client.create_promocode({
            "code": promo_data["name"],
            "promocode_type": PromocodeType(promo_data["type"]).name,
            "discount_percentage": promo_data["discount"],
            "is_active": True
        })

        # Format type display
        promo_type = PromocodeType(promo_data["type"])
        if promo_type == PromocodeType.BOOKING_DATES:
            type_icon = "📅"
            type_text = "Бронирование на конкретные даты"
        else:
            type_icon = "⏰"
            type_text = "Действие в период (бронь на любые даты)"

        # Message with copyable promo code
        message = (
            "✅ <b>Промокод успешно создан!</b>\n\n"
            f"📝 <b>Название:</b> <code>{promocode['code']}</code>\n"
            f"{type_icon} <b>Тип:</b> {type_text}\n"
            f"📅 <b>Период:</b> {promo_data['date_from'].strftime('%d.%m.%Y')} - {promo_data['date_to'].strftime('%d.%m.%Y')}\n"
            f"💰 <b>Скидка:</b> {promocode['discount_percentage']}%\n"
            f"🎯 <b>Тарифы:</b> {tariff_text}\n\n"
            f"📋 Нажмите на код, чтобы скопировать: <code>{promocode['code']}</code>"
        )

        await update.callback_query.edit_message_text(text=message, parse_mode="HTML")

        LoggerService.info(
            __name__,
            "Promocode created successfully",
            update,
            kwargs={"promocode_id": promocode['id'], "name": promocode['code']},
        )

    except APIError as e:
        logger.error(f"Failed to create promocode: {e}")
        await update.callback_query.edit_message_text(
            text=f"❌ Ошибка при создании промокода: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error creating promocode", e)

    # Clear context
    context.user_data.pop("creating_promocode", None)

    return END


@safe_callback_query()
async def cancel_promo_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel promocode creation"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="❌ Создание промокода отменено.", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text="❌ Создание промокода отменено.", parse_mode="HTML"
        )

    context.user_data.pop("creating_promocode", None)
    LoggerService.info(__name__, "Promocode creation cancelled", update)

    return END


def get_create_promocode_handler() -> ConversationHandler:
    """Returns ConversationHandler for /create_promocode command"""
    handler = ConversationHandler(
        entry_points=[CommandHandler("create_promocode", create_promocode_start)],
        states={
            CREATE_PROMO_NAME: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_name,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_TYPE: [
                CallbackQueryHandler(
                    handle_promo_type_selection, pattern="^promo_type_.+$"
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DATE_FROM: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_date_from,
                ),
                CallbackQueryHandler(
                    handle_promo_date_from_button, pattern="^promo_date_from_.+$"
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DATE_TO: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_date_to,
                ),
                CallbackQueryHandler(
                    handle_promo_date_to_button, pattern="^promo_date_to_.+$"
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_DISCOUNT: [
                MessageHandler(
                    filters.Chat(chat_id=ADMIN_CHAT_ID)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    handle_promo_discount,
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
            CREATE_PROMO_TARIFF: [
                CallbackQueryHandler(
                    handle_promo_tariff_selection,
                    pattern="^promo_tariff_.+$",
                ),
                CallbackQueryHandler(
                    cancel_promo_creation, pattern="^cancel_promo_create$"
                ),
            ],
        },
        fallbacks=[],
    )
    return handler


async def list_promocodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active promocodes with delete buttons (admin only)"""
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Эта команда не доступна в этом чате.")
        return

    api_client = BackendAPIClient()
    try:
        promocodes = await api_client.list_promocodes(is_active=True)

        if not promocodes:
            await update.message.reply_text(
                "📋 <b>Активные промокоды</b>\n\n"
                "Промокодов нет.\n\n"
                "Используйте /create_promocode для создания.",
                parse_mode="HTML",
            )
            return

        message_lines = ["📋 <b>Активные промокоды:</b>\n"]
        keyboard = []

        for promo in promocodes:
            # Format type display
            promo_type_str = promo.get("promocode_type", "USAGE_PERIOD")
            if promo_type_str == "BOOKING_DATES":
                type_icon = "📅"
                type_text = "Бронирование на даты"
            else:
                type_icon = "⏰"
                type_text = "Действие в период"

            message_lines.append(
                f"\n🎟️ <b>{promo['code']}</b>\n"
                f"   {type_icon} Тип: {type_text}\n"
                f"   💰 Скидка: {promo['discount_percentage']}%\n"
                f"   🎯 Тарифы: ВСЕ ТАРИФЫ"
            )

            # Add delete button for each promocode
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🗑 Удалить {promo['code']}",
                        callback_data=f"delete_promo_{promo['id']}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "\n".join(message_lines), parse_mode="HTML", reply_markup=reply_markup
        )

        LoggerService.info(__name__, "Listed promocodes", update)

    except APIError as e:
        logger.error(f"Failed to list promocodes: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении списка промокодов: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error listing promocodes", e)


async def handle_delete_promocode_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle promocode deletion via callback button"""
    query = update.callback_query
    await query.answer()

    # Extract promocode ID from callback_data
    callback_data = query.data
    try:
        promocode_id = int(callback_data.replace("delete_promo_", ""))
    except ValueError:
        await query.edit_message_text(
            "❌ Ошибка: неверный ID промокода", parse_mode="HTML"
        )
        return

    api_client = BackendAPIClient()
    try:
        # Deactivate promocode via API
        await api_client.delete_promocode(promocode_id)

        await query.edit_message_text(
            f"✅ Промокод с ID <b>{promocode_id}</b> успешно деактивирован!\n\n"
            f"Используйте /list_promocodes для просмотра оставшихся промокодов.",
            parse_mode="HTML",
        )
        LoggerService.info(
            __name__,
            "Promocode deactivated via button",
            update,
            kwargs={"promocode_id": promocode_id},
        )

    except APIError as e:
        logger.error(f"Failed to delete promocode: {e}")
        await query.edit_message_text(
            f"❌ Ошибка при деактивации промокода: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error deactivating promocode", e)
