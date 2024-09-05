# setup.py

from setuptools import setup, find_packages

setup(
    name='cliapp',
    version='0.1.0',
    description='A sample Python project with CLI and importable module',
    author='Ivan Cenov',
    author_email='i_cenov@botevgrad.com',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'cliapp=cliapp.cli:main',
        ],
    },
)
