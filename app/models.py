from framework.database.models import BaseModel
from framework.database.columns import *

# Its SQLAlchemy
class User(BaseModel):
    id = PrimaryKey(()
