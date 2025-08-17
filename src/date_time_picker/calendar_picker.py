from matplotlib.dates import relativedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from datetime import datetime, date, timedelta
from src.helpers import string_helper, date_time_helper
from src.constants import CALENDAR_CALLBACK, ACTION, IGNORE
import calendar

def create_callback_data(action, year, month, day, prefix: str):
    return CALENDAR_CALLBACK + prefix + "_" + "_".join([action, str(year), str(month), str(day)])

def create_calendar(selected_date: date = None, min_date: date = None, max_date: date = None, action_text: str = " ", callback_prefix: str = "", available_days: list = None):
    if selected_date == None: 
        selected_date = date.now() 

    data_ignore = create_callback_data(str(IGNORE), selected_date.year, selected_date.month, 0, callback_prefix)
    data_action = create_callback_data(str(ACTION), selected_date.year, selected_date.month, 0, callback_prefix)
    keyboard = []
    #First row - Month and Year
    row=[]
    row.append(InlineKeyboardButton(f"{date_time_helper.get_month_name(selected_date.month)} {str(selected_date.year)}", callback_data=data_ignore))
    keyboard.append(row)

    #Second row - Week Days
    row=[]
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        row.append(InlineKeyboardButton(day, callback_data = data_ignore))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(selected_date.year, selected_date.month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                # Empty day (outside month)
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            elif min_date is not None and date(selected_date.year, selected_date.month, day) < min_date:
                # Day is before minimum date
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            elif available_days is not None:
                # Check if day is in available days list
                current_date = date(selected_date.year, selected_date.month, day)
                if current_date in available_days:
                    row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data("DAY", selected_date.year, selected_date.month, day, prefix=callback_prefix)))
                else:
                    # Day is not available - show as disabled
                    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                # No available_days list provided - show all days
                row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data("DAY", selected_date.year, selected_date.month, day, prefix=callback_prefix)))
        keyboard.append(row)

    #Last row - Buttons
    row=[]
    if selected_date.month != min_date.month:
        month_name = date_time_helper.get_month_name((selected_date - relativedelta(months=1)).month)
        row.append(InlineKeyboardButton(f"⬅️ {month_name}", callback_data = create_callback_data("PREV-MONTH", selected_date.year, selected_date.month, day, prefix=callback_prefix)))
    else:
       row.append(InlineKeyboardButton(" ", callback_data = data_ignore))

    row.append(InlineKeyboardButton(action_text, callback_data = data_action))

    if selected_date.month != max_date.month:
        month_name = date_time_helper.get_month_name((selected_date + relativedelta(months=1)).month)
        row.append(InlineKeyboardButton(f"{month_name} ➡️", callback_data = create_callback_data("NEXT-MONTH", selected_date.year, selected_date.month, day, prefix=callback_prefix)))
    else:
       row.append(InlineKeyboardButton(" ", callback_data = data_ignore))

    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# async def process_calendar_selection(update, context, min_date: date = None, max_date: date = None, action_text: str = " ", callback_prefix: str = "", available_days: list = None):
async def process_calendar_selection(update, context):
    # Selected, Date, Is_action, Is_next_month, Is_prev_month
    return_data = (False, None, False, False, False)
    query = update.callback_query
    try:
        (_, action, year, month, day) = string_helper.separate_callback_data(query.data)
        selected_date = datetime(int(year), int(month), 1)
        if action == str(IGNORE):
            await context.bot.answer_callback_query(callback_query_id=query.id)
        if action == str(ACTION):
            return_data = (False, None, True, False, False)
        elif action == "DAY":
            await context.bot.edit_message_text(
                text=query.message.text,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id)
            return_data = (True, datetime(int(year), int(month), int(day)), False, False, False)
        elif action == "PREV-MONTH":
            prev_month = selected_date - timedelta(days = 1)
            return_data = (False, prev_month, False, False, True)
        elif action == "NEXT-MONTH":
            next_month = selected_date + timedelta(days = 31)
            return_data = (False, next_month, False, True, False)
        else:
            await context.bot.answer_callback_query(callback_query_id = query.id, text = "Something went wrong!")
        return return_data
    except Exception as e:
        print(e)
        await context.bot.answer_callback_query(callback_query_id = query.id, text = "Something went wrong!")
        return return_data
