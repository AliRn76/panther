from panther.db import Model


class Post(Model):
    title: str
    content: str


class Comment(Model):
    content: str
    post_id: Post  # Foreign Key (relating to Post)
