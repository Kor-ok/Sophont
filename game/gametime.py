import datetime

"""
Imperial Calendar Year 0 = 4518 AD

T5 says 4521 CE
"""

IMPERIAL_YEAR_OFFSET = 4518

def imperial_to_gregorian(imperial_year: int, imperial_month: int = 1, imperial_day: int = 1) -> datetime.date:
    """Convert an Imperial calendar date to a Gregorian date.

    Args:
        imperial_year (int): The year in the Imperial calendar (e.g., 0 for 4518 AD).
        imperial_month (int): The month in the Imperial calendar (1-12).
        imperial_day (int): The day in the Imperial calendar (1-31).

    Returns:
        datetime.date: The corresponding Gregorian date.
    """
    base_year = IMPERIAL_YEAR_OFFSET
    gregorian_year = base_year + imperial_year
    return datetime.date(gregorian_year, imperial_month, imperial_day)

def gregorian_to_imperial(gregorian_date: datetime.date) -> tuple[int, int, int]:
    """Convert a Gregorian date to an Imperial calendar date.

    Args:
        gregorian_date (datetime.date): The Gregorian date to convert.

    Returns:
        tuple[int, int, int]: A tuple containing the Imperial year, month, and day.
    """
    base_year = IMPERIAL_YEAR_OFFSET
    imperial_year = gregorian_date.year - base_year
    imperial_month = gregorian_date.month
    imperial_day = gregorian_date.day
    return (imperial_year, imperial_month, imperial_day)

"""
Imperial Calendar (IC) is formatted as "DDD-YYYY IC" where DDD is the day of the year (001-365).
"""
def parse_imperial_date_to_components(date_str: str) -> tuple[int, int, int]: # returns (year, month, day)
    """Parse an Imperial date string formatted as "DDD-YYYY IC".

    Args:
        date_str (str): The Imperial date string. Accepted examples:
            "123-0023 IC"
            "123-0023" (the trailing "IC" is optional and ignored if present)
            Whitespace around components is tolerated.

    Returns:
        tuple[int, int, int]: A tuple containing the Imperial year, month, and day.
    """
    import re

    if not isinstance(date_str, str):
        raise TypeError("date_str must be a string")

    pattern = re.compile(r"^\s*(\d{1,3})-(\d{1,5})(?:\s+IC)?\s*$", re.IGNORECASE)
    match = pattern.match(date_str)
    if not match:
        raise ValueError("Date string must match 'DDD-YYYY' optionally followed by 'IC'")

    day_of_year = int(match.group(1))
    imperial_year = int(match.group(2))

    # Validate day_of_year (allow 366 only on leap years of the translated Gregorian year)
    gregorian_year = IMPERIAL_YEAR_OFFSET + imperial_year

    def _is_leap(y: int) -> bool:
        return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

    max_day = 366 if _is_leap(gregorian_year) else 365
    if day_of_year < 1 or day_of_year > max_day:
        raise ValueError(f"Day-of-year {day_of_year} out of range for Imperial year {imperial_year} (1-{max_day})")

    # Convert day-of-year to month/day by adding offset to Jan 1
    gregorian_date = datetime.date(gregorian_year, 1, 1) + datetime.timedelta(days=day_of_year - 1)
    return (imperial_year, gregorian_date.month, gregorian_date.day)

def format_imperial_date(imperial_year: int, imperial_month: int, imperial_day: int) -> str:
    """Format an Imperial date as "DDD-YYYY IC".

    Args:
        imperial_year (int): The year in the Imperial calendar.
        imperial_month (int): The month in the Imperial calendar (1-12).
        imperial_day (int): The day in the Imperial calendar (1-31).

    Returns:
        str: The formatted Imperial date string.
    """
    gregorian_date = imperial_to_gregorian(imperial_year, imperial_month, imperial_day)
    day_of_year = (gregorian_date - datetime.date(gregorian_date.year, 1, 1)).days + 1
    return f"{day_of_year:03}-{imperial_year:04} IC"

def compute_imperial_day_name(imperial_day: int) -> str:
    """Compute the name of the day in the Imperial calendar.

    The year  is divided into 365 standard days, which are grouped into 52
    weeks of seven days each. Days are numbered consecutively, beginning w
    ith one. The first day of the year is a holiday and is not part of any
    week.

    For example,  The first day (Holiday)   of  the year 1116  is 001-1116
    and the last day of the year is 365-1116.

    The days  of each week are   named  based upon their  ordinal position
    in the week: Wonday or 1day, Tuday or 2day, Thirday or 3day, Forday or
    4day,  Fiday or 5day, Sixday or 6day, Senday  or 7day. The holiday day
    does not belong any week and is simply named "Holiday".
    
    Args:
        imperial_day (int): The day in the Imperial calendar (1-365).

    Returns:
        str: The name of the day in the Imperial calendar.
    """
    if not isinstance(imperial_day, int):
        raise TypeError("imperial_day must be an int")

    # Validate range (standard Imperial year description mentions 365 days + 1 holiday at day 1)
    if imperial_day < 1 or imperial_day > 365:
        raise ValueError("imperial_day must be in the range 1..365")

    if imperial_day == 1:
        return "Holiday"

    # Days 2..365 form 52 full weeks of 7 days (364 days)
    day_in_weeks = imperial_day - 2  # zero-based within the 364-day week structure
    names = [
        "Wonday",  # 1st day of the week
        "Tuday",   # 2nd
        "Thirday", # 3rd
        "Forday",  # 4th
        "Fiday",   # 5th
        "Sixday",  # 6th
        "Senday"   # 7th
    ]
    return names[day_in_weeks % 7]
