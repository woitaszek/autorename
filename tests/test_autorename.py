# test_autorename.py

# Python imports
import os
import logging
import datetime
from typing import Any
from pytest_mock import MockerFixture

# Test imports
import pytest

# Target imports
from autorename import autorename
from autorename.autorename import TIMEZONE


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
        1262430245,  # st_mtime  2010-01-02 10:10:45 UTC
        0,  # st_ctime
    ]
)

# Calculate expected timestamp strings using the configured timezone
MOCK_MTIME = datetime.datetime.fromtimestamp(1262430245, tz=TIMEZONE)
EXPECTED_DATE_PREFIX = MOCK_MTIME.strftime("%Y-%m-%d")
EXPECTED_DATETIME_PREFIX = MOCK_MTIME.strftime("%Y-%m-%d-%H%M")


@pytest.fixture
def mock_setup(mocker: MockerFixture) -> tuple[Any, Any, Any, Any]:
    """Mock a file that exists and has a known mtime and empty content."""
    mock_os_stat = mocker.patch("os.stat", return_value=OS_STAT_RESULT)

    # Mock module.file.open, not builtins.open
    # https://github.com/microsoft/vscode-python/issues/24811
    mock_os_open = mocker.patch(
        "autorename.autorename.open", mocker.mock_open(read_data=b"")
    )

    mock_os_path_exists = mocker.patch("os.path.exists", return_value=True)
    mock_os_path_isfile = mocker.patch("os.path.isfile", return_value=True)
    return mock_os_stat, mock_os_open, mock_os_path_exists, mock_os_path_isfile


@pytest.fixture
def mock_os_rename(mocker: MockerFixture) -> Any:
    """Mock the actions that are taken when a file is renamed."""
    return mocker.patch("os.rename")


@pytest.fixture
def mock_os_remove(mocker: MockerFixture) -> Any:
    """Mock the actions that are taken when a file is removed."""
    return mocker.patch("os.remove")


# ----------------------------------------------------------------------
# Parameterized tests for filename generation
# ----------------------------------------------------------------------

# The generate_filename function takes a path and filename and returns
# the desired new filename. As such, it is non-destructive; it reads the
# provided filename variables and the file's os.stat() metadata and contents,
# but does not perform any modifications to the filesystem.


def test_generate_filename_unexpected_extension(
    mock_setup: tuple[Any, Any, Any, Any],
) -> None:
    """Test skipping a file that has an unexpected suffix."""
    # Arrange: mock_setup provides file mocking

    # Act: /path/does/not/exist/filename.dat
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.dat")

    # Assert
    assert new_name is None


@pytest.mark.parametrize(
    "granularity,expected_prefix",
    [
        (None, EXPECTED_DATE_PREFIX),
        ("day", EXPECTED_DATE_PREFIX),
        ("minute", EXPECTED_DATETIME_PREFIX),
    ],
)
def test_generate_filename_png(
    mock_setup: tuple[Any, Any, Any, Any],
    mocker: MockerFixture,
    granularity: str | None,
    expected_prefix: str,
) -> None:
    """Test filename generation for a file."""
    # Arrange: mock_setup provides file mocking, mock config for granularity
    mock_config = {"prefix_timestamp": granularity} if granularity else None
    mocker.patch("autorename.autorename.get_directory_config", return_value=mock_config)

    # Act: /path/does/not/exist/filename.png
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.png")

    # Assert
    assert new_name == f"{expected_prefix}-d41d8cd98f.png"


