"""APScheduler-powered Windows meal logging notifications."""

from __future__ import annotations

from collections.abc import Sequence

from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification


class ReminderService:
    """Own one in-process scheduler for configurable daily reminders."""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone=None)

    @staticmethod
    def _notify(message: str) -> None:
        notification.notify(title="NutriAI reminder", message=message, app_name="NutriAI", timeout=10)

    def start(self, times: Sequence[str], message: str = "Remember to log your meal in NutriAI.") -> list[str]:
        """Replace existing reminders and schedule valid 24-hour HH:MM times."""
        parsed: list[tuple[int, int, str]] = []
        for value in times:
            try:
                hour_text, minute_text = value.split(":", 1)
                hour, minute = int(hour_text), int(minute_text)
                if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(f"Invalid reminder time '{value}'; use HH:MM") from exc
            parsed.append((hour, minute, value))
        if not parsed:
            raise ValueError("At least one reminder time is required")
        if not self.scheduler.running:
            self.scheduler.start()
        self.scheduler.remove_all_jobs()
        for hour, minute, value in parsed:
            self.scheduler.add_job(self._notify, "cron", hour=hour, minute=minute, args=[message], id=f"meal-{value}", replace_existing=True)
        return [value for _, _, value in parsed]

    def stop(self) -> None:
        """Remove all scheduled notifications while leaving the service reusable."""
        if self.scheduler.running:
            self.scheduler.remove_all_jobs()

