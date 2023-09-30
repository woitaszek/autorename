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
    """
    Mock a file that exists and has a known mtime and empty content.
    """
    mock_os_stat = mocker.patch('os.stat', return_value=OS_STAT_RESULT)
    mock_os_open = mocker.patch('builtins.open', mocker.mock_open(read_data=b''))
    mock_os_path_exists = mocker.patch('os.path.exists', return_value=True)
    mock_os_path_isfile = mocker.patch('os.path.isfile', return_value=True)
    return mock_os_stat, mock_os_open, mock_os_path_exists, mock_os_path_isfile


# ----------------------------------------------------------------------
# Tests for auto_name_file function
# ----------------------------------------------------------------------

# The auto_name_file function takes a path and filename and returns
# the desired new filename. As such, it is non-destructive; it reads the
# provided filename variables and the file's os.stat() metadata and contents,
# but does not perform any modifications to the filesystem.

def test_generate_filename_png(mock_setup):
    """
    Test filename generation for a file that matches an expected suffix:
    /path/does/not/exist/filename.png
    """
    new_name = autorename.generate_filename('/path/does/not/exist', 'filename.png')
    assert new_name == '2010-01-02-d41d8cd98f.png'


def test_generate_filename_hash_png(mock_setup):
    """
    Test filename generation for a file that matches an expected suffix with a changed hash:
    /path/does/not/exist/filename-HASH.png
    """
    new_name = autorename.generate_filename('/path/does/not/exist', 'filename.png')
    assert new_name == '2010-01-02-d41d8cd98f.png'


def test_generate_filename_unexpected_extension(mock_setup):
    """
    Test skipping a file that has an unexpected suffix: /path/does/not/exist/filename.dat
    """
    new_name = autorename.generate_filename('/path/does/not/exist', 'filename.dat')
    assert new_name is None


def test_generate_filename_skip_prefix(mock_setup):
    """
    Test skipping files that start with yyyy-mm-dd as a prefix followed by a space
    """
    for filename in ('2022-01-01 filename.png', '2022-01-XX filename.png'):
        new_name = autorename.generate_filename('/path/does/not/exist', filename)
        assert new_name is None



# ----------------------------------------------------------------------
# Test execution
# ----------------------------------------------------------------------

if __name__ == '__main__':
    pytest.main()
