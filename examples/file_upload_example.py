"""
File Upload Example for Panther

This example demonstrates how to handle file uploads in Panther using
the File and Image classes with proper validation and error handling.
"""

from datetime import datetime

from panther import Panther, status
from panther.app import API
from panther.db import Model
from panther.exceptions import APIError
from panther.file_handler import File, Image
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

# Database configuration
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': 'file_upload_example.pdb',
    }
}


# Models
class Document(Model):
    title: str
    file: File
    uploaded_at: datetime
    description: str | None = None


class Profile(Model):
    name: str
    avatar: Image
    bio: str | None = None


# Serializers
class DocumentUploadSerializer(ModelSerializer):
    class Config:
        model = Document
        fields = ['title', 'file', 'description']
        required_fields = ['title', 'file']


class ProfileUploadSerializer(ModelSerializer):
    class Config:
        model = Profile
        fields = ['name', 'avatar', 'bio']
        required_fields = ['name', 'avatar']


# APIs
@API(input_model=DocumentUploadSerializer)
async def upload_document(request: Request):
    """Upload a document with validation"""
    try:
        file_data = request.validated_data
        file = file_data.file

        # Additional validation
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise APIError(
                detail='File too large. Maximum size is 10MB.', status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        # Check file type
        allowed_types = ['application/pdf', 'text/plain', 'application/msword']
        if file.content_type not in allowed_types:
            raise APIError(
                detail='File type not allowed. Only PDF, text, and Word documents are accepted.',
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # Save file to disk
        saved_path = file.save('uploads/documents/')

        # Store in database
        document = await Document.insert_one(
            {
                'title': file_data.title,
                'file': file,
                'uploaded_at': datetime.now(),
                'description': file_data.description,
            }
        )

        return Response(
            data={
                'message': 'Document uploaded successfully',
                'document_id': document.id,
                'file_name': file.file_name,
                'file_size': file.size,
                'saved_path': saved_path,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        raise APIError(detail=f'File upload failed: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@API(input_model=ProfileUploadSerializer)
async def upload_profile_image(request: Request):
    """Upload a profile image with automatic image validation"""
    try:
        profile_data = request.validated_data
        image = profile_data.avatar

        # Image-specific validation
        if image.size > 5 * 1024 * 1024:  # 5MB limit for images
            raise APIError(
                detail='Image too large. Maximum size is 5MB.', status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        # Save image
        saved_path = image.save('uploads/images/')

        # Store in database
        profile = await Profile.insert_one({'name': profile_data.name, 'avatar': image, 'bio': profile_data.bio})

        return Response(
            data={
                'message': 'Profile image uploaded successfully',
                'profile_id': profile.id,
                'image_name': image.file_name,
                'image_size': image.size,
                'saved_path': saved_path,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        raise APIError(detail=f'Image upload failed: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@API()
async def list_documents(request: Request):
    """List all uploaded documents"""
    documents = await Document.find()

    # Convert to response format
    doc_list = []
    for doc in documents:
        doc_list.append(
            {
                'id': doc.id,
                'title': doc.title,
                'file_name': doc.file.file_name,
                'file_size': doc.file.size,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'description': doc.description,
            }
        )

    return Response(data=doc_list)


@API()
async def get_document(document_id: str):
    """Get a specific document by ID"""
    document = await Document.find_one_or_raise(document_id)

    return Response(
        data={
            'id': document.id,
            'title': document.title,
            'file_name': document.file.file_name,
            'file_size': document.file.size,
            'content_type': document.file.content_type,
            'uploaded_at': document.uploaded_at.isoformat(),
            'description': document.description,
        }
    )


# URL routing
urls = {
    'upload/document/': upload_document,
    'upload/profile/': upload_profile_image,
    'documents/': list_documents,
    'documents/<document_id>/': get_document,
}

# Create Panther app
app = Panther(__name__, configs=__name__, urls=urls)
