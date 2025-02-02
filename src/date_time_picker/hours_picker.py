from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from datetime import datetime, time, timedelta
from src.helpers import string_helper
from src.constants import HOURS_CALLBACK, ACTION

HOURS = map(chr, range(1))

def create_callback_data(action, time: time):
    return HOURS_CALLBACK + "_" + "_".join([action, time.strftime('%H%M') if time else ""])

from datetime import datetime, time, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_hours_picker(date=None, free_slots=None, action_text=""):
    hour = 0
    now = datetime.now()
    if date == now.date():
        hour = now.hour

    keyboard = []
    row = []

    if free_slots is None:
        time_slots = [time(h, 0) for h in range(hour, 24)] 
        time_slots.append(time(23, 59))
    else:
        time_slots = []
        for slot in free_slots:
            start_time, end_time = slot
            current_time = start_time
            while current_time < end_time:
                if current_time.hour > hour:
                    time_slots.append(current_time)
                next_time = (datetime.combine(now.date(), current_time) + timedelta(hours=1)).time()
                if next_time <= current_time:
                    break
                current_time = next_time

            if current_time != end_time and end_time not in time_slots:
                time_slots.append(end_time)

    for i in range(0, len(time_slots)):
        time_str = time_slots[i].strftime('%H:%M')  # Форматируем время в строку HH:MM
        callback_data = create_callback_data(str(HOURS), time_slots[i])
        row.append(InlineKeyboardButton(time_str, callback_data=callback_data))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(action_text, callback_data = create_callback_data(str(ACTION), None))])
    return InlineKeyboardMarkup(keyboard)

async def process_hours_selection(update, context):
    # Selected, Time, Is_action
    return_data = (False, None, False)
    query = update.callback_query
    (_, action, time_str) = string_helper.separate_callback_data(query.data)
    if action == str(ACTION):
        return_data = (False, None, True)
    elif action == str(HOURS):
        await context.bot.edit_message_text(
            text = query.message.text,
            chat_id = query.message.chat_id,
            message_id = query.message.message_id)
        return_data = True, time(int(time_str[:2]), int(time_str[2:])), False
    else:
        await context.bot.answer_callback_query(callback_query_id = query.id, text = "Something went wrong!")
    return return_data