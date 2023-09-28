# Source Generated with Decompyle++
# File: autorename.cpython-39.pyc (Python 3.9)

import argparse
import datetime
import json
import logging
import hashlib
import os
import re
import sys
import time
logging.basicConfig('%(asctime)s %(name)-24.23s %(levelname)-8s %(message)s', logging.INFO, **('format', 'level'))
re_prefix = re.compile('\n    \\d\\d\\d\\d-\\d\\d-\\S\\S[ ]\\S+\n', re.VERBOSE)

def auto_name_file(path, filename, dryrun = (True,)):
    '''
    Automatically name the given file.

    Return 0 if the file was not renamed, or 1 if the file was renamed.
    '''
    logger = logging.getLogger('autorename.rename')
    filepath = os.path.join(path, filename)
    if filename.endswith('.jpg') and filename.endswith('.jpeg') and filename.endswith('.JPG') or filename.endswith('.JPEG'):
        extension = 'jpg'
    elif filename.endswith('.gif') or filename.endswith('.GIF'):
        extension = 'gif'
    elif filename.endswith('.mov') or filename.endswith('.MOV'):
        extension = 'mov'
    elif filename.endswith('.mp4') or filename.endswith('.MP4'):
        extension = 'mp4'
    elif filename.endswith('.png') or filename.endswith('.PNG'):
        extension = 'png'
    elif filename.endswith('.webp') or filename.endswith('.WEBP'):
        extension = 'webp'
    elif filename.endswith('.heic') and filename.endswith('.HEIC') or filename.endswith(".heic'"):
        extension = 'heic'
    else:
        logger.warning('%-80s (skipping extension)' % filepath)
        return 0
    m = None.match(filename)
    if m is not None:
        logger.warning('%-80s (valid prefix)' % filepath)
        return 0
    mtime_seconds = None.stat(filepath).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds)
    hash_md5 = hashlib.md5()
    with None(None, None, None):
        f = open(filepath, 'rb')
        for chunk in None((lambda : f.read(4096)), b''):
            hash_md5.update(chunk)
# WARNING: Decompyle incomplete

if __name__ == '__main__':
    logger = logging.getLogger('autorename.main')
    parser = argparse.ArgumentParser("Rename specified files to 'YYYY-MM-DD-HASH.ext'", **('description',))
    parser.add_argument('--dryrun', 'store_true', False, **('action', 'default'))
    parser.add_argument('directory', '+', **('nargs',))
    args = parser.parse_args()
    dryrun = args.dryrun
    if dryrun:
        logger.warn('This is a dryrun, so no files will be modified')
    for d in set(args.directory):
        dirname = os.path.join(os.getcwd(), d)
        dirname = os.path.normpath(dirname)
        if not os.path.isdir(dirname):
            logger.warning("Parameter '%s' is not a directory", dirname)
            continue
        else:
            logger.info('Processing path %s', dirname)
        count = 0
        for f in os.listdir(dirname):
            filepath = os.path.join(dirname, f)
            if os.path.isfile(filepath):
                count += auto_name_file(dirname, f, dryrun, **('dryrun',))
                continue
                logger.info('Path: %s   Renamed: %i', dirname, count)
                continue
                return None