@pytest.mark.parametrize(
    "granularity,expected_prefix",
    [
        (None, EXPECTED_DATE_PREFIX),
        ("day", EXPECTED_DATE_PREFIX),
        ("minute", EXPECTED_DATETIME_PREFIX),
    ],
)
def test_generate_filename_hash_png(
    mock_setup: tuple[Any, Any, Any, Any],
    mocker: MockerFixture,
    granularity: str | None,
    expected_prefix: str,
) -> None:
    """Test filename generation with a changed hash."""
    # Arrange: mock_setup provides file mocking, mock config for granularity
    mock_config = {"prefix_timestamp": granularity} if granularity else None
    mocker.patch("autorename.autorename.get_directory_config", return_value=mock_config)

    # Act: /path/does/not/exist/YYYY-MM-DD-OLDHASH.png -> YYYY-MM-DD-NEWHASH.png
    new_name = autorename.generate_filename(
        "/path/does/not/exist", f"{expected_prefix}-b1946ac924.png"
    )

    # Assert
    assert new_name == f"{expected_prefix}-d41d8cd98f.png"


@pytest.mark.parametrize(
    "granularity,test_filenames",
    [
        ("day", ["2022-01-01 filename.png", "2022-01-XX filename.png"]),
        ("minute", ["2022-01-01-1234 filename.png", "2022-01-XX-12XX filename.png"]),
    ],
)
def test_generate_filename_skip_prefix(
    mock_setup: tuple[Any, Any, Any, Any],
    mocker: MockerFixture,
    granularity: str,
    test_filenames: list[str],
) -> None:
    """Test skipping files that start with timestamp prefix and space."""
    # Arrange: mock_setup provides file mocking, mock config for granularity
    mock_config = {"prefix_timestamp": granularity}
    mocker.patch("autorename.autorename.get_directory_config", return_value=mock_config)

    # Act & Assert: test multiple filenames with prefix
    for filename in test_filenames:
        new_name = autorename.generate_filename("/path/does/not/exist", filename)
        assert new_name is None


@pytest.mark.parametrize(
    "granularity,expected_prefix",
    [
        (None, EXPECTED_DATE_PREFIX),
        ("day", EXPECTED_DATE_PREFIX),
        ("minute", EXPECTED_DATETIME_PREFIX),
    ],
)
def test_generate_filename_already_correct(
    mock_setup: tuple[Any, Any, Any, Any],
    mocker: MockerFixture,
    granularity: str | None,
    expected_prefix: str,
) -> None:
    """Test skipping files that are already correctly named."""
    # Arrange: mock_setup provides file mocking, mock config for granularity
    mock_config = {"prefix_timestamp": granularity} if granularity else None
    mocker.patch("autorename.autorename.get_directory_config", return_value=mock_config)

    # Act: file is already named correctly
    expected_filename = f"{expected_prefix}-d41d8cd98f.png"
    new_name = autorename.generate_filename("/path/does/not/exist", expected_filename)

    # Assert: should return the same name
    assert new_name == expected_filename


# ----------------------------------------------------------------------
# Test extension handling
# ----------------------------------------------------------------------


def test_generate_filename_rename_extension_jpg(
    mock_setup: tuple[Any, Any, Any, Any],
) -> None:
    """Test renaming a file that includes an extension change."""
    # Arrange: mock_setup provides file mocking

    # Act: /path/does/not/exist/filename.jpeg -> .jpg
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.jpeg")

    # Assert
    assert new_name == f"{EXPECTED_DATE_PREFIX}-d41d8cd98f.jpg"


def test_generate_filename_case_insensitive_extension(
    mock_setup: tuple[Any, Any, Any, Any],
) -> None:
    """Test that extensions are matched case-insensitively."""
    # Arrange: mock_setup provides file mocking

    # Act: test uppercase extension
    new_name = autorename.generate_filename("/path/does/not/exist", "filename.PNG")

    # Assert: should still generate filename with lowercase extension
    assert new_name == f"{EXPECTED_DATE_PREFIX}-d41d8cd98f.png"


# ----------------------------------------------------------------------
# Test configuration system
# ----------------------------------------------------------------------


def test_config_file_invalid_secion(tmp_path: Any) -> None:
    """Test a configuration file with an invalid section."""
    # Arrange: create config file with invalid section
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[invalid]\nplaceholder = invalid\n")

    # Act & Assert: should raise ValueError for missing autorename section
    with pytest.raises(ValueError):
        autorename.get_directory_config(tmp_path)


