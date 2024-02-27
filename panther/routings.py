import re
from collections import Counter
from collections.abc import Callable, Mapping, MutableMapping
from copy import deepcopy
from functools import partial, reduce

from panther.configs import config
from panther.exceptions import PantherError


def flatten_urls(urls: dict) -> dict:
    return dict(_flattening_urls(urls))


def _flattening_urls(data: dict | Callable, url: str = ''):
    # Add `/` add the end of url
    if not url.endswith('/'):
        url = f'{url}/'

    if isinstance(data, dict):
        for k, v in data.items():
            yield from _flattening_urls(v, f'{url}{k}')
    else:
        # Remove `/` prefix of url
        url = url.removeprefix('/')

        # Collect it, if it doesn't have problem
        _is_url_endpoint_valid(url=url, endpoint=data)
        yield url, data


def _is_url_endpoint_valid(url: str, endpoint: Callable):
    if endpoint is ...:
        raise PantherError(f"URL Can't Point To Ellipsis. ('{url}' -> ...)")
    elif endpoint is None:
        raise PantherError(f"URL Can't Point To None. ('{url}' -> None)")
    elif url and not re.match(r'^[a-zA-Z<>0-9_/-]+$', url):
        raise PantherError(f"URL Is Not Valid. --> '{url}'")


def finalize_urls(urls: dict) -> dict:
    """Convert flat dict to nested"""
    urls_list = []
    for url, endpoint in urls.items():
        path = {}
        if url == '':
            # This condition only happen when
            #   user defines the root url == '' instead of '/'
            url = '/'

        for single_path in list(filter(lambda x: x != '', url.split('/')[:-1][::-1])) or ['']:
            if single_path != '' and not path:
                path = {single_path: {'': endpoint}}
            else:
                path = {single_path: path or endpoint}
        urls_list.append(path)
    final_urls = _merge(*urls_list) if urls_list else {}
    check_urls_path_variables(final_urls)
    return final_urls


def check_urls_path_variables(urls: dict, path: str = '', ) -> None:
    middle_route_error = []
    last_route_error = []
    for key, value in urls.items():
        new_path = f'{path}/{key}'

        if isinstance(value, dict):
            if key.startswith('<'):
                middle_route_error.append(new_path)
            check_urls_path_variables(value, path=new_path)
        elif key.startswith('<'):
            last_route_error.append(new_path)

    if len(middle_route_error) > 1:
        msg = '\n\t- ' + '\n\t- '.join(e for e in middle_route_error)
        raise PantherError(
            f"URLs can't have same-level path variables that point to a dict: {msg}")

    if len(last_route_error) > 1:
        msg = '\n\t- ' + '\n\t- '.join(e for e in last_route_error)
        raise PantherError(
            f"URLs can't have same-level path variables that point to an endpoint: {msg}")


def _merge(destination: MutableMapping, *sources) -> MutableMapping:
    return _simplify_urls(reduce(partial(_deepmerge), sources, destination))


def _simplify_urls(urls):
    simplified_urls = {}

    for key, value in urls.items():
        if isinstance(value, dict):
            simplified_value = _simplify_urls(value)
            if isinstance(simplified_value, dict) and len(simplified_value) == 1 and '' in simplified_value:
                simplified_urls[key] = simplified_value['']
            else:
                simplified_urls[key] = simplified_value
        else:
            simplified_urls[key] = value

    return simplified_urls


def _deepmerge(dst, src):
    """Credit to Travis Clarke --> https://github.com/clarketm/mergedeep"""
    for key in src:
        if key in dst:
            if _is_recursive_merge(dst[key], src[key]):
                _deepmerge(dst[key], src[key])
            else:
                dst[key] = deepcopy(src[key])
        else:
            dst[key] = deepcopy(src[key])
    return dst


def _is_recursive_merge(a, b):
    both_mapping = isinstance(a, Mapping) and isinstance(b, Mapping)
    both_counter = isinstance(a, Counter) and isinstance(b, Counter)
    return both_mapping and not both_counter


ENDPOINT_NOT_FOUND = (None, '')


def find_endpoint(path: str) -> tuple[Callable | None, str]:
    urls = config.URLS

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
