from framework.db.models import BaseModel
from framework.db.columns import *

# MongoEngine
class User(BaseModel):
    id = PrimaryKey()
