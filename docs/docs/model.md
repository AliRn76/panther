# Panther Models

Panther models allow you to define your data schema and interact with the database using Python classes. They are built on top of `pydantic.BaseModel` and extend its functionality with database query capabilities.

## Creating a Model

To create a Panther model, define a class that inherits from `panther.db.Model`:

```python title="app/models.py" linenums="1"
from panther.db import Model

class User(Model):
    username: str
    age: int
    is_active: bool
```

Panther models inherit from both `pydantic.BaseModel` and `panther.db.Query`, giving you access to data validation and database queries.

## Defining Attributes

You can define model attributes (columns) using Python type hints. Each attribute type is handled as follows:

### General Types
- **str**, **int**, **bool**: Saved in the database as-is.

**Example:**
```python title="app/models.py" linenums="1"
from panther.db import Model

class Product(Model):
    name: str
    price: int
    in_stock: bool
```

### List
- **list**: Each item in the list is processed according to its type. The child type can be a primitive, a `pydantic.BaseModel`, or another `Model`.

**Example:**
```python title="app/models.py" linenums="1"
from pydantic import BaseModel
from panther.db import Model

class Book(BaseModel):
    title: str
    author: str
    tags: list[str]

class Library(Model):
    name: str
    books: list[Book]

class School(Model):
    name: str
    libraries: list[Library]
```

### Dictionary
- **dict**: Each value in the dictionary is processed according to its type. Only plain `dict` is supported (not typed dicts like `dict[str, int]`).

**Example:**
```python title="app/models.py" linenums="1"
from panther.db import Model

class Config(Model):
    settings: dict
```

### Nested Models
- **pydantic.BaseModel**: Treated like a dictionary, but with type information for each item. Each item is processed according to its type.

**Example:**
```python title="app/models.py" linenums="1"
from pydantic import BaseModel
from panther.db import Model

class Address(BaseModel):
    city: str
    zipcode: str

class Customer(Model):
    name: str
    address: Address
```

### Foreign Keys
- **panther.db.Model**: Treated as a foreign key relationship.
    1. The related model's value is stored in the database.
    2. Its `id` is saved in the main document (table).
    3. This process is handled automatically, so you always have access to all attributes of the related model.
    4. Panther retrieves the corresponding value from the database and returns it as a fully populated model instance.

**Example:**
```python title="app/models.py" linenums="1"
from panther.db import Model

class Department(Model):
    name: str

class Employee(Model):
    name: str
    department: Department
```

### Optional Attributes
- You can make an attribute optional by using a union with `None` (e.g., `str | None`) and providing a default value (e.g., `= None`).
- If you make an attribute optional, you must assign a default value.

**Example:**
```python title="app/models.py" linenums="1"
from panther.db import Model

class Article(Model):
    title: str
    summary: str | None = None  # Optional attribute with default value
```

### File Types
- **panther.file_handler.File**: Handles file uploads and provides file manipulation capabilities.
- **panther.file_handler.Image**: Specialized File class for image uploads with automatic MIME type validation.

!!! tip "Comprehensive File Handling Guide"
    For detailed information about file handling, including advanced features, best practices, and troubleshooting, see the dedicated [File Handling](file_handling.md) documentation.

**Example:**
```python title="app/models.py" linenums="1"
from datetime import datetime
from panther.db import Model
from panther.file_handler import File, Image

class Document(Model):
    title: str
    file: File
    uploaded_at: datetime

class Profile(Model):
    name: str
    avatar: Image
    bio: str | None = None
```

When using File types in models:

- The file metadata (name, content type) is preserved
- The file path is stored in the database
- The actual file content is automatically saved to disk when inserting the model
- You can access file properties and methods on the model instance

**Example usage:**
```python
# Create a document with file
document = await Document.insert_one({
    'title': 'My Document',
    'file': File(file_name='document.pdf', content_type='application/pdf', file=file_bytes),
    'uploaded_at': datetime.now()
})

# Access file properties
print(document.file.file_name)  # 'document.pdf'
print(document.file.content_type)  # 'application/pdf'
print(document.file.size)  # File size in bytes

# Read file content
with document.file as f:
    content = f.read()
```


