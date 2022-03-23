from setuptools import setup, find_packages


setup(
    name='panther',
    version='0.1.7',
    python_requires='>=3.10',
    author='Ali RajabNezhad',
    author_email='alirn76@yahoo.com',
    keywords='fast friendly web framework',
    url='https://github.com/alirn76/panther',
    description='Fast, Friendly Python Web Framework',
    long_description=open('README.md').read(),
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





