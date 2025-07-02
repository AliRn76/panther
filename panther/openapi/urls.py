from panther.openapi.views import RapiDocOpenAPI, RedocOpenAPI, ScalarOpenAPI, SpotlightOpenAPI, SwaggerOpenAPI

url_routing = {
    'scalar/': ScalarOpenAPI,
    'swagger/': SwaggerOpenAPI,
    'redoc/': RedocOpenAPI,
    'rapidoc/': RapiDocOpenAPI,
    'spotlight/': SpotlightOpenAPI,
}
