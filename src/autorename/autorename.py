#!/usr/bin/env python3

# Python imports
import argparse
import datetime
import logging
import hashlib
import os
import re
import configparser
import zoneinfo

from typing import Literal, TypedDict

# Timezone configuration
# This ensures consistent timestamp handling across different systems
TIMEZONE = zoneinfo.ZoneInfo("America/Los_Angeles")  # Pacific Time


class DirectoryConfig(TypedDict):
    """Configuration for autorename directory settings."""

    prefix_timestamp: Literal["minute", "day"]


# Extensions to be renamed
EXTENSIONS: list[str] = [
    "jpg",
    "jpeg",
    "gif",
    "m4a",
    "mov",
    "mp4",
    "pdf",
    "png",
    "webp",
    "heic",
    "pptx",
    "docx",
    "xlsx",
]

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(name)-24.23s %(funcName)-25s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


# Regular expression for detecting manually-named files that should not
# be renamed. We allow characters other than digits in the day and minute
# fields.
# - Day granularity: yyyy-mm-XX followed by space and non-space character(s).
# - Minute granularity: yyyy-mm-dd-XXXX followed by space and non-space
#   character(s).
re_prefix_day = re.compile(
    r"""
       \d\d\d\d-\d\d-\S\S[ ]\S+
    """,
    re.VERBOSE,
)
re_prefix_minute = re.compile(
    r"""
         \d\d\d\d-\d\d-\S\S-\S\S\S\S[ ]\S+
    """,
    re.VERBOSE,
)

# ----------------------------------------------------------------------
# Directory configuration
# ----------------------------------------------------------------------

# We provide the ability to configure the autorename script using a
# configuration file in the hierarchy containing the target directory.
# For each path, we look for a file called .autorename.ini. If it exists,
# we read the configuration from that file and cache it for quick retrievals.

cached_directory_config: dict[str, DirectoryConfig | None] = {}


def get_directory_config(target_dir: str) -> DirectoryConfig | None:
    """Get the directory configuration for the autorename script.

    Searches for a .autorename.ini file in the specified directory and its
    parent directories. The configuration file should contain an [autorename]
    section with a prefix_timestamp option set to either 'minute' or 'day'.

    Args:
        target_dir: The directory path to search for configuration.

    Returns:
        A DirectoryConfig dict with configuration values, or None if no
        configuration file is found or the directory doesn't exist.

    Raises:
        ValueError: If the configuration file is missing required sections,
            options, or has invalid values.
    """

    # If the directory configuration has already been read, return it
    if target_dir in cached_directory_config:
        return cached_directory_config[target_dir]

    # Check if the target directory exists
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        logger.warning(
            f"Target directory '{target_dir}' does not exist or is not a directory"
        )
        return None

    # Recurse into parent directories to find the configuration file
    current_dir = target_dir
    found_config_file = None
    while current_dir != "/":
        config_file = os.path.join(current_dir, ".autorename.ini")
        if os.path.exists(config_file):
            found_config_file = config_file
            break
        current_dir = os.path.dirname(current_dir)

    # If no configuration file was found, return None
    if found_config_file is None:
        cached_directory_config[target_dir] = None
        return None

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read(found_config_file)

    # Check if the configuration file has the expected section and options
    if "autorename" not in config:
        raise ValueError(
            f"Configuration file '{found_config_file}' does not have the "
            f"'autorename' section"
        )
    if "prefix_timestamp" not in config["autorename"]:
        raise ValueError(
            f"Configuration file '{found_config_file}' does not have the "
            f"'prefix_timestamp' option"
        )
    if config["autorename"]["prefix_timestamp"] not in ["minute", "day"]:
        raise ValueError(
            f"Configuration file '{found_config_file}' has invalid "
            f"'prefix_timestamp' option: "
            f"{config['autorename']['prefix_timestamp']}"
        )

    # Store the configuration in the cache
    prefix_value = config["autorename"]["prefix_timestamp"]
    directory_config: DirectoryConfig = {
        "prefix_timestamp": prefix_value  # type: ignore[typeddict-item]
    }
    cached_directory_config[target_dir] = directory_config

    return directory_config


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def generate_filename(path: str, filename: str) -> str | None:
    """Generate the new desired filename for the specified file.

    Creates a new filename in the format 'YYYY-MM-DD-HASH.ext' or
    'YYYY-MM-DD-HHMM-HASH.ext' based on the file's modification time
    and MD5 hash. Files that already have a valid prefix or unsupported
    extensions are skipped by returning None.

    Args:
        path: The directory path containing the file.
        filename: The name of the file to potentially rename.

    Returns:
        The new filename with timestamp prefix, or None if the file
        should not be renamed.

    Raises:
        AssertionError: If the file does not exist or is not a regular file.
    """

    filepath = os.path.join(path, filename)
    assert os.path.exists(filepath), "File '%s' does not exist" % (filepath)
    assert os.path.isfile(filepath), "File '%s' is not a regular file" % (filepath)

    # Get the directory configuration for the target directory
    directory_config = get_directory_config(path)

    # Check to see if the file has a valid extension for renaming
    filename_lower = filename.lower()
    extension = None
    for e in EXTENSIONS:
        if filename_lower.endswith("." + e):
            extension = e
            break

    # Manual overrides
    if filename_lower.endswith(".jpeg"):
        extension = "jpg"

    # Skip files that don't have a valid extension
    if extension is None:
        # logger.debug('  Skipping extension:       %s', filename)
        return None

    # Check to see if the file already has a valid prefix
    if (
        directory_config is not None
        and directory_config["prefix_timestamp"] == "minute"
    ):
        m = re_prefix_minute.match(filename)
    else:
        m = re_prefix_day.match(filename)
    if m is not None:
        # logger.debug('  Skipping valid prefix:    %s', filename)
        return None

    # Get the file's modification time in the set time zone
    mtime_seconds = os.stat(filepath).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds)

    # Compute the MD5 hash of the file
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    hash = hash_md5.hexdigest()
    hash = hash[0:10]  # Beginning of hash, just like git

    # Generate and return the new filename
    if (
        directory_config is not None
        and directory_config["prefix_timestamp"] == "minute"
    ):
        # Add the minute from the mtime to the filename
        new_filename = (
            mtime_datetime.strftime("%Y-%m-%d-%H%M-") + hash + "." + extension
        )
    else:
        new_filename = mtime_datetime.strftime("%Y-%m-%d-") + hash + "." + extension

    return new_filename


