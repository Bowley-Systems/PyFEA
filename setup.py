"""
Filename: setup.py
Author: William Bowley
Version: 1.5.0
Date: 2025-10-13

Description:
    Install script for fea v1.5.0 framework
"""

from setuptools import setup, find_packages

setup(
    name='pyfea',
    version='1.5.0',
    description=(
        'Solver-Adaptor Engine for Multi-Physics Problems'
    ),
    author='William Bowley',
    author_email='wgrantbowley@gmail.com',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'PyYAML',
        'pyfemm',
        'matplotlib',
        'bayesian-optimization'
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
)
