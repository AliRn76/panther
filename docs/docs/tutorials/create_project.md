We assume you already have `Python 3.11+` installed, so

Create Virtual Environment with: 
  ```console
  $ python -m venv .venv
  ```

and active it with:

- In Linux or Mac:
    ```console
    $ source .venv/bin/activate
    ```
  
- In windows:
    ```console
    $ .\.venv\Scripts\activate
    ```
  
Then install the Panther using `pip`:
  ```console
  $ pip install panther
  ```

Now we can create a test project named `blog` with: 

```console
$ panther create blog
```

and if you don't want Panther to create a directory with the name of the project, so pass your custom directory name to it:

```console
$ panther create blog custom_directory
```

Now you can run the project with:
```console
$ panther run
```

and check this two sample endpoints on your browser:

  * [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

  * [http://127.0.0.1:8000/info/](http://127.0.0.1:8000/info/)
