from telegram import Update
from telegram.ext import CallbackContext

def handle(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я твой бот. Чем могу помочь?")