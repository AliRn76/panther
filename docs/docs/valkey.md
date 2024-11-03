### Structure

```python
VALKEY = {
    'class': 'address of the class',
    'arg1': 'value1',
    ...
}
```

### ValkeyConnection

```python
VALKEY = {
    'class': 'panther.db.connections.ValkeyConnection',
    'host': ...,  # default is localhost
    'port': ...,  # default is 6379
    'db': ...,  # default is 0
    'websocket_db': ...,  # default is 0
    ...
}
```

#### Notes
- The arguments are same as `valkey.Valkey.__init__()` except `websocket_db`
- You can specify which `db` is for your `websocket` connections


### How it works?

- Panther creates an async valkey connection depends on `VALKEY` block you defined in `configs`

- You can access to it from `from panther.db.connections import valkey`

- Example:
    ```python  
    from panther.db.connections import valkey
    
    await valkey.set('name', 'Ali')
    result = await valkey.get('name')
    print(result)  
    ```  
