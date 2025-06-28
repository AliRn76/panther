# Background Tasks in Panther

Panther can run background tasks in a separate thread at startup if you set `BACKGROUND_TASKS` to `True` in your configuration.

## Quick Start

1. **Enable background tasks**  
   In your `configs`, add:
   ```python
   BACKGROUND_TASKS = True
   ```

2. **Create and submit a task**  
    ```python linenums="1"
    from panther.background_tasks import BackgroundTask
    
    def do_something(name: str, age: int):
       print(f"{name} is {age} years old.")
    
    BackgroundTask(do_something, name='Ali', age=26).submit()
    ```
    - You must call `.submit()` to add the task to the queue.
      - The task function can be synchronous or asynchronous.

---

## Task Options

### 1. Interval

Control how many times a task runs:

```python
BackgroundTask(do_something, name='Ali', age=26).interval(3).submit()
```

- By default, tasks run once (`interval=1`).
- Use `interval(-1)` for infinite runs.
- Each interval is separated by the schedule you set (see below).

### 2. Scheduling

You can schedule tasks to run at specific intervals:

- **Every N seconds/minutes/hours/days/weeks:**
    ```python
    BackgroundTask(do_something, name='Ali', age=26).every_seconds(10).submit()
    BackgroundTask(do_something, name='Ali', age=26).every_minutes(5).submit()
    BackgroundTask(do_something, name='Ali', age=26).every_hours(2).submit()
    BackgroundTask(do_something, name='Ali', age=26).every_days(1).submit()
    BackgroundTask(do_something, name='Ali', age=26).every_weeks(1).submit()
    ```
    - Default value for each is `1` (e.g., every 1 minute).

- **Custom values:**  
  You can pass a custom value to any of the above, e.g., `every_days(4)` runs every 4 days.

### 3. Time of Day

Run a task at a specific time:

```python linenums="1"
from datetime import time
from panther.background_tasks import BackgroundTask

BackgroundTask(do_something, name='Ali', age=26)\
    .every_days()\
    .at(time(hour=8, minute=0))\
    .submit()
```

- The task will run when the system time matches the specified hour, minute, and second.

### 4. Day of Week

Run a task on a specific day of the week:

```python linenums="1"
from datetime import time
from panther.background_tasks import BackgroundTask, WeekDay

BackgroundTask(do_something, name='Ali', age=26)\
    .every_weeks(2)\
    .on(WeekDay.SUNDAY)\
    .at(time(hour=8))\
    .submit()
```

- Valid days: `WeekDay.MONDAY`, `WeekDay.TUESDAY`, `WeekDay.WEDNESDAY`, `WeekDay.THURSDAY`, `WeekDay.FRIDAY`, `WeekDay.SATURDAY`, `WeekDay.SUNDAY`.

---

## Passing Arguments

You can pass arguments to your task function as positional or keyword arguments:

```python
BackgroundTask(do_something, name='Ali', age=26)
BackgroundTask(do_something, 'Ali', age=26)
BackgroundTask(do_something, 'Ali', 26)
```

---

## Important Notes & Best Practices

- **Task function** can be synchronous or asynchronous.
- **You must call `.submit()`** to add the task to the background queue.
- **Default interval** is 1 (runs once). Use `.interval(-1)` for infinite runs.
- If you try to add a task before `BACKGROUND_TASKS` is enabled, it will be ignored and a warning will be logged.
- Each task runs in its own thread when triggered.
- Tasks are checked every second for their schedule.

---

## Example: Task

```python linenums="1"
import datetime
from panther.background_tasks import BackgroundTask

async def hello(name: str):
    print(f'Hello {name}')

# Run 2 times, every 5 seconds
BackgroundTask(hello, 'Ali').interval(2).every_seconds(5).submit()

# Run forever, every day at 08:00
BackgroundTask(hello, 'Saba').interval(-1).every_days().at(datetime.time(hour=8)).submit()
```
