import os
from datetime import timedelta

from panther.throttling import Throttle

# Generate Secret Key with `panther.utils.generate_secret_key`
SECRET_KEY = os.environ.get('SECRET_KEY', 'nggtD7uISmU3t61KUpOR642L2MFLUxxY3uoHGfMBH6E=')

# Database Configuration
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': 'database.pdb',
    }
}

# Enable Redis for caching and throttling
REDIS = {
    'class': 'panther.db.connections.RedisConnection',
    'host': os.environ.get('REDIS_HOST', '127.0.0.1'),
    'port': 6379,
    'db': 0,
}

# Enable JWT authentication
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
JWT_CONFIG = {
    'algorithm': 'HS256',
    'life_time': timedelta(days=1),
    'refresh_life_time': timedelta(days=7),
}

# Middleware Configuration (CORS)
ALLOW_ORIGINS = ['*']
ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
ALLOW_HEADERS = ['*']
ALLOW_CREDENTIALS = True
CORS_MAX_AGE = 3600

MIDDLEWARES = [
    'panther.middlewares.cors.CORSMiddleware',
    'panther.middlewares.monitoring.MonitoringMiddleware',
]

# Throttling Configuration
THROTTLING = Throttle(rate=5, duration=timedelta(minutes=1))

URLs = 'core.urls.url_routing'
