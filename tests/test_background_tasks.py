import time
from unittest import TestCase

from panther.background_tasks import BackgroundTasks, BackgroundTask
from panther.configs import config
from panther.utils import Singleton


class TestBackgroundTasks(TestCase):
    def setUp(self):
        self.obj = BackgroundTasks()
        config['background_tasks'] = True

    def tearDown(self):
        del Singleton._instances[BackgroundTasks]
        config['background_tasks'] = False

    def test_background_tasks_singleton(self):
        new_obj = BackgroundTasks()
        self.assertEqual(id(self.obj), id(new_obj))

    def test_initialization(self):
        self.assertTrue(hasattr(self.obj, 'initialize'))
        self.assertFalse(self.obj._initialized)

        self.obj.initialize()
        self.assertTrue(self.obj._initialized)
        self.assertEqual(self.obj.tasks, [])

    def test_add_single_task(self):
        def func():
            pass

        task = BackgroundTask(func)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])

    def test_add_wrong_task(self):
        def func(): pass

        self.obj.initialize()
        self.assertEqual(self.obj.tasks, [])

        with self.assertLogs() as captured:
            self.obj.add_task(func)

        self.assertEqual(len(captured.records), 1)
        self.assertEqual(
            captured.records[0].getMessage(),
            f'`{func.__name__}` should be instance of `background_tasks.BackgroundTask`'
        )
        self.assertEqual(self.obj.tasks, [])

    def test_add_task_with_false_background_task(self):
        numbers = []

        def func(_numbers): _numbers.append(1)

        task = BackgroundTask(func, numbers)
        with self.assertLogs() as captured:
            self.obj.add_task(task)
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(
            captured.records[0].getMessage(),
            'Task will be ignored, `BACKGROUND_TASKS` is not True in `core/configs.py`'
        )
        self.assertEqual(self.obj.tasks, [])

    def test_add_task_with_args(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])
        time.sleep(2)
        self.assertEqual(len(numbers), 1)

    def test_add_task_with_kwargs(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, _numbers=numbers)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])
        time.sleep(2)
        self.assertEqual(len(numbers), 1)

    def test_add_task_with_custom_interval(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).every_seconds().interval(3)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])
        time.sleep(4)
        self.assertEqual(len(numbers), 3)

    def test_add_task_with_custom_interval_default_timedelta(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).interval(2)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])
        time.sleep(3)
        # default timedelta is 1 minute, so it can't complete the intervals in 2 seconds
        self.assertEqual(len(numbers), 1)

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
        self.assertEqual(self.obj.tasks, [task1, task2])
        time.sleep(1)
        self.assertEqual(len(numbers), 0)
        time.sleep(1)
        self.assertEqual(len(numbers), 2)

    def test_add_task_with_custom_every_seconds(self):
        numbers = []

        def func(_numbers):
            _numbers.append(1)

        task = BackgroundTask(func, numbers).every_seconds(3).interval(2)
        self.obj.initialize()
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])
        time.sleep(3)
        self.assertEqual(len(numbers), 1)
        time.sleep(3)
        self.assertEqual(len(numbers), 2)


# TODO: Run tests for every_minutes(), every_hours(), every_days(), every_weeks(), at()
