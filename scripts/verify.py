"""Verify TUF metadata consistency and integrity."""

import json
from pathlib import Path


def main() -> None:
    """Verify TUF repository metadata consistency."""
    metadata_dir = Path("metadata")
    errors: list[str] = []
    warnings: list[str] = []

    print("Verifying TUF repository metadata...\n")

    # Check required files exist
    required_files = ["root.json", "targets.json", "snapshot.json", "timestamp.json"]
    for filename in required_files:
        if not (metadata_dir / filename).exists():
            errors.append(f"Missing required file: {filename}")

    if errors:
        for error in errors:
            print(f"❌ {error}")
        return

    # Load metadata
    metadata = {}
    for filename in required_files:
        with open(metadata_dir / filename) as f:
            metadata[filename.replace(".json", "")] = json.load(f)

    # Verify root metadata
    root = metadata["root"]["signed"]
    print("Checking root.json...")

    # Check all required roles are defined
    required_roles = ["root", "targets", "snapshot", "timestamp"]
    for role in required_roles:
        if role not in root.get("roles", {}):
            errors.append(f"Root missing role definition: {role}")
        else:
            role_def = root["roles"][role]
            if not role_def.get("keyids"):
                errors.append(f"Role '{role}' has no keyids")
            if role_def.get("threshold", 0) < 1:
                errors.append(f"Role '{role}' has invalid threshold")

    # Check keys are defined
    keys = root.get("keys", {})
    for role in required_roles:
        if role in root.get("roles", {}):
            for keyid in root["roles"][role].get("keyids", []):
                if keyid not in keys:
                    errors.append(f"Role '{role}' references undefined key: {keyid[:16]}...")

    # Verify snapshot references
    print("Checking snapshot.json...")
    snapshot = metadata["snapshot"]["signed"]
    snapshot_meta = snapshot.get("meta", {})

    if "targets.json" not in snapshot_meta:
        warnings.append("Snapshot doesn't reference targets.json")

    # Verify timestamp references snapshot
    print("Checking timestamp.json...")
    timestamp = metadata["timestamp"]["signed"]
    timestamp_meta = timestamp.get("meta", {})

    if "snapshot.json" not in timestamp_meta:
        errors.append("Timestamp doesn't reference snapshot.json")

    # Check targets directory consistency
    print("Checking targets consistency...")
    targets = metadata["targets"]["signed"]
    targets_meta = targets.get("targets", {})
    targets_dir = Path("targets")

    if targets_dir.exists():
        # Check if files in targets/ are registered in targets.json
        for target_file in targets_dir.rglob("*"):
            if target_file.is_file():
                rel_path = target_file.relative_to(targets_dir).as_posix()
                if rel_path not in targets_meta:
                    warnings.append(f"Unregistered target file: {rel_path}")

    # Report results
    print("\n" + "=" * 60)

    if errors:
        print(f"\n❌ {len(errors)} error(s) found:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("\n✅ No errors found")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"   • {warning}")

    print()


if __name__ == "__main__":
    main()
