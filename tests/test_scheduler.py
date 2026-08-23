import unittest

from search_engine.scheduler.weekly_update import interval_days_to_seconds


class SchedulerTests(unittest.TestCase):
    def test_interval_days_to_seconds(self):
        self.assertEqual(interval_days_to_seconds(7), 604800)
        self.assertEqual(interval_days_to_seconds(0.5), 43200)

    def test_interval_days_to_seconds_rejects_non_positive_values(self):
        with self.assertRaises(ValueError):
            interval_days_to_seconds(0)


if __name__ == "__main__":
    unittest.main()
