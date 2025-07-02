import pydantic

from panther import status
from panther.serializer import ModelSerializer


class EmptyResponseModel(pydantic.BaseModel):
    pass


class OutputSchema:
    def __init__(
        self,
        model: type[ModelSerializer] | type[pydantic.BaseModel] = EmptyResponseModel,
        status_code: int = status.HTTP_200_OK,
        exclude_in_docs: bool = False,
        tags: list[str] | None = None,  # If None, we use parsed.title or endpoint.__module__
        deprecated: bool = False,  # Marked as deprecated endpoint
    ):
        self.model = model
        self.status_code = status_code
        self.exclude_in_docs = exclude_in_docs
        self.tags = tags
        self.deprecated = deprecated