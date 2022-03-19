import argparse
from argparse import ArgumentParser
import uvicorn
import os


def create_project(args):
    ...


def parser(args):
    match args:
        case {'command': 'run'}:
            uvicorn.run('main:app', host=args.get('host'), port=args.get('port'))
        case {'command': 'test'}:
            print('soon')
        case {'command': 'migrate'}:
            print('Soon.')
        case {'command': 'makeproject'}:
            create_project(args)
    return 0


def main():
    arg_parser = ArgumentParser(description='Panther, Fast & Easy Python Framework.')
    arg_parser.add_argument('-v', '--version', action='store_true', help='Panther Version.')
    arg_parser.add_argument('command', help='Command.', choices=('run', 'makeproject', 'makeapp', 'test', 'migrate'))
    optional = arg_parser.add_argument_group(title='optional')
    optional.add_argument('-host', default='127.0.0.1', type=str, help='host')
    optional.add_argument('-port', default=8000, type=int, help='port')
    optional.add_argument('-path', default=os.getcwd(), type=str, help='path')
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    print(main().__dict__)
    parser(main().__dict__)
