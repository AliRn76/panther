import argparse
from argparse import ArgumentParser
import uvicorn


def parser(args):
    match args:
        case {'version': True}:
            print('0.1.4')
        case {'run': True}:
            uvicorn.run('main:app', host=args.get('host'), port=args.get('port'))
        case {'test': True}:
            ...
        case {'createproject': True}:
            ...


def main():
    arg_parser = ArgumentParser(description='Panther, Fast & Easy Python Framework.')
    arg_parser.add_argument('-v', '--version', help='panther version.', action='store_true')
    arg_parser.add_argument('-r', '--run', help='run project.', action='store_true')
    arg_parser.add_argument('-t', '--test', help='run tests.', action='store_true')
    arg_parser.add_argument('-host', default='127.0.0.1', help='host')
    arg_parser.add_argument('-port', default=8000, help='port')
    arg_parser.add_argument('-cp', '--createproject', help='create project files.', action='store_true')
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    print(main().__dict__)
    parser(main().__dict__)
