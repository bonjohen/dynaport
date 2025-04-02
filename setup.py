from setuptools import setup, find_packages

setup(
    name="dynaport",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "dynaport=dynaport.cli:main",
        ],
    },
    python_requires=">=3.9",
    author="DynaPort Team",
    author_email="info@dynaport.example.com",
    description="Dynamic port management for Flask applications",
    long_description=open("readme.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/dynaport",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
