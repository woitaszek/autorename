# test_autorename.py

# Python imports
import os
import logging
import datetime

# Test imports
import pytest

# Target imports
import autorename


# ----------------------------------------------------------------------
# General mocking for reading a mock file
# ----------------------------------------------------------------------

OS_STAT_RESULT = os.stat_result(
    [
        0,  # st_mode
        0,  # st_ino
        0,  # st_dev
        1,  # st_nlink
        0,  # st_uid
        0,  # st_gid
        0,  # st_size
        0,  # st_atime
        1262430245,  # st_mtime  2010-01-02 10:10:45
        0,  # st_ctime
    ]
)


@pytest.fixture
def mock_setup(mocker):
    """
    Mock a file that exists and has a known mtime and empty content.
    """
    mock_os_stat = mocker.patch("os.stat", return_value=OS_STAT_RESULT)

    # Mock module.file.open, not builtins.open
    # https://github.com/microsoft/vscode-python/issues/24811
    mock_os_open = mocker.patch("autorename.open", mocker.mock_open(read_data=b""))

    mock_os_path_exists = mocker.patch("os.path.exists", return_value=True)
    mock_os_path_isfile = mocker.patch("os.path.isfile", return_value=True)
    return mock_os_stat, mock_os_open, mock_os_path_exists, mock_os_path_isfile


@pytest.fixture
def mock_os_rename(mocker):
    """
    Mock the actions that are taken when a file is renamed.
    """
    return mocker.patch("os.rename")


@pytest.fixture
def mock_os_remove(mocker):
    """
    Mock the actions that are taken when a file is removed.
    """
    return mocker.patch("os.remove")


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
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.png")
    assert new_name == "2010-01-02-d41d8cd98f.png"


def test_generate_filename_hash_png(mock_setup):
    """
    Test filename generation for a file that matches an expected suffix with a changed hash:
    /path/does/not/exist/filename-HASH.png
    """
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.png")
    assert new_name == "2010-01-02-d41d8cd98f.png"


def test_generate_filename_unexpected_extension(mock_setup):
    """
    Test skipping a file that has an unexpected suffix: /path/does/not/exist/filename.dat
    """
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.dat")
    assert new_name is None


def test_generate_filename_skip_prefix(mock_setup):
    """
    Test skipping files that start with yyyy-mm-dd as a prefix followed by a space
    """
    for filename in ("2022-01-01 filename.png", "2022-01-XX filename.png"):
        new_name = autorename.generate_filename("/path/does/not/exist", filename)
        assert new_name is None


def test_generate_filename_rename_extension_jpg(mock_setup):
    """
    Test renaming a file that includes an extension change
    """

    # Test renaming a file that matches an expected suffix: /path/does/not/exist/filename.jpg
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.jpeg")
    assert new_name == "2010-01-02-d41d8cd98f.jpg"


# ----------------------------------------------------------------------
# Test configuration system
# ----------------------------------------------------------------------


def test_config_file_invalid_secion(tmp_path):
    """
    Test a configuration file with an invalid section
    """

    # Create an empty "jpg" file in the test directory
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    # Create the ".autorename.ini" file in the test directory
    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[invalid]\nplaceholder = invalid\n")

    # Check that the configuration file read raises an exception
    with pytest.raises(Exception):
        autorename.get_directory_config(tmp_path)


def test_config_file_invalid_value(tmp_path):
    """
    Test a configuration file with an invalid value
    """

    # Create an empty "jpg" file in the test directory
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    # Create the ".autorename.ini" file in the test directory
    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[autorename]\nprefix_timestamp = invalid\n")

    # Check that the configuration file read raises an exception
    with pytest.raises(Exception):
        autorename.get_directory_config(tmp_path)


def test_config_file_invalid_key(tmp_path):
    """
    Test a configuration file with an invalid key
    """

    # Create an empty "jpg" file in the test directory
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    # Create the ".autorename.ini" file in the test directory
    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[autorename]\ninvalid_key = invalid\n")

    # Check that the configuration file read raises an exception
    with pytest.raises(Exception):
        autorename.get_directory_config(tmp_path)


def test_config_file_hierarchy(tmp_path):
    """
    Test a nontrivial configuration file hierarchy
    """

    # Create the ".autorename.ini" file in the test directory
    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[autorename]\nprefix_timestamp = minute\n")

    # Create a temporary subdirectory that contains a jpg file
    subdir = tmp_path / "testdir"
    subdir.mkdir(exist_ok=True)
    jpg_file = subdir / "empty.jpg"
    with jpg_file.open("w") as f:
        f.write("X\n")  # hash: 253bcac7dd806bb7cf57dc19f71f2fa0

    # Get the mtime of the jpg file and create the expected filename
    mtime_seconds = os.stat(jpg_file).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds)
    expected_filename = mtime_datetime.strftime("%Y-%m-%d-%H%M-") + "253bcac7dd.jpg"
    # Check that the configuration file is read when starting in the test directory
    config = autorename.get_directory_config(tmp_path)
    assert config["prefix_timestamp"] == "minute"

    # Check that the configuration file is read when starting in a subdirectory
    config = autorename.get_directory_config(subdir)
    assert config["prefix_timestamp"] == "minute"

    # Test renaming a file in the subdirectory
    logging.info(f"Renaming file in {subdir}")
    target_file = subdir / "empty.jpg"
    logging.info(f"Renaming file {target_file}")
    assert target_file.exists()

    autorename.process_directory(subdir, dryrun=False)
    assert os.path.exists(subdir / expected_filename)


# ----------------------------------------------------------------------
# Test rename action
# ----------------------------------------------------------------------


def test_process_filename_does_not_exist():
    """
    Test raising an exception on a file that does not exist
    """
    with pytest.raises(FileNotFoundError):
        autorename.process_file("/path/does/not/exist", "filename.png")


def test_process_filename_png(mock_setup, mock_os_rename):
    """
    Test renaming a file that matches an expected suffix: /path/does/not/exist/filename.png
    """
    autorename.process_file("/path/does/not/exist", "filename.png", dryrun=False)
    mock_os_rename.assert_called_once_with(
        "/path/does/not/exist/filename.png",
        "/path/does/not/exist/2010-01-02-d41d8cd98f.png",
    )


def test_process_remove_ds_store(mock_setup, mock_os_remove):
    """
    Test renaming a file that matches an expected suffix: /path/does/not/exist/.DS_Store
    """
    autorename.process_file("/path/does/not/exist", ".DS_Store", dryrun=False)
    mock_os_remove.assert_called_once_with("/path/does/not/exist/.DS_Store")


# ----------------------------------------------------------------------
# Test execution
# ----------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main()
