import os
from argparse import ArgumentParser
import uvicorn
from os import getcwd
import subprocess
from pathlib import Path

ui_folder = Path(__file__).resolve().parent
OS_name = os.name


# TODO: write shell scrip for making app and project
def parser(args):
    match args:
        case {'version': True}:
            print('0.1.4')
        case {'name': _, 'path': _}:
            if OS_name == 'nt':
                subprocess.call([ui_folder / 'project.bat', args.get('path'), args.get('name')])
            else:
                subprocess.call(['sh', ui_folder / 'linux.sh', args.get('path'), args.get('name')])
        case {'app': _, 'path': _}:
            if OS_name == 'nt':
                subprocess.call([ui_folder / 'app.bat', args.get('path'), args.get('app')])
            else:
                subprocess.call(['sh', ui_folder / 'linux.sh', args.get('path'), args.get('name')])


def main():
    arg_parser = ArgumentParser(description='Panther, Fast & Easy Python Framework.')
    arg_parser.add_argument('-v', '--version', action='store_true', help='panther version.')
    sub_parser = arg_parser.add_subparsers(title='Main Commands')
    # make project command
    make_project_parser = sub_parser.add_parser(name='makeproject', help='make project files.')
    make_project_parser.add_argument('name', type=str, help='project name.')
    make_project_parser.add_argument('-path', default=getcwd(), type=str, help='path')
    # makeapp command
    makeapp = sub_parser.add_parser('makeapp', help='make app files.')
    makeapp.add_argument('app', type=str, help='app names.')
    makeapp.add_argument('-path', default=getcwd(), help='path')
    args = arg_parser.parse_args()
    parser(args.__dict__)