def test_config_file_invalid_value(tmp_path: Any) -> None:
    """Test a configuration file with an invalid value."""
    # Arrange: create config file with invalid prefix_timestamp value
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[autorename]\nprefix_timestamp = invalid\n")

    # Act & Assert: should raise ValueError for invalid value
    with pytest.raises(ValueError):
        autorename.get_directory_config(tmp_path)


def test_config_file_invalid_key(tmp_path: Any) -> None:
    """Test a configuration file with an invalid key."""
    # Arrange: create config file with missing required prefix_timestamp key
    jpg_file = tmp_path / "empty.jpg"
    jpg_file.touch()

    ini_file = tmp_path / ".autorename.ini"
    with ini_file.open("w") as f:
        f.write("[autorename]\ninvalid_key = invalid\n")

    # Act & Assert: should raise ValueError for missing required key
    with pytest.raises(ValueError):
        autorename.get_directory_config(tmp_path)


def test_config_file_hierarchy(tmp_path: Any) -> None:
    """Test a nontrivial configuration file hierarchy."""

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
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds, tz=TIMEZONE)
    expected_filename = mtime_datetime.strftime("%Y-%m-%d-%H%M-") + "253bcac7dd.jpg"
    # Check that the configuration file is read when starting in the
    # test directory
    config = autorename.get_directory_config(tmp_path)
    assert config is not None
    assert config["prefix_timestamp"] == "minute"

    # Check that the configuration file is read when starting in a
    # subdirectory
    config = autorename.get_directory_config(subdir)
    assert config is not None
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


def test_process_filename_does_not_exist() -> None:
    """Test raising an exception on a file that does not exist."""
    # Arrange: no mocking needed

    # Act & Assert: should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        autorename.process_file("/path/does/not/exist", "filename.png")


def test_process_filename_png(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_rename: Any
) -> None:
    """Test renaming a file that matches an expected suffix."""
    # Arrange: mock_setup provides file mocking, mock_os_rename mocks rename

    # Act: /path/does/not/exist/filename.png
    autorename.process_file("/path/does/not/exist", "filename.png", dryrun=False)

    # Assert
    mock_os_rename.assert_called_once_with(
        "/path/does/not/exist/filename.png",
        f"/path/does/not/exist/{EXPECTED_DATE_PREFIX}-d41d8cd98f.png",
    )


def test_process_remove_ds_store(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_remove: Any
) -> None:
    """Test removing a .DS_Store file."""
    # Arrange: mock_setup provides file mocking, mock_os_remove mocks remove

    # Act: /path/does/not/exist/.DS_Store
    autorename.process_file("/path/does/not/exist", ".DS_Store", dryrun=False)

    # Assert
    mock_os_remove.assert_called_once_with("/path/does/not/exist/.DS_Store")


# ----------------------------------------------------------------------
# Test dryrun mode
# ----------------------------------------------------------------------


def test_process_filename_png_dryrun(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_rename: Any
) -> None:
    """Test that dryrun mode does not actually rename files."""
    # Arrange: mock_setup provides file mocking, mock_os_rename mocks rename

    # Act: /path/does/not/exist/filename.png with dryrun=True
    autorename.process_file("/path/does/not/exist", "filename.png", dryrun=True)

    # Assert: os.rename should NOT be called
    mock_os_rename.assert_not_called()


def test_process_remove_ds_store_dryrun(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_remove: Any
) -> None:
    """Test that dryrun mode does not actually remove files."""
    # Arrange: mock_setup provides file mocking, mock_os_remove mocks remove

    # Act: /path/does/not/exist/.DS_Store with dryrun=True
    autorename.process_file("/path/does/not/exist", ".DS_Store", dryrun=True)

    # Assert: os.remove should NOT be called
    mock_os_remove.assert_not_called()


# ----------------------------------------------------------------------
# Test execution
# ----------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main()
