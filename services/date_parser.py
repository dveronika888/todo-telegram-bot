from datetime import datetime, timedelta
import re


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


def parse_task_message(user_input: str):
    original_text = user_input.strip()
    text = original_text.lower()

    date_value, date_fragment = find_date(text)
    start_time, end_time, time_fragment = find_time(text)

    if date_value is None or start_time is None:
        return None, None, None

    task_text = original_text

    for fragment in [date_fragment, time_fragment]:
        if fragment:
            task_text = remove_fragment(task_text, fragment)

    task_text = clean_task_text(task_text)

    if not task_text:
        return None, None, None

    start = datetime.combine(date_value, start_time)
    end = datetime.combine(date_value, end_time)

    if end <= start:
        end = start + timedelta(hours=1)

    return task_text, start.isoformat(), end.isoformat()


def find_date(text: str):
    today = datetime.now().date()

    if "сегодня" in text:
        return today, "сегодня"

    if "завтра" in text:
        return today + timedelta(days=1), "завтра"

    date_match = re.search(r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\b", text)

    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3)) if date_match.group(3) else today.year

        try:
            parsed = datetime(year, month, day).date()

            if parsed < today:
                parsed = parsed.replace(year=today.year + 1)

            return parsed, date_match.group(0)
        except ValueError:
            return None, None

    month_names = "|".join(MONTHS.keys())
    text_date_match = re.search(rf"\b(\d{{1,2}})\s+({month_names})\b", text)

    if text_date_match:
        day = int(text_date_match.group(1))
        month = MONTHS[text_date_match.group(2)]
        year = today.year

        try:
            parsed = datetime(year, month, day).date()

            if parsed < today:
                parsed = datetime(year + 1, month, day).date()

            return parsed, text_date_match.group(0)
        except ValueError:
            return None, None

    return None, None


def find_time(text: str):
    time_range_match = re.search(
        r"\b(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\b",
        text
    )

    if time_range_match:
        start = parse_single_time(time_range_match.group(1))
        end = parse_single_time(time_range_match.group(2))

        if start is None or end is None:
            return None, None, None

        return start, end, time_range_match.group(0)

    time_match = re.search(r"\b(?:в\s*)?(\d{1,2}:\d{2})\b", text)

    if time_match:
        start = parse_single_time(time_match.group(1))

        if start is None:
            return None, None, None

        end_datetime = datetime.combine(datetime.now().date(), start) + timedelta(hours=1)

        return start, end_datetime.time(), time_match.group(0)

    return None, None, None


def parse_single_time(time_text: str):
    try:
        return datetime.strptime(time_text, "%H:%M").time()
    except ValueError:
        return None


def remove_fragment(text: str, fragment: str):
    pattern = re.escape(fragment)
    text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\bв\s*$", "", text, flags=re.IGNORECASE)

    return text


def clean_task_text(text: str):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+[,.;:!?]", "", text)
    text = re.sub(r"[,.;:!?]\s*$", "", text)

    return text.strip()