from setuptools import setup, find_packages

setup(
    name="devnote",
    version="1.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "devnote = backend.cli:main",
        ],
    },
)
