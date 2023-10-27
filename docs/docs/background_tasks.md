## Intro
Panther is going to run the background tasks as a thread in the background

## Usage
import the `background_tasks` from `panther.background_tasks`:
```python
from panther.background_tasks import background_tasks
```
now you can add tasks to the `background_tasks`, but the task should be an instance of `BackgroundTask` which you can import it from `panther.background_tasks` too
```python
from panther.background_tasks import BackgroundTask, background_tasks

background_tasks.add_task(BackgroundTask(...))
```

### Create a new task
Task should be an instance of `BackgroundTask` and you have to pass a function and its parameters to it

```python
from panther.background_tasks import BackgroundTask, background_tasks


def send_otp(name: str):
    print(f'OTP Sent To {name} In Background')
    
task = BackgroundTask(send_otp, name='Ali')
background_tasks.add_task(task)
```

### Set Interval For A Task
Assume we want to send this OTP 5 times.

```python
from panther.background_tasks import BackgroundTask, background_tasks


def send_otp(name: str):
    print(f'OTP Sent To {name} In Background')
    
task = BackgroundTask(send_otp, name='Ali').interval(5)
background_tasks.add_task(task)
```

### Set Wait For Intervals
Now assume we want to send these 5 OTPs at 5-minute intervals

```python
from datetime import timedelta

from panther.background_tasks import BackgroundTask, background_tasks


def send_otp(name: str):
    print(f'OTP Sent To {name} In Background')
    
task = BackgroundTask(send_otp, name='Ali').interval(5).interval_wait(timedelta(minutes=5))
background_tasks.add_task(task)
```

### Run The Task At A Specific Time
Let's Write a task which is going to send a 'Hello' message to a user every morning at 08:00 O'clock 

```python
from datetime import time

from panther.background_tasks import BackgroundTask, background_tasks


async def send_hello(name: str):
    print(f'Hello {name}')
    
task = BackgroundTask(send_hello, name='Ali').interval(-1).on_time(time(hour=8, minute=0))
background_tasks.add_task(task)
```

### PS
> - The -1 interval means infinite, 
>
> - Default interval is 1.
> 
> - The function can be sync or async
> 
> - You can't use on_time() and interval_wait() together
> 
> - on_time() has higher priority than interval_wait()