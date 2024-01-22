from pydantic import create_model
from pydantic_core._pydantic_core import PydanticUndefined


class ModelSerializer:
    def __new__(cls, *args, **kwargs):
        if len(args) == 0:
            msg = f"you should not inherit the 'ModelSerializer', you should use it as 'metaclass' -> {cls.__name__}"
            raise TypeError(msg)
        model_name = args[0]
        if 'model' not in kwargs:
            msg = f"'model' required while using 'ModelSerializer' metaclass -> {model_name}"
            raise AttributeError(msg)

        model_fields = kwargs['model'].model_fields
        field_definitions = {}
        if 'fields' not in args[2]:
            msg = f"'fields' required while using 'ModelSerializer' metaclass. -> {model_name}"
            raise AttributeError(msg) from None
        for field_name in args[2]['fields']:
            if field_name not in model_fields:
                msg = f"'{field_name}' is not in '{kwargs['model'].__name__}' -> {model_name}"
                raise AttributeError(msg) from None

            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])
        for required in args[2].get('required_fields', []):
            if required not in field_definitions:
                msg = f"'{required}' is in 'required_fields' but not in 'fields' -> {model_name}"
                raise AttributeError(msg) from None
            field_definitions[required][1].default = PydanticUndefined
        return create_model(
            __model_name=model_name,
            **field_definitions
        )
