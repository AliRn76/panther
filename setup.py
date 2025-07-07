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
    'pantherdb~=2.3.1',
    'orjson~=3.10.18',
    'pydantic~=2.11.7',
    'rich~=14.0.0',
    'uvicorn~=0.35.0',
    'pytz~=2025.2',
    'Jinja2~=3.1.6',
    'simple-ulid~=1.0.0',
]
if sys.version_info <= (3, 12):
    INSTALL_REQUIRES.append('httptools~=0.6.4')

EXTRAS_REQUIRE = {
    'full': [
        'redis==6.2.0',
        'motor~=3.7.1',
        'ipython~=9.4.0',
        'python-jose~=3.5.0',
        'ruff~=0.12.2',
        'websockets~=15.0.1',
        'cryptography~=45.0.5',
        'watchfiles~=1.1.0',
    ],
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
