import os
import re

from setuptools import setup


def panther_version() -> str:
    with open(os.path.join('panther/__init__.py')) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


VERSION = panther_version()
DESCRIPTION = open('README.md').read()

EXTRAS_REQUIRE = {
    'full': [
        'pymongo>=4.3.3',
    ]
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
    license='MIT',
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
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
        'bpython~=0.24',
        'bson~=0.5',
        'httptools~=0.5',
        'pantherdb~=1.2',
        'pydantic~=2.0',
        'redis~=4.5',
        'rich~=13.3',
        'uvicorn~=0.21',
        'watchfiles~=0.18',
        'python-jose~=3.3',
    ],
    extras_require=EXTRAS_REQUIRE,
)
