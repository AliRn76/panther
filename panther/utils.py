import os
import random
import string
from pathlib import Path
from panther.logger import logger


def load_env(env_file: str | Path, /) -> dict[str, str]:
    variables = dict()

    if env_file is None or not os.path.isfile(env_file):
        logger.critical(f'"{env_file}" is not valid file for load_env()')
        return variables

    with open(env_file) as file:
        for line in file.readlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                variables[key] = value
    return variables


def generate_secret_key(length: int = 10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

