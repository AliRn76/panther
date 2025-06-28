import argparse
import os
import sys

import pytest
from _pytest.config import ExitCode

TEST_DIR = os.path.dirname(__file__)

TEST_SUCCESS_CONDITIONS = [ExitCode.OK, ExitCode.NO_TESTS_COLLECTED]


def run_test_file(path, flags: list) -> int:
    print(f'Running {os.path.basename(path)}')
    return pytest.main([path, *flags])


def main():
    """
    We have to separate load of test so we can have more isolated test cases,
    We had issue on testing `config`, some attributes been filled on the load of file,
        for example we collect models on __init_subclass__ of their parent

    Example Usage:
        python tests --not_slow --not_mongodb
    """
    parser = argparse.ArgumentParser(description='Run test files individually.')
    # Make sure to define each flag in here, pyproject.toml and on top of the test target.
    parser.add_argument('--mongodb', action='store_true', help='Only run mongodb tests.')
    parser.add_argument('--not_mongodb', action='store_true', help='Does not run mongodb tests.')
    parser.add_argument('--slow', action='store_true', help='Only run slow tests.')
    parser.add_argument('--not_slow', action='store_true', help='Does not run slow tests.')
    args = parser.parse_args()

    files = [os.path.join(TEST_DIR, f) for f in os.listdir(TEST_DIR) if f.startswith('test_') and f.endswith('.py')]

    flags = []
    if args.not_mongodb:
        flags.append('not mongodb')
    if args.not_slow:
        flags.append('not slow')
    if args.mongodb:
        flags.append('mongodb')
    if args.slow:
        flags.append('slow')
    if flags:
        flags = ['-m', ' and '.join(f for f in flags)]

    results = [run_test_file(file, flags) for file in files]
    for code, file in zip(results, files):
        if code not in TEST_SUCCESS_CONDITIONS:
            print(f'[FAIL] Some tests failed in {os.path.basename(file)}', file=sys.stderr)

    if any(code not in TEST_SUCCESS_CONDITIONS for code in results):
        sys.exit(1)
    print('\n[PASS] All tests passed.')


if __name__ == '__main__':
    main()