# ----------------------------------------------------------------------
# Filesystem Traversal
# ----------------------------------------------------------------------


def traverse(target: str, dryrun: bool = True) -> None:
    """Traverse and process files or directories.

    If the target is a directory, recursively processes all files within it.
    If the target is a file, processes just that file. Non-existent targets
    are skipped with a warning.

    Args:
        target: Path to a file or directory to process.
        dryrun: If True, only simulate renames without making changes.
            Defaults to True.
    """

    # Skip things that don't exist
    if not os.path.exists(target):
        logger.warning("Argument '%s' is not a file or a directory, skipping", target)
        return

    # Process arguments that are files
    if os.path.isfile(target):
        logger.info("Processing filename argument '%s'", target)
        path = os.path.dirname(target)
        filename = os.path.basename(target)
        process_file(path, filename, dryrun)
        return

    # Process arguments that are directories
    if os.path.isdir(target):
        logger.info("Processing directory argument '%s'", target)

        # Create a list of every directory and file in the tree, sorted,
        # including the root directory
        all_dirs = []
        for root, dirs, files in os.walk(target):
            # We process every directory as it is found by the walk
            all_dirs.append(root)
        all_dirs.sort()

        # Now, process each directory
        for root in all_dirs:
            process_directory(root, dryrun)
        return

    assert False, (
        "Should not get here, directory entry '%s' is not a file or "
        "directory" % (target)
    )


def process_directory(path: str, dryrun: bool = True) -> None:
    """Process all files in the specified directory.

    Iterates through all regular files in the directory and processes each
    one for potential renaming.

    Args:
        path: The directory path to process.
        dryrun: If True, only simulate renames without making changes.
            Defaults to True.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """

    # Check that the target directory exists
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # Build the list of the files in the directory, capturing the
    # maximum filename length and the number of files in the directory
    max_filename_length = 0
    filelist = []
    for filename in os.listdir(path):
        if not os.path.isfile(os.path.join(path, filename)):
            continue
        filelist.append((path, filename))
        max_filename_length = max(max_filename_length, len(filename))

    logger.info("Processing directory '%s' (%i files)", path, len(filelist))

    # Process each file in the directory
    for path, filename in filelist:
        process_file(path, filename, dryrun, max_filename_length=max_filename_length)


def process_file(
    path: str, filename: str, dryrun: bool = True, max_filename_length: int = 0
) -> bool:
    """Process a single file for potential renaming.

    Checks if the file should be renamed based on its current name and
    extension. Special handling for .DS_Store files (deletion). If renaming
    is needed, either performs or simulates the rename based on dryrun mode.

    Args:
        path: The directory path containing the file.
        filename: The name of the file to process.
        dryrun: If True, only simulate changes without making them.
            Defaults to True.
        max_filename_length: Maximum filename length for formatting output.
            Defaults to 0.

    Returns:
        True if the file was renamed or deleted, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """

    # Check that the source file exists
    fullpath = os.path.join(path, filename)
    if not os.path.exists(fullpath):
        raise FileNotFoundError(fullpath)

    # Hardcoded override: If this is a .DS_Store file, make it go away
    if filename == ".DS_Store":
        if dryrun:
            logger.warning("  Deleting file (dryrun):   %s", filename)
        else:
            logger.warning("  Deleting file:            %s", filename)
            os.remove(fullpath)
        return True

    # Generate the new filename
    new_filename = generate_filename(path, filename)

    # Skip if the file is not to be renamed
    if new_filename is None:
        # logger.debug('  Skipping file:            %s', filename)
        return False

    # Skip if the file is already named correctly
    if filename == new_filename:
        # logger.debug('  Skipping file:            %s', filename)
        return False

    # Rename the file
    new_fullpath = os.path.join(path, new_filename)
    filename_with_spacing = filename.ljust(max_filename_length)
    if dryrun:
        logger.debug(
            "  Renaming file (dryrun):   %s -> %s",
            filename_with_spacing,
            new_filename,
        )  # Filename at 50 chars for info
    else:
        logger.debug(
            "  Renaming file:            %s -> %s",
            filename_with_spacing,
            new_filename,
        )  # Filename at 50 chars for info
        os.rename(fullpath, new_fullpath)

    return True


# ----------------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------------


def main() -> None:
    """Main entry point for the autorename command-line tool.

    Parses command-line arguments and processes all specified files and
    directories. Runs in dry-run mode by default unless --commit is specified.
    """
    parser = argparse.ArgumentParser(
        description="Rename specified files to 'YYYY-MM-DD-HASH.ext'"
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="Commit mode, files will be renamed",
    )
    parser.add_argument("target", nargs="+")
    args = parser.parse_args()

    # Run in dry run mode by default unless --commit is specified
    if args.commit:
        logger.info("Commit mode enabled, files will be renamed")
        dryrun = False
    else:
        logger.warning("Dry run mode enabled, no files will be renamed")
        dryrun = True

    # Process each command line argument
    for _t in args.target:
        traverse(_t, dryrun)

    logger.info("Terminating normally")


if __name__ == "__main__":
    main()
