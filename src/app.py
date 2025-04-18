import timeit
import panther_core
from example import test_cases
from panther.configs import config
from panther.routings import find_endpoint

def initialize_routing():
    """Initialize the routing once for the Rust implementation"""
    panther_core.parse(config.FLAT_URLS)

def test_python():
    """Test the Python implementation"""
    for test_url, expected in test_cases.items():
        actual = find_endpoint(path=test_url)
        # print(actual)
        assert actual == expected, f'{actual} != {expected}'

def test_rust():
    """Test the Rust implementation using global static storage"""
    for test_url, expected in test_cases.items():
        # With our updated code, we don't need to pass endpoints anymore
        result = panther_core.get(test_url)
        print(result)
        # Handle the new return format which includes path parameters
        # if result is not None:
        #     name, handler, _ = result  # Ignoring path_params for this test
        #     actual = (name, handler)
        # else:
        #     actual = None
        #
        # assert actual == expected, f'{actual} != {expected}'

def test():
    # Initialize the Rust routing once
    initialize_routing()

    test_rust()
    print(f"Python Minimum time: {min(timeit.Timer(test_python).repeat(repeat=100, number=1))}")
    print(f"Rust Minimum time: {min(timeit.Timer(test_rust).repeat(repeat=100, number=1))}")

if __name__ == "__main__":
    test()
    # print(config.FLAT_URLS)
    # print("\n\n")
    # parse_urls(config.FLAT_URLS)
