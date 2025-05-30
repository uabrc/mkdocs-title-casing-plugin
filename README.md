![PyPI](https://img.shields.io/pypi/v/mkdocs-title-casing-plugin)
![PyPI - License](https://img.shields.io/pypi/l/mkdocs-title-casing-plugin)

# mkdocs-title-casing-plugin

A lightweight mkdocs plugin to add title casing to all mkdocs sections, pages, and links in the navigation and in HTML content. Uses [python-titlecase](https://github.com/ppannuto/python-titlecase) for formatting.

## Setup

Install the plugin using pip:

```bash
pip install git+https://github.com/uabrc/mkdocs-title-casing-plugin.git@stable
```

Include the plugin in `mkdocs.yml`. For example:

```yml
plugins:
  - search
  - title-casing:
    - capitalization_type: title (default) | first_letter
    - mode: warn (default) | fix
```

> If this is the first `plugins` entry that you are adding, you should probably also add `search` as this is enabled by default.

## Usage

When the plugin is enabled, all section and page titles will be converted to use Title Case. For example, `War and peace` becomes `War and Peace`.

### Configuration

- `capitalization_type` (string)
  - `title` - default - gives `War and Peace`.
  - `first_letter` - gives `War And Peace`.
- `mode` (string)
  - `warn` - default - produces warnings
  - `fix` - changes titles in HTML ouptut

#### Example mkdocs.yml

```yml
plugins:
  - search
  - title-casing:
      capitalization_type: title
      mode: warn
```
