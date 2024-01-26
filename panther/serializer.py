import typing

from pydantic import create_model
from pydantic_core._pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo

from panther.db import Model


class MetaModelSerializer:
    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[typing.Any], ...],
            namespace: dict[str, typing.Any],
            **kwargs
    ):
        if cls_name == 'ModelSerializer':
            return super().__new__(cls)

        known_config_attrs = ['model', 'fields', 'required_fields']

        address = f'{namespace["__module__"]}.{cls_name}'
        # Check `Config`
        if (config := namespace.pop('Config', None)) is None:
            msg = f'`class Config` is required in {address}.'
            raise AttributeError(msg) from None

        # Check `model`
        if (model := getattr(config, 'model', None)) is None:
            msg = f'`{cls_name}.Config.model` is required.'
            raise AttributeError(msg) from None

        # Check `model` type
        try:
            if not issubclass(model, Model):
                msg = f'`{cls_name}.Config.model` is not subclass of `panther.db.Model`.'
                raise AttributeError(msg) from None
        except TypeError:
            msg = f'`{cls_name}.Config.model` is not subclass of `panther.db.Model`.'
            raise AttributeError(msg) from None

        # Check `fields`
        if (fields := getattr(config, 'fields', None)) is None:
            msg = f'`{cls_name}.Config.fields` is required.'
            raise AttributeError(msg) from None

        model_fields = model.model_fields
        field_definitions = {}

        # Define `fields`
        for field_name in fields:
            if field_name not in model_fields:
                msg = f'`{cls_name}.Config.fields.{field_name}` is not valid.'
                raise AttributeError(msg) from None
            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])

        # Change `required_fields
        for required in getattr(config, 'required_fields', []):
            if required not in field_definitions:
                msg = f'`{cls_name}.Config.required_fields.{required}` should be in `Config.fields` too.'
                raise AttributeError(msg) from None
            field_definitions[required][1].default = PydanticUndefined

        # Collect Doc
        doc = namespace.pop('__doc__', '')

        # Collect `pydantic.model_config` (Should be before `Collect Validators`)
        model_config = {
            attr: getattr(config, attr) for attr in dir(config)
            if not attr.startswith('__') and attr not in known_config_attrs
        } | namespace.pop('model_config', {})

        # Collect and Override `Class Fields`
        for key, value in namespace.pop('__annotations__', {}).items():
            field_info = namespace.pop(key, FieldInfo(required=True))
            field_info.annotation = value
            field_definitions[key] = (value, field_info)

        # Collect `Validators`
        validators = {key: value for key, value in namespace.items() if not key.startswith('__')}

        # Create model
        return create_model(
            __model_name=cls_name,
            __validators__=validators,
            __config__=model_config,
            __doc__=doc,
            **field_definitions
        )


class ModelSerializer(metaclass=MetaModelSerializer):
    pass
