from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.services.logger_service import LoggerService
from src.decorators.callback_error_handler import safe_callback_query
from src.services.database_service import DatabaseService
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
from datetime import datetime

database_service = DatabaseService()


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

    # Check if already exists
    existing = database_service.get_promocode_by_name(promo_name)
    if existing:
        await update.message.reply_text(
            f"❌ Промокод <b>{promo_name}</b> уже существует!\n\n"
            "Введите другое название:",
            parse_mode="HTML",
        )
        return CREATE_PROMO_NAME

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
        __name__, "Promo name set", update, **{"promo_name": promo_name}
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
        __name__, "Promo type set", update, **{"promo_type": promo_type.name}
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
        __name__, "Promo date_from set", update, **{"date_from": date_from}
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
        __name__, "Promo date_to set", update, **{"date_to": date_to}
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

    # Initialize tariff selection
    context.user_data["creating_promocode"]["selected_tariffs"] = set()

    # Show tariff selection
    keyboard = []
    keyboard.append(
        [InlineKeyboardButton("☐ ВСЕ ТАРИФЫ", callback_data="promo_tariff_ALL")]
    )

    # Add individual tariffs
    for tariff in Tariff:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"☐ {tariff.name}", callback_data=f"promo_tariff_{tariff.value}"
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
        f"🎯 <b>Выбрано:</b> Не выбрано\n\n"
        "Нажмите на тарифы для включения/выключения.\n"
        "После выбора нажмите <b>✔️ Подтвердить выбор</b>."
    )

    await update.message.reply_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    LoggerService.info(
        __name__, "Promo discount set", update, **{"discount": discount}
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
        __name__, "Promo date_from set via button", update, **{"date_from": date_from}
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
        __name__, "Promo date_to set via button", update, **{"date_to": date_to}
    )
    return CREATE_PROMO_DISCOUNT


