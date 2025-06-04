from pathlib import Path

from setuptools import find_packages, setup

with Path("README.md").open("r") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="mkdocs-title-casing-plugin",
    description=(
        "A lightweight mkdocs plugin to add title casing to all mkdocs"
        " sections, pages, and links."
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords="mkdocs title case casing plugin",
    url="https://github.com/uabrc/mkdocs-title-casing-plugin",
    author="wwarriner",
    version="1.2.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "mkdocs>=1.5",
        "titlecase>=2.3",
    ],
    license="GPLv3",
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "mkdocs.plugins": [
            "title-casing = mkdocs_title_casing_plugin.plugin:TitleCasingPlugin",
        ],
    },
)
