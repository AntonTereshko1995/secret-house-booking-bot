import asyncio
import io
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import Flask, jsonify, request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from src.config.config import ADMIN_CHAT_ID, INFORM_CHAT_ID, TELEGRAM_TOKEN
from src.handlers.admin_handler import _create_booking_keyboard
from src.helpers.string_helper import (
    generate_booking_info_message,
    generate_gift_info_message,
)
from src.services.database.booking_repository import BookingRepository
from src.services.database.gift_repository import GiftRepository
from src.services.calendar_service import CalendarService
from src.services.logger_service import LoggerService

calendar_service = CalendarService()

flask_app = Flask(__name__)


def _run_async(coro):
    return asyncio.run(coro)


def _get_booking_and_chat_id(booking_id: int):
    repo = BookingRepository()
    booking = repo.get_booking_by_id(booking_id)
    if not booking:
        return None, None
    user_chat_id = (booking.user.chat_id or 0) if booking.user else 0
    return booking, user_chat_id


@flask_app.route("/api/receipt", methods=["POST"])
def receipt():
    booking_id = request.form.get("booking_id")
    file = request.files.get("file")

    if not booking_id or not file:
        LoggerService.warning(__name__, "receipt: missing booking_id or file")
        return jsonify({"error": "Missing booking_id or file"}), 400

    booking, user_chat_id = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        LoggerService.warning(__name__, f"receipt: booking not found id={booking_id}")
        return jsonify({"error": "Booking not found"}), 404

    LoggerService.info(__name__, f"receipt: booking_id={booking_id} file={file.filename}")

    caption = generate_booking_info_message(booking, booking.user)
    reply_markup = _create_booking_keyboard(user_chat_id, booking.id, is_payment_by_cash=False)

    file_data = file.read()
    content_type = file.content_type or ""
    filename = file.filename or "receipt"

    async def send():
        async with Bot(TELEGRAM_TOKEN) as bot:
            if "image" in content_type:
                msg = await bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=io.BytesIO(file_data),
                    caption=caption,
                    reply_markup=reply_markup,
                )
                return msg.photo[-1].file_id
            else:
                msg = await bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=io.BytesIO(file_data),
                    filename=filename,
                    caption=caption,
                    reply_markup=reply_markup,
                )
                return msg.document.file_id

    try:
        file_id = _run_async(send())
    except Exception as e:
        LoggerService.error(__name__, f"receipt: send to telegram failed booking_id={booking_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    LoggerService.info(__name__, f"receipt: sent successfully booking_id={booking_id} file_id={file_id}")
    return jsonify({"file_id": file_id})


@flask_app.route("/api/new-booking", methods=["POST"])
def new_booking():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")

    if not booking_id:
        LoggerService.warning(__name__, "new_booking: missing booking_id")
        return jsonify({"error": "Missing booking_id"}), 400

    booking, user_chat_id = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        LoggerService.warning(__name__, f"new_booking: booking not found id={booking_id}")
        return jsonify({"error": "Booking not found"}), 404

    LoggerService.info(__name__, f"new_booking: notify admin booking_id={booking_id}")

    text = f"🆕 Новое бронирование #{booking_id}\n\n"
    text += generate_booking_info_message(booking, booking.user)
    reply_markup = _create_booking_keyboard(user_chat_id, booking.id, is_payment_by_cash=False)

    async def send():
        async with Bot(TELEGRAM_TOKEN) as bot:
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=text,
                reply_markup=reply_markup,
            )

    try:
        _run_async(send())
    except Exception as e:
        LoggerService.error(__name__, f"new_booking: send failed booking_id={booking_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True})


@flask_app.route("/api/gifts/notify", methods=["POST"])
def gift_notify():
    gift_id = request.form.get("gift_id")
    file = request.files.get("file")

    if not gift_id:
        LoggerService.warning(__name__, "gift_notify: missing gift_id")
        return jsonify({"error": "Missing gift_id"}), 400

    gift = GiftRepository().get_gift_by_id(int(gift_id))
    if not gift:
        LoggerService.warning(__name__, f"gift_notify: gift not found id={gift_id}")
        return jsonify({"error": "Gift not found"}), 404

    LoggerService.info(__name__, f"gift_notify: notify admin gift_id={gift_id}")

    caption = "🎁 Новый подарочный сертификат!\n\n" + generate_gift_info_message(gift)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"gift_1_chatid_0_giftid_{gift.id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"gift_2_chatid_0_giftid_{gift.id}")],
    ])

    file_data = file.read() if file else None
    content_type = file.content_type if file else ""
    filename = file.filename if file else "receipt"

    async def send():
        async with Bot(TELEGRAM_TOKEN) as bot:
            if file_data and "image" in content_type:
                await bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=io.BytesIO(file_data),
                    caption=caption,
                    reply_markup=keyboard,
                )
            elif file_data:
                await bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=io.BytesIO(file_data),
                    filename=filename,
                    caption=caption,
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=caption,
                    reply_markup=keyboard,
                )

    try:
        _run_async(send())
    except Exception as e:
        LoggerService.error(__name__, f"gift_notify: send failed gift_id={gift_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    LoggerService.info(__name__, f"gift_notify: sent successfully gift_id={gift_id}")
    return jsonify({"ok": True})


@flask_app.route("/api/notify/inform", methods=["POST"])
def notify_inform():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Missing text"}), 400

    if not INFORM_CHAT_ID:
        LoggerService.warning(__name__, "notify_inform: INFORM_CHAT_ID is not configured")
        return jsonify({"ok": True})

    async def send():
        async with Bot(TELEGRAM_TOKEN) as bot:
            await bot.send_message(chat_id=INFORM_CHAT_ID, text=text)

    try:
        _run_async(send())
    except Exception as e:
        LoggerService.error(__name__, "notify_inform: send failed", exception=e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True})


