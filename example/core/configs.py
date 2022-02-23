from datetime import timedelta

from framework.authentications import JWTAuthentication
from framework.db.drivers import MYSQLDriver
from example.core import urls, middlewares
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__name__).parent.parent
env = load_dotenv(BASE_DIR / '.env')

URLs = urls

# Go To https://framework.org/Middlewares For More Options
Middlewares = middlewares

# Go To https://framework.org/Authentications For More Options
Authentication = JWTAuthentication

# Only If JWT
JWTConfig = {
    'Algorithm': 'HSA256',
    'Payload': ('token_type', 'user_id', 'exp'),
    'TokenLifeTime': timedelta(days=2),
}


# Go To https://framework.org/DatabaseDrivers For More Options
DatabaseDriver = MYSQLDriver

LogQueries: True



