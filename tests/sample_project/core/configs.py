from datetime import timedelta
from pathlib import Path

from panther.throttling import Throttling
from panther.utils import load_env

BASE_DIR = Path(__name__).resolve().parent
BASE_DIR = BASE_DIR / 'tests/sample_project'  # noqa

env = load_env(BASE_DIR / '.env')

SECRET_KEY = env['SECRET_KEY']

MONITORING = True
LOG_QUERIES = True
MIDDLEWARES = [
    ('panther.middlewares.db.DatabaseMiddleware', {'url': f'pantherdb://test.pdb'}),
]
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
JWTConfig = {
    'algorithm': 'HS256',
    'life_time': timedelta(days=2),
    'key': SECRET_KEY,
}

URLs = 'core.urls.url_routing'

USER_MODEL = 'app.models.User'

DEFAULT_CACHE_EXP = timedelta(seconds=10)

THROTTLING = Throttling(rate=10, duration=timedelta(seconds=10))
