import argparse
import os
from argparse import ArgumentParser
import uvicorn
from os import getcwd
from shutil import copytree
from pathlib import Path


def parser(args):
    match args:
        case {'version': True}:
            print('0.1.4')
        case {'host': _, 'port': _}:
            uvicorn.run('main:app', host=args.get('host'), port=args.get('port'))
        case {'path': _}:
            make_project(args)
        case {'apps': _}:
            ...
    return 0


def make_project(args):
    try:
        project_dir = os.path.join(args['path'], args['name'])
        print(project_dir)
        os.mkdir(project_dir)
        project_files_dir = Path(__file__).resolve() / 'template/project'
        print(project_files_dir)
        copytree(project_files_dir, project_dir)
    except FileExistsError:
        print('Folder Exists.')


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
    makeapp.add_argument('-apps', default=[], nargs='*', help='app names.')
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    parser(main().__dict__)
