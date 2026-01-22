"""Add a new release to the TUF targets directory.

Downloads artifacts, creates metadata with checksums, and updates latest pointers.
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def download_file(url: str, dest: Path) -> None:
    """Download a file from URL to destination."""
    print(f"Downloading {dest.name}...")
    try:
        urllib.request.urlretrieve(url, dest)
        size = dest.stat().st_size
        if size == 0:
            raise ValueError(f"Downloaded file is empty: {dest}")
        print(f"  ✓ {dest.name} ({size:,} bytes)")
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e


def sha256_file(path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def add_release(
    version: str,
    channel: str,
    windows_url: str,
    linux_url: str,
    macos_url: str,
    targets_dir: Path = Path("targets"),
) -> dict:
    """
    Add a release to the targets directory.

    Returns metadata dict for the release.
    """
    version_dir = targets_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    # Define artifacts
    artifacts = {
        "windows-x64": {
            "filename": "synodic-windows-x64.zip",
            "url": windows_url,
        },
        "linux-x64": {
            "filename": "synodic-linux-x64.tar.gz",
            "url": linux_url,
        },
        "macos-x64": {
            "filename": "synodic-macos-x64.tar.gz",
            "url": macos_url,
        },
    }

    # Download artifacts and calculate checksums
    print(f"\nDownloading artifacts for {version}...")
    for platform, info in artifacts.items():
        dest = version_dir / info["filename"]
        download_file(info["url"], dest)
        info["sha256"] = sha256_file(dest)
        print(f"  SHA256: {info['sha256']}")

    # Create metadata
    metadata = {
        "version": version,
        "channel": channel,
        "release_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifacts": {
            platform: {"filename": info["filename"], "sha256": info["sha256"]}
            for platform, info in artifacts.items()
        },
    }

    metadata_path = version_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n✓ Created {metadata_path}")

    # Update latest pointers
    print("\nUpdating latest pointers...")

    # Channel-specific latest
    channel_latest = targets_dir / f"latest-{channel}.txt"
    channel_latest.write_text(f"{version}\n")
    print(f"  ✓ {channel_latest} -> {version}")

    # Global latest (stable only)
    if channel == "stable":
        global_latest = targets_dir / "latest.txt"
        global_latest.write_text(f"{version}\n")
        print(f"  ✓ {global_latest} -> {version}")

    return metadata


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Add a release to TUF targets")
    parser.add_argument("--version", required=True, help="Release version")
    parser.add_argument(
        "--channel",
        required=True,
        choices=["stable", "development"],
        help="Release channel",
    )
    parser.add_argument("--windows-url", required=True, help="Windows artifact URL")
    parser.add_argument("--linux-url", required=True, help="Linux artifact URL")
    parser.add_argument("--macos-url", required=True, help="macOS artifact URL")
    parser.add_argument(
        "--targets-dir",
        type=Path,
        default=Path("targets"),
        help="Targets directory",
    )

    args = parser.parse_args()

    try:
        # Strip 'v' prefix if present
        version = args.version.lstrip("v")

        metadata = add_release(
            version=version,
            channel=args.channel,
            windows_url=args.windows_url,
            linux_url=args.linux_url,
            macos_url=args.macos_url,
            targets_dir=args.targets_dir,
        )

        print(f"\n{'=' * 60}")
        print(f"✓ Successfully added {args.channel} release {version}")
        print(json.dumps(metadata, indent=2))
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
