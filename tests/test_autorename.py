# test_autorename.py

# Python imports
import os
import logging
import datetime
import hashlib
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


def test_process_skip_unsupported_extension(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_rename: Any
) -> None:
    """Test that files with unsupported extensions are skipped."""
    # Arrange: mock_setup provides file mocking, mock_os_rename mocks rename

    # Act: /path/does/not/exist/filename.dat with unsupported extension
    result = autorename.process_file(
        "/path/does/not/exist", "filename.dat", dryrun=False
    )

    # Assert: should return False and not call os.rename
    assert result is False
    mock_os_rename.assert_not_called()


def test_process_skip_already_correct_name(
    mock_setup: tuple[Any, Any, Any, Any], mock_os_rename: Any
) -> None:
    """Test that files already having the correct name are skipped."""
    # Arrange: mock_setup provides file mocking, mock_os_rename mocks rename
    # Use a filename that already matches the expected format

    # Act: filename that already has the correct format
    result = autorename.process_file(
        "/path/does/not/exist", f"{EXPECTED_DATE_PREFIX}-d41d8cd98f.png", dryrun=False
    )

    # Assert: should return False and not call os.rename
    assert result is False
    mock_os_rename.assert_not_called()


# ----------------------------------------------------------------------
# Test traverse function
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "granularity,format_str",
    [
        (None, "%Y-%m-%d"),
        ("day", "%Y-%m-%d"),
        ("minute", "%Y-%m-%d-%H%M"),
    ],
)
def test_traverse_single_file(
    tmp_path: Any, granularity: str | None, format_str: str
) -> None:
    """Test traversing and processing a single file."""
    # Arrange: create a test file with known content
    test_file = tmp_path / "test.png"
    test_content = b"test content"
    with test_file.open("wb") as f:
        f.write(test_content)

    # Create config file if granularity is specified
    if granularity is not None:
        ini_file = tmp_path / ".autorename.ini"
        with ini_file.open("w") as f:
            f.write(f"[autorename]\nprefix_timestamp = {granularity}\n")

    # Calculate expected filename based on actual file stats
    mtime_seconds = os.stat(test_file).st_mtime
    mtime_datetime = datetime.datetime.fromtimestamp(mtime_seconds, tz=TIMEZONE)
    expected_prefix = mtime_datetime.strftime(format_str)

    # Calculate expected hash
    hash_md5 = hashlib.md5()
    hash_md5.update(test_content)
    expected_hash = hash_md5.hexdigest()[0:10]
    expected_filename = f"{expected_prefix}-{expected_hash}.png"

    # Act: traverse the single file
    autorename.traverse(str(test_file), dryrun=False)

    # Assert: file should be renamed
    assert not test_file.exists()
    assert (tmp_path / expected_filename).exists()


# ----------------------------------------------------------------------
# Test format_size function
# ----------------------------------------------------------------------


def test_format_size_bytes() -> None:
    """Test formatting file sizes in bytes."""
    assert autorename.format_size(0) == "0 bytes"
    assert autorename.format_size(512) == "512 bytes"
    assert autorename.format_size(1023) == "1023 bytes"


def test_format_size_kilobytes() -> None:
    """Test formatting file sizes in kilobytes."""
    assert autorename.format_size(1024) == "1.0 KB"
    assert autorename.format_size(2048) == "2.0 KB"
    assert autorename.format_size(1536) == "1.5 KB"


def test_format_size_megabytes() -> None:
    """Test formatting file sizes in megabytes."""
    assert autorename.format_size(1024 * 1024) == "1.0 MB"
    assert autorename.format_size(2 * 1024 * 1024) == "2.0 MB"
    assert autorename.format_size(1536 * 1024) == "1.5 MB"


def test_format_size_gigabytes() -> None:
    """Test formatting file sizes in gigabytes."""
    assert autorename.format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert autorename.format_size(2 * 1024 * 1024 * 1024) == "2.0 GB"


# ----------------------------------------------------------------------
# Test traverse function edge cases
# ----------------------------------------------------------------------


def test_traverse_nonexistent_target() -> None:
    """Test traversing a non-existent target."""
    # Act & Assert: should log warning and return without error
    autorename.traverse("/path/that/does/not/exist", dryrun=True)


