from argument import ArgParser, Mode, Color


APP = {
    "apis": """

    """,
    "models": """
    
    """,
    "serializer": """
    
    """,
    "urls": """
        
    """,
}

PROJECT = {
    "core": {
        "configs": """
        
        """,
        "middlewares": """
        
        """,
        "urls": """
        
        """,
    },
    ".env": """
    
    """,
    "alembic.ini": """
    
    """,
    "main": """
    
    """
}

def create_app(inp):
    ...

def create_project(inp: list | str):
    ...

if __name__ == "__main__":
    ap = ArgParser()
    ap.add_arg(
        name="app",
        desc="create app template folder",
        mode=Mode.INPUT,
        func=create_app
    )