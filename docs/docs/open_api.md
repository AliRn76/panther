# OpenAPI Integration in Panther

Panther automatically generates an OpenAPI specification for your APIs. This makes it easy to document, test, and share your API endpoints.

## How to Enable OpenAPI in Your Project

Panther provides multiple OpenAPI UI options that you can import directly into your project. You don't need to add the bundled `openapi.urls.url_routing` - instead, you can choose the specific UI component you prefer.

### Available OpenAPI UI Components

Panther offers several OpenAPI UI options available in `panther.openapi.views`:

- **`ScalarOpenAPI`** - Modern, customizable API documentation UI
- **`SwaggerOpenAPI`** - Classic Swagger UI interface
- **`RedocOpenAPI`** - Clean, responsive documentation interface
- **`RapiDocOpenAPI`** - Fast, lightweight API documentation
- **`SpotlightOpenAPI`** - Stoplight Elements integration

### Adding OpenAPI to Your Project

You can import and use any of these UI components directly in your URL configuration:

```python title="urls.py" linenums="1"
from panther.openapi.views import ScalarOpenAPI, SwaggerOpenAPI, RedocOpenAPI

url_routing = {
    'docs/scalar/': ScalarOpenAPI,    # Modern UI at /docs/scalar/
    'docs/swagger/': SwaggerOpenAPI,  # Classic Swagger at /docs/swagger/
    'docs/redoc/': RedocOpenAPI,      # Clean interface at /docs/redoc/
    # Other urls
}
```

### Alternative: Using All UI Components

If you want to include all OpenAPI UI options at once, you can still use the bundled routing:

```python title="urls.py" linenums="1"
from panther.openapi.urls import url_routing as openapi_url_routing

url_routing = {
    'docs/': openapi_url_routing,  # Includes all UI options
    # Other urls
}
```

This will make the following endpoints available:

- `/docs/scalar/` - Scalar UI
- `/docs/swagger/` - Swagger UI  
- `/docs/redoc/` - ReDoc UI
- `/docs/rapidoc/` - RapiDoc UI
- `/docs/spotlight/` - Spotlight UI

## How Panther Determines Response Models and Status Codes

Panther follows a specific logic to generate the OpenAPI YAML for your APIs:

1. **`output_schema`**: Panther first looks for an `output_schema` attribute to generate the OpenAPI documentation. This is the recommended and most accurate way to specify your response model and status code.
2. **`output_model`**: If `output_schema` does not exist, Panther looks for an `output_model` attribute to generate the response type. It will also attempt to extract the status code from your source code.
3. **Source Code Analysis**: If neither `output_schema` nor `output_model` is available, Panther tries to extract the response data and status code directly from your source code using static analysis with `ast`.

For best results and more accurate documentation, always specify `output_schema` in your APIs.

## How Panther Generates OpenAPI Docs

Panther inspects your API views for an `output_schema` attribute. This attribute should be an instance of `panther.openapi.OutputSchema`, which describes the response model and status code for your endpoint.

- `model` in `OutputSchema` can be either a `pydantic.BaseModel` or a `panther.serializer.ModelSerializer`.
- `status_code` should be an integer (e.g., `status.HTTP_200_OK`).

### Example

=== "Function-Base API"

    ```python linenums="1"
    from pydantic import BaseModel
    from panther import status
    from panther.app import API
    from panther.openapi import OutputSchema
    
    class UserSerializer(BaseModel):
        username: str
        age: int
    
    @API(output_schema=OutputSchema(model=UserSerializer, status_code=status.HTTP_200_OK))
    def user_api():
        ...
    ```

=== "Class-Base API"

    ```python linenums="1"
    from pydantic import BaseModel
    from panther import status
    from panther.app import GenericAPI
    from panther.openapi import OutputSchema
    
    class UserSerializer(BaseModel):
        username: str
        age: int
    
    class UserAPI(GenericAPI):
        output_schema = OutputSchema(model=UserSerializer, status_code=status.HTTP_200_OK)
        ...
    ```

---

**Note:** The OpenAPI integration is currently in beta. Contributions, feedback, and ideas are very welcome!