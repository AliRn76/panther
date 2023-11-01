import asyncio
import datetime
import sys
import time
from threading import Thread
from typing import Callable, ClassVar

from panther._utils import is_function_async
from panther.logger import logger
from panther.utils import Singleton

__all__ = (
    'BackgroundTask',
    'background_tasks',
)


if sys.version_info.minor >= 11:
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BackgroundTask')


class BackgroundTask:
    def __init__(self, func, *args, **kwargs):
        self._func: Callable = func
        self._args: tuple = args
        self._kwargs: dict = kwargs
        self._interval: int = 1
        self._called_count: int = 0
        self._last_run: datetime.datetime | None = None
        self._timedelta: datetime.timedelta | None = None
        self._time: datetime.time | None = None

    def interval(self, interval: int, /) -> Self:
        """
        interval = -1 --> Infinite
        """
        self._interval = interval
        if self._timedelta is None:
            self._timedelta = datetime.timedelta(minutes=1)
        return self

    def interval_wait(self, _timedelta: datetime.timedelta, /) -> Self:
        """
        default is 1 minute
        """
        if self._time:
            logger.warning(
                'You may not want to use `BackgroundTask.interval_wait()` with `.on_time()`, '
                '`.on_time()` has higher priority.')
        self._timedelta = _timedelta
        return self

    def on_time(self, _time: datetime.time, /) -> Self:
        if self._timedelta:
            logger.warning(
                'You may not want to use `BackgroundTask.on_time()` with `.interval_wait()`, '
                '`.on_time()` has higher priority.')
        if isinstance(_time, datetime.datetime):
            _time = _time.time()

        self._time = _time
        return self

    def _has_interval(self) -> bool:
        return self._interval == -1 or (self._interval > self._called_count)

    def _should_wait(self) -> bool:
        """
        Return:
        ------
            True means you have to wait and do nothing
            False means don't wait and Run this task
        """
        now = datetime.datetime.now()
        if self._time is None and self._timedelta is None:
            return False

        if self._time:
            return not bool(
                now.hour == self._time.hour and
                now.minute == self._time.minute and
                now.second == self._time.second,
            )

        if self._last_run is None:
            self._last_run = now
            return False

        if (self._last_run + self._timedelta) < now:
            return False

        return True

    def __call__(self) -> bool:
        """
        Return:
        ------
            True means everything is ok
            False means this task is done, remove it from `BackgroundTasks.tasks`
        """
        if self._has_interval() is False:
            return False

        if self._should_wait():
            # Just wait, it's not your time yet :)
            return True

        logger.info(
            f'{self._func.__name__}('
            f'{", ".join(a for a in self._args)}, '
            f'{", ".join(f"{k}={v}" for k, v in self._kwargs.items())}'
            f') Called {self._called_count + 1}/ {self._interval}',
        )
        self._called_count += 1
        if is_function_async(self._func):
            asyncio.run(self._func(*self._args, **self._kwargs))
        else:
            self._func(*self._args, **self._kwargs)

        return True


class BackgroundTasks(Singleton):
    tasks: ClassVar[list] = list()
    _initialized: bool = False

    def add_task(self, task: BackgroundTask):
        if not isinstance(task, BackgroundTask):
            name = getattr(task, '__name__', task.__class__.__name__)
            logger.error(f'`{name}` should be instance of `background_tasks.BackgroundTask`')
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
                time.sleep(1)
                [Thread(target=__run_task, args=(task,)).start() for task in self.tasks[:]]

        if self._initialized is False:
            self._initialized = True
            Thread(target=__run_tasks, daemon=True).start()


background_tasks = BackgroundTasks()

"""
-------------------------------------------------------------
Example:
-------------------------------------------------------------
import datetime


async def hello(name: str):
    time.sleep(5)
    print(f'Done {name}')


task = (
  BackgroundTask(hello, 'Ali')
  .interval(2)
  .interval_wait(datetime.timedelta(seconds=5))
 # .on_time(datetime.time(hour=19, minute=18, second=10))
)

background_tasks.add_task(task)
"""
