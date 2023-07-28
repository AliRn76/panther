from panther import status
from panther.exceptions import APIException

from pydantic import ValidationError


def validate_input(model, data: dict):
    try:
        return model(**data)
    except ValidationError as validation_error:
        error = {e['loc'][0]: e['msg'] for e in validation_error.errors()}
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
