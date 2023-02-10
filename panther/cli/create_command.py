import os
import sys
import time
from panther.cli.utils import error
from panther.cli.template import Template


def create(args: list):
    load_animation1()

    # Get Project Name
    if len(args) == 0:
        return error('Not Enough Parameters.')
    project_name = args[0]

    # Get Base Directory
    base_directory = project_name
    if len(args) > 1:
        base_directory = args[1]

    # Check All The Directories Existence
    existence = check_all_directories(base_directory)
    if existence:
        return error(f'"{existence}" Directory Already Exists.')

    # Create Base Directory
    if base_directory != '.':
        os.makedirs(base_directory)

    for file_name, data in Template.items():
        if isinstance(data, dict):
            # Create Sub Directory
            sub_directory = f'{base_directory}/{file_name}'
            os.makedirs(sub_directory)

            # Create Files of Sub Directory
            for sub_file_name, sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                sub_data = sub_data.replace('{PROJECT_NAME}', project_name.lower())
                with open(file_path, 'x') as file:
                    file.write(sub_data)
        else:
            # Create File
            data = data.replace('{PROJECT_NAME}', project_name.lower())
            file_path = f'{base_directory}/{file_name}'
            with open(file_path, 'x') as file:
                file.write(data)
    else:
        print('Project Created Successfully.')


def check_all_directories(base_directory: str) -> str | None:
    """
    return folder_name means that the directory exist
    """
    if base_directory != '.':
        if os.path.isdir(base_directory):
            return base_directory

    for file_name, data in Template.items():
        sub_directory = f'{base_directory}/{file_name}'
        if os.path.exists(sub_directory):
            return sub_directory

        if isinstance(data, dict):
            for sub_file_name, sub_data in data.items():
                file_path = f'{sub_directory}/{sub_file_name}'
                if os.path.exists(file_path):
                    return file_path


def load_animation1():
    animation = [
        "■□□□□□□□□□□",
        "■■□□□□□□□□□",
        "■■■□□□□□□□□",
        "■■■■□□□□□□□",
        "■■■■■□□□□□□",
        "■■■■■■□□□□□",
        "■■■■■■■□□□□",
        "■■■■■■■■□□□",
        "■■■■■■■■■□□",
        "■■■■■■■■■■□",
        "■■■■■■■■■■■",
    ]

    for i in range(len(animation)):
        time.sleep(0.2)
        sys.stdout.write('\r' + 'Creating Your Project: ' + animation[i % len(animation)])
        sys.stdout.flush()

    print('\n')


def load_animation2():
    # String to be displayed when the application is loading
    load_str = 'creating your project ...    '
    ls_len = len(load_str)

    # String for creating the rotating line
    animation = '|/-\\'
    ani_count = 0

    # used to keep the track of
    # the duration of animation
    count_time = 0

    # pointer for travelling the loading string
    i = 0

    while count_time != 30:

        # used to change the animation speed
        # smaller the value, faster will be the animation
        time.sleep(0.09)

        # converting the string to list
        # as string is immutable
        load_str_list = list(load_str)

        # x->obtaining the ASCII code
        x = ord(load_str_list[i])

        # y->for storing altered ASCII code
        y = 0

        # if the character is '.' or ' ', keep it unaltered
        # switch uppercase to lowercase and vice-versa
        if x != 32 and x != 46:
            if x > 90:
                y = x - 32
            else:
                y = x + 32
            load_str_list[i] = chr(y)

        # for storing the resultant string
        res = ''
        for j in range(ls_len):
            res = res + load_str_list[j]

        # displaying the resultant string
        sys.stdout.write('\r' + res + animation[ani_count])
        sys.stdout.flush()

        # Assigning loading string
        # to the resultant string
        load_str = res

        ani_count = (ani_count + 1) % 4
        i = (i + 1) % ls_len
        count_time = count_time + 1

    sys.stdout.write('\r')
    sys.stdout.flush()
