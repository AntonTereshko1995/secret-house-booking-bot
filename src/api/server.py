import asyncio
import io
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import Flask, jsonify, request
from telegram import Bot

from src.config.config import ADMIN_CHAT_ID, TELEGRAM_TOKEN
from src.handlers.admin_handler import _create_booking_keyboard
from src.helpers.string_helper import generate_booking_info_message
from src.services.database.booking_repository import BookingRepository

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
        return jsonify({"error": "Missing booking_id or file"}), 400

    booking, user_chat_id = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

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
        return jsonify({"error": str(e)}), 500

    return jsonify({"file_id": file_id})


@flask_app.route("/api/new-booking", methods=["POST"])
def new_booking():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")

    if not booking_id:
        return jsonify({"error": "Missing booking_id"}), 400

    booking, user_chat_id = _get_booking_and_chat_id(int(booking_id))
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

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
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True})


def run(host: str = "0.0.0.0", port: int = 8080):
    flask_app.run(host=host, port=port, use_reloader=False)
