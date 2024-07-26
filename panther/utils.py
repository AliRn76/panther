import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import ClassVar

import pytz

from panther.configs import config

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
        raise ValueError(f'"{env_file}" is not a file.') from None

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
    """
    Example:
        >>> round_datetime(datetime(2024, 7, 15, 13, 22, 11, 562159), timedelta(days=2))
        datetime.datetime(2024, 7, 16, 0, 0)

        >>> round_datetime(datetime(2024, 7, 16, 13, 22, 11, 562159), timedelta(days=2))
        datetime.datetime(2024, 7, 16, 0, 0)

        >>> round_datetime(datetime(2024, 7, 17, 13, 22, 11, 562159), timedelta(days=2))
        datetime.datetime(2024, 7, 18, 0, 0)

        >>> round_datetime(datetime(2024, 7, 18, 13, 22, 11, 562159), timedelta(days=2))
        datetime.datetime(2024, 7, 18, 0, 0)
    """
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
    return derived_key


class ULID:
    """https://github.com/ulid/spec"""

    crockford_base32_characters = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'

    @classmethod
    def new(cls):
        current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        epoch_bits = '{0:050b}'.format(current_timestamp)
        random_bits = '{0:080b}'.format(secrets.randbits(80))
        bits = epoch_bits + random_bits
        return cls._generate(bits)

    @classmethod
    def _generate(cls, bits: str) -> str:
        return ''.join(
            cls.crockford_base32_characters[int(bits[i: i + 5], base=2)]
            for i in range(0, 130, 5)
        )


def timezone_now():
    tz = pytz.timezone(config.TIMEZONE)
    return datetime.now(tz=tz)
