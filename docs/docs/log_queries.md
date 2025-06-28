# Query Performance Logging

Panther provides built-in query performance monitoring that logs the execution time of each database query when enabled. 

## Configuration

To enable query performance logging, set the `LOG_QUERIES` configuration option to `True`:

```python
LOG_QUERIES = True  # Default is False
```

## How It Works

When `LOG_QUERIES` is enabled, Panther automatically:

- **Measures execution time** for every database query
- **Logs performance data** to `logs/query.log`
- **Includes query details** such as method name and execution time in milliseconds

## Log Format

Each log entry follows this format:

```
INFO: | [Timestamp] | [Query] [Method] takes [Duration] ms
```

### Example Log Entries

```python
INFO: | 2023-03-19 20:37:27 | [Query] User.insert_one() takes 1.612 ms
INFO: | 2023-03-19 20:37:28 | [Query] User.find() takes 45.234 ms
INFO: | 2023-03-19 20:37:29 | [Query] Post.update_one() takes 12.891 ms
INFO: | 2023-03-19 20:37:30 | [Query] Comment.delete_one() takes 3.445 ms
```

## Use Cases

Query logging is particularly useful for:

- **Development**: Identifying slow queries during development
- **Debugging**: Troubleshooting performance issues
- **Optimization**: Finding bottlenecks in database operations
- **Monitoring**: Tracking query performance over time

## Performance Considerations

Keep `LOG_QUERIES = False` in production environments for optimal performance.

Query logging adds a small overhead to each database operation, which can impact application performance under high load.
