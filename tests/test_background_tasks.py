from unittest import TestCase

from panther.background_tasks import BackgroundTasks, BackgroundTask
from panther.utils import Singleton


class TestBackgroundTasks(TestCase):
    def setUp(self):
        self.obj = BackgroundTasks()
        # Comment the line below to see the error :(
        self.obj.tasks = []

    def tearDown(self):
        del Singleton._instances[BackgroundTasks]

    def test_background_tasks_singleton(self):
        new_obj = BackgroundTasks()
        self.assertEqual(id(self.obj), id(new_obj))

    def test_initialization(self):
        self.assertTrue(hasattr(self.obj, 'initialize'))
        self.assertFalse(self.obj._initialized)
        self.obj.initialize()
        self.assertTrue(self.obj._initialized)
        self.assertEqual(self.obj.tasks, [])

    def test_single_add_task(self):
        def func1():
            pass

        task = BackgroundTask(func1)
        self.obj.add_task(task)
        self.assertEqual(self.obj.tasks, [task])

    def test_wrong_add_task(self):
        def func2():
            pass

        self.assertEqual(self.obj.tasks, [])

        # # # Commented For Amin
        # with self.assertLogs() as captured:
        #     self.obj.add_task(func2)
        #
        # self.assertEqual(len(captured.records), 1)
        # self.assertEqual(
        #     captured.records[0].getMessage(),
        #     f'`{func2.__name__}` should be instance of `background_tasks.BackgroundTask`'
        # )
