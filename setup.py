from setuptools import setup, find_packages

setup(
    name="committy",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "gitpython>=3.1.30",
        "llama-index>=0.8.0",
        "click>=8.1.8",
        "rich>=12.0.0",
        "requests>=2.28.0",
        "PyYAML>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "committy=committy.cli.main:main",
        ],
    },
    python_requires=">=3.10",
)