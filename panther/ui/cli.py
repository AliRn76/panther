import os
from argparse import ArgumentParser
import uvicorn
from os import getcwd
import subprocess
from pathlib import Path

ui_folder = Path(__file__).resolve().parent
OS_name = os.name


def parser(args):
    match args:
        case {'version': True}:
            print('0.1.4')
        case {'host': _, 'port': _}:
            uvicorn.run('main:app', host=args.get('host'), port=args.get('port'))
        case {'name': _, 'path': _}:
            if OS_name == 'nt':
                subprocess.call([ui_folder / 'project.bat', args.get('path'), args.get('name')])
            else:
                subprocess.call(['sh', ui_folder / 'linux.sh'])
        case {'app': _, 'path': _}:
            if OS_name == 'nt':
                subprocess.call([ui_folder / 'app.bat', args.get('path'), args.get('app')])
            else:
                subprocess.call(['sh', ui_folder / 'linux.sh'])


def main():
    arg_parser = ArgumentParser(description='Panther, Fast & Easy Python Framework.')
    arg_parser.add_argument('-v', '--version', action='store_true', help='panther version.')
    sub_parser = arg_parser.add_subparsers(title='Main Commands')
    # run command
    run_parser = sub_parser.add_parser(name='run', help='run server.')
    run_parser.add_argument('-host', default='127.0.0.1', type=str, help='host')
    run_parser.add_argument('-port', default=8000, type=int, help='port')
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
