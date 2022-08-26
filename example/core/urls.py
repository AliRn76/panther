from app.urls import app_urls

from panther.app import API
from panther.response import Response


urls = {
    # '/': test,
    # '': None,
    'user/': app_urls,
    # 'admin/': admin_func,
}
# He can import another dict as url here
