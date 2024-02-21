## Intro
Panther is going to run the `background tasks` as a thread in the background on startup if you set the `BACKGROUND_TASKS` to `True`

## Usage
- Add the `BACKGROUND_TASKS = True` in the `configs`  

- Import the `background_tasks` from `panther.background_tasks`:
    ```python
    from panther.background_tasks import background_tasks
    ```

- Create a `task`
    ```python
    from panther.background_tasks import background_tasks, BackgroundTask
    
    def do_something(name: str, age: int):
        pass
  
    task = BackgroundTask(do_something, name='Ali', age=26)
    ```
  
- Now you can add your task to the `background_tasks`
    ```python
    from panther.background_tasks import background_tasks, BackgroundTask
    
    def do_something(name: str, age: int):
        pass
  
    task = BackgroundTask(do_something, name='Ali', age=26)
    background_tasks.add_task(task)
    ```


## Options
- ### Interval
    You can set custom `interval` for the `tasks`, let's say we want to run the `task` below for `3 times`.
    
    ```python
    from panther.background_tasks import BackgroundTask, background_tasks
    
    
    def do_something(name: str, age: int):
        pass
        
    task = BackgroundTask(do_something, name='Ali', age=26).interval(3)
    background_tasks.add_task(task)
    ```
  
- ### Schedule
  `BackgroundTask` has some methods to `schedule` the run time, (Default value of them is `1`)
  - `every_seconds()`
  - `every_minutes()` 
  - `every_hours()` 
  - `every_days()`
  - `every_weeks()`
  - `at()`  # Set Custom Time
  - `on()`  # Set Custom Day Of Week
  > You can pass your custom value to them too, 
  > 
  > **Example**: Run Every 4 days: `every_days(4)`.
 

- ### Time Specification
  You can set a custom `time` to tasks too
  
  let's say we want to run the `task` below every day on `8:00` o'clock. 

  ```python
  from datetime import time
  
  from panther.background_tasks import BackgroundTask, background_tasks
  
  
  def do_something(name: str, age: int):
          pass
      
  task = BackgroundTask(do_something, name='Ali', age=26).every_days().at(time(hour=8))
  background_tasks.add_task(task)
  ```

- ### Day Of Week Specification
  Now we want to run the `task` below every 2 week on `monday`, on `8:00` o'clock. 

  ```python
  from datetime import time
  
  from panther.background_tasks import BackgroundTask, background_tasks
  
  
  def do_something(name: str, age: int):
          pass
      
  task = BackgroundTask(do_something, name='Ali', age=26).every_weeks(2).on('monday').at(time(hour=8))
  background_tasks.add_task(task)
  ```

## Notice
- > The `task` function can be `sync` or `async`

- > You can pass the arguments to the task as `args` and `kwargs` 
  
    ```python
    def do_something(name: str, age: int):
            pass
        
    task = BackgroundTask(do_something, name='Ali', age=26)
    or 
    task = BackgroundTask(do_something, 'Ali', age=26)
    or 
    task = BackgroundTask(do_something, 'Ali', 26)
    ```

- > Default interval is 1.

- > The -1 interval means infinite, 

- > The `.at()` only useful when you are using `.every_days()` or `.every_weeks()`

- > The `.on()` only useful when you are using `.every_weeks()`
