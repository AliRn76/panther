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
    ):
        self.model = model
        self.status_code = status_code
