from panther.panel.apis import documents_api, models_api, single_document_api

urls = {
    '': models_api,
    '<index>/': documents_api,
    '<index>/<id>/': single_document_api,
}
