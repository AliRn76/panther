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
        'redis>=4.5.1',
        'pymongo>=4.3.3',
        'python-jose>=3.3.0',
        'bpython>=0.24',
    ]
}

setup(
    name='panther',
    version=VERSION,
    python_requires='>=3.11',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    keywords='fast friendly web framework',
    url='https://github.com/alirn76/panther',
    description='Fast & Friendly Python Web Framework',
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': ['panther=panther.cli.main:start'],
    },
    package_data={
        'panther': ['cli/*'],
    },
    install_requires=[
        'uvicorn[standard]',
        'pydantic>=1.10.5',
        'tinydb>=4.7.1',
        'orjson>=3.8.6',
        'rich>=13.3.1',
    ],
    extras_require=EXTRAS_REQUIRE,
)
