"""SimClock: advances simulation time week-by-week through 2026."""

from datetime import date, datetime, timedelta
from typing import Iterator, NamedTuple


class SimWeek(NamedTuple):
    """A single week in the simulation."""
    week_number: int   # 1-52
    monday: date       # The Monday of this week
    quarter: int       # 1-4


class SimClock:
    """Iterates week-by-week from Jan 5 2026 to Dec 28 2026 (52 weeks)."""

    def __init__(
        self,
        start: date = date(2026, 1, 5),
        end: date = date(2026, 12, 28),
    ):
        self.start = start
        self.end = end

    def weeks(self) -> Iterator[SimWeek]:
        """Yield one SimWeek per week across the simulation period."""
        current = self.start
        week_num = 1
        while current <= self.end:
            quarter = (current.month - 1) // 3 + 1
            yield SimWeek(week_number=week_num, monday=current, quarter=quarter)
            current += timedelta(weeks=1)
            week_num += 1

    @staticmethod
    def date_in_week(week: SimWeek, weekday: int = 0, hour: int = 9) -> datetime:
        """Return a datetime within the given week.

        Args:
            week: The simulation week.
            weekday: 0=Monday .. 4=Friday.
            hour: Hour of day (0-23).
        """
        d = week.monday + timedelta(days=weekday)
        return datetime(d.year, d.month, d.day, hour, 0, 0)
