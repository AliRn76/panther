Panther ODM

### find_one:
- Find the first match document
- Example: 
	```python 
  User.find_one(id=1, name='Ali')
   ```

	```python
   User.find_one({'id': 1, 'name': 'Ali'})
	```

	 ```python
   User.find_one({'id': 1}, name='Ali')
	```
	
### find:
- Find all of the matches documents
- Example: 
	```python 
  User.find(id=1, name='Ali')
   ```

	```python
   User.find({'id': 1, 'name': 'Ali'})
	```

	 ```python
   User.find({'id': 1}, name='Ali')
	```
	
### insert_one:
- Insert only one document into database
- Example: 
	```python 
  User.insert_one(id=1, name='Ali')
   ```

	```python
   User.insert_one({'id': 1, 'name': 'Ali'})
	```

	 ```python
   User.insert_one({'id': 1}, name='Ali')
	```
	
### insert_one:
- Insert only one document into database
- Example: 
	```python 
  User.insert_one(id=1, name='Ali')
   ```

	```python
   User.insert_one({'id': 1, 'name': 'Ali'})
	```

	 ```python
   User.insert_one({'id': 1}, name='Ali')
	```