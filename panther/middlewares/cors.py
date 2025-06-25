from panther.configs import config
from panther.middlewares import HTTPMiddleware
from panther.request import Request
from panther.response import Response


class CORSMiddleware(HTTPMiddleware):
    """
    Middleware to handle Cross-Origin Resource Sharing (CORS) for Panther applications.

    This middleware automatically adds the appropriate CORS headers to all HTTP responses
    based on configuration variables defined in your Panther config file (e.g., core/configs.py).
    It also handles preflight (OPTIONS) requests.

    Configuration attributes (set these in your config):
    ---------------------------------------------------
    ALLOW_ORIGINS: list[str]
        List of allowed origins. Use ["*"] to allow all origins. Default: ["*"]
    ALLOW_METHODS: list[str]
        List of allowed HTTP methods. Default: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ALLOW_HEADERS: list[str]
        List of allowed request headers. Use ["*"] to allow all headers. Default: ["*"]
    ALLOW_CREDENTIALS: bool
        Whether to allow credentials (cookies, authorization headers, etc.). Default: False
    EXPOSE_HEADERS: list[str]
        List of headers that can be exposed to the browser. Default: []
    CORS_MAX_AGE: int
        Number of seconds browsers are allowed to cache preflight responses. Default: 600

    Usage:
    ------
    1. Set the above config variables in your config file as needed.
    2. Add 'panther.middlewares.cors.CORSMiddleware' to your MIDDLEWARES list.
    """

    async def __call__(self, request: Request) -> Response:
        # Fetch CORS settings from config, with defaults
        allow_origins = config.ALLOW_ORIGINS or ['*']
        allow_methods = config.ALLOW_METHODS or ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
        allow_headers = config.ALLOW_HEADERS or ['*']
        allow_credentials = config.ALLOW_CREDENTIALS or False
        expose_headers = config.EXPOSE_HEADERS or []
        max_age = config.CORS_MAX_AGE or 600

        # Handle preflight (OPTIONS) requests
        if request.method == 'OPTIONS':
            response = Response(status_code=204)
        else:
            response = await self.dispatch(request=request)

        origin = request.headers['origin'] or '*'
        if '*' in allow_origins:
            allow_origin = '*'
        elif origin in allow_origins:
            allow_origin = origin
        else:
            allow_origin = allow_origins[0] if allow_origins else '*'

        response.headers['Access-Control-Allow-Origin'] = allow_origin
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allow_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(allow_headers)
        response.headers['Access-Control-Max-Age'] = str(max_age)
        if allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        if expose_headers:
            response.headers['Access-Control-Expose-Headers'] = ', '.join(expose_headers)
        return response
