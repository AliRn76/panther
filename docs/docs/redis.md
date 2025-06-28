# Redis Integration

Redis is a fast, in-memory key-value store commonly used for caching, session management, real-time analytics, and pub/sub messaging. Panther supports Redis natively, allowing you to leverage its power for authentication, caching, throttling, and websocket pub/sub features.

## Configuration

To enable Redis in Panther, fill out the `REDIS` block in your configuration file:

```python
REDIS = {
    'class': 'panther.db.connections.RedisConnection',
    'host': 'localhost',  # Optional, default is 'localhost'
    'port': 6379,         # Optional, default is 6379
    'db': 0,              # Optional, default is 0
    # Add any other redis-py supported parameters here
}
```

**Note:** The arguments are the same as those accepted by `redis.Redis.__init__()` from the [redis documentation](https://redis.readthedocs.io/en/latest/).

## How It Works

- Panther creates an asynchronous Redis connection based on the `REDIS` block you define in your configuration.
- You can access the Redis connection via:

    ```python
    from panther.db.connections import redis
    ```

- Example usage:

    ```python
    from panther.db.connections import redis

    await redis.set('name', 'Ali')
    result = await redis.get('name')
    print(result)
    ```

## Features Using Redis

- **Authentication:** Store and retrieve JWT tokens for logout functionality.
- **Caching:** Cache responses for faster access.
- **Throttling:** Track and limit request rates.
- **WebSocket:** Manage pub/sub connections for real-time features.
