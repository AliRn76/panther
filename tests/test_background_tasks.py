import datetime
import time
from unittest import TestCase

import pytest

from panther.background_tasks import BackgroundTask, BackgroundTasks, WeekDay, _background_tasks
from panther.configs import config
from panther.utils import Singleton, timezone_now


@pytest.mark.slow
class TestBackgroundTasks(TestCase):
    def setUp(self):
        self.obj = BackgroundTasks()
        config.BACKGROUND_TASKS = True

    def tearDown(self):
        del Singleton._instances[BackgroundTasks]
        config.BACKGROUND_TASKS = False

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    def test_background_tasks_singleton(self):
        new_obj = BackgroundTasks()
        assert id(self.obj) == id(new_obj)

    def test_initialization(self):
        assert hasattr(self.obj, 'initialize') is True
        assert self.obj._initialized is False

        self.obj.initialize()
        assert self.obj._initialized is True
        assert self.obj.tasks == []

    def test_add_single_task(self):
        def func():
            pass

        task = BackgroundTask(func)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]

    def test_add_wrong_task(self):
        def func():
            pass

        self.obj.initialize()
        assert self.obj.tasks == []

        with self.assertLogs() as captured:
            self.obj.add_task(func)

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage() == f'`{func.__name__}` '
            f'should be instance of `background_tasks.BackgroundTask`'
        )
        assert self.obj.tasks == []

    def test_add_task_with_false_background_task(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers)
        with self.assertLogs() as captured:
            self.obj.add_task(task)
        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'Task will be ignored, `BACKGROUND_TASKS` is not True in `configs`'
        assert self.obj.tasks == []

    def test_add_task_with_args(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]
        time.sleep(2)
        assert len(numbers) == 1

    def test_add_task_with_kwargs(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, _numbers=numbers)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]
        time.sleep(2)
        assert len(numbers) == 1

    def test_add_task_with_custom_interval(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).every_seconds().interval(3)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]
        time.sleep(4)
        assert len(numbers) == 3

    def test_add_task_with_custom_interval_default_timedelta(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).interval(2)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]
        time.sleep(3)
        # default timedelta is 1 minute, so it can't complete the intervals in 2 seconds
        assert len(numbers) == 1

    def test_add_multiple_tasks(self):
        numbers = []

        def func1(_numbers):
            _numbers.append(1)

        def func2(_numbers):
            _numbers.append(1)

        task2 = BackgroundTask(func1, numbers)
        task1 = BackgroundTask(func2, numbers)
        self.obj.initialize()
        self.obj.add_task(task1)
        self.obj.add_task(task2)
        assert self.obj.tasks == [task1, task2]
        assert len(numbers) == 0
        time.sleep(2)
        assert len(numbers) == 2

    def test_concurrent_tasks(self):
        numbers = []

        def func1(_numbers):
            time.sleep(3)
            _numbers.append(1)

        def func2(_numbers):
            time.sleep(3)
            _numbers.append(1)

        _background_tasks.initialize()
        BackgroundTask(func1, numbers).submit()
        BackgroundTask(func2, numbers).submit()
        assert len(numbers) == 0
        time.sleep(5)  # Initialization takes 2 second
        assert len(numbers) == 2

    def test_add_task_with_custom_every_3_seconds(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).every_seconds(3).interval(2)
        self.obj.initialize()
        self.obj.add_task(task)
        assert self.obj.tasks == [task]
        time.sleep(3)
        assert len(numbers) == 1
        time.sleep(3)
        assert len(numbers) == 2

    def test_submit_single_task(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        _background_tasks.initialize()
        task = BackgroundTask(func, numbers).submit()
        assert _background_tasks.tasks == [task]
        assert len(numbers) == 0
        time.sleep(2)
        assert len(numbers) == 1

    def test_task_at_3second_later(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        now = timezone_now()

        _background_tasks.initialize()
        BackgroundTask(func, numbers).at((now + datetime.timedelta(seconds=3)).time()).submit()
        time.sleep(2)
        assert len(numbers) == 0
        time.sleep(2)
        assert len(numbers) == 1

    def test_task_on_specific_weekday(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        now = timezone_now()
        week_days = {
            0: WeekDay.MONDAY,
            1: WeekDay.TUESDAY,
            2: WeekDay.WEDNESDAY,
            3: WeekDay.THURSDAY,
            4: WeekDay.FRIDAY,
            5: WeekDay.SATURDAY,
            6: WeekDay.SUNDAY,
        }

        _background_tasks.initialize()
        BackgroundTask(func, numbers).on(week_days[now.weekday()]).submit()
        assert len(numbers) == 0
        time.sleep(1)
        assert len(numbers) == 1
