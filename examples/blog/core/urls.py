from app.urls import url_routing as app_url_routing
from user.urls import url_routing as user_url_routing

from panther.openapi.views import ScalarOpenAPI
from panther.panel.urls import url_routing as panel_url_routing

url_routing = {
    'admin/': panel_url_routing,
    'docs/': ScalarOpenAPI,
    'user/': user_url_routing,
    '/': app_url_routing,
}
