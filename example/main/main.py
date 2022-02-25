from framework import Framework
from framework import include
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__name__).resolve().parent

KEY = "a{DLA#D(Jd33)--qqe0q-iwe[aw{DLA#--qqe0q-iwe[aw{DLA#D(Jd33)--qqD(Jd33)--qqe0q-iwee9]"

DEBUG = True  # show error if True

AUTHENTICATION_TYPE = "jwt"  # or token

APPS = {
    "admin": "admin/",
    # ^ app    ^ path
    "panel": "/",
    # ^ app   ^ path
}

JWT_CONFIG = {
    'Algorithm': 'HSA256',
    'TokenLifeTime': timedelta(days=2),
    'Key': KEY
}

AUTHENTICATIONS = (
    include("framework.auth.DefaultAuth")
)

DATABASE = {
    "default": {
        "type": "postgres",
        "name": "XXX",
        "username": "XXX",
        "host": "XXX",
        "port": 000,
        "password": ""
    },
    "cache": {
        "type": "redis",
        "host": "XXX",
        "port": 000,
    }
}

MIDDLEWARES = (
    include("admin.middlewares.UsernameMiddleware"),
    #         ^ App  ^ file        ^ class
    include("framework.middlewares.CSRFMiddleware"),
    #         ^ App     ^ file        ^ class
)
