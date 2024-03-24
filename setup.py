import re

from setuptools import setup


def panther_version() -> str:
    with open('panther/__init__.py') as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


VERSION = panther_version()
with open('README.md', encoding='utf-8') as file:
    DESCRIPTION = file.read()

EXTRAS_REQUIRE = {
    'full': [
        'redis==5.0.1',
        'motor~=3.3',
        'bpython~=0.24',
        'ruff~=0.1.9',
        'python-jose~=3.3',
        'websockets~=12.0',
        'cryptography~=42.0',
        'watchfiles~=0.21.0',
    ],
}

setup(
    name='panther',
    version=VERSION,
    python_requires='>=3.10',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    url='https://github.com/alirn76/panther',
    description='Fast &  Friendly, Web Framework For Building Async APIs',
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    include_package_data=True,
    license='BSD-3-Clause license',
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    entry_points={
        'console_scripts': ['panther=panther.cli.main:start'],
    },
    package_data={
        'panther': ['cli/*'],
    },
    install_requires=[
        'httptools~=0.6',
        'pantherdb==2.1.0',
        'pydantic~=2.6',
        'rich~=13.7',
        'uvicorn~=0.27',
        'pytz~=2024.1',
    ],
    extras_require=EXTRAS_REQUIRE,
)
