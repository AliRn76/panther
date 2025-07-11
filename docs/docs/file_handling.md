# File Handling in Panther

Panther provides file handling capabilities through the `File` and `Image` classes for file uploads and processing.

---

## Overview

- **`File`**: General-purpose file handling for any type of file
- **`Image`**: Specialized file handling for images with automatic MIME type validation

---

## Basic Usage

### Importing File Classes

```python
from panther.file_handler import File, Image
```

### Creating File Objects

```python
# Create from bytes (in-memory file)
file = File(
    file_name='document.pdf',
    content_type='application/pdf',
    file=b'PDF content here...'
)

# Create image file
image = Image(
    file_name='photo.jpg',
    content_type='image/jpeg',
    file=b'JPEG content here...'
)
```

---

## File Properties

| Property | Type | Description |
|----------|------|-------------|
| `file_name` | str | The name of the file |
| `content_type` | str | The MIME type of the file |
| `file` | bytes \| None | The file content in bytes |
| `size` | int | File size in bytes |

---

## File Methods

```python
# Read file content
content = file.read()

# Save file to disk
path = file.save("uploads/")

# Use as context manager
with file as f:
    content = f.read()
```

---

## Saving Files

The `save()` method provides flexible file saving with several features:

### Basic Saving

```python
# Save with original filename
path = file.save()

# Save with custom filename
path = file.save("custom_name.txt")

# Save with overwrite
path = file.save("existing_file.txt", overwrite=True)
```

### Directory Path Handling

When you provide a path ending with `/`, it's treated as a directory:

```python
# Save to directory with original filename
path = file.save("uploads/")  # Saves as "uploads/original_filename.ext"

# Save to nested directory
path = file.save("uploads/images/")  # Saves as "uploads/images/original_filename.ext"

# Save to directory with custom filename
path = file.save("uploads/custom_name.txt")  # Saves as "uploads/custom_name.txt"
```

### Idempotent Behavior

The `save()` method is **idempotent** - calling it multiple times on the same file instance returns the same path:

```python
file = File(file_name='test.txt', content_type='text/plain', file=b'content')

# First call - creates file and returns path
path1 = file.save("uploads/")
print(path1)  # "uploads/test.txt"

# Subsequent calls - returns same path without creating new files
path2 = file.save("uploads/")
path3 = file.save("uploads/")

assert path1 == path2 == path3  # All return the same path
```

This prevents accidental creation of duplicate files with different timestamps.

### Automatic Directory Creation

The `save()` method automatically creates directories if they don't exist:

```python
# This will create the "uploads/images" directory structure if it doesn't exist
path = file.save("uploads/images/")
```

---

## Integration with Models

Files can be used as model attributes:

```python
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

---

## Integration with Serializers

```python
from panther.serializer import ModelSerializer
from panther.file_handler import File, Image

class FileUploadSerializer(ModelSerializer):
    class Config:
        model = FileUpload
        fields = ['file', 'description']
        required_fields = ['file']

class ImageUploadSerializer(ModelSerializer):
    class Config:
        model = ImageUpload
        fields = ['image', 'title']
        required_fields = ['image']
```

### File Validation

```python
from pydantic import field_validator
from panther import status
from panther.exceptions import APIError
from panther.file_handler import File
from panther.serializer import ModelSerializer

class DocumentUploadSerializer(ModelSerializer):
    class Config:
        model = DocumentUpload
        fields = ['file', 'title']
        required_fields = ['file']

    @field_validator('file')
    @classmethod
    def validate_file_size(cls, file: File) -> File:
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise APIError(
                detail='File size must be less than 10MB',
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        return file
```

---

## API Integration

### File Upload API

```python
from panther.app import API
from panther.request import Request
from panther.response import Response

@API(input_model=FileUploadSerializer)
async def upload_file(request: Request):
    file_data = request.validated_data
    file = file_data.file
    
    # Save file to disk
    saved_path = file.save("uploads/")
    
    # Store in database
    document = await Document.insert_one({
        'title': file_data.description,
        'file': file,
        'uploaded_at': datetime.now()
    })
    
    return Response(data={
        "message": "File uploaded successfully",
        "saved_path": saved_path
    })
```

---

## Error Handling

```python
from panther import status
from panther.exceptions import APIError

@API(input_model=FileUploadSerializer)
async def upload_file(request: Request):
    try:
        file_data = request.validated_data
        file = file_data.file
        
        # Check file size
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise APIError(
                detail="File too large. Maximum size is 10MB.",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        saved_path = file.save("uploads/")
        return Response(data={"saved_path": saved_path})
        
    except Exception as e:
        raise APIError(
            detail=f"File upload failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## Best Practices

1. **Validate file types**: Always check MIME types to prevent malicious uploads
2. **Limit file sizes**: Set reasonable size limits to prevent abuse
3. **Use context managers**: When reading files, use `with` statements for proper cleanup
4. **Handle errors gracefully**: Provide clear error messages for validation failures
5. **Secure file storage**: Always validate and sanitize file names before saving
6. **Leverage idempotency**: The `save()` method is idempotent, so you can call it multiple times safely
7. **Use directory paths**: When saving files, use directory paths ending with `/` for better organization

This guide covers the essential aspects of file handling in Panther. For more advanced features and detailed examples, refer to the API documentation and examples. 