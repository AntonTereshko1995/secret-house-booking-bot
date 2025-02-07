from telegram.ext import ConversationHandler

END = ConversationHandler.END
# Global
MENU, STOPPING, BACK, CONFIRM, CANCEL = map(chr, range(5))
# Type of menu
BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE, SUBSCRIPTION = map(chr, range(6, 14))
# AVAILABLE_DATES
GET_AVAILABLE_DATES = map(chr, range(14))
# CANCEL_BOOKING
VALIDATE_USER, SET_BOOKING_DATE = map(chr, range(15, 17))
# CHANGE_BOOKING_DATE
SET_OLD_START_DATE, SET_START_DATE, SET_START_TIME, SET_FINISH_DATE, SET_FINISH_TIME = map(chr, range(17, 22))
# GIFT_CERTIFICATE
SET_USER, SELECT_TARIFF, INCLUDE_SECRET_ROOM, INCLUDE_SAUNA, PAY, CONFIRM_PAY, PHOTO_UPLOAD = map(chr, range(22, 29))
# SUBSCRIPTION
SUBSCRIPTION_TYPE = map(chr, range(30))
# BOOKING
INCLUDE_PHOTOSHOOT, SELECT_BEDROOM, ADDITIONAL_BEDROOM, NUMBER_OF_PEOPLE, COMMENT, SALE, WRITE_CODE, SKIP, CASH_PAY = map(chr, range(31, 40))
# DATE TIME PIKER
HOURS_CALLBACK, CALENDAR_CALLBACK, ACTION, IGNORE = map(chr, range(40, 44))
# QUESTIONS
MESSAGE = map(chr, range(44))