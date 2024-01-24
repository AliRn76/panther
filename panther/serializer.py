from pydantic import create_model
from pydantic_core._pydantic_core import PydanticUndefined


class ModelSerializer:
    def __new__(cls, *args, model=None, **kwargs):
        # Check `metaclass`
        if len(args) == 0:
            address = f'{cls.__module__}.{cls.__name__}'
            msg = f"you should not inherit the 'ModelSerializer', you should use it as 'metaclass' -> {address}"
            raise TypeError(msg)

        model_name = args[0]
        data = args[2]
        address = f'{data["__module__"]}.{model_name}'

        # Check `model`
        if model is None:
            msg = f"'model' required while using 'ModelSerializer' metaclass -> {address}"
            raise AttributeError(msg)
        # Check `fields`
        if 'fields' not in data:
            msg = f"'fields' required while using 'ModelSerializer' metaclass. -> {address}"
            raise AttributeError(msg) from None

        model_fields = model.model_fields
        field_definitions = {}

        # Collect `fields`
        for field_name in data['fields']:
            if field_name not in model_fields:
                msg = f"'{field_name}' is not in '{model.__name__}' -> {address}"
                raise AttributeError(msg) from None
            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])

        # Change `required_fields
        for required in data.get('required_fields', []):
            if required not in field_definitions:
                msg = f"'{required}' is in 'required_fields' but not in 'fields' -> {address}"
                raise AttributeError(msg) from None
            field_definitions[required][1].default = PydanticUndefined

        # Create Model
        return create_model(
            __model_name=model_name,
            **field_definitions
        )
