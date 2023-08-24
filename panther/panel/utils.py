from pydantic import ValidationError

from panther import status
from panther.db.models import Model
from panther.exceptions import APIException


def validate_input(model, data: dict):
    try:
        return model(**data)
    except ValidationError as validation_error:
        error = {e['loc'][0]: e['msg'] for e in validation_error.errors()}
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)


def get_model_fields(model):
    result = dict()

    for k, v in model.model_fields.items():
        try:
            is_model = issubclass(v.annotation, Model)
        except TypeError:
            is_model = False

        if is_model:
            result[k] = get_model_fields(v.annotation)
        else:
            result[k] = getattr(v.annotation, '__name__', str(v.annotation))
    return result
