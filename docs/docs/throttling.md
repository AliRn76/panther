> <b>Variable:</b> `THROTTLING` 
> 
> <b>Type:</b> `str` 
 
For `Throttling` you can set a default value in `configs` or set custom value per `API()`

The default value is going to use for all the APIs unless it has custom value

The `Throttling` class has 2 fields, `rate` & `duration`

> rate: int
> 
> duration: datetime.timedelta

It will return `Too Many Request (status_code: 429)`, if user trying to send requests more than `rate` in the `duration`,  
and user will be banned( gets `Too Many Request` ) for `duration`.

### Set Throttling For All APIs:
in `configs`
```python
from datetime import timedelta

from panther.throttling import Throttling


# User only can request 5 times in every minute
THROTTLING = Throttling(rate=5, duration=timedelta(minutes=1))
```

### Set Throttling For Single API:
in `apis.py`
```python
from datetime import timedelta

from panther.throttling import Throttling
from panther.app import API, GenericAPI


# User only can request 5 times in every minute
InfoThrottling = Throttling(rate=5, duration=timedelta(minutes=1))


@API(throttling=InfoThrottling)
async def info_api():
    pass

class InfoAPI(GenericAPI):
    throttling = InfoThrottling
    pass
```
