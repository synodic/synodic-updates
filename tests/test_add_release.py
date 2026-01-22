"""Tests for add_release script."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.add_release import add_release


@pytest.fixture
def mock_downloads(tmp_path: Path):
    """Mock downloads to create fake artifacts."""
    def fake_download(url: str, dest: Path) -> None:
        dest.write_text(f"fake content for {url}")

    with patch("scripts.add_release.download_file", side_effect=fake_download):
        yield


def test_stable_updates_all_latest_pointers(tmp_path: Path, mock_downloads) -> None:
    """Stable releases update both latest.txt and latest-stable.txt."""
    targets = tmp_path / "targets"

    add_release(
        version="1.0.0",
        channel="stable",
        windows_url="http://example.com/win.zip",
        linux_url="http://example.com/linux.tar.gz",
        macos_url="http://example.com/mac.tar.gz",
        targets_dir=targets,
    )

    assert (targets / "latest.txt").read_text().strip() == "1.0.0"
    assert (targets / "latest-stable.txt").read_text().strip() == "1.0.0"


def test_dev_only_updates_channel_latest(tmp_path: Path, mock_downloads) -> None:
    """Dev releases only update latest-development.txt, not latest.txt."""
    targets = tmp_path / "targets"

    add_release(
        version="1.0.0-dev.1",
        channel="development",
        windows_url="http://example.com/win.zip",
        linux_url="http://example.com/linux.tar.gz",
        macos_url="http://example.com/mac.tar.gz",
        targets_dir=targets,
    )

    assert not (targets / "latest.txt").exists()
    assert (targets / "latest-development.txt").read_text().strip() == "1.0.0-dev.1"


def test_metadata_schema(tmp_path: Path, mock_downloads) -> None:
    """Metadata JSON has expected structure for TUF clients."""
    targets = tmp_path / "targets"

    add_release(
        version="1.0.0",
        channel="stable",
        windows_url="http://example.com/win.zip",
        linux_url="http://example.com/linux.tar.gz",
        macos_url="http://example.com/mac.tar.gz",
        targets_dir=targets,
    )

    metadata = json.loads((targets / "1.0.0" / "metadata.json").read_text())

    # Required top-level fields
    assert metadata["version"] == "1.0.0"
    assert metadata["channel"] == "stable"
    assert "release_date" in metadata

    # Required artifact structure
    for platform in ["windows-x64", "linux-x64", "macos-x64"]:
        assert "filename" in metadata["artifacts"][platform]
        assert "sha256" in metadata["artifacts"][platform]
