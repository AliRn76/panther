import typing
from typing import Any

from pydantic import create_model, BaseModel, ConfigDict
from pydantic.fields import FieldInfo, Field
from pydantic_core._pydantic_core import PydanticUndefined

from panther.db import Model
from panther.request import Request


class MetaModelSerializer:
    KNOWN_CONFIGS = ['model', 'fields', 'exclude', 'required_fields', 'optional_fields']

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[typing.Any], ...],
            namespace: dict[str, typing.Any],
            **kwargs
    ):
        if cls_name == 'ModelSerializer':
            # Put `model` and `request` to the main class with `create_model()`
            namespace['__annotations__'].pop('model')
            namespace['__annotations__'].pop('request')
            cls.model_serializer = type(cls_name, (), namespace)
            return super().__new__(cls)

        # 1. Initial Check
        cls.check_config(cls_name=cls_name, namespace=namespace)
        config = namespace.pop('Config')

        # 2. Collect `Fields`
        field_definitions = cls.collect_fields(config=config, namespace=namespace)

        # 3. Collect `pydantic.model_config`
        model_config = cls.collect_model_config(config=config, namespace=namespace)
        namespace |= {'model_config': model_config}

        # 4. Create a serializer
        return create_model(
            cls_name,
            __module__=namespace['__module__'],
            __validators__=namespace,
            __base__=(cls.model_serializer, BaseModel),
            model=(typing.ClassVar[type[BaseModel]], config.model),
            request=(Request, Field(None, exclude=True)),
            **field_definitions
        )

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
            if not issubclass(model, (Model, BaseModel)):
                msg = f'`{cls_name}.Config.model` is not subclass of `panther.db.Model` or `pydantic.BaseModel`.'
                raise AttributeError(msg) from None
        except TypeError:
            msg = f'`{cls_name}.Config.model` is not subclass of `panther.db.Model`.'
            raise AttributeError(msg) from None

        # Check `fields`
        if not hasattr(config, 'fields'):
            msg = f'`{cls_name}.Config.fields` is required.'
            raise AttributeError(msg) from None

        if config.fields != '*':
            for field_name in config.fields:
                if field_name == '*':
                    msg = f"`{cls_name}.Config.fields.{field_name}` is not valid. Did you mean `fields = '*'`"
                    raise AttributeError(msg) from None

                if field_name not in model.model_fields:
                    msg = f'`{cls_name}.Config.fields.{field_name}` is not in `{model.__name__}.model_fields`'
                    raise AttributeError(msg) from None

        # Check `required_fields`
        if not hasattr(config, 'required_fields'):
            config.required_fields = []

        if config.required_fields != '*':
            for required in config.required_fields:
                if required not in config.fields:
                    msg = f'`{cls_name}.Config.required_fields.{required}` should be in `Config.fields` too.'
                    raise AttributeError(msg) from None

        # Check `optional_fields`
        if not hasattr(config, 'optional_fields'):
            config.optional_fields = []

        if config.optional_fields != '*':
            for optional in config.optional_fields:
                if optional not in config.fields:
                    msg = f'`{cls_name}.Config.optional_fields.{optional}` should be in `Config.fields` too.'
                    raise AttributeError(msg) from None

        # Check `required_fields` and `optional_fields` together
        if (
                (config.optional_fields == '*' and config.required_fields != []) or
                (config.required_fields == '*' and config.optional_fields != [])
        ):
            msg = (
                f"`{cls_name}.Config.optional_fields` and "
                f"`{cls_name}.Config.required_fields` can't include same fields at the same time"
            )
            raise AttributeError(msg) from None
        for optional in config.optional_fields:
            for required in config.required_fields:
                if optional == required:
                    msg = (
                        f"`{optional}` can't be in `{cls_name}.Config.optional_fields` and "
                        f"`{cls_name}.Config.required_fields` at the same time"
                    )
                    raise AttributeError(msg) from None

        # Check `exclude`
        if not hasattr(config, 'exclude'):
            config.exclude = []

        for field_name in config.exclude:
            if field_name not in model.model_fields:
                msg = f'`{cls_name}.Config.exclude.{field_name}` is not valid.'
                raise AttributeError(msg) from None

            if config.fields != '*' and field_name not in config.fields:
                msg = f'`{cls_name}.Config.exclude.{field_name}` is not defined in `Config.fields`.'
                raise AttributeError(msg) from None

    @classmethod
    def collect_fields(cls, config: typing.Callable, namespace: dict) -> dict:
        field_definitions = {}

        # Define `fields`
        if config.fields == '*':
            for field_name, field in config.model.model_fields.items():
                field_definitions[field_name] = (field.annotation, field)
        else:
            for field_name in config.fields:
                field_definitions[field_name] = (
                    config.model.model_fields[field_name].annotation,
                    config.model.model_fields[field_name]
                )

        # Apply `exclude`
        for field_name in config.exclude:
            del field_definitions[field_name]

        # Apply `required_fields`
        if config.required_fields == '*':
            for value in field_definitions.values():
                value[1].default = PydanticUndefined
        else:
            for field_name in config.required_fields:
                field_definitions[field_name][1].default = PydanticUndefined

        # Apply `optional_fields`
        if config.optional_fields == '*':
            for value in field_definitions.values():
                value[1].default = value[0]()
        else:
            for field_name in config.optional_fields:
                field_definitions[field_name][1].default = field_definitions[field_name][0]()

        # Collect and Override `Class Fields`
        for key, value in namespace.pop('__annotations__', {}).items():
            field_info = namespace.pop(key, FieldInfo(annotation=value))
            field_definitions[key] = (value, field_info)

        return field_definitions

    @classmethod
    def collect_model_config(cls, config: typing.Callable, namespace: dict) -> dict:
        return {
            attr: getattr(config, attr) for attr in dir(config)
            if not attr.startswith('__') and attr not in cls.KNOWN_CONFIGS
        } | namespace.pop('model_config', {}) | {'arbitrary_types_allowed': True}


class ModelSerializer(metaclass=MetaModelSerializer):
    """
    Doc:
        https://pantherpy.github.io/serializer/#style-2-model-serializer
    Example:
        class PersonSerializer(ModelSerializer):
            class Meta:
                model = Person
                fields = '*'
                exclude = ['created_date']  # Optional
                required_fields = ['first_name', 'last_name']  # Optional
                optional_fields = ['age']  # Optional
    """
    model: type[BaseModel]
    request: Request

    async def create(self, validated_data: dict):
        """
        validated_data = ModelSerializer.model_dump()
        """
        return await self.model.insert_one(validated_data)

    async def update(self, instance: Model, validated_data: dict):
        """
        instance = UpdateAPI.object()
        validated_data = ModelSerializer.model_dump()
        """
        await instance.update(validated_data)
        return instance

    async def partial_update(self, instance: Model, validated_data: dict):
        """
        instance = UpdateAPI.object()
        validated_data = ModelSerializer.model_dump(exclude_none=True)
        """
        await instance.update(validated_data)
        return instance

    async def prepare_response(self, instance: Any, data: dict) -> dict:
        return data
