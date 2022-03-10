from framework.middlewares import CSRF

DEBUG = False / True

""" middleware for all apps """
MIDDLEWARES = {
    CSRF
}

""" database for all apps """
DATABASE = {
    'type': 'mysql',
    'name': '',
    'user': '',
    'password': '',
    'host': '',
    'port': '',
}