async def handle_promo_tariff_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle tariff selection with toggle functionality"""
    await update.callback_query.answer()

    data = update.callback_query.data

    if data == "cancel_promo_create":
        return await cancel_promo_creation(update, context)

    # Initialize selected tariffs set if not exists
    if "selected_tariffs" not in context.user_data["creating_promocode"]:
        context.user_data["creating_promocode"]["selected_tariffs"] = set()

    selected_tariffs = context.user_data["creating_promocode"]["selected_tariffs"]

    # Handle tariff toggle
    if data == "promo_tariff_ALL":
        # Toggle all tariffs on/off
        if len(selected_tariffs) == len(Tariff):
            # All selected - deselect all
            selected_tariffs.clear()
        else:
            # Not all selected - select all
            selected_tariffs.clear()
            for tariff in Tariff:
                selected_tariffs.add(tariff.value)
    elif data == "promo_tariff_confirm":
        # User confirmed selection - create promocode
        return await create_promocode_with_tariffs(update, context)
    else:
        # Toggle individual tariff
        tariff_value = int(data.replace("promo_tariff_", ""))
        if tariff_value in selected_tariffs:
            selected_tariffs.remove(tariff_value)
        else:
            selected_tariffs.add(tariff_value)

    # Update keyboard with current selection state
    keyboard = []

    # All tariffs button
    all_selected = len(selected_tariffs) == len(Tariff)
    all_button_text = "✅ ВСЕ ТАРИФЫ" if all_selected else "☐ ВСЕ ТАРИФЫ"
    keyboard.append([InlineKeyboardButton(all_button_text, callback_data="promo_tariff_ALL")])

    # Individual tariff buttons
    for tariff in Tariff:
        is_selected = tariff.value in selected_tariffs
        icon = "✅" if is_selected else "☐"
        keyboard.append([
            InlineKeyboardButton(
                f"{icon} {tariff.name}",
                callback_data=f"promo_tariff_{tariff.value}"
            )
        ])

    # Add confirm and cancel buttons
    if selected_tariffs:
        keyboard.append([
            InlineKeyboardButton("✔️ Подтвердить выбор", callback_data="promo_tariff_confirm")
        ])
    keyboard.append([
        InlineKeyboardButton("Отмена", callback_data="cancel_promo_create")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Create selection summary
    if selected_tariffs:
        if len(selected_tariffs) == len(Tariff):
            tariff_text = "ВСЕ ТАРИФЫ"
        else:
            tariff_names = [Tariff(t).name for t in sorted(selected_tariffs)]
            tariff_text = ", ".join(tariff_names)
    else:
        tariff_text = "Не выбрано"

    promo_data = context.user_data["creating_promocode"]
    message = (
        f"✅ Скидка: <b>{promo_data['discount']}%</b>\n\n"
        "Шаг 6 из 6: Выберите тарифы, к которым применим промокод\n\n"
        f"🎯 <b>Выбрано:</b> {tariff_text}\n\n"
        "Нажмите на тарифы для включения/выключения.\n"
        "После выбора нажмите <b>✔️ Подтвердить выбор</b>."
    )

    await update.callback_query.edit_message_text(
        text=message, reply_markup=reply_markup, parse_mode="HTML"
    )

    return CREATE_PROMO_TARIFF


async def create_promocode_with_tariffs(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Create promocode with selected tariffs"""
    promo_data = context.user_data["creating_promocode"]
    selected_tariffs = promo_data.get("selected_tariffs", set())

    if not selected_tariffs:
        await update.callback_query.answer(
            "❌ Выберите хотя бы один тариф!",
            show_alert=True
        )
        return CREATE_PROMO_TARIFF

    # Determine applicable tariffs
    if len(selected_tariffs) == len(Tariff):
        applicable_tariffs = None  # None = all tariffs
        tariff_text = "ВСЕ ТАРИФЫ"
    else:
        applicable_tariffs = sorted(list(selected_tariffs))
        tariff_names = [Tariff(t).name for t in applicable_tariffs]
        tariff_text = ", ".join(tariff_names)

    # Create promocode in database
    try:
        promocode = database_service.add_promocode(
            name=promo_data["name"],
            promocode_type=promo_data["type"],
            date_from=promo_data["date_from"],
            date_to=promo_data["date_to"],
            discount_percentage=promo_data["discount"],
            applicable_tariffs=applicable_tariffs,
        )

        # Format type display
        promo_type = PromocodeType(promocode.promocode_type)
        if promo_type == PromocodeType.BOOKING_DATES:
            type_icon = "📅"
            type_text = "Бронирование на конкретные даты"
        else:
            type_icon = "⏰"
            type_text = "Действие в период (бронь на любые даты)"

        # Message with copyable promo code
        message = (
            "✅ <b>Промокод успешно создан!</b>\n\n"
            f"📝 <b>Название:</b> <code>{promocode.name}</code>\n"
            f"{type_icon} <b>Тип:</b> {type_text}\n"
            f"📅 <b>Период:</b> {promocode.date_from.strftime('%d.%m.%Y')} - {promocode.date_to.strftime('%d.%m.%Y')}\n"
            f"💰 <b>Скидка:</b> {promocode.discount_percentage}%\n"
            f"🎯 <b>Тарифы:</b> {tariff_text}\n\n"
            f"📋 Нажмите на код, чтобы скопировать: <code>{promocode.name}</code>"
        )

        await update.callback_query.edit_message_text(text=message, parse_mode="HTML")

        LoggerService.info(
            __name__,
            "Promocode created successfully",
            update,
            **{"promocode_id": promocode.id, "name": promocode.name},
        )

    except Exception as e:
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

    try:
        promocodes = database_service.list_active_promocodes()

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
            # Format tariffs display
            if promo.applicable_tariffs:
                import json

                tariff_ids = json.loads(promo.applicable_tariffs)
                from src.models.enum.tariff import Tariff

                tariff_names = [Tariff(t_id).name for t_id in tariff_ids]
                tariffs_text = ", ".join(tariff_names)
            else:
                tariffs_text = "ВСЕ ТАРИФЫ"

            # Format type display
            promo_type = PromocodeType(promo.promocode_type)
            if promo_type == PromocodeType.BOOKING_DATES:
                type_icon = "📅"
                type_text = "Бронирование на даты"
            else:
                type_icon = "⏰"
                type_text = "Действие в период"

            message_lines.append(
                f"\n🎟️ <b>{promo.name}</b>\n"
                f"   {type_icon} Тип: {type_text}\n"
                f"   💰 Скидка: {promo.discount_percentage}%\n"
                f"   📅 Период: {promo.date_from.strftime('%d.%m.%Y')} - {promo.date_to.strftime('%d.%m.%Y')}\n"
                f"   🎯 Тарифы: {tariffs_text}"
            )

            # Add delete button for each promocode
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🗑 Удалить {promo.name}",
                        callback_data=f"delete_promo_{promo.id}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "\n".join(message_lines), parse_mode="HTML", reply_markup=reply_markup
        )

        LoggerService.info(__name__, "Listed promocodes", update)

    except Exception as e:
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

    try:
        # Deactivate promocode
        success = database_service.deactivate_promocode(promocode_id)

        if success:
            await query.edit_message_text(
                f"✅ Промокод с ID <b>{promocode_id}</b> успешно деактивирован!\n\n"
                f"Используйте /list_promocodes для просмотра оставшихся промокодов.",
                parse_mode="HTML",
            )
            LoggerService.info(
                __name__,
                "Promocode deactivated via button",
                update,
                **{"promocode_id": promocode_id},
            )
        else:
            await query.edit_message_text(
                f"❌ Промокод с ID <b>{promocode_id}</b> не найден или уже деактивирован.",
                parse_mode="HTML",
            )

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка при деактивации промокода: {str(e)}", parse_mode="HTML"
        )
        LoggerService.error(__name__, "Error deactivating promocode", e)