def test_traverse_directory(tmp_path: Any) -> None:
    """Test traversing a directory with multiple files."""
    # Arrange: create multiple files
    (tmp_path / "file1.png").write_bytes(b"content1")
    (tmp_path / "file2.jpg").write_bytes(b"content2")
    (tmp_path / "ignored.txt").write_bytes(b"ignored")  # unsupported extension

    # Act: traverse the directory
    autorename.traverse(str(tmp_path), dryrun=False)

    # Assert: PNG and JPG files should be renamed, TXT file should remain
    assert not (tmp_path / "file1.png").exists()
    assert not (tmp_path / "file2.jpg").exists()
    assert (tmp_path / "ignored.txt").exists()  # txt not renamed
    assert len(list(tmp_path.glob("2025-*.png"))) == 1
    assert len(list(tmp_path.glob("2025-*.jpg"))) == 1


def test_traverse_directory_with_subdirectories(tmp_path: Any) -> None:
    """Test traversing a directory tree with subdirectories."""
    # Arrange: create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (tmp_path / "root.png").write_bytes(b"root content")
    (subdir / "sub.png").write_bytes(b"sub content")

    # Act: traverse the root directory
    autorename.traverse(str(tmp_path), dryrun=False)

    # Assert: files in both root and subdirectory should be renamed
    assert not (tmp_path / "root.png").exists()
    assert not (subdir / "sub.png").exists()
    assert len(list(tmp_path.glob("2025-*.png"))) == 1
    assert len(list(subdir.glob("2025-*.png"))) == 1


# ----------------------------------------------------------------------
# Test process_directory edge cases
# ----------------------------------------------------------------------


def test_process_directory_nonexistent() -> None:
    """Test process_directory raises FileNotFoundError for non-existent path."""
    with pytest.raises(FileNotFoundError):
        autorename.process_directory("/path/does/not/exist", dryrun=True)


def test_process_directory_with_subdirectories(tmp_path: Any) -> None:
    """Test that process_directory skips subdirectories."""
    # Arrange: create files and subdirectory
    (tmp_path / "file.png").write_bytes(b"content")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.png").write_bytes(b"nested")

    # Act: process only the root directory
    autorename.process_directory(str(tmp_path), dryrun=False)

    # Assert: only root file should be renamed, subdirectory should be skipped
    assert len(list(tmp_path.glob("file.png"))) == 0
    assert len(list(tmp_path.glob("2025-*.png"))) == 1
    # Nested file should still exist with original name
    assert (subdir / "nested.png").exists()


# ----------------------------------------------------------------------
# Test main function
# ----------------------------------------------------------------------


def test_main_dryrun_default(tmp_path: Any, monkeypatch: Any) -> None:
    """Test main function with default dryrun mode."""
    # Arrange: create test file
    test_file = tmp_path / "test.png"
    test_file.write_bytes(b"content")

    # Mock sys.argv
    monkeypatch.setattr("sys.argv", ["autorename", str(test_file)])

    # Act: run main
    autorename.main()

    # Assert: file should NOT be renamed (dryrun mode)
    assert test_file.exists()


def test_main_commit_mode(tmp_path: Any, monkeypatch: Any) -> None:
    """Test main function with --commit flag."""
    # Arrange: create test file
    test_file = tmp_path / "test.png"
    test_file.write_bytes(b"content")

    # Mock sys.argv
    monkeypatch.setattr("sys.argv", ["autorename", "--commit", str(test_file)])

    # Act: run main
    autorename.main()

    # Assert: file should be renamed (commit mode)
    assert not test_file.exists()
    assert len(list(tmp_path.glob("2025-*.png"))) == 1


def test_main_multiple_targets(tmp_path: Any, monkeypatch: Any) -> None:
    """Test main function with multiple target arguments."""
    # Arrange: create multiple test files in different directories
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()
    file1 = dir1 / "test1.png"
    file2 = dir2 / "test2.jpg"
    file1.write_bytes(b"content1")
    file2.write_bytes(b"content2")

    # Mock sys.argv with multiple targets
    monkeypatch.setattr("sys.argv", ["autorename", "--commit", str(file1), str(file2)])

    # Act: run main
    autorename.main()

    # Assert: both files should be renamed
    assert not file1.exists()
    assert not file2.exists()
    assert len(list(dir1.glob("2025-*.png"))) == 1
    assert len(list(dir2.glob("2025-*.jpg"))) == 1


# ----------------------------------------------------------------------
# Test execution
# ----------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main()
