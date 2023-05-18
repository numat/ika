"""Python driver and command line tool for IKA instruments."""
from setuptools import setup

with open('README.md') as in_file:
    long_description = in_file.read()

setup(
    name="ika-control",
    version="0.2.0",
    description="Python driver for IKA instruments.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/numat/ika/",
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
            'ruff==0.0.269',
            'mypy==1.3.0',
            'types-pyserial==3.5.0.8'
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
