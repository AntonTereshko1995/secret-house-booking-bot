import sys
import os
from src.services.database_service import DatabaseService
from src.services.logger_service import LoggerService
from src.services.navigation_service import NavigatonService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.models.rental_price import RentalPrice
from src.config.config import BANK_PHONE_NUMBER, BANK_CARD_NUMBER
from src.services.calculation_rate_service import CalculationRateService
from telegram import Document, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.handlers import admin_handler, menu_handler
from src.helpers import string_helper, tariff_helper
from src.models.enum.tariff import Tariff
from src.constants import (
    END,
    GIFT_VALIDATE_USER,
    MENU,
    GIFT_CERTIFICATE,
    SET_USER,
    CONFIRM,
    GIFT_PHOTO_UPLOAD,
)

navigation_service = NavigatonService()

user_contact: str
tariff: Tariff
is_sauna_included: bool
is_secret_room_included: bool
is_additional_bedroom_included: bool
rate_service = CalculationRateService()
database_service = DatabaseService()
rental_rate: RentalPrice
price: int


def get_handler():
    return [
        CallbackQueryHandler(
            enter_user_contact, pattern=f"^GIFT-USER_({SET_USER}|{END})$"
        ),
        CallbackQueryHandler(select_tariff, pattern=f"^GIFT-TARIFF_(\d+|{END})$"),
        CallbackQueryHandler(
            include_secret_room, pattern=f"^GIFT-SECRET_(?i:true|false|{END})$"
        ),
        CallbackQueryHandler(
            include_sauna, pattern=f"^GIFT-SAUNA_(?i:true|false|{END})$"
        ),
        CallbackQueryHandler(
            select_additional_bedroom,
            pattern=f"^GIFT-ADD-BEDROOM_(?i:true|false|{END})$",
        ),
        CallbackQueryHandler(
            confirm_pay, pattern=f"^GIFT-CONFIRM-PAY_({END}|{SET_USER})$"
        ),
        CallbackQueryHandler(pay, pattern=f"^GIFT-PAY_({END})$"),
        CallbackQueryHandler(confirm_gift, pattern=f"^GIFT-CONFIRM_({CONFIRM}|{END})$"),
        CallbackQueryHandler(back_navigation, pattern=f"^GIFT_{END}$"),
    ]


async def back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Back to menu", update)
    await menu_handler.show_menu(update, context)
    return MENU


async def enter_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    LoggerService.info(__name__, "enter user contact", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="📲 Укажите ваш <b>Telegram</b> или номер телефона:\n\n"
        "🔹 <b>Telegram:</b> @username (начинайте с @)\n"
        "🔹 <b>Телефон:</b> +375XXXXXXXXX (обязательно с +375)\n"
        "❗️ Пожалуйста, вводите данные строго в указанном формате.",
        reply_markup=reply_markup,
    )
    return GIFT_VALIDATE_USER


