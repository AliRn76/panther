import os

from panther.cli.template import Template
from panther.cli.utils import error


def create(args: list):
    # TODO: os.getcwd()
    if len(args) == 0:
        return error('Not Enough Parameters.')
    project_name = args[0]

    # TODO: Add Custom BaseDirectory

    if os.path.isdir(project_name):
        return error(f'"{project_name}" Directory Already Exists.')
    os.makedirs(project_name)

    for file_name, data in Template.items():
        if isinstance(data, dict):
            sub_directory = f'{project_name}/{file_name}'
            os.makedirs(sub_directory)
            for sub_file_name, sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                sub_data = sub_data.replace('{PROJECT_NAME}', project_name.lower())
                with open(file_path, 'x') as file:
                    file.write(sub_data)
        else:
            data = data.replace('{PROJECT_NAME}', project_name.lower())

            file_path = f'{project_name}/{file_name}'
            with open(file_path, 'x') as file:
                file.write(data)
    else:
        print('Project Created Successfully.')
