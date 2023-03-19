> <b>Variable:</b> `MONITORING` 
> 
> <b>Type:</b> `bool` 
> 
> <b>Default:</b> `False`

Panther has a `Monitoring` middleware that process the `perf_time` of every request

It will create a `monitoring.log` file and log the records

Then you can watch them live with: `panther monitor`


#### The Monitoring Middleware:

```python
    async def before(self, request: Request) -> Request:
        ip, port = request.client
        self.log = f'{request.method} | {request.path} | {ip}:{port}'
        self.start_time = perf_counter()
        return request
```

```python
    async def after(self, status_code: int):
        response_time = (perf_counter() - self.start_time) * 1_000
        monitoring_logger.info(f'{self.log} | {response_time: .3} ms | {status_code}')
```