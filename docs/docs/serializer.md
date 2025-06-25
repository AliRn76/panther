# Panther Serializers

Panther provides flexible ways to define serializers for your APIs. Serializers are responsible for validating and transforming input data. This guide covers the three supported styles and when to use each.

---

## Introduction

**serializer** in Panther is a class that defines how input data is validated and (optionally) transformed before being processed by your API logic. Panther supports three main styles:

- **Pydantic Serializer**: Use a standard Pydantic model.

- **ModelSerializer**: Generate fields from a Panther model.

- **ModelSerializer + Pydantic**: Combine model-based fields with Pydantic features and custom validation.

---

## Style 1: Pydantic Serializer

Use a regular Pydantic class as your serializer. This is the most direct approach and is ideal for simple use cases or when you want full control over the fields.

```python
from pydantic import BaseModel, Field
from panther.app import API
from panther.request import Request
from panther.response import Response

class UserSerializer(BaseModel):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)

@API(input_model=UserSerializer)
async def serializer_example(request: Request):
    return Response(data=request.validated_data)
```

---

## Style 2: ModelSerializer

Use Panther's `ModelSerializer` to automatically generate serializer fields from your model. This is useful for DRY code and consistency between your models and serializers.

```python
from pydantic import Field
from panther import status
from panther.app import API
from panther.db import Model
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

class User(Model):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)

# Option 1: Specify fields explicitly
class UserModelSerializer(ModelSerializer):
    class Config:
        model = User
        fields = ['username', 'first_name', 'last_name']
        required_fields = ['first_name']

# Option 2: Exclude specific fields
class UserModelSerializer(ModelSerializer):
    class Config:
        model = User
        fields = '*'
        required_fields = ['first_name']
        exclude = ['id', 'password']

@API(input_model=UserModelSerializer)
async def model_serializer_example(request: Request):
    return Response(data=request.validated_data, status_code=status.HTTP_202_ACCEPTED)
```

---

## Style 3: ModelSerializer with Pydantic Features

Combine `ModelSerializer` with Pydantic features for advanced use cases. This allows you to add custom fields, validators, and configuration.

```python
from pydantic import Field, field_validator, ConfigDict
from panther import status
from panther.app import API
from panther.db import Model
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

class User(Model):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)

class UserModelSerializer(ModelSerializer):
    model_config = ConfigDict(str_to_upper=True)
    age: int = Field(default=20)
    is_male: bool
    username: str

    class Config:
        model = User
        fields = ['first_name', 'last_name']
        required_fields = ['first_name']
        optional_fields = ['last_name']

    @field_validator('username')
    def validate_username(cls, username):
        print(f'{username=}')
        return username

@API(input_model=UserModelSerializer)
async def model_serializer_example(request: Request):
    return Response(data=request.validated_data, status_code=status.HTTP_202_ACCEPTED)
```

---

## Comparison Table

| Feature                | Pydantic Serializer | ModelSerializer | ModelSerializer + Pydantic |
|------------------------|:------------------:|:--------------:|:-------------------------:|
| Model-based fields     |         ❌          |       ✅        |            ✅             |
| Custom fields          |         ✅          |       ❌        |            ✅             |
| Pydantic validators    |         ✅          |       ❌        |            ✅             |
| Field inclusion/exclude|         Manual      |   Configurable |        Configurable       |
| Best for               |  Simple cases      |  DRY, model-aligned | Advanced/Hybrid      |

---

## Notes & Best Practices

- `ModelSerializer` uses your model's field types and default values for validation.
- `Config.model` and `Config.fields` are required for `ModelSerializer`.
- Use `Config.required_fields` to force fields to be required.
- Use `Config.optional_fields` to force fields to be optional.
- A field cannot be in both `required_fields` and `optional_fields`.
- If you use `required_fields` or `optional_fields`, those fields must also be listed in `fields`.
- You can use `'*'` for `fields`, `required_fields`, or `optional_fields` to include all model fields.
- `Config.exclude` is useful when `fields` is set to `'*'`.
- You can add custom fields and validators when combining `ModelSerializer` with Pydantic features.


