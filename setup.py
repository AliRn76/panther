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
        'python-jose>=3.3.0',
        'pymongo>=4.3.3',
    ]
}

setup(
    name='panther',
    version=VERSION,
    python_requires='>=3.11',
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
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': ['panther=panther.cli.main:start'],
    },
    package_data={
        'panther': ['cli/*'],
    },
    install_requires=[
        'bpython>=0.24',
        'bson>=0.5.10',
        'httptools>=0.5.0',
        'pantherdb>=1.2.2',
        'pydantic>=1.10.7',
        'redis>=4.5.3',
        'rich>=13.3.2',
        'uvicorn>=0.21.1',
        'uvloop>=0.17.0',
        'watchfiles>=0.18.1',
    ],
    extras_require=EXTRAS_REQUIRE,
)
