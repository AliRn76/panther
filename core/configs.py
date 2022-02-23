from framework.authentication import JWTAuthentication
from config import urls, middlewares
from framework.database.drivers import MYSQLDriver

URLs = urls

Middlewares = middlewares

Authentication = JWTAuthentication

DatabaseDriver = MYSQLDriver

LogQueries = True
