"""In-memory GUI scheduler for one Streamlit-controlled crawl update."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Event, Lock, Thread
from typing import Callable
from uuid import uuid4

from search_engine.scheduler.weekly_update import ScheduledUpdateResult, run_update_once


UpdateRunner = Callable[..., ScheduledUpdateResult]


@dataclass(frozen=True)
class GuiScheduleState:
    status: str = "idle"
    job_id: str | None = None
    scheduled_for: datetime | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    max_listing_pages: int | None = None
    max_profile_pages: int | None = None
    max_publications: int | None = None
    result: ScheduledUpdateResult | None = None
    error: str | None = None


_lock = Lock()
_state = GuiScheduleState()
_cancel_event: Event | None = None
_worker: Thread | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _set_state(job_id: str, **changes) -> None:
    global _state
    with _lock:
        if _state.job_id == job_id:
            _state = replace(_state, **changes)


def _run_at_scheduled_time(
    job_id: str,
    cancel_event: Event,
    update_runner: UpdateRunner,
) -> None:
    state = get_gui_schedule_state()
    if state.scheduled_for is None:
        return

    wait_seconds = max(0.0, (state.scheduled_for - _utc_now()).total_seconds())
    if cancel_event.wait(wait_seconds):
        _set_state(job_id, status="cancelled", finished_at=_utc_now())
        return

    _set_state(job_id, status="running", started_at=_utc_now())
    try:
        result = update_runner(
            max_listing_pages=state.max_listing_pages,
            max_profile_pages=state.max_profile_pages,
            max_publications=state.max_publications,
        )
    except Exception as exc:
        _set_state(
            job_id,
            status="failed",
            finished_at=_utc_now(),
            error=str(exc),
        )
        return

    _set_state(
        job_id,
        status="completed",
        finished_at=_utc_now(),
        result=result,
    )


def get_gui_schedule_state() -> GuiScheduleState:
    with _lock:
        return _state


def schedule_gui_update(
    scheduled_for: datetime,
    max_listing_pages: int,
    max_profile_pages: int,
    max_publications: int,
    update_runner: UpdateRunner = run_update_once,
) -> GuiScheduleState:
    """Schedule one crawl/index update while the Streamlit server is running."""
    global _cancel_event, _state, _worker

    if scheduled_for.tzinfo is None:
        scheduled_for = scheduled_for.replace(tzinfo=timezone.utc)

    scheduled_for = scheduled_for.astimezone(timezone.utc)
    now = _utc_now()
    if scheduled_for <= now:
        raise ValueError("Scheduled date and time must be in the future.")

    with _lock:
        if _state.status in {"waiting", "running"}:
            raise RuntimeError("A scheduled crawl update is already active.")

        job_id = uuid4().hex
        _cancel_event = Event()
        _state = GuiScheduleState(
            status="waiting",
            job_id=job_id,
            scheduled_for=scheduled_for,
            created_at=now,
            max_listing_pages=max_listing_pages,
            max_profile_pages=max_profile_pages,
            max_publications=max_publications,
        )
        _worker = Thread(
            target=_run_at_scheduled_time,
            args=(job_id, _cancel_event, update_runner),
            daemon=True,
        )
        _worker.start()
        return _state


def cancel_gui_update() -> GuiScheduleState:
    """Cancel a waiting GUI scheduled update."""
    global _state

    with _lock:
        if _state.status != "waiting" or _cancel_event is None:
            return _state

        _cancel_event.set()
        _state = replace(_state, status="cancelled", finished_at=_utc_now())
        return _state


def _reset_for_tests() -> None:
    global _cancel_event, _state, _worker

    with _lock:
        worker = _worker
        cancel_event = _cancel_event

    if cancel_event is not None:
        cancel_event.set()
    if worker is not None and worker.is_alive():
        worker.join(timeout=1)

    with _lock:
        _state = GuiScheduleState()
        _cancel_event = None
        _worker = None
