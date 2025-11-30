from datetime import datetime, time, date, timedelta
from typing import Iterable, List, Tuple
from matplotlib.dates import relativedelta
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
    months = {next_month.strftime("%Y_%m"): get_month_name(next_month.month)}
    for _ in range(count_future_months):
        next_month = next_month.replace(day=28) + timedelta(days=4)
        months[next_month.strftime("%Y_%m")] = get_month_name(next_month.month)
    return months


def parse_date(date_string: str, date_format="%d.%m.%Y") -> datetime:
    try:
        date = datetime.strptime(date_string, date_format)
        return date
    except (ValueError, AttributeError, TypeError) as e:
        print(e)
        return None


def get_free_time_slots(
    bookings: Iterable,
    day: date,
    start_time: time = time(0, 0),
) -> List[Tuple[time, time]]:
    cleaning = timedelta(hours=CLEANING_HOURS)

    day0 = datetime.combine(day, time(0, 0))
    DAY_END_EXCL = 24 * 60
    LAST_MINUTE = 23 * 60 + 59

    def minutes_from_day_start(dt: datetime) -> int:
        return int((dt - day0).total_seconds() // 60)

    def clamp(m: int) -> int:
        return max(0, min(DAY_END_EXCL, m))

    def to_time(m: int) -> time:
        if m >= DAY_END_EXCL:
            m = LAST_MINUTE
        h, mm = divmod(max(0, min(LAST_MINUTE, m)), 60)
        return time(h, mm)

    def ceil_hour(m: int) -> int:
        return ((m + 59) // 60) * 60

    now = datetime.now()
    if day == now.date():
        next_full_hour = now.replace(minute=0, second=0, microsecond=0)
        if now.minute > 0 or now.second > 0 or now.microsecond > 0:
            next_full_hour += timedelta(hours=1)
        requested = day0 + timedelta(hours=start_time.hour, minutes=start_time.minute)
        day_start_dt = max(requested, next_full_hour)
    else:
        day_start_dt = day0 + timedelta(
            hours=start_time.hour, minutes=start_time.minute
        )

    day_start_min = clamp(minutes_from_day_start(day_start_dt))

    # 1) собираем занятые интервалы [s,e) в пределах окна дня
    busy: List[Tuple[int, int]] = []
    for b in sorted(bookings, key=lambda x: x.start_date):
        occ_start = b.start_date - cleaning
        occ_end = b.end_date + cleaning
        s = minutes_from_day_start(occ_start)
        e = minutes_from_day_start(occ_end)
        s = max(s, day_start_min)
        e = min(e, DAY_END_EXCL)
        if s < e:
            busy.append((s, e))

    busy.sort()
    merged: List[Tuple[int, int]] = []
    for s, e in busy:
        if not merged or s > merged[-1][1]:
            merged.append((s, e))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))

    free: List[Tuple[int, int]] = []
    cursor = day_start_min
    for s, e in merged:
        if cursor < s:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < DAY_END_EXCL:
        free.append((cursor, DAY_END_EXCL))

    if not merged and not free and day_start_min < DAY_END_EXCL:
        free.append((day_start_min, DAY_END_EXCL))

    slots: List[Tuple[time, time]] = []
    for fs, fe in free:
        cur = ceil_hour(fs) if fs % 60 else fs
        while cur < fe:
            if cur // 60 >= 23:
                end = min(fe, DAY_END_EXCL)
            else:
                end = min(fe, cur + 60)
            if end <= cur:
                break
            start_t = to_time(cur)
            end_t = to_time(end if end < DAY_END_EXCL else LAST_MINUTE)
            if (start_t.hour, start_t.minute) < (end_t.hour, end_t.minute):
                slots.append((start_t, end_t))
            cur += 60

    return slots


def seconds_to_hours(seconds: int) -> float:
    return seconds / 3600


def get_free_dayes_slots(
    bookings,
    cleaning_time: timedelta = timedelta(hours=CLEANING_HOURS),
    target_month: int = None,
    target_year: int = None,
):
    """
    Returns list of available dates that have free time slots
    Adds cleaning_time to end of each booking and subtracts from start
    Considers current time for today's date
    Shows all days in month, not just days with bookings
    """
    now = datetime.now()
    today = now.date()

    # Set target month/year
    target_month = target_month or now.month
    target_year = target_year or now.year

    # Get month boundaries
    start_of_month = date(target_year, target_month, 1)
    end_of_month = _get_month_end_date(target_year, target_month)

    # Initialize available days
    available_days = _initialize_month_availability(start_of_month, end_of_month, today)

    if not bookings:
        return available_days

    # Process bookings and update availability
    date_bookings = _group_bookings_by_date(bookings, cleaning_time)
    available_days = _update_availability_with_bookings(
        available_days, date_bookings, today, now
    )

    return available_days


