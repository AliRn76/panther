from app.urls import app_urls

def admin_func():
    ...


urls = {
    # '': None,
    'user/': app_urls,
    'admin/': admin_func,
}
# He can import another dict as url here
