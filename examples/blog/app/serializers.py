from typing import Any

from app.models import Comment, Post

from panther.serializer import ModelSerializer


class PostSerializer(ModelSerializer):
    class Config:
        model = Post
        fields = ['title', 'content']


class PostOutputSerializer(ModelSerializer):
    class Config:
        model = Post
        fields = ['id', 'title', 'content']


class PostDetailOutputSerializer(ModelSerializer):
    class Config:
        model = Post
        fields = ['id', 'title', 'content']

    async def to_response(self, instance: Any, data: dict) -> dict:
        data['comments'] = await Comment.find(post_id=instance.id)
        return data


class CommentSerializer(ModelSerializer):
    class Config:
        model = Comment
        fields = ['content']
