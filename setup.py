"""Setup script for DynaPort."""

import os
from setuptools import setup, find_packages

# Read the long description from README.md
with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from dynaport/core/__init__.py
try:
    with open(os.path.join("dynaport", "core", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"\'')
                break
        else:
            version = "0.2.0"
except (FileNotFoundError, IOError):
    version = "0.2.0"

setup(
    name="dynaport",
    version=version,
    author="DynaPort Team",
    author_email="info@dynaport.example.com",
    description="Framework-agnostic dynamic port management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/dynaport",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "flask": ["flask>=2.0.0"],
        "django": ["django>=3.2.0"],
        "fastapi": ["fastapi>=0.68.0", "uvicorn>=0.15.0"],
        "all": [
            "flask>=2.0.0",
            "django>=3.2.0",
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "mypy>=0.812",
            "flake8>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dynaport=dynaport.core.cli:main",
        ],
    },
)
