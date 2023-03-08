from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()


@app.get("/")
async def root():
    return Response(status_code=200)
