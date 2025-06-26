"""
Example:
-------------------------------------------------------------
>>> import datetime


>>> async def hello(name: str):
>>>     print(f'Hello {name}')

# Run it every 5 seconds for 2 times
>>> BackgroundTask(hello, 'Ali').interval(2).every_seconds(5).submit()

# Run it every day at 08:00 O'clock forever
>>> BackgroundTask(hello, 'Saba').interval(-1).every_days().at(datetime.time(hour=8)).submit()
"""

import asyncio
import datetime
import logging
import sys
import time
from enum import Enum
from threading import Lock, Thread
from typing import TYPE_CHECKING, Any, Literal

from panther._utils import is_function_async
from panther.utils import Singleton, timezone_now

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ('BackgroundTask', 'WeekDay')

logger = logging.getLogger('panther')

if sys.version_info.minor >= 11:
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BackgroundTask')


class WeekDay(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class BackgroundTask:
    """
    Schedules and runs a function periodically in the background.

    Default: Task runs once. If only a custom interval is specified, default interval time is 1 minute.
    Use submit() to add the task to the background queue.
    """

    def __init__(self, func: 'Callable', *args: Any, **kwargs: Any):
        self._func: 'Callable' = func
        self._args: tuple = args
        self._kwargs: dict = kwargs
        self._remaining_interval: int = 1
        self._last_run: datetime.datetime | None = None
        self._timedelta: datetime.timedelta = datetime.timedelta(minutes=1)
        self._time: datetime.time | None = None
        self._day_of_week: WeekDay | None = None
        self._unit: Literal['seconds', 'minutes', 'hours', 'days', 'weeks'] | None = None

    def interval(self, interval: int, /) -> Self:
        """Set how many times to run the task. interval = -1 for infinite."""
        self._remaining_interval = interval
        return self

    def every_seconds(self, seconds: int = 1, /) -> Self:
        """Run every N seconds (default 1)."""
        self._unit = 'seconds'
        self._timedelta = datetime.timedelta(seconds=seconds)
        return self

    def every_minutes(self, minutes: int = 1, /) -> Self:
        """Run every N minutes (default 1)."""
        self._unit = 'minutes'
        self._timedelta = datetime.timedelta(minutes=minutes)
        return self

    def every_hours(self, hours: int = 1, /) -> Self:
        """Run every N hours (default 1)."""
        self._unit = 'hours'
        self._timedelta = datetime.timedelta(hours=hours)
        return self

    def every_days(self, days: int = 1, /) -> Self:
        """Run every N days (default 1)."""
        self._unit = 'days'
        self._timedelta = datetime.timedelta(days=days)
        return self

    def every_weeks(self, weeks: int = 1, /) -> Self:
        """Run every N weeks (default 1)."""
        self._unit = 'weeks'
        self._timedelta = datetime.timedelta(weeks=weeks)
        return self

    def on(self, day_of_week: WeekDay, /) -> Self:
        """
        Set day to schedule the task. Accepts string like 'monday', 'tuesday', etc.
        """
        self._day_of_week = day_of_week
        return self

    def at(self, _time: datetime.time, /) -> Self:
        """Set a time to schedule the task."""
        if isinstance(_time, datetime.time):
            self._time = _time
        elif isinstance(_time, datetime.datetime):
            self._time = _time.time()
        else:
            raise TypeError(
                f'Argument should be instance of `datetime.time()` or `datetime.datetime()` not `{type(_time)}`',
            )
        return self

    def _should_wait(self) -> bool:
        """
        Returns True if the task should wait (not run yet), False if it should run now.
        """
        now = timezone_now()

        # Wait
        if self._last_run and (self._last_run + self._timedelta) > now:
            return True

        # Check day of week
        if self._day_of_week is not None and self._day_of_week.value != now.weekday():
            return True

        # We don't have time condition, so run
        if self._time is None:
            self._last_run = now
            return False

        # Time is ok, so run
        if now.hour == self._time.hour and now.minute == self._time.minute and now.second == self._time.second:
            self._last_run = now
            return False

        # Time was not ok, wait
        return True

    def __call__(self) -> bool:
        """
        Executes the task if it's time. Returns True if the task should remain scheduled, False if done.
        """
        if self._remaining_interval == 0:
            return False
        if self._should_wait():
            return True
        logger.info(
            f'{self._func.__name__}('
            f'{", ".join(str(a) for a in self._args)}, '
            f'{", ".join(f"{k}={v}" for k, v in self._kwargs.items())}'
            f') Remaining Interval -> {"∞" if self._remaining_interval == -1 else self._remaining_interval - 1}',
        )
        if self._remaining_interval != -1:
            self._remaining_interval -= 1
        try:
            if is_function_async(self._func):
                asyncio.run(self._func(*self._args, **self._kwargs))
            else:
                self._func(*self._args, **self._kwargs)
        except Exception as e:
            logger.error(f'Exception in background task {self._func.__name__}: {e}', exc_info=True)
        return True

    def submit(self) -> Self:
        """Add this task to the background task queue."""
        _background_tasks.add_task(self)
        return self


class BackgroundTasks(Singleton):
    _initialized: bool = False

    def __init__(self):
        self.tasks: list[BackgroundTask] = []
        self._lock = Lock()

    def add_task(self, task: BackgroundTask):
        if self._initialized is False:
            logger.error('Task will be ignored, `BACKGROUND_TASKS` is not True in `configs`')
            return
        if not self._is_instance_of_task(task):
            return
        with self._lock:
            if task not in self.tasks:
                self.tasks.append(task)
                logger.info(f'Task {task._func.__name__} submitted.')

    def initialize(self):
        """Call once to start background task processing."""
        if self._initialized is False:
            self._initialized = True
            Thread(target=self._run_tasks, daemon=True).start()

    def _run_task(self, task: BackgroundTask):
        should_continue = task()
        if should_continue is False:
            with self._lock:
                if task in self.tasks:
                    self.tasks.remove(task)

    def _run_tasks(self):
        while True:
            with self._lock:
                tasks_snapshot = self.tasks[:]
            for task in tasks_snapshot:
                Thread(target=self._run_task, args=(task,)).start()
            time.sleep(1)

    @classmethod
    def _is_instance_of_task(cls, task: Any, /) -> bool:
        if not isinstance(task, BackgroundTask):
            name = getattr(task, '__name__', task.__class__.__name__)
            logger.error(f'`{name}` should be instance of `background_tasks.BackgroundTask`')
            return False
        return True


_background_tasks = BackgroundTasks()