def month_bounds(base: date) -> tuple[date, date]:
    first = base.replace(day=1)
    last = first + relativedelta(months=1) - timedelta(days=1)
    return first, last


def _get_month_end_date(year: int, month: int) -> date:
    """Get the last day of the specified month"""
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)


def _initialize_month_availability(
    start_date: date, end_date: date, today: date
) -> list:
    """Initialize and return list of available days in month (future days only)"""
    available_days = []
    current_date = start_date

    while current_date <= end_date:
        # Only include future days (including today)
        if current_date >= today:
            available_days.append(current_date)
        current_date += timedelta(days=1)

    return available_days


def _group_bookings_by_date(bookings, cleaning_time: timedelta) -> dict:
    """Group bookings by date with cleaning time adjustments"""
    date_bookings = {}

    for booking in bookings:
        start_date = booking.start_date.date()
        end_date = booking.end_date.date()

        # Add cleaning time adjustments
        adjusted_start = booking.start_date - cleaning_time
        adjusted_end = booking.end_date + cleaning_time

        # Add to all dates this booking covers
        current_date = start_date
        while current_date <= end_date:
            if current_date not in date_bookings:
                date_bookings[current_date] = []

            date_bookings[current_date].append(
                {"start": adjusted_start, "end": adjusted_end}
            )

            current_date += timedelta(days=1)

    return date_bookings


def _update_availability_with_bookings(
    available_days: list, date_bookings: dict, today: date, now: datetime
) -> list:
    """Update available days based on existing bookings"""
    updated_available_days = []

    for date_key in available_days:
        if date_key in date_bookings:
            # Day has bookings - check for free slots
            day_bookings = sorted(date_bookings[date_key], key=lambda x: x["start"])
            has_free_slots = _check_day_availability(date_key, day_bookings, today, now)

            if has_free_slots:
                updated_available_days.append(date_key)
                # Log availability status
                _log_day_availability(
                    date_key, has_free_slots, day_bookings, today, now
                )
        else:
            # Day has no bookings - keep as available
            updated_available_days.append(date_key)
            print(
                f"Available slots for {date_key.strftime('%d.%m.%Y')}: 00:00-23:59 (no bookings)"
            )

    return updated_available_days


def _check_day_availability(
    date_key: date, day_bookings: list, today: date, now: datetime
) -> bool:
    """Check if a specific day has free time slots"""
    # Determine start time for the day
    if date_key == today:
        current_hour = now.hour + 1 if now.minute > 0 else now.hour
        current_hour = min(current_hour, 23)  # Ensure hour is in valid range 0-23
        day_start = datetime.combine(date_key, time(current_hour, 0))
    else:
        day_start = datetime.combine(date_key, time(0, 0))

    day_end = datetime.combine(date_key, time(23, 59))

    # Find free slots
    free_slots = _find_free_slots(day_bookings, day_start, day_end)

    # Filter past slots for today
    if date_key == today:
        free_slots = [slot for slot in free_slots if slot[0] > now]

    return len(free_slots) > 0


def _find_free_slots(
    day_bookings: list, day_start: datetime, day_end: datetime
) -> list:
    """Find free time slots between bookings"""
    free_slots = []
    prev_end = day_start

    for booking in day_bookings:
        # Check gap before this booking
        if prev_end < booking["start"]:
            free_slots.append((prev_end, booking["start"]))

        # Update previous end
        if booking["end"] > prev_end:
            prev_end = booking["end"]

    # Check gap after last booking
    if prev_end < day_end:
        free_slots.append((prev_end, day_end))

    return free_slots


def _log_day_availability(
    date_key: date, has_free_slots: bool, day_bookings: list, today: date, now: datetime
):
    """Log availability information for a day"""
    if has_free_slots:
        # Find and log free slots
        if date_key == today:
            current_hour = now.hour + 1 if now.minute > 0 else now.hour
            current_hour = min(current_hour, 23)  # Ensure hour is in valid range 0-23
            day_start = datetime.combine(date_key, time(current_hour, 0))
        else:
            day_start = datetime.combine(date_key, time(0, 0))

        day_end = datetime.combine(date_key, time(23, 59))
        free_slots = _find_free_slots(day_bookings, day_start, day_end)

        if date_key == today:
            free_slots = [slot for slot in free_slots if slot[0] > now]

        slot_info = [
            f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
            for start, end in free_slots
        ]
        print(
            f"Available slots for {date_key.strftime('%d.%m.%Y')}: {', '.join(slot_info)}"
        )
    else:
        print(f"No available slots for {date_key.strftime('%d.%m.%Y')} - fully booked")
