import unittest
from datetime import datetime, timezone

from search_engine.app import format_datetime


class AppDatetimeTests(unittest.TestCase):
    def test_format_datetime_shows_local_date_hour_and_minute(self):
        formatted = format_datetime(datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc))

        self.assertRegex(formatted, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


if __name__ == "__main__":
    unittest.main()
