import os
import re
from setuptools import setup, find_packages


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
    packages=find_packages(where='.', exclude=(), include=('*',)),
    # package_dir={'': 'panther'},
    # install_requires=[],
    # include_dirs=[],
)





