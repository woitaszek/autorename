#!/usr/bin/env python3

# Python imports
import argparse
import datetime
import logging
import hashlib
import os
import re

from typing import Union

# Extensions to be renamed
EXTENSIONS = ['jpg', 'jpeg', 'gif',
              'm4a', 'mov', 'mp4',
              'pdf',
              'png', 'webp', 'heic',
              'pptx', 'docx', 'xlsx']

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(name)-24.23s %(levelname)-8s %(message)s",
    level=logging.DEBUG)

# Regular expression for detecting manually-named files that should not
# be renamed; these start with yyyy-mm-XX and then have a space followed
# by non-space character(s). Note that we allow characters other than
# digits in the day field.
re_prefix = re.compile(r"""
       \d\d\d\d-\d\d-\S\S[ ]\S+
        """, re.VERBOSE)

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def generate_filename(path: str, filename: str) -> Union[str, None]:
    """
    Generate and return the new desired filename for the specified file.
    If the file is not to be renamed, return None.

    The specified file must exist and be a regular file. The specified
    file's metadata is retrieved using os.stat(), and the contents are
    read to compute the MD5 hash. Note that the file is not renamed
    in this routine; the caller is responsible for renaming the file.

    Arguments:
        path: The path to the file
        filename: The filename of the file
    """
    logger = logging.getLogger('autorename.auto_name_file')

    filepath = os.path.join(path, filename)
    assert os.path.exists(filepath), "File '%s' does not exist" % (filepath)
    assert os.path.isfile(filepath), "File '%s' is not a regular file" % (filepath)

    # Check to see if the file has a valid extension for renaming
    f = filename.lower()
    extension = None
    for e in EXTENSIONS:
        if f.endswith('.' + e):
            extension = e
            break

    # Manual overrides
    if f.endswith('.jpeg'):
        extension = 'jpg'

    # Skip files that don't have a valid extension
    if extension is None:
        logger.debug('  Skipping extension:       %s', filename)  # Filename at 51 chars
        return None

    # Check to see if the file already has a valid prefix
    m = re_prefix.match(filename)
    if m is not None:
        # logger.debug('  Skipping valid prefix:    %s', filename)  # Filename at 51 chars
        return None

    # Get the file's modification time and compute the MD5 hash
    mtime_seconds = os.stat(filepath).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds)
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    hash = hash_md5.hexdigest()
    hash = hash[0:10]  # Beginning of hash, just like git

    # Generate and return the new filename
    new_filename = mtime_datetime.strftime('%Y-%m-%d-') + hash + '.' + extension
    return new_filename


# ----------------------------------------------------------------------
# Filesystem Traversal
# ----------------------------------------------------------------------

def traverse(target, dryrun=True):
    """
    Traverse the specified command line arguments. If the argument is a
    directory, traverse the directory recursively. If the argument is a
    file, process the file.
    """

    logger = logging.getLogger('autorename.traverse')

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

    assert False, "Should not get here, directory entry '%s' is not a file or directory" % (target)


def process_directory(path, dryrun=True):
    """
    Process the specified directory.
    """
    logger = logging.getLogger('autorename.process_directory')

    # Check that the target directory exists
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # Prescan the filename strings to get the longest length
    max_filename_length = 0
    file_count = 0
    for filename in os.listdir(path):
        if not os.path.isfile(os.path.join(path, filename)):
            continue
        max_filename_length = max(max_filename_length, len(filename))
        file_count += 1

    logger.info("Processing directory '%s' (%i files)", path, file_count)

    # Process each file in the directory
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            process_file(path, filename, dryrun,
                         max_filename_length=max_filename_length,
                         file_count=file_count)


def process_file(path, filename, dryrun=True,
                 max_filename_length=0,
                 file_count=0):
    """
    Process the specified file.

    Return True if the file was renamed, False if the file was not renamed.
    """
    logger = logging.getLogger('autorename.process_file')

    # Check that the source file exists
    fullpath = os.path.join(path, filename)
    if not os.path.exists(fullpath):
        raise FileNotFoundError(fullpath)

    # Hardcoded override: If this is a .DS_Store file, make it go away
    if filename == '.DS_Store':
        if dryrun:
            logger.warning('  Deleting file (dryrun):   %s', filename)
        else:
            logger.warning('  Deleting file:            %s', filename)
            os.remove(fullpath)
        return True

    # Generate the new filename
    new_filename = generate_filename(path, filename)

    # Skip if the file is not to be renamed
    if new_filename is None:
        # logger.debug('  Skipping file:            %s', filename)  # Reason is logged by generate_filename
        return False

    # Skip if the file is already named correctly
    if filename == new_filename:
        # logger.debug('  Skipping file:            %s', filename) # Filename at 50 chars
        return False

    # Rename the file
    new_fullpath = os.path.join(path, new_filename)
    filename_with_spacing = filename.ljust(max_filename_length)
    if dryrun:
        logger.debug('  Renaming file (dryrun):   %s -> %s',
                     filename_with_spacing, new_filename)  # Filename at 50 chars for info
    else:
        logger.debug('  Renaming file:            %s -> %s',
                     filename_with_spacing, new_filename)  # Filename at 50 chars for info
        os.rename(fullpath, new_fullpath)

    return True


# ----------------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------------

if __name__ == '__main__':

    logger = logging.getLogger('autorename.main')

    parser = argparse.ArgumentParser(
        description="Rename specified files to 'YYYY-MM-DD-HASH.ext'")
    parser.add_argument('--commit', action='store_true', default=False,
                        help='Commit mode, files will be renamed')
    parser.add_argument('target', nargs='+')
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

    logger.info('Terminating normally')
