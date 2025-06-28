# Timezone Configuration

Panther provides built-in timezone support to ensure consistent datetime handling across your application.

## Configuration

You can specify your timezone in the configuration using the `TIMEZONE` setting:

```python
TIMEZONE = 'UTC'  # Options are available in `pytz.all_timezones`
```

To see all available timezone options, you can run:

```python
import pytz
print(pytz.all_timezones)
```

This will show you the complete list of timezone identifiers you can use in your `TIMEZONE` configuration.


## Using Panther's Timezone-Aware DateTime

Panther provides a utility function `panther.utils.timezone_now()` that returns the current datetime relative to your configured timezone:

```python
from panther.utils import timezone_now

# Get current datetime in your configured timezone
current_time = timezone_now()
print(current_time)  # 2024-01-15 14:30:00+00:00 (if TIMEZONE='UTC')
```

## Where It's Used

The `timezone_now()` function is automatically used in several Panther components:

- **User Authentication**: `BaseUser.date_created` and `BaseUser.last_login` use timezone-aware timestamps
- **Background Tasks**: DateTime checking for scheduled and queued tasks

> Use `timezone_now()` Instead of `datetime.now()`, to maintain consistency across your application.
