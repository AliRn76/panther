import timeit
from typing import Callable

from panther_core import initialize_routing, find_endpoint as rust_find_endpoint


def t1():
    pass


URLS = {
    'users': {
        '': t1,
        '1': {
            'name': t1,
            'age': t1
        },
        '<admin>': {
            'name': t1,
            'age': t1
        },
        '<ali>': {
            'name2': t1,
            'age2': t1
        },
        '<user_id>': {
            'who': {
                '': t1,
                'are': t1,
                'you': t1,
            }
        }
    }
}

PATH = '/users/5/name'

ENDPOINT_NOT_FOUND = (None, '')


def find_endpoint(urls: dict, path: str) -> tuple[Callable | None, str]:
    # 'user/list/?name=ali' --> 'user/list/' --> 'user/list' --> ['user', 'list']
    parts = path.split('?')[0].strip('/').split('/')
    paths_len = len(parts)

    found_path = []
    for i, part in enumerate(parts):
        last_path = bool((i + 1) == paths_len)
        found = urls.get(part)

        if last_path:
            # `found` is callable
            if callable(found):
                found_path.append(part)
                return found, '/'.join(found_path)

            # `found` is dict
            if isinstance(found, dict) and (endpoint := found.get('')):
                if callable(endpoint):
                    found_path.append(part)
                    return endpoint, '/'.join(found_path)
                else:
                    return ENDPOINT_NOT_FOUND

            # `found` is None
            for key, value in urls.items():
                if key.startswith('<'):
                    if callable(value):
                        found_path.append(key)
                        return value, '/'.join(found_path)

                    elif isinstance(value, dict) and (endpoint := value.get('')):
                        if callable(endpoint):
                            found_path.append(key)
                            return endpoint, '/'.join(found_path)
                        else:
                            return ENDPOINT_NOT_FOUND

            return ENDPOINT_NOT_FOUND

        # `found` is dict
        elif isinstance(found, dict):
            found_path.append(part)
            urls = found
            continue

        # `found` is callable
        elif callable(found):
            return ENDPOINT_NOT_FOUND

        else:
            # `found` is None
            for key, value in urls.items():
                if key.startswith('<'):
                    if isinstance(value, dict):
                        found_path.append(key)
                        urls = value
                        break
            else:
                return ENDPOINT_NOT_FOUND



def test_python():
    # 1.3410026440396905e-06 --> 'users/'
    # 0.0000024439941626042128 --> 'users/1/age'
    x = find_endpoint(URLS, PATH)
    print(f'{x=}')


def test_rust():
    # 1.9080995116382837e-05 --> 'users/'        --> debug
    # 3.5492994356900454e-05 --> 'users/1/age'   --> debug
    # 0.0000035179982660338283 --> 'users/1/age'   --> release
    urls = initialize_routing(URLS)  # Just for rust
    rust_find_endpoint(urls, PATH)


def test_bench():
    initialize_routing(URLS)  # Just for rust

    print(f"Minimum time: {min(timeit.Timer(test_rust).repeat(repeat=100000, number=1))}")


py_result = find_endpoint(URLS, PATH)
print(f'{py_result=}')

urls = initialize_routing(URLS)
print(urls)
rust_result = rust_find_endpoint(urls, PATH)
print(f'{rust_result=}')

print(py_result == rust_result)
