# OpenAPI (Swagger) Integration in Panther

Panther automatically generates an OpenAPI (Swagger) specification for your APIs. This makes it easy to document, test, and share your API endpoints.

## How to Enable OpenAPI in Your Project

To enable OpenAPI documentation, simply add the Panther OpenAPI URL routing to your project's URL configuration:

```python title="core/urls.py" linenums="1"
from panther.openapi.urls import url_routing as openapi_url_routing

url_routing = {
    'swagger/': openapi_url_routing,
    # Other urls
}
```

This will make your OpenAPI documentation available at the `/swagger/` endpoint.

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

If `output_schema` is not provided, Panther will attempt to infer the status code and response structure by analyzing your code with `ast`. However, for best results and more accurate documentation, it is recommended to always specify `output_schema`.

---

**Note:** The OpenAPI integration is currently in beta. Contributions, feedback, and ideas are very welcome!