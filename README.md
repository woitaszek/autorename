# autorename

[![CI](https://github.com/woitaszek/autorename/actions/workflows/ci.yml/badge.svg)](https://github.com/woitaszek/autorename/actions/workflows/ci.yml)

This script renames the files in a directory tree to a new name based on each file's modification time and md5 hash for recognized extensions.

## Synopsis

Do you have a directory tree full of files that you clipped from the Internet that you want to keep, but they all have nonsensical and unhelpful names that makes the whole thing turn into a big unorganized pile? If so, this script is for you!

This script turns an unwieldy tree of bizarrely-named files into a tree with files that at least sort in the order they were created. It renames files to a name based on the file's modification time and md5 hash, with a few configurable options. It also deletes all those pesky `.DS_Store` files that macOS likes to create.

Features:

- Recognizes specific file extensions and renames them accordingly. Skips the rest.

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

- Supports naming files with **day** or **minute** granularity in a directory (and its subdirectories) via the placement of `autorename.ini` or `.autorename.ini` configuration files.

  The `prefix_timestamp` option can be set to either `day` or `minute`. If this option is not set, the script will default to `day` granularity.

  | Option | Example                        |
  | ------ | ------------------------------ |
  | day    | 2020-01-01-98ecf8427e.jpg      |
  | minute | 2020-01-01-1234-98ecf8427e.jpg |

- Skips files that start with valid prefixes that look like dates and words. The format depends on the directory configuration:
  - With **day** granularity (default), skips files like `2020-01-01 My Picture.jpg` or `2020-01-XX My Picture.jpg`.
  - With **minute** granularity, skips files like `2020-01-01-1234 My Picture.jpg` or `2020-01-XX-12XX My Picture.jpg`.

  This way, if you had renamed files to get them "close enough" to date ordering but with descriptive file names, they won't get renamed.

- Supports **skip_regex** patterns in the configuration file to skip files whose stems match user-defined regular expressions. Useful for preserving files from specific sources (e.g., Tumblr, Facebook) that have recognizable naming patterns.

- Deletes all those `.DS_Store` files that macOS likes to create.

- Can be run in a dry-run mode to see what it would do without actually doing anything.

## In-Place Configuration

The script can be configured to name files with **day** or **minute** granularity in a directory (and its subdirectories) via the placement of configuration files. The script recognizes two file names:

- `autorename.ini`
- `.autorename.ini`

If a directory contains **both** files, the script raises an error. Remove one to resolve the conflict.

The script searches for these files in the directory tree, starting from the directory containing the file to be renamed and going up to the root directory, stopping at the first directory that contains either configuration file.

The configuration file is a simple INI file with the following format:

```ini
[autorename]
prefix_timestamp = <day | minute>
skip_regex =
    ^pattern1-
    ^pattern2_
```

### prefix_timestamp

Controls the granularity of the timestamp prefix in renamed files. See the table above for examples.

### skip_regex

An optional multi-line value listing regular expressions (one per line). If any pattern matches a file's **stem** (the filename without its extension), that file is skipped and not renamed.

Patterns are matched using `re.search()`, so anchors like `^` and `$` work as expected. Standard regex metacharacters (e.g., `\s`, `\d`, `.`) are supported.

Example: to skip files whose stems start with `tumblr_` or `reblogme-`, or stems that are exactly 15 characters long:

```ini
[autorename]
prefix_timestamp = minute
skip_regex =
    ^tumblr_
    ^reblogme-
    ^.{15}$
```

A safety check validates that the patterns are not overly broad. If the patterns match **all** built-in sample stems, the configuration is rejected with an error.

> **Note:** In the future, it would be great to support the configuration of arbitrary prefix format configurations, but that's a real pain to test at runtime to prevent a misconfiguration from renaming files in a way that could be destructive.

## Installation

### For exploration

No installation is necessary. Simply clone the repository and run with uv directly:

```bash
uv run /path/to/autorename/autorename.py [--commit] <files | directories...>
```

### For development

Clone the repository and install with uv:

```bash
uv sync
```

### For system-wide usage

Install the package using uv:

```bash
uv tool install .
```

### For packaging and distribution

To create a distributable package that can be copied to another computer:

1. Build the package:

   ```bash
   uv build
   ```

2. This creates distribution files in the `dist/` directory:
   - `autorename-0.1.0-py3-none-any.whl` (wheel file - recommended)
   - `autorename-0.1.0.tar.gz` (source distribution)

3. Copy the `.whl` file to another computer and install it:

   ```bash
   uv tool install autorename-0.1.0-py3-none-any.whl
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
