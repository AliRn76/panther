You can write your `serializer` in 2 style:


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
Use panther `ModelSerializer` to write your serializer which will use your `model` fields as its fields, and you can say which fields are `required`

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
   
   
   class UserModelSerializer(metaclass=ModelSerializer, model=User):
       fields = ['username', 'first_name', 'last_name']
       required_fields = ['first_name']
   
   
   @API(input_model=UserModelSerializer)
   async def model_serializer_example(request: Request):
       return Response(data=request.validated_data, status_code=status.HTTP_202_ACCEPTED)
   ```

## Notes
1. In the example above `UserModelSerializer` only accepts the values of `fields` attribute

2. In default the `UserModelSerializer.fields` are same as `User.fields` but you can change their default and make them required with `required_fields` attribute  
    
3. If you want to use `required_fields` you have to put them in `fields` too.

4. `fields` attribute is `required` when you are using `ModelSerializer` as `metaclass`

5. `model=` is required when you are using `ModelSerializer` as `metaclass`

6. You have to use `ModelSerializer` as `metaclass` (not as a parent)

7. Panther is going to create a `pydantic` model as your `UserModelSerializer` in the startup