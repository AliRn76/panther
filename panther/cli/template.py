from datetime import datetime


apis_py = """from panther.app import API
from panther.request import Request
from app.models import User


@API.post(input_model=UserInputSerializer)
async def create_user(request: Request):
    obj: UserInputSerializer = request.data
    User.create(username=obj.username, password=obj.password)
    return Response(status_code=201)


@API.get(output_model=UserOutputSerializer)
async def get_users(request: Request):
    _users = User.list()
    users = [User(**user).dict() for user in _users]
    return Response(data=users)

"""

models_py = """from panther.db import BaseModel

class User(BaseModel):
    username: str
    password: str

"""

serializers_py = """from pydantic import BaseModel, constr


class UserInputSerializer(BaseModel):
    username: str
    password: constr(min_length=8)


class UserOutputSerializer(BaseModel):
    id: str
    username: str

"""

app_urls_py = """from app.apis import hello_world

urls = {
    'create/': create_user,
    'list/': get_users,
}

"""

configs_py = """\"""
Generated by Panther on %s
\"""

from pathlib import Path
from dotenv import dotenv_values


DEBUG = True 
BASE_DIR = Path(__name__).resolve().parent
env = dotenv_values(BASE_DIR / '.env')

DB_NAME = env['DB_NAME']
DB_HOST = env['DB_HOST']
DB_PORT = env['DB_PORT']
SECRET_KEY = env['SECRET_KEY']

Middlewares = [
    ('panther/middlewares/db.py', {'url': f'mongodb://{DB_HOST}:{DB_PORT}/{DB_NAME}'}),
]

URLs = 'core/urls.py'

""" % datetime.now().date().isoformat()

middlewares_py = """from panther.middlewares import BaseMiddleware

"""

env = """
SECRET_KEY = 'THIS_IS_THE_SECRET_SECRET_KEY'

DB_NAME = '{DATABASE_NAME}'
DB_HOST = '127.0.0.1'
DB_PORT = '27017'

"""

main_py = """import uvicorn
from panther import Panther

app = Panther(__name__)

if __name__ == '__main__':
    uvicorn.run('main:app')

"""

urls_py = """from app.urls import urls as app_urls

urls = {
    '': app_urls, 
}

"""

alembic_ini = """# A generic, single database configuration (Generated by panther).

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os  
sqlalchemy.url = {SQLALCHEMY_URL}

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

Template = {
    'app': {
        'apis.py': apis_py,
        'models.py': models_py,
        'serializer.py': serializers_py,
        'urls.py': app_urls_py,
    },
    'core': {
        'configs.py': configs_py,
        'middlewares.py': middlewares_py,
        'urls.py': urls_py,
    },
    '.env': env,
    'alembic.ini': alembic_ini,
    'main.py': main_py,
}
