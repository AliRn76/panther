from .actor import MainActor

MASTER_PATH = 'dashboard/'
PATHS = {
    'user/': MainActor,
}

MIDDLEWARE_PANEL = {

}

DATABASE_USER = {
    'type': 'sqlite',
    'name': '',
    'user': '',
    'password': '',
    'host': '',
    'port': '',
}
