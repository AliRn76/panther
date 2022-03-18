from setuptools import setup, find_packages

# from panther import __version__

setup(
    name='panther',
    version='0.1.4',
    python_requires='>=3.10',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    keywords='fast friendly web framework',
    url='https://github.com/alirn76/panther',
    description='Fast, Friendly Python Web Framework',
    long_description='file: README.md',
    include_package_data=True,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Framework :: Django',
    ],
    packages=find_packages(where='.', exclude=(), include=('*',)),
    # package_dir={'': 'panther'},
    # install_requires=[],
    # include_dirs=[],
)





