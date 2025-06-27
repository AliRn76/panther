# Template Responses

Panther provides `TemplateResponse` for serving HTML templates with dynamic content. This guide explains how to configure and use templates in your Panther application.

## Configuration

To use `TemplateResponse` with template files, you must configure the `TEMPLATES_DIR` setting in your application configuration.

### Setting Templates Directory

The `TEMPLATES_DIR` can be a single string or a list of strings representing template directory paths:

```python
# Single directory
TEMPLATES_DIR = 'templates/'

# Multiple directories (searched in order)
TEMPLATES_DIR = ['templates/', 'app/templates/', 'shared/templates/']
```

**Default value:** `'./'` (current directory)

## Usage

### Using Template Files (Recommended)

When you have template files, use the `name` parameter to specify the template file:

```python linenums="1"
from panther.app import API
from panther.response import TemplateResponse


@API()
def my_html():
    return TemplateResponse(
        name='index.html', 
        context={'name': 'Ali', 'title': 'Welcome'}
    )
```

**Benefits:**

- Cleaner code separation
- Template reusability
- Better maintainability

### Using Inline HTML Content

For simple cases or when you need to generate HTML dynamically, you can pass the HTML content directly:

```python linenums="1"
from panther.app import API
from panther.response import TemplateResponse


@API()
def my_html():
    html_content = open('index.html', 'r').read()
    return TemplateResponse(
        source=html_content, 
        context={'name': 'Ali', 'title': 'Welcome'}
    )
```

**Note:** This approach requires you to manage the HTML content manually and doesn't provide the benefits of template files.

## Template Context

The `context` parameter allows you to pass variables to your templates:

```python linenums="1"
from panther.app import API
from panther.response import TemplateResponse

def get_user(user_id: int):
    return ...

@API()
def user_profile(user_id: int):
    user = get_user(user_id)  # Your user fetching logic
    return TemplateResponse(
        name='profile.html',
        context={
            'user': user,
            'page_title': f'{user.name}\'s Profile',
            'is_admin': user.role == 'admin'
        }
    )
```

## Example Project Structure

```
my_panther_app/
├── core/
│   ├── __init__.py
│   ├── configs.py
│   └── urls.py
├── app/
│   ├── __init__.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └── profile.html
└── main.py
```

With this structure, your configuration would be:

```python title="core/configs.py"
TEMPLATES_DIR = 'templates/'
```
 
