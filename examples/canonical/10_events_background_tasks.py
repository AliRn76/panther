from datetime import time

from panther import Panther
from panther.app import API
from panther.background_tasks import BackgroundTask
from panther.events import Event


BACKGROUND_TASKS = True


async def clean_temp_files():
    print('Cleaning temporary files')


@Event.startup
async def on_startup():
    print('Panther app started')
    BackgroundTask(clean_temp_files).interval(-1).every_days().at(time(hour=3)).submit()


@Event.shutdown
def on_shutdown():
    print('Panther app stopped')


@API()
async def health():
    return {'status': 'ok'}


url_routing = {
    'health/': health,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
