import sys
import os
import telegram
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from telegram import (Update)
from telegram.ext import (ContextTypes)

async def disable_last_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message:  # ✅ If it's a normal text message
            message = update.message
        elif update.callback_query and update.callback_query.message:  # ✅ If it's an inline button press
            message = update.callback_query.message
        else:
            return  # No message found

        # ✅ Ensure it's a bot message (Only bot messages can be edited)
        if message.from_user and message.from_user.is_bot:
            await message.edit_reply_markup(reply_markup=None)
        else:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=last_message_id,
                reply_markup=None)

    except telegram.error.BadRequest as e:
        print(f"❌ Error: {e}")  # Handles "Message can't be edited" errors