from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from datetime import datetime, time
from src.helpers import string_helper
from src.constants import HOURS_CALLBACK, ACTION

HOURS = map(chr, range(1))

def create_callback_data(action, hour):
    return HOURS_CALLBACK + "_" + "_".join([action, str(hour)])

def create_hours_picker(hour = None, min_hour = 0, max_hour = 24, action_text = " "):
    now = datetime.now()
    if hour == None: hour = now.hour
    keyboard = []
    row=[]

    for index in range(min_hour, max_hour):
        row.append(InlineKeyboardButton(string_helper.convert_hours_to_time_string(index), callback_data=create_callback_data(str(HOURS), index)))
        if index % 2:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton(action_text, callback_data = create_callback_data(str(ACTION), None))])
    return InlineKeyboardMarkup(keyboard)

async def process_hours_selection(update, context):
    # Selected, Time, Is_action
    return_data = (False, None, False)
    query = update.callback_query
    (_, action, hours) = string_helper.separate_callback_data(query.data)
    if action == str(ACTION):
        return_data = (False, None, True)
    elif action == str(HOURS):
        await context.bot.edit_message_text(
            text = query.message.text,
            chat_id = query.message.chat_id,
            message_id = query.message.message_id)
        return_data = True, time(hour=int(hours)), False
    else:
        await context.bot.answer_callback_query(callback_query_id = query.id, text = "Something went wrong!")
    return return_data
