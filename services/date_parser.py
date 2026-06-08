from datetime import datetime, timedelta


MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_user_datetime(user_input: str):
    text = user_input.lower().strip()

    if "," not in text:
        return None, None

    date_part, time_part = text.split(",", 1)

    date_part = date_part.strip()
    time_part = time_part.strip()

    date_value = parse_date(date_part)
    start_time, end_time = parse_time(time_part)

    if date_value is None or start_time is None:
        return None, None

    start = datetime.combine(date_value, start_time)
    end = datetime.combine(date_value, end_time)

    if end <= start:
        end = start + timedelta(hours=1)

    return start.isoformat(), end.isoformat()


def parse_date(date_text: str):
    today = datetime.now().date()

    if date_text == "сегодня":
        return today

    if date_text == "завтра":
        return today + timedelta(days=1)

    for date_format in ["%d.%m.%Y", "%d.%m"]:
        try:
            parsed = datetime.strptime(date_text, date_format).date()

            if date_format == "%d.%m":
                parsed = parsed.replace(year=today.year)

                if parsed < today:
                    parsed = parsed.replace(year=today.year + 1)

            return parsed
        except ValueError:
            pass

    parts = date_text.split()

    if len(parts) == 2:
        day_text, month_text = parts

        if day_text.isdigit() and month_text in MONTHS:
            day = int(day_text)
            month = MONTHS[month_text]
            year = today.year

            try:
                parsed = datetime(year, month, day).date()

                if parsed < today:
                    parsed = datetime(year + 1, month, day).date()

                return parsed
            except ValueError:
                return None

    return None


def parse_time(time_text: str):
    if "-" in time_text:
        start_text, end_text = time_text.split("-", 1)

        start = parse_single_time(start_text.strip())
        end = parse_single_time(end_text.strip())

        return start, end

    start = parse_single_time(time_text.strip())

    if start is None:
        return None, None

    end_datetime = datetime.combine(datetime.now().date(), start) + timedelta(hours=1)

    return start, end_datetime.time()


def parse_single_time(time_text: str):
    try:
        return datetime.strptime(time_text, "%H:%M").time()
    except ValueError:
        return None