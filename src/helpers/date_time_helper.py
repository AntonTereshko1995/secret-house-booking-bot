import datetime
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
    today = datetime.date.today()
    months = { today.month: get_month_name(today.month)}
    for number in range(count_future_months - 1):
        next_month = today.replace(day=28) + datetime.timedelta(days=4)
        months[next_month.month] = get_month_name(next_month.month)
    return months

def parse_date(date_string, date_format="%d.%m.%Y"):
    try:
        if isinstance(date_string, str):
            # Преобразуем строку в дату
            date_obj = parser.parse(date_string)
        elif isinstance(date_string, datetime):
            date_obj = date_string
        else:
            raise TypeError("Дата должна быть строкой или объектом datetime")
        
        return date_obj.strftime(date_format)
    except ValueError as e:
        print(e)
        return None
