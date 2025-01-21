from datetime import datetime, time, date, timedelta
from dateutil import parser

def get_month_name(month: int):
    if (month == 1):
        return "Январь"
    elif (month == 2):
        return "Февраль"
    elif (month == 3):
        return "Март"
    elif (month == 4):
        return "Апрель"
    elif (month == 5):
        return "Май"
    elif (month == 6):
        return "Июнь"
    elif (month == 7):
        return "Июль"
    elif (month == 7):
        return "Август"
    elif (month == 8):
        return "Сентябрь"
    elif (month == 9):
        return "Октябрь"
    elif (month == 10):
        return "Ноябрь"
    elif (month == 11):
        return "Декабрь"

def get_future_months(count_future_months: int):
    today = date.today()
    months = { today.month: get_month_name(today.month)}
    for number in range(count_future_months - 1):
        next_month = today.replace(day=28) + timedelta(days=4)
        months[next_month.month] = get_month_name(next_month.month)
    return months

def parse_date(date_string: str, date_format="%d.%m.%Y") -> datetime:
    try:
        date = datetime.strptime(date_string, date_format)
        return date
    except (ValueError, AttributeError) as e:
        print(e)
        return None
   
def parse_time(time_string: str) -> time:
    try:
        hours = int(time_string)
        if (hours >= 0 and hours < 24):
            return time(hour=hours, minute=0)
        else:
            return None
    except (ValueError, AttributeError) as e:
        print(e)
        return None
