import os
from .argument import ArgParser, Mode
import sys
from panther.ui.template import APP, PROJECT


def create_app(name: list | str, path: str):
    os.mkdir(f"{path}/{name}")
    for filename, data in APP.items():
        file = open(f"{path}/{name}/{filename}", 'x')
        file.write(data.replace("{}", name))
        file.close()


def create_project(name: list | str, path: str):
    project_path = f"{path}/{name}"
    os.mkdir(project_path)
    for filename, data in PROJECT.items():
        
        if isinstance(data, dict):
            sub_folder = f"{project_path}/{filename}"
            os.mkdir(sub_folder)
            for new_file, data in data.items():
                file = open(f"{sub_folder}/{new_file}", 'x')
                file.write(data)
                file.close()
        else:
            file = open(f"{project_path}/{filename}", 'x')
            file.write(data.replace("{}", name))
            file.close()


def main():
    ap = ArgParser(os.getcwd())
    ap.add_arg(
        name="app",
        desc="create app template folder",
        mode=Mode.INPUT,
        func=create_app,
    )
    ap.add_arg(
        name="project",
        desc="create project template folder",
        mode=Mode.INPUT,
        func=create_project,
    )
    ap.parser(sys.argv)
