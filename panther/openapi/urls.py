from panther.openapi.views import ScalarOpenAPI, SwaggerOpenAPI, RedocOpenAPI, RapiDocOpenAPI, SpotlightOpenAPI

url_routing = {
    'scalar/': ScalarOpenAPI,
    'swagger/': SwaggerOpenAPI,
    'redoc/': RedocOpenAPI,
    'rapidoc/': RapiDocOpenAPI,
    'spotlight/': SpotlightOpenAPI,
}
