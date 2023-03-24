> <b>Variable:</b> `THROTTLING` 
> 
> <b>Type:</b> `str` 
 
In Panther, you can use `Throttling` for all APIs at once in `core/configs.py` or per API in its `@API` decorator

The `Throttling` class has 2 field `rate` & `duration`

> rate: int
> 
> duration: datetime.timedelta

It will return `Too Many Request` `status_code: 429` if user try to request in the `duration` more than `rate`
And user will baned( get`Too Many Request` ) for `duration`

And keep that in mind if you have `Throttling` in `@API()`, the `Throttling` of `core/configs.py` will be ignored.

### For All APIs Example:
core/configs.py
```python
from datetime import timedelta

from panther.throttling import Throttling


# User only can request 5 times in every minutes
THROTTLING = Throttling(rate=5, duration=timedelta(minutes=1))
```

### For Single API Example:
apis.py
```python
from datetime import timedelta

from panther.throttling import Throttling
from panther.app import API


# User only can request 5 times in every minutes
InfoThrottling = Throttling(rate=5, duration=timedelta(minutes=1))


@API(throttling=InfoThrottling)
async def info_api():
    pass
```
