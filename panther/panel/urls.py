from panther.panel.views import home_page_view, table_view

urls = {
    # '': models_api,
    # '<index>/': documents_api,
    # '<index>/<document_id>/': single_document_api,
    # 'health': healthcheck_api,
    '': home_page_view,
    '<index>/': table_view,
}
