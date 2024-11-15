from panther.app import API
from panther.configs import config
from panther.panel.utils import get_model_fields
from panther.response import TemplateResponse, Response


@API(methods=['GET'])
def home_page_view():
    models = [{
        'index': i,
        'name': model.__name__,
        'module': model.__module__,
    } for i, model in enumerate(config.MODELS)]
    return TemplateResponse(path='home.html', context={'tables': models})


@API(methods=['GET'])
async def table_view(index: int):
    model = config.MODELS[index]

    if data := await model.find():
        data = data
    else:
        data = []

    return TemplateResponse(
        path='table.html',
        context={
            'table': model.__name__,
            'fields': get_model_fields(model),
            'records': Response.prepare_data(data),
        }
    )
