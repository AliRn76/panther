import re
import sys

from setuptools import setup


def panther_version() -> str:
    with open('panther/__init__.py') as f:
        return re.search('__version__ = [\'"]([^\'"]+)[\'"]', f.read()).group(1)


VERSION = panther_version()
with open('README.md', encoding='utf-8') as file:
    DESCRIPTION = file.read()

INSTALL_REQUIRES = [
    'pantherdb~=2.3.0',
    'orjson~=3.9.15',
    'pydantic~=2.10.6',
    'rich~=13.9.4',
    'uvicorn~=0.34.0',
    'pytz~=2025.2',
    'Jinja2~=3.1',
    'simple-ulid~=1.0.0',
]
if sys.version_info <= (3, 12):
    INSTALL_REQUIRES.append('httptools~=0.6.4')

EXTRAS_REQUIRE = {
    'full': [
        'redis==5.2.1',
        'motor~=3.7.0',
        'ipython~=9.0.2',
        'python-jose~=3.4.0',
        'ruff~=0.11.2',
        'websockets~=15.0.1',
        'cryptography~=44.0.2',
        'watchfiles~=1.0.4',
    ],
    'dev': ['ruff~=0.11.2', 'pytest~=8.3.5'],
}

setup(
    name='panther',
    version=VERSION,
    python_requires='>=3.10',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    url='https://github.com/alirn76/panther',
    description='Fast & Friendly, Web Framework For Building Async APIs',
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    include_package_data=True,
    license='BSD-3-Clause license',
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    entry_points={
        'console_scripts': ['panther=panther.cli.main:start'],
    },
    package_data={
        'panther': ['cli/*', 'panel/templates/*', 'openapi/templates/*'],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
)
