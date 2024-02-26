Panther currently built-in supports 2 database (`MongoDB`, `PantherDB`), but you can define your own custom database connection and queries too.


### Structure

```python
REDIS = {
    'class': 'address of the class',
    'arg1': 'value1',
    ...
}
```

### RedisConnection

```python
REDIS = {
    'class': 'panther.db.connections.RedisConnection',
    'host': ...,  # default is localhost
    'port': ...,  # default is 6379
    'db': ...,  # default is 0
    'websocket_db': ...,  # default is 0
    ...
}
```

#### Notes
- The arguments are same as `redis.Redis.__init__()` except `websocket_db`
- You can specify which `db` is for your `websocket` connections 


### How it works?

- Panther creates an async redis connection depends on `REDIS` block you defined in `configs`

- You can access to it from `from panther.db.connections import redis`

- Example: 
    ```python  
    from panther.db.connections import redis
    
    await redis.set('name', 'Ali')
    result = await redis.get('name')
    print(result)  
    ```  