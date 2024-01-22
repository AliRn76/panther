from pydantic import create_model
from pydantic_core._pydantic_core import PydanticUndefined


class ModelSerializer:
    def __new__(cls, *args, **kwargs):
        model_fields = kwargs['model'].model_fields
        field_definitions = {}
        for field_name in args[2]['fields']:
            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])
        for required in args[2]['required_fields']:
            field_definitions[required][1].default = PydanticUndefined
        return create_model(
            __model_name=args[0],
            **field_definitions
        )
