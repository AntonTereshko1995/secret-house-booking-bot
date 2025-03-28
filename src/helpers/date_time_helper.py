from datetime import datetime, time, date, timedelta
from src.config.config import CLEANING_HOURS

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
    next_month = date.today()
    months = { next_month.strftime("%Y_%m"): get_month_name(next_month.month)}
    for _ in range(count_future_months):
        next_month = next_month.replace(day=28) + timedelta(days=4)
        months[next_month.strftime("%Y_%m")] = get_month_name(next_month.month)
    return months

def parse_date(date_string: str, date_format="%d.%m.%Y") -> datetime:
    try:
        date = datetime.strptime(date_string, date_format)
        return date
    except (ValueError, AttributeError) as e:
        print(e)
        return None
    
def get_free_time_slots(
        bookings, 
        date: date, 
        start_time: time = time(0, 0), 
        cleaning_time=timedelta(hours=CLEANING_HOURS), 
        minus_time_from_start: bool = False,
        add_time_to_end: bool = False):
    day_start = datetime.combine(date, start_time)
    day_end = datetime.combine(date, time(23, 59))
    free_slots = []

    if not bookings or len(bookings) == 0:
        free_slots.append((day_start.time(), day_end.time()))
        return free_slots

    previous_end = day_start
    sorted_bookings = sorted(bookings, key=lambda x: x.start_date)
    for booking in sorted_bookings:
        if booking.start_date.date() == date:
            booking_start = datetime.combine(date, booking.start_date.time())
        else:
            booking_start = datetime.combine(date, time(0, 0))
        
        if booking.end_date.date() == date:
            booking_end = datetime.combine(date, booking.end_date.time())
        else:
            booking_end = datetime.combine(date, time(23, 59))

        if minus_time_from_start:
            booking_start = booking_start - cleaning_time
        if add_time_to_end:
            booking_end = booking_end + cleaning_time

        if booking_start > previous_end:
            free_slots.append((previous_end.time(), booking_start.time()))

        if booking_end > previous_end:
            previous_end = booking_end

    if previous_end < day_end:
        free_slots.append((previous_end.time(), day_end.time()))

    return free_slots

def seconds_to_hours(seconds: int) -> float:
    return seconds / 3600