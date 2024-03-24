## Startup Event

Use `Event.startup` decorator

```python
from panther.events import Event


@Event.startup
def do_something_on_startup():
    print('Hello, I am at startup')
```

## Shutdown Event

```python
from panther.events import Event


@Event.shutdown
def do_something_on_shutdown():
    print('Good Bye, I am at shutdown')
```


## Notice

- You can have **multiple** events on `startup` and `shutdown`
- Events can be `sync` or `async`
