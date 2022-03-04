from .actor import UserActor

MASTER_PATH = '/'
PATHS = {
    '': UserActor,
}

MIDDLEWARE_USER = {

}

DATABASE_USER = {
    'type': 'postgresql',
    'name': '',
    'user': '',
    'password': '',
    'host': '',
    'port': '',
}
