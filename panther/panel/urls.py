from panther.panel.apis import list_models, model_list, model_retrieve

urls = {
    '': list_models,
    '<index>/': model_list,
    '<index>/<id>/': model_retrieve,
}
