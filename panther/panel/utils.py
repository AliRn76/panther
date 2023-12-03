from panther.db.models import Model


def get_model_fields(model):
    result = {}

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
