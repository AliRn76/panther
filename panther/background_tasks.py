import asyncio
import time
from typing import Callable
from threading import Thread
from panther.utils import Singleton

from panther._utils import is_function_async


class BackgroundTask:
    def __init__(self, func, interval, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.interval = interval
        self._called_count = 0

    @property
    def is_alive(self) -> bool:
        return self.interval == -1 or (self.interval > self._called_count)

    def __call__(self) -> bool:
        if self.is_alive:
            print(f'{self.func.__name__}({self.args[0]}) Called {self._called_count + 1}/ {self.interval}')
            self._called_count += 1
            if is_function_async(self.func):
                asyncio.run(self.func(*self.args, **self.kwargs))
            else:
                self.func(*self.args, **self.kwargs)
            return True
        return False


class BackgroundTasks(Singleton):
    tasks: list = list()

    def add_task(self, func: Callable, *args, interval=1, **kwargs):
        """
        interval = -1 --> Infinite
        """
        self.tasks.append(BackgroundTask(func, interval, *args, **kwargs))

    def run_tasks(self):
        def _run_task():
            i = 0
            while True:
                time.sleep(2)
                i += 1
                _tasks = self.tasks.copy()
                for task in _tasks:
                    if task() is False:
                        self.tasks.remove(task)
                        del task
                else:
                    print(i)
        Thread(target=_run_task).start()


async def hello(name: str):
    with open(f'{name}.txt', 'a') as f:
        f.writelines('ok')


background_tasks = BackgroundTasks()
background_tasks.add_task(hello, 'ali', interval=2)
background_tasks.run_tasks()
background_tasks.add_task(hello, 'arian')
