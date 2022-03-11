import argparse
from argparse import ArgumentParser


def cli_handler() -> argparse:
    parser = ArgumentParser()
    parser.add_argument('run', type=int, required=True)
    parser.add_argument('--y', type=int, required=True)
    args = parser.parse_args()
    return args