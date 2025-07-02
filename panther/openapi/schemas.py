import pydantic

from panther.serializer import ModelSerializer


class OutputSchema:
    """
    Configuration class for defining API endpoint output schemas.

    This class allows you to specify the response model, status code, and other
    metadata for API endpoints to generate proper OpenAPI documentation.

    Attributes:
        model: The Pydantic model or ModelSerializer class for the response
        status_code: HTTP status code for the response
        exclude_in_docs: Whether to exclude this endpoint from OpenAPI docs (defaults to False)
        tags: List of tags for grouping endpoints in documentation (defaults to Function Name/ Class Name)
        deprecated: Whether this endpoint is marked as deprecated (defaults to False)
    """

    def __init__(
        self,
        model: type[ModelSerializer] | type[pydantic.BaseModel] | None = None,
        status_code: int | None = None,
        exclude_in_docs: bool = False,
        tags: str | None = None,
        deprecated: bool = False,
    ):
        self.model = model
        self.status_code = status_code
        self.exclude_in_docs = exclude_in_docs
        self.tags = tags
        self.deprecated = deprecated
