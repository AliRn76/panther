import asyncio
import sys
import time
import datetime
from threading import Thread
from panther.logger import logger
from panther._utils import is_function_async
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
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._interval = 1
        self._called_count = 0
        self._last_run = None
        self._timedelta = None
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
            logger.warning("You can't use `BackgroundTask.interval_wait()` with `.on_time()`, "
                           "`.on_time()` has higher priority.")
        self._timedelta = _timedelta
        return self

    def has_interval(self) -> bool:
        return self._interval == -1 or (self._interval > self._called_count)

    def on_time(self, _time: datetime.time, /):
        if self._timedelta:
            logger.warning("You can't use `BackgroundTask.on_time()` with `.interval_wait()`, "
                           "`.on_time()` has higher priority.")
        if isinstance(_time, datetime.datetime):
            _time = _time.time()

        self._time = _time
        return self

    def should_wait(self) -> bool:
        now = datetime.datetime.now()
        if self._time is None and self._timedelta is None:
            return False

        if self._time:
            if now.hour == self._time.hour and now.minute == self._time.minute and now.second == self._time.second:
                return False
            else:
                return True

        if self._last_run is None:
            self._last_run = now
            return False

        if (self._last_run + self._timedelta) < now:
            return False

        return True

    def __call__(self) -> bool:
        if self.has_interval() is False:
            return False
        if self.should_wait():
            return True

        logger.info(
            f'{self._func.__name__}('
            f'{", ".join(a for a in self._args)}, '
            f'{", ".join(f"{k}={v}" for k, v in self._kwargs.items())}'
            f') Called {self._called_count + 1}/ {self._interval}'
        )
        self._called_count += 1
        if is_function_async(self._func):
            asyncio.run(self._func(*self._args, **self._kwargs))
        else:
            self._func(*self._args, **self._kwargs)

        return True


class BackgroundTasks(Singleton):
    tasks: list = list()
    _is_alive: bool = False

    def add_task(self, task: BackgroundTask):
        if not isinstance(task, BackgroundTask):
            name = getattr(task, '__name__', task.__class__.__name__)
            logger.error(f'`{name}` should be instance of `background_tasks.BackgroundTask`')
            return

        if task not in self.tasks:
            self.tasks.append(task)

    def _run_tasks(self):
        """
        We only call _run_tasks() once in the load_configs()
        """

        def __run_task(task):
            if task() is False:
                self.tasks.remove(task)
                del task

        def __run_tasks():
            while True:
                time.sleep(1)
                for task in self.tasks[:]:
                    Thread(target=__run_task, args=(task,)).start()

        if self._is_alive is False:
            self._is_alive = True
            Thread(target=__run_tasks, daemon=True).start()


background_tasks = BackgroundTasks()

"""
-------------------------------------------------------------
Example:
-------------------------------------------------------------

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