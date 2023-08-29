from pydantic import BaseModel


class File(BaseModel):
    file_name: str
    content_type: str
    file: bytes

    def __repr__(self) -> str:
        return f'{self.__repr_name__()}(file_name={self.file_name}, content_type={self.content_type})'

    __str__ = __repr__
