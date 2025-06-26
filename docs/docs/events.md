# Application Events

Panther provides a simple way to execute custom logic during your application's lifecycle using event decorators. You can hook into the **startup** and **shutdown** phases to run code when your app starts or stops.

---

## Startup Event

To run code when your application starts, use the `@Event.startup` decorator:

```python
from panther.events import Event

@Event.startup
def do_something_on_startup():
    print('Hello, I am at startup')
```

You can define multiple startup event handlers. They will be executed in the order they are registered.

---

## Shutdown Event

To run code when your application is shutting down, use the `@Event.shutdown` decorator:

```python
from panther.events import Event

@Event.shutdown
def do_something_on_shutdown():
    print('Good Bye, I am at shutdown')
```

You can define multiple shutdown event handlers as well.

---

## Additional Notes

- **Multiple Handlers:** You can register multiple functions for both `startup` and `shutdown` events. All will be called.
- **Sync & Async Support:** Event handlers can be either synchronous or asynchronous functions.
- **Use Cases:** Common use cases include initializing resources (like database connections) on startup and cleaning up resources on shutdown.
