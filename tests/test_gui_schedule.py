from datetime import datetime, timedelta, timezone
import time
import unittest

from search_engine.scheduler.gui_schedule import (
    _reset_for_tests,
    get_gui_schedule_state,
    schedule_gui_update,
)
from search_engine.scheduler.weekly_update import ScheduledUpdateResult


def fake_update_runner(**_kwargs):
    now = datetime.now(timezone.utc)
    return ScheduledUpdateResult(
        started_at=now,
        finished_at=now,
        publications_extracted=2,
        publications_saved=2,
        pages_visited=1,
        profile_pages_visited=1,
        crawl_run_id="fake-run",
        index_message="fake index rebuilt",
    )


class GuiScheduleTests(unittest.TestCase):
    def setUp(self):
        _reset_for_tests()

    def tearDown(self):
        _reset_for_tests()

    def test_schedule_rejects_past_datetime(self):
        scheduled_for = datetime.now(timezone.utc) - timedelta(seconds=1)

        with self.assertRaises(ValueError):
            schedule_gui_update(
                scheduled_for=scheduled_for,
                max_listing_pages=1,
                max_profile_pages=1,
                max_publications=1,
                update_runner=fake_update_runner,
            )

    def test_scheduled_update_runs_with_runner(self):
        scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=0.05)
        schedule_gui_update(
            scheduled_for=scheduled_for,
            max_listing_pages=1,
            max_profile_pages=1,
            max_publications=2,
            update_runner=fake_update_runner,
        )

        state = get_gui_schedule_state()
        for _ in range(100):
            state = get_gui_schedule_state()
            if state.status == "completed":
                break
            time.sleep(0.02)

        self.assertEqual(state.status, "completed")
        self.assertIsNotNone(state.result)
        self.assertEqual(state.result.publications_saved, 2)


if __name__ == "__main__":
    unittest.main()
