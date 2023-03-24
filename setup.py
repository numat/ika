"""Python driver and command line tool for IKA instruments."""
from sys import version_info

from setuptools import setup

if version_info < (3, 7):
    raise ImportError("This module requires Python >=3.7.")

with open('README.md', 'r') as in_file:
    long_description = in_file.read()

setup(
    name="ika-control",
    version="0.2.0",
    description="Python driver for IKA instruments.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/alexrudd2/ika/",
    author="Alex Ruddick",
    author_email="a.ruddick@numat-tech.com",
    packages=['ika'],
    install_requires=['pyserial'],
    extras_require={
        'test': [
            'pytest>=6,<8',
            'pytest-cov>=4,<5',
            'pytest-asyncio==0.*',
            'pytest-xdist==3.*',
            'flake8==6.*',
            'flake8-docstrings==1.*',
            'mypy==1.0.1',
        ],
    },
    entry_points={
        'console_scripts': [('ika = ika:command_line')]
    },
    license='GPLv3',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
    ],
)
