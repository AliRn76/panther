from functools import cached_property

from panther import status
from pydantic import BaseModel, field_validator, model_serializer

from panther.exceptions import APIError


class File(BaseModel):
    file_name: str
    content_type: str
    file: bytes

    @cached_property
    def size(self):
        return len(self.file)

    def save(self) -> str:
        if hasattr(self, '_file_name'):
            return self._file_name

        self._file_name = self.file_name
        # TODO: check for duplication
        with open(self._file_name, 'wb') as file:
            file.write(self.file)

        return self.file_name

    @model_serializer(mode='wrap')
    def _serialize(self, handler):
        result = handler(self)
        result['path'] = self.save()
        return result

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}(file_name={self.file_name}, content_type={self.content_type})'

    __str__ = __repr__


class Image(File):
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, content_type: str) -> str:
        if not content_type.startswith('image/'):
            msg = f"{content_type} is not a valid image 'content_type'"
            raise APIError(detail=msg, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        return content_type
