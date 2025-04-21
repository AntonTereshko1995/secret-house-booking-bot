from telegram import CallbackQuery
from telegram.error import BadRequest

async def safe_edit_message_text(callback_query: CallbackQuery, text, reply_markup=None):
    try:
        await callback_query.edit_message_text(
            text=text,
            parse_mode='HTML',
            reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Ignore no-op edits
            pass
        else:
            raise