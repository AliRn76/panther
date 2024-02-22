from panther.panel.apis import documents_api, models_api, single_document_api, healthcheck_api

urls = {
    '': models_api,
    '<index>/': documents_api,
    '<index>/<document_id>/': single_document_api,
    'health': healthcheck_api,
}
