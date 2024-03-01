You can write your `serializer` in ۳ style:


## Style 1 (Pydantic)
Write a normal `pydantic` class and use it as serializer:

   ```python
    from pydantic import BaseModel
    from pydantic import Field
    
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

## Style 2 (Model Serializer)
Use panther `ModelSerializer` to write your serializer which will use your `model` to create fields.

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
    
    # type 1 - using fields
    class UserModelSerializer(ModelSerializer):
        class Config:
            model = User
            fields = ['username', 'first_name', 'last_name']
            required_fields = ['first_name']
    
    # type 2 - using exclude
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

### Notes
1. In the example above, `ModelSerializer` will look up for the value of `Config.fields` in the `User.model_fields` and use their `type` and `value` for the `validation`.
2. `Config.model` and `Config.fields` are `required` when you are using `ModelSerializer`.
3. You can force a field to be required with `Config.required_fields` 
4. You can force a field to be optional with `Config.optional_fields` 
5. `Config.required_fields` and `Config.optional_fields` can't include same fields 
6. If you want to use `Config.required_fields` or `Config.optional_fields` you have to put their value in `Config.fields` too.
7. `Config.fields` & `Config.required_fields` & `Config.optional_fields` can be `*` too (Include all the model fields)
8. `Config.exclude` is mostly used when `Config.fields` is `'*'`



## Style 3 (Model Serializer + Pydantic)

You can use `pydantic.BaseModel` features in `ModelSerializer` too.

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

### Notes
1. You can add custom `fields` 
2. You can add `model_config` as `attribute` or as `Config`
3. You can use `@field_validator` and other `validators` of `pydantic`.
 

