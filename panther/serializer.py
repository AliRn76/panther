from pydantic import create_model
from pydantic_core._pydantic_core import PydanticUndefined


class ModelSerializer:
    def __new__(cls, *args, **kwargs):
        model_fields = kwargs['model'].model_fields
        model_name = args[0]
        field_definitions = {}
        for field_name in args[2]['fields']:
            if field_name not in model_fields:
                msg = f"{model_name}('{field_name}' is not in '{kwargs['model'].__name__}')"
                raise KeyError(msg) from None

            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])
        for required in args[2]['required_fields']:
            if required not in field_definitions:
                msg = f"{model_name}('{required}' is in 'required_fields' but not in 'fields')"
                raise KeyError(msg) from None
            field_definitions[required][1].default = PydanticUndefined
        return create_model(
            __model_name=model_name,
            **field_definitions
        )
