"""
Filename: setup.py
Author: William Bowley
Version: 1.4.1
Date: 2025-10-13

Description:
    Install script for blueshark v1.4.1 framework
"""

from setuptools import setup, find_packages

setup(
    name='blueshark',
    version='1.4.1',
    description=(
        'Modular FEMM-based linear and tubular motor simulation framework'
    ),
    author='William Bowley',
    author_email='wgrantbowley@gmail.com',
    packages=find_packages(include=["blueshark", "blueshark.*"]),
    install_requires=[
        'PyYAML',
        'pyfemm',
        'matplotlib'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
    ],
    python_requires='>=3.8',
    include_package_data=True,
    package_data={
        "blueshark.library": [
            "material.toml"
        ],
        "blueshark.models": [
            "**/*.yaml"
        ]
    },
)
