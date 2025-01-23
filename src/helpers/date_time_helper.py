from datetime import datetime, time, date, timedelta

def get_month_name(month: int):
    match month:
        case 1:
            return "Январь"
        case 2:
            return "Февраль"
        case 3:
            return "Март"
        case 4:
            return "Апрель"
        case 5:
            return "Май"
        case 6:
            return "Июнь"
        case 7:
            return "Июль"
        case 8:
            return "Август"
        case 9:
            return "Сентябрь"
        case 10:
            return "Октябрь"
        case 11:
            return "Ноябрь"
        case 12:
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
