# setup.py

from setuptools import setup, find_packages

setup(
    name='cliapp',
    version='0.1.0',
    description='A sample Python project with CLI and importable module',
    author='Ivan Cenov',
    author_email='i_cenov@botevgrad.com',
    url='https://github.com/jwalkerbg/cliapp',  # Project's GitHub or website
    packages=find_packages(),
    install_requires=[
        'jsonschema'  # Add your dependencies here
    ],
    entry_points={
        'console_scripts': [
            'cliapp=cliapp.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Update with your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Specify the minimum Python version
)
