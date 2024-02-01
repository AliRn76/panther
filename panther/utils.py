import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger('panther')

URANDOM_SIZE = 16


class Singleton(object):
    _instances: ClassVar[dict] = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]


def load_env(env_file: str | Path, /) -> dict[str, str]:
    variables = {}

    if env_file is None or not Path(env_file).is_file():
        logger.critical(f'"{env_file}" is not valid file for load_env()')
        return variables

    with open(env_file) as file:
        for line in file.readlines():
            striped_line = line.strip()
            if not striped_line.startswith('#') and '=' in striped_line:
                key, value = striped_line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                variables[key] = value

                # Load them as system environment variable
                os.environ[key] = value
    return variables


def generate_secret_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def round_datetime(dt: datetime, delta: timedelta):
    return datetime.min + round((dt - datetime.min) / delta) * delta


def generate_hash_value_from_string(string_value: str, /) -> str:
    # The point of this method is for maintenance, if we want to change
    # the hash algorithm in the future, it will be easy.
    return hashlib.sha256(string_value.encode('utf-8')).hexdigest()


def scrypt(password: str, salt: bytes, digest: bool = False) -> str | bytes:
    """
    n: CPU/memory cost parameter – Must be a power of 2 (e.g. 1024)
    r: Block size parameter, which fine-tunes sequential memory read size and performance. (8 is commonly used)
    p: Parallelization parameter. (1 .. 232-1 * hLen/MFlen)
    dk_len: Desired key length in bytes (
        Intended output length in octets of the derived key; a positive integer satisfying dkLen ≤ (232− 1) * hLen.)
    h_len: The length in octets of the hash function (32 for SHA256).
    mf_len: The length in octets of the output of the mixing function (SMix below). Defined as r * 128 in RFC7914.
    """
    n = 2 ** 14  # 16384
    r = 8
    p = 10
    dk_len = 64

    derived_key = hashlib.scrypt(
        password=password.encode(),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=dk_len
    )
    if digest:

        return hashlib.md5(derived_key).hexdigest()
    else:
        return derived_key


def encrypt_password(password: str) -> str:
    salt = os.urandom(URANDOM_SIZE)
    derived_key = scrypt(password=password, salt=salt, digest=True)

    return f'{salt.hex()}{derived_key}'


def check_password(stored_password: str, new_password: str) -> bool:
    size = URANDOM_SIZE * 2
    salt = stored_password[:size]
    stored_hash = stored_password[size:]
    derived_key = scrypt(password=new_password, salt=bytes.fromhex(salt), digest=True)

    return derived_key == stored_hash
