import re
from copy import deepcopy
from runpy import run_path
from typing import Callable
from collections import Counter
from typing import MutableMapping
from collections.abc import Mapping
from functools import reduce, partial


from panther.configs import config


def check_urls(urls: str | None) -> dict | None:
    from panther.logger import logger

    if urls is None:
        return logger.critical("configs.py Does Not Have 'URLs'")

    try:
        full_urls_path = config['base_dir'] / urls
        urls_dict = run_path(str(full_urls_path))['urls']
    except FileNotFoundError:
        return logger.critical("Couldn't Open 'URLs' Address.")
    except KeyError:
        return logger.critical("'URLs' Address Does Not Have 'urls'")
    if not isinstance(urls_dict, dict):
        return logger.critical("'urls' Of URLs Is Not dict.")
    return urls_dict


def collect_urls(pre_url: str, urls: dict, final: dict):
    from panther.logger import logger

    for url, endpoint in urls.items():
        if endpoint is ...:
            logger.error(f"URL Can't Point To Ellipsis. ('{pre_url}{url}' -> ...)")
        elif endpoint is None:
            logger.error(f"URL Can't Point To None. ('{pre_url}{url}' -> None)")
        elif url and not re.match(r'[a-zA-Z<>0-9_/-]', url):
            logger.error(f"URL Is Not Valid. --> '{pre_url}{url}'")
        else:
            if not url.endswith('/'):
                url = f'{url}/'
            if isinstance(endpoint, dict):
                if url != '/':
                    if pre_url:
                        pre_url = f'{pre_url}/{url}'
                    else:
                        pre_url = url
                collect_urls(pre_url, endpoint, final)
            else:
                final[f'{pre_url}{url}'] = endpoint

    return urls


def find_endpoint(path: str) -> tuple[Callable | None, str]:
    if (location := path.find('?')) != -1:
        path = path[:location]
    path = path.removesuffix('/').removeprefix('/')  # 'user/list'
    paths = path.split('/')  # ['user', 'list']
    paths_len = len(paths)
    sub = config['urls']
    # sub = {
    #     'user': {
    #         '<id>': <function users at 0x7f579d060220>,
    #         '': <function single_user at 0x7f579d060e00>
    #     }
    # }
    found_path = ''
    for i, split_path in enumerate(paths):
        last_path = bool((i + 1) == paths_len)
        found = sub.get(split_path)
        if last_path and callable(found):
            found_path += f'{split_path}/'
            return found, found_path
        if isinstance(found, dict):
            found_path += f'{split_path}/'
            if last_path and callable(endpoint := found.get('')):
                return endpoint, found_path

            sub = found
            continue

        # found = None
        # sub = {'<id>': <function return_list at 0x7f0757baff60>} (Example)
        _continue = False
        for key, value in sub.items():
            if key.startswith('<'):
                if last_path:
                    if callable(value):
                        found_path += f'{key}/'
                        return value, found_path
                    else:
                        return None, ''

                sub = value
                found_path += f'{key}/'
                _continue = True
                break

        if _continue:
            continue

    return None, ''


def is_recursive_merge(a, b):
    both_mapping = isinstance(a, Mapping) and isinstance(b, Mapping)
    both_counter = isinstance(a, Counter) and isinstance(b, Counter)
    return both_mapping and not both_counter


def deepmerge(dst, src):
    for key in src:
        if key in dst:
            if is_recursive_merge(dst[key], src[key]):
                deepmerge(dst[key], src[key])
            else:
                dst[key] = deepcopy(src[key])
        else:
            dst[key] = deepcopy(src[key])
    return dst


def merge(destination: MutableMapping, *sources) -> MutableMapping:
    """Credit to Travis Clarke --> https://github.com/clarketm/mergedeep"""
    return reduce(partial(deepmerge), sources, destination)


def finalize_urls(urls: dict):
    urls_list = list()
    for url, endpoint in urls.items():
        path = dict()
        for single_path in url.split('/')[:-1][::-1]:
            path = {single_path: path or endpoint}
        urls_list.append(path)
    return merge(*urls_list)
