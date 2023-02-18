from runpy import run_path
from typing import Callable
import re

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


def check_path(path):
    if not re.match(r"^(()|([a-zA-Z\-\d]+)|(<[a-zA-Z]+>))$", path):
        raise TypeError(f"{path} is not Valid")
    return path


def collect_urls(urls):
    from panther.logger import logger
    collected_url = {}

    for url, endpoint in urls.items():  # TODO: parse /some/thing/: func to dict
        url = check_path(url)
        if endpoint is ...:
            logger.error(f"URL Can't Point To Ellipsis. ('{url}' -> ...)")
        if endpoint is None:
            logger.error(f"URL Can't Point To None. ('{url}' -> None)")
        if isinstance(endpoint, dict):
            collected_url[url] = collect_urls(endpoint)
        else:
            collected_url[url] = endpoint
    return collected_url


def find_endpoint(path: str) -> Callable | None:
    if location := path.find('?') != -1:
        path = path[:location]
    paths = path.split('/')
    paths.pop(0)
    sub = config['urls']
    for split_path in paths:
        sub = sub.get(split_path)
        if callable(sub):
            return sub
        elif isinstance(sub, dict):
            continue
        else:
            return None