async def generate_tariff_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "generate tariff menu", update)
    reset_variables()
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_DAY)} — {rate_service.get_price(Tariff.INCOGNITA_DAY)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.INCOGNITA_DAY.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.INCOGNITA_HOURS)} — {rate_service.get_price(Tariff.INCOGNITA_HOURS)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.INCOGNITA_HOURS.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.DAY)} — {rate_service.get_price(Tariff.DAY)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.DAY.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.DAY_FOR_COUPLE)} — {rate_service.get_price(Tariff.DAY_FOR_COUPLE)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.DAY_FOR_COUPLE.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.HOURS_12)} — от {rate_service.get_price(Tariff.HOURS_12)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.HOURS_12.value}",
            )
        ],
        [
            InlineKeyboardButton(
                f"🔹 {tariff_helper.get_name(Tariff.WORKER)} — от {rate_service.get_price(Tariff.WORKER)} руб",
                callback_data=f"GIFT-TARIFF_{Tariff.WORKER.value}",
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"GIFT_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="🎟 <b>Выберите тариф для сертификата.</b>",
        reply_markup=reply_markup,
    )
    return GIFT_CERTIFICATE


async def check_user_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_input = update.message.text
        is_valid, cleaned_contact = string_helper.is_valid_user_contact(user_input)
        if is_valid:
            global user_contact
            user_contact = cleaned_contact

            # Save contact to database
            try:
                chat_id = navigation_service.get_chat_id(update)
                user = database_service.get_user_by_chat_id(chat_id)

                if user:
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.info(
                        __name__,
                        "User contact saved to database",
                        update,
                        kwargs={"chat_id": chat_id, "contact": cleaned_contact},
                    )
                else:
                    user_name = update.effective_user.username or cleaned_contact
                    database_service.update_user_chat_id(user_name, chat_id)
                    database_service.update_user_contact(chat_id, cleaned_contact)
                    LoggerService.warning(
                        __name__,
                        "User not found by chat_id, created new user",
                        update,
                        kwargs={"chat_id": chat_id, "contact": cleaned_contact},
                    )
            except Exception as e:
                LoggerService.error(
                    __name__,
                    "Failed to save user contact to database",
                    exception=e,
                    kwargs={"contact": cleaned_contact},
                )

            return await pay(update, context)
        else:
            LoggerService.warning(__name__, "User name is invalid", update)
            await update.message.reply_text(
                "❌ <b>Ошибка!</b>\n"
                "Имя пользователя в Telegram или номер телефона введены некорректно.\n\n"
                "🔄 Пожалуйста, попробуйте еще раз.",
                parse_mode="HTML",
            )
    return GIFT_VALIDATE_USER


async def select_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    global \
        tariff, \
        rental_rate, \
        is_sauna_included, \
        is_secret_room_included, \
        is_additional_bedroom_included
    tariff = tariff_helper.get_by_str(data)
    rental_rate = rate_service.get_by_tariff(tariff)
    LoggerService.info(__name__, "select tariff", update, kwargs={"tariff": tariff})

    if tariff == Tariff.INCOGNITA_HOURS or tariff == Tariff.INCOGNITA_DAY:
        is_sauna_included = True
        is_secret_room_included = True
        is_additional_bedroom_included = True
        return await confirm_pay(update, context)
    elif tariff == Tariff.DAY or tariff == Tariff.DAY_FOR_COUPLE:
        is_secret_room_included = True
        is_additional_bedroom_included = True
        return await sauna_message(update, context)
    elif tariff == Tariff.HOURS_12 or tariff == Tariff.WORKER:
        return await additional_bedroom_message(update, context)


async def select_additional_bedroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    global is_additional_bedroom_included
    is_additional_bedroom_included = eval(data)
    LoggerService.info(
        __name__,
        "select additional bedroom",
        update,
        kwargs={"is_additional_bedroom_included": is_additional_bedroom_included},
    )
    return await secret_room_message(update, context)


async def include_secret_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    global is_secret_room_included
    is_secret_room_included = eval(data)
    LoggerService.info(
        __name__,
        "include secret room",
        update,
        kwargs={"is_secret_room_included": is_secret_room_included},
    )
    return await sauna_message(update, context)


async def include_sauna(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    data = string_helper.get_callback_data(update.callback_query.data)
    if data == str(END):
        return await back_navigation(update, context)

    global is_sauna_included
    is_sauna_included = eval(data)
    LoggerService.info(
        __name__,
        "include sauna",
        update,
        kwargs={"is_sauna_included": is_sauna_included},
    )
    return await confirm_pay(update, context)


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        data = string_helper.get_callback_data(update.callback_query.data)
        if data == str(END):
            return await back_navigation(update, context)

    LoggerService.info(__name__, "pay", update)
    keyboard = [[InlineKeyboardButton("Отмена", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n\n"
        "📌 <b>Информация для оплаты (Альфа-Банк):</b>\n"
        f"📱 По номеру телефона: <b>{BANK_PHONE_NUMBER}</b>\n"
        "или\n"
        f"💳 По номеру карты: <b>{BANK_CARD_NUMBER}</b>\n\n"
        "❗️ <b>После оплаты отправьте скриншот или PDF документ с чеком об оплате.</b>\n"
        "К сожалению, только так мы можем подтвердить, что именно вы отправили предоплату.\n"
        "🙏 Спасибо за понимание.\n\n"
        "✅ Как только мы получим оплату, администратор свяжется с вами и отправит ваш <b>электронный подарочный сертификат</b>.",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
    return GIFT_PHOTO_UPLOAD


async def confirm_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if update.callback_query:
        data = string_helper.get_callback_data(update.callback_query.data)
        if data == str(END):
            return await back_navigation(update, context)

    keyboard = [
        [
            InlineKeyboardButton(
                "Перейти к оплате.", callback_data=f"GIFT-USER_{SET_USER}"
            )
        ],
        [InlineKeyboardButton("Назад в меню", callback_data=f"GIFT-USER_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    global price
    price = rate_service.calculate_price(
        rental_rate,
        is_sauna_included,
        is_secret_room_included,
        is_additional_bedroom_included,
    )
    categories = rate_service.get_price_categories(
        rental_rate,
        is_sauna_included,
        is_secret_room_included,
        is_additional_bedroom_included,
    )
    LoggerService.info(__name__, "confirm pay", update, kwargs={"price": price})
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text=f"💰 <b>Общая сумма оплаты:</b> {price} руб.\n"
        f"📌 <b>В стоимость входит:</b> {categories}.\n\n"
        "✅ <b>Подтверждаете покупку сертификата?</b>",
        reply_markup=reply_markup,
    )
    return GIFT_CERTIFICATE


async def secret_room_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"GIFT-SECRET_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"GIFT-SECRET_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"GIFT-SECRET_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="🔞 <b>Планируете ли вы пользоваться 'Секретной комнатой'?</b>\n\n"
        f"💰 <b>Стоимость:</b> {rental_rate.secret_room_price} руб. \n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
        reply_markup=reply_markup,
    )
    return GIFT_CERTIFICATE


async def sauna_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"GIFT-SAUNA_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"GIFT-SAUNA_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"GIFT-SAUNA_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="🧖‍♂️ <b>Планируете ли вы пользоваться сауной?</b>\n\n"
        f"💰 <b>Стоимость:</b> {rental_rate.sauna_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
        reply_markup=reply_markup,
    )
    return GIFT_CERTIFICATE


async def confirm_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LoggerService.info(__name__, "Confirm gift", update)
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data=END)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="🙏 <b>Спасибо за доверие к The Secret House!</b>\n\n"
        "📩 Ваша заявка получена.\n"
        "🔍 Администратор проверит оплату и свяжется с вами в ближайшее время.\n\n"
        "⏳ Пожалуйста, ожидайте подтверждения.",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def additional_bedroom_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data=f"GIFT-ADD-BEDROOM_{str(True)}")],
        [InlineKeyboardButton("Нет", callback_data=f"GIFT-ADD-BEDROOM_{str(False)}")],
        [InlineKeyboardButton("Назад в меню", callback_data=f"GIFT-ADD-BEDROOM_{END}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await navigation_service.safe_edit_message_text(
        callback_query=update.callback_query,
        text="🛏 <b>Планируете ли вы пользоваться второй спальней комнатой?</b>\n\n"
        f"💰 <b>Стоимость:</b> {rental_rate.second_bedroom_price} руб.\n"
        f"📌 <b>Для тарифа:</b> {tariff_helper.get_name(tariff)}",
        reply_markup=reply_markup,
    )
    return GIFT_CERTIFICATE


def save_gift_information():
    code = string_helper.get_generated_code()
    gift = database_service.add_gift(
        user_contact,
        tariff,
        is_sauna_included,
        is_secret_room_included,
        is_additional_bedroom_included,
        price,
        code,
    )
    return gift


def reset_variables():
    global \
        user_contact, \
        tariff, \
        is_sauna_included, \
        is_secret_room_included, \
        is_additional_bedroom_included, \
        rental_rate, \
        price
    user_contact = None
    tariff = None
    is_sauna_included = None
    is_secret_room_included = None
    is_additional_bedroom_included = None
    rental_rate = None
    price = None


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = None
    photo: str = None
    chat_id = update.message.chat.id
    if (
        update.message.document != None
        and update.message.document.mime_type == "application/pdf"
    ):
        document = update.message.document
    else:
        photo = update.message.photo[-1].file_id

    gift = save_gift_information()
    LoggerService.info(__name__, "handle photo", update)
    await admin_handler.accept_gift_payment(
        update, context, gift, chat_id, photo, document
    )
    return await confirm_gift(update, context)
