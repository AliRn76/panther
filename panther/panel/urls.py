from panther.panel.views import TableView, CreateView, LoginView, DetailView, HomeView

urls = {
    # '': models_api,
    # '<index>/': documents_api,
    # '<index>/<document_id>/': single_document_api,
    # 'health': healthcheck_api,
    '': HomeView,
    '<index>/': TableView,
    '<index>/create/': CreateView,
    'login/': LoginView,
    '<index>/<document_id>/': DetailView,
}
