from telegram.ext import ConversationHandler

END = ConversationHandler.END
# Global
MENU, STOPPING, BACK = map(chr, range(3))
# Type of menu
BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE = map(chr, range(3, 10))
# AVAILABLE_DATES
GET_AVAILABLE_DATES  = map(chr, range(11))
# CANCEL_BOOKING
CHECK_USER_NAME, START_DATE, CANCEL_RESULT_MESSAGE = map(chr, range(12, 13))