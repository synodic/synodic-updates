"""Show TUF repository status and metadata summary."""

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    """Display current TUF repository status."""
    metadata_dir = Path("metadata")

    if not metadata_dir.exists():
        print("❌ No metadata directory found")
        return

    print("=" * 60)
    print("TUF Repository Status")
    print("=" * 60)

    # Check each metadata file
    for role in ["root", "targets", "snapshot", "timestamp"]:
        file_path = metadata_dir / f"{role}.json"
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)

            signed = data.get("signed", {})
            version = signed.get("version", "?")
            expires = signed.get("expires", "?")

            # Parse expiry and check status
            status = "✅"
            if expires != "?":
                try:
                    exp_date = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    days_left = (exp_date - now).days

                    if days_left < 0:
                        status = "❌ EXPIRED"
                    elif days_left < 30:
                        status = f"⚠️  {days_left} days left"
                    else:
                        status = f"✅ {days_left} days left"
                except ValueError:
                    pass

            print(f"\n{role.upper()}")
            print(f"  Version: {version}")
            print(f"  Expires: {expires}")
            print(f"  Status:  {status}")
        else:
            print(f"\n{role.upper()}")
            print("  ❌ Not found")

    # Check targets directory
    targets_dir = Path("targets")
    if targets_dir.exists():
        versions = [d.name for d in targets_dir.iterdir() if d.is_dir()]
        print(f"\n{'=' * 60}")
        print(f"Targets: {len(versions)} version(s)")

        # Show latest pointers
        for latest_file in ["latest.txt", "latest-stable.txt", "latest-development.txt"]:
            latest_path = targets_dir / latest_file
            if latest_path.exists():
                print(f"  {latest_file}: {latest_path.read_text().strip()}")

        if versions:
            print(f"  Versions: {', '.join(sorted(versions, reverse=True)[:5])}")
            if len(versions) > 5:
                print(f"            ... and {len(versions) - 5} more")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
