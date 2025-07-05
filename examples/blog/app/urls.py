from app.apis import CommentAPI, PostAPI, PostDetailAPI

url_routing = {
    'posts': PostAPI,
    'comments/<post_id>': CommentAPI,
    'posts/<post_id>': PostDetailAPI,
}
