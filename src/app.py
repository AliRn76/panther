import timeit

import panther_core

from example import test_cases
from panther.configs import config
from panther.routings import find_endpoint


def test_python():
    # Minimum time: 5.815300391986966e-05
    for test_url, expected in test_cases.items():
        actual = find_endpoint(path=test_url)
        assert actual == expected, f'{actual} != {expected}'


def test_rust():
    endpoints = panther_core.parse_urls(config.URLS)
    for test_url, expected in test_cases.items():
        actual = panther_core.get(endpoints, path=test_url)
        assert actual == expected, f'{actual} != {expected}'


def test():
    initialize_routing(config.URLS)  # Just for rust
    print(f"Python Minimum time: {min(timeit.Timer(test_python).repeat(repeat=100, number=1))}")
    print(f"Rust Minimum time: {min(timeit.Timer(test_rust).repeat(repeat=100, number=1))}")


test()
