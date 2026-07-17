from pathlib import Path

from panther import Panther
from panther.app import API
from panther.response import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse, TemplateResponse

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = str(BASE_DIR / 'templates')


@API()
async def html_page():
    return HTMLResponse('<h1>Hello from Panther HTMLResponse</h1>')


@API()
async def template_page():
    return TemplateResponse(name='hello.html', context={'name': 'Panther'})


@API()
async def download_readme():
    return FileResponse('README.md')


@API()
async def redirect_to_html():
    return RedirectResponse('/html/')


@API()
async def stream_numbers():
    async def numbers():
        for number in range(3):
            yield {'number': number}

    return StreamingResponse(numbers())


url_routing = {
    'html/': html_page,
    'template/': template_page,
    'download/readme/': download_readme,
    'go/html/': redirect_to_html,
    'stream/numbers/': stream_numbers,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
