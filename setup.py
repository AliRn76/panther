import os
import re
from setuptools import setup


def panther_version() -> str:
    with open(os.path.join('panther/__init__.py')) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


_version = panther_version()
_long_description = open('README.md').read()

setup(
    name='panther',
    version=_version,
    python_requires='>=3.10',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    keywords='fast friendly web framework',
    url='https://github.com/alirn76/panther',
    description='Fast, Friendly Python Web Framework',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
    ],
    entry_points={
        'console_scripts': ['panther=panther.cli.main:start'],
    },
    package_data={
        'panther': ['cli/*']
    },
    install_requires=[
        'uvicorn[standard]',
        'orjson>=3.7.12',
        'pydantic>=1.9.2',
        'sqlalchemy>=1.4.20',
        'redis>=4.3.4',
        'alembic>=1.8.1',
        'pymongo>=4.2.0',
    ],
)
