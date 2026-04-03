from datetime import datetime, date
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Asia/Taipei")


def now_tw() -> datetime:
    return datetime.now(APP_TIMEZONE)


def today_tw() -> date:
    return now_tw().date()


def parse_month_filter(month_str: str):
    if not month_str:
        return None, None

    try:
        year, month = month_str.split("-")
        year = int(year)
        month = int(month)

        start_date = f"{year:04d}-{month:02d}-01"

        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"

        return start_date, end_date
    except Exception:
        return None, None