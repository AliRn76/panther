from functools import cached_property
from io import BufferedReader, BytesIO
from pathlib import Path

from pydantic import BaseModel, field_validator

from panther import status
from panther.exceptions import APIError
from panther.utils import timezone_now


class File(BaseModel):
    file_name: str
    content_type: str
    file: bytes | None = None
    _file_path: Path | None = None
    _buffer: BytesIO | BufferedReader | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.file:
            self._buffer = BytesIO(self.file)
        elif 'file_name' in data:
            self._file_path = Path(data['file_name'])
        self._saved_path: str | None = None

    def __enter__(self):
        if not self._buffer:
            # Open file lazily in binary read mode
            self._buffer = open(self._file_path, 'rb')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._buffer:
            self._buffer.close()
            self._buffer = None

    def read(self, size: int = -1) -> bytes:
        self._ensure_buffer()
        return self._buffer.read(size)

    def seek(self, offset: int, whence: int = 0):
        self._ensure_buffer()
        return self._buffer.seek(offset, whence)

    def tell(self) -> int:
        self._ensure_buffer()
        return self._buffer.tell()

    def write(self, data: bytes):
        if isinstance(self._buffer, BytesIO):
            self._buffer.seek(0, 2)
            self._buffer.write(data)
            self.file = self._buffer.getvalue()  # sync updated bytes
        else:
            raise IOError('Write is only supported for in-memory files.')

    def save(self, path: str | None = None, overwrite: bool = False) -> str:
        # If already saved, return the same path
        if self._saved_path is not None:
            return self._saved_path

        self._ensure_buffer()

        # Handle directory paths (ending with slash)
        if path and str(path).endswith('/'):
            # Treat as directory, use original file name
            base_path = Path(path) / self.file_name
        else:
            base_path = Path(path or self.file_name)

        if not overwrite:
            file_path = base_path
            if file_path.exists():
                # Format: file_YYYYMMDD_HHMMSS[_N].ext
                timestamp = timezone_now().strftime('%Y%m%d_%H%M%S')
                file_path = base_path.with_name(f'{base_path.stem}_{timestamp}{base_path.suffix}')

                # Ensure uniqueness if file with same timestamp exists
                counter = 1
                while file_path.exists():
                    file_path = base_path.with_name(f'{base_path.stem}_{timestamp}_{counter}{base_path.suffix}')
                    counter += 1
        else:
            file_path = base_path

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, 'wb') as f:
            f.write(self._buffer.read())
            self._buffer.seek(0)

        # Store the saved path for idempotency
        self._saved_path = str(file_path)
        return self._saved_path

    @cached_property
    def size(self) -> int:
        if self.file is not None:
            return len(self.file)
        if self._file_path:
            return self._file_path.stat().st_size
        return 0

    def _ensure_buffer(self):
        if not self._buffer:
            if self._file_path:
                self._buffer = open(self._file_path, 'rb')
            elif self.file is not None:
                self._buffer = BytesIO(self.file)
            else:
                raise ValueError('No file source to read from.')

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
