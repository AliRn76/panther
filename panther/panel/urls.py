from panther.panel.views import CreateView, DetailView, HomeView, LoginView, TableView

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
