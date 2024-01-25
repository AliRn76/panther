import typing

from pydantic import create_model
from pydantic.fields import FieldInfo
from pydantic_core._pydantic_core import PydanticUndefined

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

        address = f'{namespace["__module__"]}.{cls_name}'
        # Check `Meta`
        if (meta := namespace.get('Meta')) is None:
            msg = f'`class Meta` is required in {address}.'
            raise AttributeError(msg) from None

        # Check `model`
        if (model := getattr(meta, 'model', None)) is None:
            msg = f'`{cls_name}.Meta.model` is required.'
            raise AttributeError(msg) from None

        # Check `model` type
        try:
            if not issubclass(model, Model):
                msg = f'`{cls_name}.Meta.model` is not subclass of `panther.db.Model`.'
                raise AttributeError(msg) from None
        except TypeError:
            msg = f'`{cls_name}.Meta.model` is not subclass of `panther.db.Model`.'
            raise AttributeError(msg) from None

        # Check `fields`
        if (fields := getattr(meta, 'fields', None)) is None:
            msg = f'`{cls_name}.Meta.fields` is required.'
            raise AttributeError(msg) from None

        model_fields = model.model_fields
        field_definitions = {}

        # Define `fields`
        for field_name in fields:
            if field_name not in model_fields:
                msg = f'`{cls_name}.Meta.fields.{field_name}` is not valid.'
                raise AttributeError(msg) from None
            field_definitions[field_name] = (model_fields[field_name].annotation, model_fields[field_name])

        # Change `required_fields
        for required in getattr(meta, 'required_fields', []):
            if required not in field_definitions:
                msg = f'`{cls_name}.Meta.required_fields.{required}` should be in `Meta.fields` too.'
                raise AttributeError(msg) from None
            field_definitions[required][1].default = PydanticUndefined

        # Collect and Override `Class Fields`
        for key, value in namespace.get('__annotations__', {}).items():
            field_info = namespace.pop(key, FieldInfo(required=True))
            field_info.annotation = value
            field_definitions[key] = (value, field_info)

        # Collect `Validators`
        validators = {}
        for key, value in namespace.items():
            if key in ['__module__', '__qualname__', '__annotations__', 'Meta']:
                continue

            validators[key] = value

        # Create model
        return create_model(
            __model_name=cls_name,
            __validators__=validators,
            **field_definitions
        )


class ModelSerializer(metaclass=MetaModelSerializer):
    pass
