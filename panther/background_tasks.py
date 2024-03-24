import asyncio
import datetime
import logging
import sys
import time
from threading import Thread
from typing import Callable, Literal

from panther._utils import is_function_async
from panther.utils import Singleton

__all__ = (
    'BackgroundTask',
    'background_tasks',
)


logger = logging.getLogger('panther')


if sys.version_info.minor >= 11:
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BackgroundTask')


class BackgroundTask:
    """
    Default: Task is going to run once,
    and if you only specify a custom interval, default interval time is 1 minutes
    """
    def __init__(self, func, *args, **kwargs):
        self._func: Callable = func
        self._args: tuple = args
        self._kwargs: dict = kwargs
        self._remaining_interval: int = 1
        self._last_run: datetime.datetime | None = None
        self._timedelta: datetime.timedelta = datetime.timedelta(minutes=1)
        self._time: datetime.time | None = None
        self._day_of_week: int | None = None
        self._unit: Literal['seconds', 'minutes', 'hours', 'days', 'weeks'] | None = None

    def interval(self, interval: int, /) -> Self:
        """
        interval = -1 --> Infinite
        """
        self._remaining_interval = interval
        return self

    def every_seconds(self, seconds: int = 1, /) -> Self:
        """
        Every How Many Seconds? (Default is 1)
        """
        self._unit = 'seconds'
        self._timedelta = datetime.timedelta(seconds=seconds)
        return self

    def every_minutes(self, minutes: int = 1, /) -> Self:
        """
        Every How Many Minutes? (Default is 1)
        """
        self._unit = 'minutes'
        self._timedelta = datetime.timedelta(minutes=minutes)
        return self

    def every_hours(self, hours: int = 1, /) -> Self:
        """
        Every How Many Hours? (Default is 1)
        """
        self._unit = 'hours'
        self._timedelta = datetime.timedelta(hours=hours)
        return self

    def every_days(self, days: int = 1, /) -> Self:
        """
        Every How Many Days? (Default is 1)
        """
        self._unit = 'days'
        self._timedelta = datetime.timedelta(days=days)
        return self

    def every_weeks(self, weeks: int = 1, /) -> Self:
        """
        Every How Many Weeks? (Default is 1)
        """
        self._unit = 'weeks'
        self._timedelta = datetime.timedelta(weeks=weeks)
        return self

    def on(
            self,
            day_of_week: Literal['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
            /
    ) -> Self:
        """
        Set day to schedule the task, useful on `.every_weeks()`
        """
        week_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if day_of_week not in week_days:
            msg = f'Argument should be one of {week_days}'
            raise TypeError(msg)

        self._day_of_week = week_days.index(day_of_week)

        if self._unit != 'weeks':
            logger.warning('`.on()` only useful when you are using `.every_weeks()`')
        return self

    def at(self, _time: datetime.time, /) -> Self:
        """
        Set a time to schedule the task,
        Only useful on `.every_days()` and `.every_weeks()`
        """
        if isinstance(_time, datetime.time):
            self._time = _time
        elif isinstance(_time, datetime.datetime):
            _time = _time.time()
        else:
            raise TypeError(
                f'Argument should be instance of `datetime.time()` or `datetime.datetime()` not `{type(_time)}`')

        if self._unit not in ['days', 'weeks']:
            logger.warning('`.at()` only useful when you are using `.every_days()` or `.every_weeks()`')

        return self

    def _should_wait(self) -> bool:
        """
        Return:
        ------
            True: Wait and do nothing
            False: Don't wait and Run this task
        """
        now = datetime.datetime.now()

        # Wait
        if self._last_run and (self._last_run + self._timedelta) > now:
            return True

        # Check day of week
        if self._day_of_week is not None:
            if self._day_of_week != now.weekday():
                return True

        # We don't have time condition, so run
        if self._time is None:
            self._last_run = now
            return False

        # Time is ok, so run
        if bool(
                now.hour == self._time.hour and
                now.minute == self._time.minute and
                now.second == self._time.second,
        ):
            self._last_run = now
            return False

        # Time was not ok
        return True

    def __call__(self) -> bool:
        """
        Return:
        ------
            True: Everything is ok
            False: This task is done, remove it from `BackgroundTasks.tasks`
        """
        if self._remaining_interval == 0:
            return False

        if self._should_wait():
            # Just wait, it's not your time yet :)
            return True

        logger.info(
            f'{self._func.__name__}('
            f'{", ".join(str(a) for a in self._args)}, '
            f'{", ".join(f"{k}={v}" for k, v in self._kwargs.items())}'
            f') Remaining Interval -> {"∞" if self._remaining_interval == -1 else self._remaining_interval - 1}',
        )
        if self._remaining_interval != -1:
            self._remaining_interval -= 1
        if is_function_async(self._func):
            asyncio.run(self._func(*self._args, **self._kwargs))
        else:
            self._func(*self._args, **self._kwargs)

        return True


class BackgroundTasks(Singleton):
    _initialized: bool = False

    def __init__(self):
        self.tasks = []

    def add_task(self, task: BackgroundTask):
        if self._initialized is False:
            logger.error('Task will be ignored, `BACKGROUND_TASKS` is not True in `configs`')
            return

        if not self._is_instance_of_task(task):
            return

        if task not in self.tasks:
            self.tasks.append(task)

    def initialize(self):
        """
        We only call initialize() once in the panther.main.Panther.load_configs()
        """

        def __run_task(task):
            if task() is False:
                self.tasks.remove(task)

        def __run_tasks():
            while True:
                [Thread(target=__run_task, args=(task,)).start() for task in self.tasks[:]]
                time.sleep(1)

        if self._initialized is False:
            self._initialized = True
            Thread(target=__run_tasks, daemon=True).start()

    @classmethod
    def _is_instance_of_task(cls, task, /):
        if not isinstance(task, BackgroundTask):
            name = getattr(task, '__name__', task.__class__.__name__)
            logger.error(f'`{name}` should be instance of `background_tasks.BackgroundTask`')
            return False
        return True


background_tasks = BackgroundTasks()

"""
-------------------------------------------------------------
Example:
-------------------------------------------------------------
>>> import datetime


>>> async def hello(name: str):
>>>     print(f'Hello {name}')

# Run it every 5 seconds for 2 times

>>> task1 = BackgroundTask(hello, 'Ali').interval(2).every_seconds(5)
>>> background_tasks.add_task(task1)

# Run it every day at 08:00 O'clock forever

>>> task2 = BackgroundTask(hello, 'Saba').interval(-1).every_days().at(datetime.time(hour=8))
>>> background_tasks.add_task(task2)
"""
