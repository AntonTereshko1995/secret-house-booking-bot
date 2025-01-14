# State definitions for top level conversation
MENU = map(chr, range(0))
BOOKING, CANCEL_BOOKING, CHANGE_BOOKING_DATE, AVAILABLE_DATES, QUESTIONS, PRICE, GIFT_CERTIFICATE = map(chr, range(1, 8))
# State definitions for second level conversation
# State definitions for descriptions conversation
# SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# # Meta states
# STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
# END = ConversationHandler.END