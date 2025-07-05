from datetime import timedelta

from panther import status
from panther.app import GenericAPI
from panther.db import Model
from panther.exceptions import BadRequestAPIError
from panther.generics import CreateAPI, DeleteAPI, ListAPI, RetrieveAPI, UpdateAPI
from panther.pagination import Pagination
from panther.permissions import IsAuthenticated, IsAuthenticatedOrReadonly
from panther.request import Request
from panther.response import Response
from panther.throttling import Throttle

from app.models import Post
from app.serializers import CommentSerializer, PostDetailOutputSerializer, PostOutputSerializer, PostSerializer


# PostAPI - For Listing Posts and Creating a Post
class PostAPI(ListAPI, CreateAPI):
    permissions = [IsAuthenticatedOrReadonly]
    input_model = PostSerializer
    throttling = Throttle(rate=5, duration=timedelta(minutes=1))
    pagination = Pagination
    output_model = PostOutputSerializer
    cache = timedelta(minutes=1)

    async def get_query(self, request: Request, **kwargs):
        return await Post.find()


# PostDetailAPI - For Retrieving, Updating, and Deleting a Post
class PostDetailAPI(UpdateAPI, RetrieveAPI, DeleteAPI):
    input_model = PostSerializer
    output_model = PostDetailOutputSerializer

    async def get_instance(self, request: Request, **kwargs) -> Model:
        return await Post.find_one_or_raise(id=kwargs['post_id'])


class CommentAPI(GenericAPI):
    input_model = CommentSerializer
    permissions = IsAuthenticated

    async def post(self, request: Request, post_id: str):
        if not await Post.exists(id=post_id):
            raise BadRequestAPIError('Post with this ID does not exists.')
        instance = await request.validated_data.model.insert_one(request.validated_data, post_id=post_id)
        return Response(data=instance, status_code=status.HTTP_201_CREATED)