@flask_app.route("/api/calendar/cancel", methods=["POST"])
def calendar_cancel():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "Missing booking_id"}), 400

    booking, _ = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        LoggerService.warning(__name__, f"calendar_cancel: booking not found id={booking_id}")
        return jsonify({"error": "Booking not found"}), 404

    if not booking.calendar_event_id:
        LoggerService.info(__name__, f"calendar_cancel: no event_id, skipping id={booking_id}")
        return jsonify({"ok": True, "skipped": "no_event_id"})

    try:
        calendar_service.cancel_event(booking.calendar_event_id)
    except Exception as e:
        LoggerService.error(__name__, f"calendar_cancel: failed id={booking_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    LoggerService.info(__name__, f"calendar_cancel: done id={booking_id}")
    return jsonify({"ok": True})


@flask_app.route("/api/calendar/update-info", methods=["POST"])
def calendar_update_info():
    """Update event summary/description after tariff or services change."""
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "Missing booking_id"}), 400

    booking, _ = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        LoggerService.warning(__name__, f"calendar_update_info: booking not found id={booking_id}")
        return jsonify({"error": "Booking not found"}), 404

    if not booking.calendar_event_id:
        LoggerService.info(__name__, f"calendar_update_info: no event_id, skipping id={booking_id}")
        return jsonify({"ok": True, "skipped": "no_event_id"})

    try:
        calendar_service.update_event_info(booking.calendar_event_id, booking, booking.user)
    except Exception as e:
        LoggerService.error(__name__, f"calendar_update_info: failed id={booking_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    LoggerService.info(__name__, f"calendar_update_info: done id={booking_id}")
    return jsonify({"ok": True})


@flask_app.route("/api/calendar/reschedule", methods=["POST"])
def calendar_reschedule():
    """Move event to new dates after a reschedule."""
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "Missing booking_id"}), 400

    booking, _ = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        LoggerService.warning(__name__, f"calendar_reschedule: booking not found id={booking_id}")
        return jsonify({"error": "Booking not found"}), 404

    if not booking.calendar_event_id:
        LoggerService.info(__name__, f"calendar_reschedule: no event_id, skipping id={booking_id}")
        return jsonify({"ok": True, "skipped": "no_event_id"})

    try:
        calendar_service.move_event(
            booking.calendar_event_id,
            booking.start_date,
            booking.end_date,
            booking=booking,
            user=booking.user,
        )
    except Exception as e:
        LoggerService.error(__name__, f"calendar_reschedule: failed id={booking_id}", exception=e)
        return jsonify({"error": str(e)}), 500

    LoggerService.info(__name__, f"calendar_reschedule: done id={booking_id}")
    return jsonify({"ok": True})


def run(host: str = "0.0.0.0", port: int = 8080):
    flask_app.run(host=host, port=port, use_reloader=False)
