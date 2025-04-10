import timeit
import panther_core
from example import test_cases
from panther.configs import config

def initialize_routing(urls):
    """Initialize the routing once for the Rust implementation"""
    panther_core.parse_urls(urls)

def test_python():
    """Test the Python implementation"""
    for test_url, expected in test_cases.items():
        actual = panther_core.find_endpoint(path=test_url)
        assert actual == expected, f'{actual} != {expected}'

def test_rust():
    """Test the Rust implementation using global static storage"""
    for test_url, expected in test_cases.items():
        # With our updated code, we don't need to pass endpoints anymore
        result = panther_core.get(test_url)

        # Handle the new return format which includes path parameters
        if result is not None:
            name, handler, _ = result  # Ignoring path_params for this test
            actual = (name, handler)
        else:
            actual = None

        assert actual == expected, f'{actual} != {expected}'

def test():
    # Initialize the Rust routing once
    initialize_routing(config.URLS)

    print(f"Python Minimum time: {min(timeit.Timer(test_python).repeat(repeat=100, number=1))}")
    print(f"Rust Minimum time: {min(timeit.Timer(test_rust).repeat(repeat=100, number=1))}")

if __name__ == "__main__":
    test()
