> <b>Variable:</b> `LOG_QUERIES` 
> 
> <b>Type:</b> `bool` 
> 
> <b>Default:</b> `False`

Panther log `perf_time` of every query if this variable is `True`

Make sure it is `False` on production for better performance

#### Log Example:

```python
INFO:     | 2023-03-19 20:37:27 | Query -->  User.insert_one() --> 1.6 ms
```
