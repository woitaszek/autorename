# test_autorename.py

# Python imports
import os
import sys

# Test imports
import pytest

# Target imports
import autorename

# ----------------------------------------------------------------------
# General mocking for reading a mock file
# ----------------------------------------------------------------------

OS_STAT_RESULT = os.stat_result([
        0, # st_mode
        0, # st_ino
        0, # st_dev
        1, # st_nlink
        0, # st_uid
        0, # st_gid
        0, # st_size
        0, # st_atime
        1262430245, # st_mtime  2010-01-02 10:10:45
        0 # st_ctime
    ])

@pytest.fixture
def mock_setup(mocker):
    mock_os_stat = mocker.patch('os.stat', return_value=OS_STAT_RESULT)
    mock_os_open = mocker.patch('builtins.open', mocker.mock_open(read_data=b''))
    return mock_os_stat, mock_os_open


# ----------------------------------------------------------------------
# Tests for auto_name_file function
# ----------------------------------------------------------------------

# The auto_name_file function takes a path and filename and returns
# the desired new filename. As such, it is non-destructive; it reads the
# provided filename variables and the file's os.stat() metadata and contents,
# but does not perform any modifications to the filesystem.

def test_rename_filename_png(mock_setup):
    """
    Test renaming a file that matches an expected suffix: /path/does/not/exist/filename.png
    """
    new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.png')
    assert new_name == '2010-01-02-d41d8cd98f.png'


def test_rename_filename_hash_png(mock_setup):
    """
    Test renaming a file that matches an expected suffix with a changed hash: /path/does/not/exist/filename-HASH.png
    """
    new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.png')
    assert new_name == '2010-01-02-d41d8cd98f.png'


def test_skip_filename_dat(mock_setup):
    """
    Test skipping a file that has an unexpected suffix: /path/does/not/exist/filename.dat
    """
    sys.stderr.write('\n')
    new_name = autorename.auto_name_file('/path/does/not/exist', 'filename.dat')
    assert new_name is None


def test_skip_filename_prefix(mock_setup):
    """
    Test skipping files that start with yyyy-mm-dd as a prefix followed by a space
    """
    sys.stderr.write('\n')
    for filename in ('2022-01-01 filename.png', '2022-01-XX filename.png'):
        new_name = autorename.auto_name_file('/path/does/not/exist', filename)
        assert new_name is None



# ----------------------------------------------------------------------
# Test execution
# ----------------------------------------------------------------------

if __name__ == '__main__':
    pytest.main()
