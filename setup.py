import re
import sys

from setuptools import setup


def panther_version() -> str:
    with open('panther/__init__.py') as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


VERSION = panther_version()
with open('README.md', encoding='utf-8') as file:
    DESCRIPTION = file.read()

INSTALL_REQUIRES = [
    'pantherdb~=2.1.0',
    'pydantic~=2.8.2',
    'rich~=13.7.1',
    'uvicorn~=0.27.1',
    'pytz~=2024.1',
    'Jinja2~=3.1',
]
if sys.version_info <= (3, 12):
    INSTALL_REQUIRES.append('httptools~=0.6.1')

EXTRAS_REQUIRE = {
    'full': [
        'redis==5.0.1',
        'motor~=3.5.0',
        'bpython~=0.24',
        'python-jose~=3.3.0',
        'ruff~=0.1.9',
        'websockets~=12.0',
        'cryptography~=42.0.8',
        'watchfiles~=0.21.0',
    ],
    'dev': [
        'ruff~=0.1.9',
        'pytest~=8.3.3'
    ]
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
        'panther': ['cli/*'],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
)
