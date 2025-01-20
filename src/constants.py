from telegram.ext import ConversationHandler

END = ConversationHandler.END
# Global
MENU, STOPPING, BACK, CONFIRM = map(chr, range(4))
# Type of menu
BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE, SUBSCRIPTION = map(chr, range(5, 13))
# AVAILABLE_DATES
GET_AVAILABLE_DATES  = map(chr, range(13))
# CANCEL_BOOKING
VALIDATE_USER, SET_BOOKING_DATE = map(chr, range(14, 16))
# CHANGE_BOOKING_DATE
SET_OLD_START_DATE, SET_NEW_START_DATE, SET_NEW_START_TIME, SET_NEW_FINISH_DATE, SET_NEW_FINISH_TIME = map(chr, range(16, 21))
# GIFT_CERTIFICATE
SELECT_TARIFF, INCLUDE_SECRET_ROOM, INCLUDE_SAUNA, PAY, CONFIRM_PAY = map(chr, range(21, 26))