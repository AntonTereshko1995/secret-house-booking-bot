import requests as http_requests
from flask import Blueprint, request, jsonify

from src.config.config import TELEGRAM_TOKEN, ADMIN_CHAT_ID
from src.handlers.admin_handler import _create_booking_keyboard
from src.helpers import string_helper
from src.services.database_service import DatabaseService

receipt_bp = Blueprint("receipt", __name__)
_db = DatabaseService()


@receipt_bp.post("/api/receipt")
def handle_web_receipt():
    booking_id = request.form.get("booking_id")
    file = request.files.get("file")
    if not booking_id or not file:
        return jsonify({"ok": False, "error": "booking_id and file are required"}), 400

    booking = _db.get_booking_by_id(int(booking_id))
    if not booking:
        return jsonify({"ok": False, "error": "booking not found"}), 404

    user = _db.get_user_by_id(booking.user_id)
    message = "🌐 Бронирование через веб-сайт\n\n" + string_helper.generate_booking_info_message(booking, user, False)
    reply_markup = _create_booking_keyboard(0, booking.id, False).to_json()

    file_content = file.read()
    filename = file.filename or "receipt"
    content_type = file.content_type or "application/octet-stream"
    is_image = content_type.startswith("image/")
    method = "sendPhoto" if is_image else "sendDocument"
    field = "photo" if is_image else "document"

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    tg_response = http_requests.post(
        tg_url,
        data={"chat_id": str(ADMIN_CHAT_ID), "caption": message, "reply_markup": reply_markup},
        files={field: (filename, file_content, content_type)},
        timeout=30,
    )

    file_id = None
    if tg_response.ok:
        result = tg_response.json().get("result", {})
        if is_image and "photo" in result:
            file_id = result["photo"][-1]["file_id"]
        elif "document" in result:
            file_id = result["document"]["file_id"]

    return jsonify({"ok": True, "file_id": file_id})
