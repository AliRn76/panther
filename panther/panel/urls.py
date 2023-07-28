from panther.panel.apis import models_api, documents_api, single_document_api

urls = {
    '': models_api,
    '<index>/': documents_api,
    '<index>/<id>/': single_document_api,
}
