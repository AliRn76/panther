from argument import ArgParser, Mode, Color
import sys

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


def create_app(inp: list | str):
    print(inp)

def create_project(inp: list | str):
    print(inp)

if __name__ == "__main__":
    ap = ArgParser()
    ap.add_arg(
        name="app",
        desc="create app template folder",
        mode=Mode.INPUT,
        func=create_app
    )
    ap.add_arg(
        name="project",
        desc="create project template folder",
        mode=Mode.INPUT,
        func=create_project
    )
    ap.parser(sys.argv)
