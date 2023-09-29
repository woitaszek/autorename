#!/usr/bin/env python3

# Python imports
import argparse
import datetime
import json
import logging
import hashlib
import os
import re
import sys
import time

from typing import Union

# Extensions to be renamed
EXTENSIONS = ['jpg', 'jpeg', 'gif', 'm4a', 'mov', 'mp4', 'png', 'webp', 'heic']

# Configure logging
logging.basicConfig(
        format="%(asctime)s %(name)-24.23s %(levelname)-8s %(message)s",
        level=logging.DEBUG)

# Regular expression for detecting manually-named files that should not
# be renamed; these start with yyyy-mm-XX and then have a space followed
# by non-space character(s). Note that we allow characters other than
# digits in the day field.
re_prefix = re.compile("""
       \d\d\d\d-\d\d-\S\S[ ]\S+
        """, re.VERBOSE)

# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------


def auto_name_file(path: str, filename: str) -> Union[str, None]:
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
    assert os.path.exists(filepath)
    assert os.path.isfile(filepath)

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
        logger.debug('Skipping extension:    %s', filepath)
        return None

    # Check to see if the file already has a valid prefix
    m = re_prefix.match(filename)
    if m is not None:
        logger.debug('Skipping valid prefix: %-80s ', filepath)
        return None
    
    # Get the file's modification time and compute the MD5 hash
    mtime_seconds = os.stat(filepath).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds)
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    hash = hash_md5.hexdigest()
    hash = hash[0:10]

    # Generate and return the new filename
    new_filename = mtime_datetime.strftime('%Y-%m-%d-') + hash + '.' + extension
    return new_filename


# ----------------------------------------------------------------------
# Filesystem Traversal
# ----------------------------------------------------------------------

def traverse(target, dryrun = True):
    """
    Traverse the specified command line arguments. If the argument is a
    directory, traverse the directory recursively. If the argument is a
    file, process the file.
    """
    
    logger = logging.getLogger('autorename.traverse')

    # Skip things that don't exist
    if not os.path.exists(t):
        logger.warning("Argument '%s' is not a file or a directory, skipping", t)
        return

    # Process singleton files
    if os.path.isfile(t):
        logger.info("Processing filename argument '%s'", t)
        path = os.path.dirname(t)
        filename = os.path.basename(t)
        process_file(path, filename, dryrun)
        return

    # Process directories recursively
    if os.path.isdir(t):
        logger.info("Processing directory argument '%s'", t)
        for root, dirs, files in os.walk(t):
            for file in files:
                process_file(root, file, dryrun)
        return


def process_file(path, filename, dryrun = True):
    """
    Process the specified file.

    Return True if the file was renamed, False if the file was not renamed.
    """
    logger = logging.getLogger('autorename.process_file')

    logger.debug("Processing file %s     %s", path, filename)

    return


#     for d in set(args.directory):
#         dirname = os.path.join(os.getcwd(), d)
#         dirname = os.path.normpath(dirname)

#             if os.path.isfile(filepath):
#                 count += auto_name_file(dirname, f, dryrun, **('dryrun',))

#                 logger.info('Renaming: %-80s -> %s', filepath, new_filepath)
#                 if not dryrun:
#                     os.rename(filepath, new_filepath)
#                 return new_filename

#                 continue
#                 logger.info('Path: %s   Renamed: %i', dirname, count)
#                 continue
#                 return None



# ----------------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------------

if __name__ == '__main__':

    logger = logging.getLogger('autorename.main')

    parser = argparse.ArgumentParser(
        description="Rename specified files to 'YYYY-MM-DD-HASH.ext'")
    parser.add_argument('--dryrun', action='store_true', default=False)
    parser.add_argument('target', nargs='+')
    args = parser.parse_args()

    dryrun = args.dryrun
    if dryrun:
        logger.info("Dry run mode enabled, no files will be renamed")

    for t in args.target:
        traverse(t, dryrun)

    logger.info('Terminating normally')

