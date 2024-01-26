import typing

from pydantic import create_model
from pydantic.fields import FieldInfo
from pydantic_core._pydantic_core import PydanticUndefined

from panther.db import Model


class MetaModelSerializer:
    KNOWN_CONFIGS = ['model', 'fields', 'required_fields']

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[typing.Any], ...],
            namespace: dict[str, typing.Any],
            **kwargs
    ):
        if cls_name == 'ModelSerializer':
            cls.model_serializer = type(cls_name, (), namespace)
            return super().__new__(cls)

        # 1. Initial Check
        cls.check_config(cls_name=cls_name, namespace=namespace)

        # 2. Config
        config = namespace.pop('Config')

        # 3. Collect `Fields`
        field_definitions = cls.collect_fields(config=config, namespace=namespace)

        # 4. Collect `pydantic.model_config`
        model_config = cls.collect_model_config(config=config, namespace=namespace)

        # 5. Collect `Validators`
        validators = cls.collect_validators(namespace=namespace)

        # 6. Create a serializer
        serializer = create_model(
            __model_name=cls_name,
            __module__=namespace['__module__'],
            __validators__=validators,
            __config__=model_config,
            __doc__=namespace.get('__doc__'),
            **field_definitions
        )
        # 7. Fix serializer __bases__ & ...
        cls.finalization(config=config, serializer=serializer)

        return serializer

    @classmethod
    def check_config(cls, cls_name: str, namespace: dict) -> None:
        module = namespace['__module__']
        address = f'{module}.{cls_name}'

        # Check `Config`
        if (config := namespace.get('Config')) is None:
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

        for field_name in fields:
            if field_name not in model.model_fields:
                msg = f'`{cls_name}.Config.fields.{field_name}` is not valid.'
                raise AttributeError(msg) from None

        # Check `required_fields`
        if not hasattr(config, 'required_fields'):
            config.required_fields = []

        for required in config.required_fields:
            if required not in config.fields:
                msg = f'`{cls_name}.Config.required_fields.{required}` should be in `Config.fields` too.'
                raise AttributeError(msg) from None

    @classmethod
    def collect_fields(cls, config: typing.Callable, namespace: dict) -> dict:
        field_definitions = {}

        # Define `fields`
        for field_name in config.fields:
            field_definitions[field_name] = (
                config.model.model_fields[field_name].annotation,
                config.model.model_fields[field_name]
            )

        # Apply `required_fields`
        for required in config.required_fields:
            field_definitions[required][1].default = PydanticUndefined

        # Collect and Override `Class Fields`
        for key, value in namespace.pop('__annotations__', {}).items():
            field_info = namespace.pop(key, FieldInfo(required=True))
            field_info.annotation = value
            field_definitions[key] = (value, field_info)

        return field_definitions

    @classmethod
    def collect_model_config(cls, config: typing.Callable, namespace: dict) -> dict:
        return {
            attr: getattr(config, attr) for attr in dir(config)
            if not attr.startswith('__') and attr not in cls.KNOWN_CONFIGS
        } | namespace.pop('model_config', {})

    @classmethod
    def collect_validators(cls, namespace: dict) -> dict:
        return {
            key: value for key, value in namespace.items()
            if not key.startswith('__') and key != 'model_config'
        }

    @classmethod
    def finalization(cls, config: typing.Callable, serializer: typing.Callable):
        cls.model_serializer.model = config.model
        serializer.__bases__ = (cls.model_serializer, *serializer.__bases__)


class ModelSerializer(metaclass=MetaModelSerializer):

    def create(self):
        validated_data = self.model_dump()

        if hasattr(self, 'perform_create'):
            validated_data = self.perform_create(validated_data)

        return self.model.insert_one(**validated_data)
