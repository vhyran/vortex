#!/usr/bin/env python3
"""
Setup script for Vortex: A Lightweight MySQL Client-Compatible Database in Python.

This script manages the packaging and distribution of Vortex for installation via pip.
"""

from setuptools import setup, find_packages
import pathlib

# Define project root directory
PROJECT_ROOT = pathlib.Path(__file__).parent


def read_file(filename):
    """Read a file and return its contents."""
    try:
        with open(PROJECT_ROOT / filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "File not found"


# Read long description from README.md
long_description = read_file("README.md")

# Package configuration
setup(
    # Basic package information
    name="vortex-db",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Metadata
    description=(
        "A lightweight, MySQL-compatible database implemented in pure Python, "
        "designed for embedded use and flexible data management."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="vhyran",
    author_email="yasouo@proton.me",
    url="https://github.com/vhyran/vortex",
    license="MIT",
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # Requirements
    python_requires=">=3.8, <4",
    install_requires=[
        "sqlparse>=0.4.4",
        "anyio>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "pytest-cov>=4.0",
        ],
        "docs": [
            "sphinx>=6.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    # Package data and configuration
    include_package_data=True,
    package_data={
        "": ["py.typed"],  # Changed from "vortex" to "" since it's flat
    },
    # Keywords for searchability
    keywords=[
        "mysql",
        "database",
        "sql",
        "embedded",
        "lightweight",
        "python",
        "data-management",
    ],
    # Entry points
    entry_points={
        "console_scripts": [
            "vortex=vortex:main",  # Assuming main() is in src/vortex.py
        ]
    },
    # Additional options
    zip_safe=False,
    platforms=["any"],
)

if __name__ == "__main__":
    setup()
