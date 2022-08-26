from panther import Panther
import uvicorn

app = Panther(__name__)

if __name__ == '__main__':
    uvicorn.run('main:app')

