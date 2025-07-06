> **⚠️ WARNING: The Panther Admin Panel is currently in development. Do NOT use it in production environments!**
> 
> **Contributions, feedback, and ideas are welcome!**

# Panther Admin Panel

Panther provides a built-in admin panel that allows you to easily manage your database models through a web interface.

## Enabling the Admin Panel

To enable the admin panel in your project, follow these steps:

### 1. Add the Admin Panel URLs

First, ensure your main URL configuration includes the admin panel routes. e.g. open your `core/urls.py` and add the following:

```python title="core/urls.py"
from panther.panel.urls import url_routing as panel_url_routing

url_routing = {
    'panel/': panel_url_routing,
    # ... other routes ...
}
```

> **Note:** If you are using a different file for your URL routing, adjust the import and assignment accordingly.

### 2. Update Your Configs (if needed)

If your project uses a custom configuration file for URLs, make sure it points to your updated URL routing. For example, in `core/configs.py`:

```python title="core/configs.py"
URLs = 'core.urls.url_routing'
```

### 3. Run Your Application

Start your Panther application as usual:

```bash
panther run main:app
```

### 4. Access the Admin Panel

Open your browser and navigate to:

[http://127.0.0.1:8000/panel/](http://127.0.0.1:8000/panel/)

You should see the Panther Admin Panel interface, where you can manage your database models. 

### 5. Create an Admin User

To access the admin panel, you need at least one user account. You can create a user using the following command:

```bash
panther createuser main.py
```

Replace `main.py` with the path to your main application file if it is different. This command will create a new user based on your `USER_MODEL` (by default, `panther.db.models.BaseUser`).

Once the user is created, you can log in to the admin panel using the credentials you set during user creation. 