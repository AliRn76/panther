import pymongo
from framework.middlewares.base import BaseMiddleware
from framework.configs import DatabaseConfig, DatabaseDriver

client = pymongo.MongoClient(
    host=DatabaseConfig['HOST'],
    port=DatabaseConfig['PORT'],
    username=DatabaseConfig['USERNAME'],
    password=DatabaseConfig['PASSWORD'],
    document_class=dict,
)
db = client[DatabaseConfig['NAME']]
