#!/usr/bin/env python3

from setuptools import setup

packages = [
    "hackathonbaobab2021",
    "hackathonbaobab2021.core",
    "hackathonbaobab2021.solver",
    "hackathonbaobab2021.execution",
    "hackathonbaobab2021.schemas",
    "hackathonbaobab2021.tests",
]

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = ["pytups", "click", "pandas", "orloge", "cornflow_client"]

extras_require = {
    "solvers": ["pyomo", "ortools"],
}

kwargs = {
    "name": "hackathonbaobab2021",
    "version": "0.1.0",
    "packages": packages,
    "description": "Hackathon 2021 at baobab soluciones",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "Franco Peschiera",
    "maintainer": "Franco Peschiera",
    "author_email": "pchtsp@gmail.com",
    "maintainer_email": "pchtsp@gmail.com",
    "install_requires": install_requires,
    "extras_require": extras_require,
    "url": "https://github.com/baobabsoluciones/hackathonbaobab2021",
    "download_url": "https://github.com/baobabsoluciones/hackathonbaobab2021/archive/main.zip",
    "keywords": "math hackathon pulp ortools pyomo",
    "include_package_data": True,
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
}

setup(**kwargs)
