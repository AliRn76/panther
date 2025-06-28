# User Model Configuration

You can specify which model should be used as your User model by setting the `USER_MODEL` variable in your configuration files.

The value of `USER_MODEL` should be the import path (address) of a model class that inherits from `panther.db.models.BaseUser`. Panther relies on this model for user authentication and management within the AdminPanel and all built-in authentication classes.

## Usage

- **Login and Authentication in AdminPanel:** The specified User model will be used to authenticate users accessing the AdminPanel.
- **Built-in Authentication Classes:** All built-in authentication mechanisms will utilize this User model for user-related operations.

## Default Value

If you do not specify a `USER_MODEL`, Panther will use `panther.db.models.BaseUser` as the default User model.

## Example

```python
# In your configuration file
USER_MODEL = 'your_app.models.CustomUser'
```
