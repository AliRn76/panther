  
### find_one:  
- Find the first match document  
- Example:  

	```python  
	user: User = User.find_one(id=1, name='Ali')  
	  
	user: User = User.find_one({'id': 1, 'name': 'Ali'})  
	  
	user: User = User.find_one({'id': 1}, name='Ali')  
	```  
  
### find:  
- Find all the matches documents  
- Example:  
  
	```python  
	users: list[User] = User.find(id=1, name='Ali')  
	  
	users: list[User] = User.find({'id': 1, 'name': 'Ali'})  
	  
	users: list[User] = User.find({'id': 1}, name='Ali')  
	```  
  
### insert_one:  
- Insert only one document into database  
- Example:  
  
	```python  
	User.insert_one(id=1, name='Ali')  
	  
	User.insert_one({'id': 1, 'name': 'Ali'})  
	  
	User.insert_one({'id': 1}, name='Ali')  
	```

### delete:  
- Delete the selected document from database
- Example:  
  
	```python  
	user: User = User.find_one(name='Ali')
	user.delete()
	```

### delete_one:  
- Delete the first match document  from database
- Example:  
  
	```python  
	is_deleted: bool = User.delete_one(id=1, name='Ali')
	```

### delete_many:  
- Delete all the matches document  from database
- Example:  
  
	```python  
	deleted_count: int = User.delete_many(id=1, name='Ali')
	
	deleted_count: int = User.delete_many({'id': 1}, name='Ali')
	
	deleted_count: int = User.delete_many({'id': 1, 'name': 'Ali'})
	```

### update:  
- Update the selected document in database
- Example:  
  
	```python  
	user = User.find_one(name='Ali')
	user.update(name='Saba')
	```

### update_one:  
- Update the first match document in database
- You should filter with `dictionary` as `first parameter` 
and pass the fields you want to update as `kwargs` or another `dictionary` as `second parameter`
- Example:  
  
	```python  
	is_updated: bool = User.update_one({'id': 1, 'name': 'Ali'}, name='Saba', age=26)
 
	is_updated: bool = User.update_one({'id': 1, 'name': 'Ali'}, {'name': 'Saba', 'age': 26})
 
	is_updated: bool = User.update_one({'id': 1, 'name': 'Ali'}, {'name': 'Saba'}, age=26)
	```

### update_many:  
- Update all the matches document in database
- You should filter with `dictionary` as `first parameter` 
and pass the fields you want to update as `kwargs` or another `dictionary` as `second parameter`
- Example:  
  
	```python  
	updated_count: int = User.update_many({'name': 'Ali'}, name='Saba', age=26)
 
	updated_count: int = User.update_many({'name': 'Ali'}, {'name': 'Saba', 'age': 26})
 
	updated_count: int = User.update_many({'name': 'Ali'}, {'name': 'Saba'}, age=26)
	```

### last:  
- Find the last match document
- Example:  
  
	```python  
	user: User = User.last(name='Ali', age=26)  
	  
	user: User = User.last({'name': 'Ali', 'age': 26})  
	  
	user: User = User.last({'name': 'Ali'}, age=26)  
	```

### count:  
- Count of the matches documents
- Example:  
  
	```python  
	users_count: int = User.count(name='Ali')
	```

### find_or_insert:  
- Find the match document or Create one if none exists
- Example:  
  
	```python  
	user: User = User.find_or_insert(name='Ali')
	```


### In next step we are going to authentication