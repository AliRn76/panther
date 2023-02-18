from runpy import run_path

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


def collect_urls(pre_url: str, urls: dict):
    from panther.logger import logger

    for url, endpoint in urls.items():
        if endpoint is ...:
            logger.error(f"URL Can't Point To Ellipsis. ('{pre_url}{url}' -> ...)")
        if endpoint is None:
            logger.error(f"URL Can't Point To None. ('{pre_url}{url}' -> None)")

        if isinstance(endpoint, dict):
            collect_urls(f'{pre_url}/{url}', endpoint)
        else:
            config['urls'][f'{pre_url}{url}'] = endpoint
    return urls


def find_endpoint(path: str):
    for url in config['urls']:
        if path == url:
            return config['urls'][url]
