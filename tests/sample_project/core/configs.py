from datetime import timedelta
from pathlib import Path

from panther.throttling import Throttle
from panther.utils import load_env

BASE_DIR = Path(__name__).resolve().parent / 'tests/sample_project'

env = load_env(BASE_DIR / '.env')

SECRET_KEY = env['SECRET_KEY']

MIDDLEWARES = ['panther.middlewares.monitoring.MonitoringMiddleware']

LOG_QUERIES = True
DATABASE = {
    'engine': {'class': 'panther.db.connections.PantherDBConnection'},
}
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
JWT_CONFIG = {
    'algorithm': 'HS256',
    'life_time': timedelta(days=2),
    'key': SECRET_KEY,
}

URLs = 'core.urls.url_routing'

USER_MODEL = 'app.models.User'

THROTTLING = Throttle(rate=10, duration=timedelta(seconds=10))
