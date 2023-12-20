You can set functionalities on events by using `on_event` function.

Available events:

- `startup`
- `shutdown`

Here is an example:

```python
app = Panther(__name__)

@app.on_event("startup")
def startup():
    pass

@app.on_event("shutdown")
def shutdown():
    pass
```