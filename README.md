# autorename

This script renames the files in a directory tree to a new name based on each file's modification time and md5 hash for recognized extensions.

![build status](https://github.com/woitaszek/autorename/actions/workflows/python-app.yml/badge.svg)

## Synopsis

Do you have a directory tree full of files that you clipped from the Internet that you want to keep, but they all have nonsensical and unhelpful names that makes the whole thing turn into a big unorganized pile? If so, this script is for you!

This script turns an unwieldy tree of bizarrely-named files into a tree with files that at least sort in the order they were created. It renames files to a name based on the file's modification time and md5 hash, with a few configurable options. It also deletes all those pesky `.DS_Store` files that macOS likes to create.

Features:

- Renames files to a name based on the file's modification time and md5 hash. For example:

  ```text
  Copy of IMAGE-1 (2).JPG -> 2020-01-01-98ecf8427e.jpg
  ```

  The first 10 characters of the md5 hash are used to avoid collisions:

  ```text
  d41d8cd98f00b204e9800998ecf8427e
  ^^^^^^^^^^......................
  ```

  (The front of the hash is used just like git, as opposed to the back of the hash like GPG.)

- Supports naming files with **day** or **minute** granularity in a directory (and its subdirectories) via the placement of `.autorename.ini` configuration files.

- Recognizes specific file extensions and renames them accordingly. Skips the rest.

- Can be run in a dry-run mode to see what it would do without actually doing anything.

- Skips files that start with prefixes that look like dates and words, such as `2020-01-01 My Picture.jpg` or `2020-01-XX My Picture.jpg`. This way, if you had renamed files to get them "close enough" to date ordering but with descriptive file names, they won't get renamed.

- Deletes all those `.DS_Store` files that macOS likes to create.

## In-Place Configuration

The script can be configured to name files with **day** or **minute** granularity in a directory (and its subdirectories) via the placement of `.autorename.ini` configuration files. The script will look for these files in the directory tree, starting from the directory containing the file to be renamed and going up to the root directory, stopping at the first `.autorename.ini` file it finds.

The configuration file is a simple INI file with the following format:

```ini
[autorename]
prefix_timestamp = <day | minute>
```

The `prefix_timestamp` option can be set to either `day` or `minute`. If this option is not set, the script will default to `day` granularity.

| Option | Example                        |
|--------|--------------------------------|
| day    | 2020-01-01-98ecf8427e.jpg      |
| minute | 2020-01-01-1234-98ecf8427e.jpg |

> 💡 **Note:** In the future, it would be great to support the configuration of arbitrary prefix format configurations, but that's a real pain to test at runtime to prevent a misconfiguration from renaming files in a way that could be destructive.

## Installation

### For exploration

No installation is necessary. Simply clone the repository and run with uv directly:

```bash
uv run /path/to/autorename/autorename.py [--commit] <files | directories...>
```

### For development

Clone the repository and install with uv:

```bash
uv sync --extra dev
```

### For system-wide usage

Install the package using pip:

```bash
pip install .
```

## Usage

Invoke the command with directory names or file names:

```bash
autorename [--commit] <files | directories...>
```

For example:

First, run in dry-run mode (default) to see what it would do:

```bash
autorename ~/Clippings
```

Then, run with `--commit` to actually rename the files:

```bash
autorename --commit ~/Clippings
```

### Development Usage

When developing, use `uv run` to execute the command:

```bash
uv run autorename ~/Clippings
```
