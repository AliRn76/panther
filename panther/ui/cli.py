import os
from argparse import ArgumentParser
import uvicorn
from os import getcwd
import subprocess


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
    if os.name == 'nt':
        subprocess.call(['windows.bat', 'p', args.get('path'), args.get('name')])
    else:
        subprocess.call(['sh', 'linux.sh', ''])


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
    print(main().__dict__)
