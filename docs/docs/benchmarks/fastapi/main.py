from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI()


@app.get('/')
async def root():
    data = {'detail': 'hello world'}
    return JSONResponse(content=data, status_code=200)
