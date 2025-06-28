from panther.panel.views import CreateView, DetailView, HomeView, LoginView, TableView

url_routing = {
    '': HomeView,
    '<index>/': TableView,
    '<index>/create/': CreateView,
    'login/': LoginView,
    '<index>/<document_id>/': DetailView,
}
