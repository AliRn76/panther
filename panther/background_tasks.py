import asyncio
import time
import datetime
from threading import Thread
from typing import Self

from panther._utils import is_function_async
from panther.utils import Singleton


class BackgroundTask:
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._interval = 1
        self._called_count = 0
        self._last_run = None
        self._datetime = None
        self._timedelta = None
        self._time: datetime.time | None = None

    def on_interval(self, interval: int, /) -> Self:
        """
        interval = -1 --> Infinite
        """
        self._interval = interval
        if self._timedelta is None:
            self._timedelta = datetime.timedelta(minutes=1)
        return self

    def on_datetime(self, _datetime: datetime, /) -> Self:
        self._datetime = _datetime
        return self

    def interval_wait(self, _timedelta: datetime.timedelta, /) -> Self:
        """
        default is 1 minute
        ** You can't use it with `on_time()`
        """
        self._timedelta = _timedelta
        return self

    def has_interval(self) -> bool:
        return self._interval == -1 or (self._interval > self._called_count)

    def on_time(self, _time: datetime.time, /):
        """
        ** You can't use it with `interval_wait()`, it has higher priority than that
        """
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

        print(f'{self._func.__name__}({self._args[0]}) Called {self._called_count + 1}/ {self._interval}')
        self._called_count += 1
        if is_function_async(self._func):
            asyncio.run(self._func(*self._args, **self._kwargs))
        else:
            self._func(*self._args, **self._kwargs)

        return True


class BackgroundTasks(Singleton):
    tasks: list = list()

    def add_task(self, task: BackgroundTask):
        self.tasks.append(task)

    def run_task(self, task):
        if task() is False:
            self.tasks.remove(task)
            del task

    def run_tasks(self):
        def _run_tasks():
            i = 0
            while True:
                time.sleep(1)
                i += 1
                for task in self.tasks[:]:
                    Thread(target=self.run_task, args=(task,)).start()
                else:
                    print(i)

        Thread(target=_run_tasks).start()


background_tasks = BackgroundTasks()


async def hello(name: str):
    time.sleep(5)
    print(f'done {name}')
    with open(f'{name}.txt', 'a') as f:
        f.writelines('ok')


task1 = (
    BackgroundTask(hello, 'ali1')
    .on_interval(2)
    .on_time(datetime.time(hour=19, minute=18, second=10))
    .interval_wait(datetime.timedelta(seconds=5))
)
background_tasks.add_task(task1)
task2 = BackgroundTask(hello, 'arian')
background_tasks.add_task(task2)

background_tasks.run_tasks()
