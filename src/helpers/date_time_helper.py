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
        day: date,
        start_time: time = time(0, 0),
        cleaning_time: timedelta = timedelta(hours=CLEANING_HOURS),
        minus_time_from_start: bool = False,
        add_time_to_end: bool = False):
    def floor_hour(dt: datetime) -> datetime:
        return dt.replace(minute=0, second=0, microsecond=0)

    def ceil_hour(dt: datetime) -> datetime:
        return dt if dt.minute == dt.second == dt.microsecond == 0 \
               else dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    def t00(dt: datetime) -> time:        # HH:00
        return time(dt.hour, 0)

    now = datetime.now()
    is_today = day == now.date()

    if is_today:
        base_dt = datetime.combine(day, start_time)
        base_dt = base_dt if now.time() < start_time else now
        day_start = ceil_hour(base_dt)
    else:
        day_start = datetime.combine(day, start_time)

    day_end_real = datetime.combine(day, time(23, 59)) 
    free_slots = []

    if not bookings:
        if day_start < day_end_real:
            free_slots.append((t00(day_start), time(23, 59)))
        return free_slots

    prev_end = day_start

    for b in sorted(bookings, key=lambda x: x.start_date):
        b_start = datetime.combine(day, b.start_date.time()) \
            if b.start_date.date() == day else day_start
        b_end = datetime.combine(day, b.end_date.time()) \
            if b.end_date.date() == day else day_end_real

        if minus_time_from_start:
            b_start -= cleaning_time
        if add_time_to_end:
            b_end += cleaning_time

        free_start = ceil_hour(prev_end)
        free_end = floor_hour(b_start)

        if free_start < free_end:
            free_slots.append((t00(free_start), t00(free_end)))

        if b_end > prev_end:
            prev_end = b_end

    tail_start = ceil_hour(prev_end if not is_today else max(prev_end, now))
    if tail_start < day_end_real:
        free_slots.append((t00(tail_start), time(23, 59)))

    return free_slots

def seconds_to_hours(seconds: int) -> float:
    return seconds / 3600