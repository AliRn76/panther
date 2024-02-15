import timeit
from typing import Callable

from panther_core import initialize_routing, find_endpoint as rust_find_endpoint


def t1():
    pass


def t2():
    pass


def t3():
    pass


def t4():
    pass


def t5():
    pass


def t6():
    pass


def t7():
    pass


def t8():
    pass


def t9():
    pass


def t10():
    pass


URLS = {
    'users': {
        '': t1,
        '1': {
            'name': t2,
            'age': t3
        },
        '<user_id>': {
            'detail': {
                '': t4,
                'ali': t5,
                '<id>': t6
            }
        },
        '3': t7
    },
    'admins': t8,
    '<admin_id>': t9,
    '<lang_id>': {
        '1': t10,
    },
}
RUST_URLS = initialize_routing(URLS)


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
    rust_find_endpoint(RUST_URLS, PATH)


def test_bench():
    p_bench = timeit.Timer(test_python).repeat(repeat=100000, number=1)
    r_bench = timeit.Timer(test_rust).repeat(repeat=100000, number=1)
    print(f"Python Min: {min(p_bench)}, Sum: {sum(p_bench)}")
    print(f"Rust Min: {min(r_bench)}, Sum: {sum(r_bench)}")


PATH = '/users/5/name'


def test_results():
    paths = [
        'users',                  # (<function t1 at 0x7f13b811cd60>, 'users')
        'users/1',                # (None, '')
        'users/1/name',           # (<function t2 at 0x7f13b8b5c680>, 'users/1/name')
        'users/1/age',            # (<function t3 at 0x7f13b801de40>, 'users/1/age')
        'users/2/',               # (None, '')
        'users/2/detail',         # (<function t4 at 0x7f13b801e7a0>, 'users/<user_id>/detail')
        'users/2/detail/ali',     # (<function t5 at 0x7f13b801e840>, 'users/<user_id>/detail/ali')
        'users/2/detail/10',      # (<function t6 at 0x7f13b801e980>, 'users/<user_id>/detail/<id>')
        'users/3',                # (<function t7 at 0x7f13b801ea20>, 'users/3')
        'admins',                 # (<function t8 at 0x7f13b801eac0>, 'admins')
        'admin_5',                # (<function t9 at 0x7f13b801eb60>, '<admin_id>')
        '10/1'                    # (<function t10 at 0x7f13b801ec00>, '<lang_id>/1')
    ]
    results = []
    for path in paths:
        python_result = find_endpoint(URLS, path)
        py_endpoint_name = getattr(python_result[0], '__name__', '  ')
        print(f'python={py_endpoint_name}(), {python_result[1]}')

        rust_result = rust_find_endpoint(RUST_URLS, path)
        rust_endpoint_name = getattr(rust_result[0], '__name__', '  ')
        print(f'rust  ={rust_endpoint_name}(), {rust_result[1]}\n')
        results.append(python_result == rust_result)

    return results


print('Result: ', all(test_results()))
