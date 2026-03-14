"""
Filename: setup.py

Description:
    Installation script via setuptools:
    
    Run "pip install -e ."
"""

from setuptools import setup, find_packages

setup(
    name='pyfea',
    version='0.1.0',
    description=(
        'Solver-Adaptor Engine for Multi-Physics Problems'
    ),
    author='William Bowley',
    author_email='wgrantbowley@gmail.com',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "pyfea": ["library/*.ut", "library/*.uiv"],
    },
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