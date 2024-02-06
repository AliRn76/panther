import logging
import re
from collections import Counter
from collections.abc import Callable, Mapping, MutableMapping
from copy import deepcopy
from functools import partial, reduce

from panther.configs import config


logger = logging.getLogger('panther')


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
        if _is_url_endpoint_valid(url=url, endpoint=data):
            yield url, data


def _is_url_endpoint_valid(url: str, endpoint: Callable) -> bool:
    if endpoint is ...:
        logger.error(f"URL Can't Point To Ellipsis. ('{url}' -> ...)")
    elif endpoint is None:
        logger.error(f"URL Can't Point To None. ('{url}' -> None)")
    elif url and not re.match(r'^[a-zA-Z<>0-9_/-]+$', url):
        logger.error(f"URL Is Not Valid. --> '{url}'")
    else:
        return True
    return False


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
    return _merge(*urls_list) if urls_list else {}


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


class Router:
    ENDPOINT_NOT_FOUND = (None, '')
    found_path: str
    last_path: bool

    @classmethod
    def _add_part(cls, part: str):
        cls.found_path += f'{part}/'

    @classmethod
    def _check_callable(cls, endpoint: Callable, part: str) -> tuple[Callable | None, str]:
        if cls.last_path:
            cls._add_part(part=part)
            return endpoint, cls.found_path
        return cls.ENDPOINT_NOT_FOUND

    @classmethod
    def _check_dict(cls, sub_urls: dict) -> tuple[Callable | None, str]:
        if callable(endpoint := sub_urls.get('')):
            return endpoint, cls.found_path
        return cls.ENDPOINT_NOT_FOUND

    @classmethod
    def find_endpoint(cls, path: str) -> tuple[Callable | None, str]:
        urls = config['urls']

        # 'user/list/?name=ali' --> 'user/list/' --> 'user/list' --> ['user', 'list']
        parts = path.split('?')[0].strip('/').split('/')

        cls.found_path = ''
        for i, part in enumerate(parts):
            cls.last_path = bool((i + 1) == len(parts))

            match urls.get(part):
                case endpoint if callable(endpoint):
                    return cls._check_callable(endpoint=endpoint, part=part)

                case dict(sub_urls):
                    cls._add_part(part=part)
                    if cls.last_path:
                        return cls._check_dict(sub_urls=sub_urls)
                    urls = sub_urls
                    continue

                case _:
                    for key, value in urls.items():
                        if key.startswith('<'):
                            match value:
                                case endpoint if callable(endpoint):
                                    return cls._check_callable(endpoint=endpoint, part=key)

                                case dict(sub_urls):
                                    cls._add_part(part=key)
                                    if cls.last_path:
                                        return cls._check_dict(sub_urls=sub_urls)
                                    urls = sub_urls
                                    break

                                case _:
                                    return cls.ENDPOINT_NOT_FOUND
                    else:
                        return cls.ENDPOINT_NOT_FOUND
        return cls.ENDPOINT_NOT_FOUND


def collect_path_variables(request_path: str, found_path: str) -> dict:
    found_path = found_path.removesuffix('/').removeprefix('/')
    request_path = request_path.removesuffix('/').removeprefix('/')
    path_variables = {}
    for f_path, r_path in zip(found_path.split('/'), request_path.split('/')):
        if f_path.startswith('<'):
            path_variables[f_path[1:-1]] = r_path
    return path_variables
