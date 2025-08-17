from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from datetime import datetime, time, timedelta
from src.helpers import string_helper
from src.constants import HOURS_CALLBACK, ACTION

HOURS = map(chr, range(1))

def create_callback_data(action, time: time, prefix: str):
    return HOURS_CALLBACK + prefix + "_" + "_".join([action, time.strftime('%H%M') if time else ""])

from datetime import datetime, time, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_hours_picker(date=None, free_slots=None, action_text="", callback_prefix=""):
    hour = 0
    now = datetime.now()
    if date == now.date():
        hour = now.hour + 1

    keyboard = []
    row = []

    # Create all time slots from current hour to 23:59
    all_time_slots = [time(h, 0) for h in range(hour, 24)]
    all_time_slots.append(time(23, 59))

    # If free_slots is provided, mark which slots are available
    if free_slots is not None:
        # Convert free_slots to a set of available times for quick lookup
        available_times = set()
        for slot in free_slots:
            start_time, end_time = slot
            current_time = start_time
            while current_time <= end_time:
                if current_time.hour >= hour:
                    available_times.add(current_time)
                next_time = (datetime.combine(now.date(), current_time) + timedelta(hours=1)).time()
                if next_time <= current_time:
                    break
                current_time = next_time

            if current_time != end_time and end_time not in available_times:
                available_times.add(end_time)

        # Create buttons for each time slot
        for i in range(0, len(all_time_slots)):
            time_slot = all_time_slots[i]
            time_str = time_slot.strftime('%H:%M')
            
            if time_slot in available_times:
                # Available slot - create clickable button
                callback_data = create_callback_data(str(HOURS), time_slot, callback_prefix)
                row.append(InlineKeyboardButton(time_str, callback_data=callback_data))
            else:
                # Occupied slot - show shorter text to avoid truncation
                row.append(InlineKeyboardButton(f"⛔ {time_str}", callback_data="occupied"))
                
            if len(row) == 4:
                keyboard.append(row)
                row = []  
    else:
        # No free_slots provided - show all slots as available
        for i in range(0, len(all_time_slots)):
            time_str = all_time_slots[i].strftime('%H:%M')
            callback_data = create_callback_data(str(HOURS), all_time_slots[i], callback_prefix)
            row.append(InlineKeyboardButton(time_str, callback_data=callback_data))

            if len(row) == 4:
                keyboard.append(row)
                row = []  

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(action_text, callback_data=create_callback_data(str(ACTION), None, callback_prefix))])
    return InlineKeyboardMarkup(keyboard)

async def process_hours_selection(update, context):
    # Selected, Time, Is_action
    return_data = (False, None, False)
    query = update.callback_query 
    # TODO exception
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