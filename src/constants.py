from telegram.ext import ConversationHandler

MENU = 0
END = ConversationHandler.END
# Type of menu
BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE = map(chr, range(1, 8))
STOPPING = map(chr, range(9))
