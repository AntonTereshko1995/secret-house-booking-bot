from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from datetime import datetime, date, timedelta
from src.helpers import string_helper, date_time_helper
from src.constants import CALENDAR_CALLBACK, ACTION, IGNORE
import calendar

def create_callback_data(action, year, month, day):
    return CALENDAR_CALLBACK + "_" + "_".join([action, str(year), str(month), str(day)])

def create_calendar(year: int = None, month: int = None, max_date: date = None, action_text: str = " "):
    now = datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    data_ignore = create_callback_data(str(IGNORE), year, month, 0)
    data_action = create_callback_data(str(ACTION), year, month, 0)
    keyboard = []
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(f"{date_time_helper.get_month_name(month)} {str(year)}", callback_data=data_ignore))
    keyboard.append(row)

    #Second row - Week Days
    row=[]
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        row.append(InlineKeyboardButton(day, callback_data = data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ",callback_data = data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data = create_callback_data("DAY", year, month, day)))
        keyboard.append(row)

    #Last row - Buttons
    row=[]
    if month != now.month:
        row.append(InlineKeyboardButton("<", callback_data = create_callback_data("PREV-MONTH", year, month, day)))
    else:
       row.append(InlineKeyboardButton(" ", callback_data = data_ignore))

    row.append(InlineKeyboardButton(action_text, callback_data = data_action))

    if date(year, month, 1) != max_date:
        row.append(InlineKeyboardButton(">", callback_data = create_callback_data("NEXT-MONTH", year, month, day)))
    else:
       row.append(InlineKeyboardButton(" ", callback_data = data_ignore))

    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def process_calendar_selection(update, context, max_date: date = None, action_text: str = " "):
    # Selected, Time, Is_action
    return_data = (False, None, False)
    query = update.callback_query
    (_, action, year, month, day) = string_helper.separate_callback_data(query.data)
    curr = datetime(int(year), int(month), 1)
    if action == str(IGNORE):
        await context.bot.answer_callback_query(callback_query_id=query.id)
    if action == str(ACTION):
        return_data = (False, None, True)
    elif action == "DAY":
        await context.bot.edit_message_text(
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id)
        return_data = (True, datetime(int(year), int(month), int(day)), False)
    elif action == "PREV-MONTH":
        prev_month = curr - timedelta(days = 1)
        await context.bot.edit_message_text(
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup = create_calendar(int(prev_month.year), int(prev_month.month), max_date, action_text))
    elif action == "NEXT-MONTH":
        next_month = curr + timedelta(days = 31)
        await context.bot.edit_message_text(
            text=query.message.text,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup = create_calendar(int(next_month.year), int(next_month.month), max_date, action_text))
    else:
        await context.bot.answer_callback_query(callback_query_id = query.id, text = "Something went wrong!")
    return return_data
