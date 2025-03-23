from setuptools import setup, find_packages

setup(
    name="committy",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "gitpython",
        "llama-index",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "committy=committy.cli.main:main",
        ],
    },
    python_requires=">=3.10",
)
