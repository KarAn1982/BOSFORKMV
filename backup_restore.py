import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).parent
DIST = ROOT / "dist"
BACKUP_DIR = ROOT / "backups"
SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
}
SECRET_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_release(dist=DIST):
    archives = sorted(dist.glob("bosfor-prototype-release-*.zip"))
    manifests = sorted(dist.glob("bosfor-prototype-release-*.manifest.json"))
    if not archives or not manifests:
        raise FileNotFoundError("release_bundle_missing")
    archive = archives[-1]
    expected_manifest = archive.with_suffix(".manifest.json")
    manifest = expected_manifest if expected_manifest.exists() else manifests[-1]
    return archive, manifest


def is_secret(path):
    return path.name.lower() in SECRET_NAMES or path.suffix.lower() in SECRET_SUFFIXES


def operational_files(root=ROOT, dist=DIST):
    release, release_manifest = latest_release(dist)
    files = [
        release,
        release_manifest,
        root / "deployment" / "backup-policy.json",
        root / "BOSFOR_REDIRECTS_PRODUCTION.json",
        root / "BOSFOR_MIGRATION_RUNBOOK.md",
        root / "BOSFOR_STAGING_AND_OPERATIONS.md",
    ]
    files.extend(
        item
        for item in (root / "deployment").rglob("*")
        if item.is_file()
    )
    unique = []
    seen = set()
    for item in files:
        resolved = item.resolve()
        if resolved in seen:
            continue
        if is_secret(item):
            raise ValueError(f"secret_file_rejected:{item.name}")
        if not item.exists():
            raise FileNotFoundError(f"backup_source_missing:{item}")
        seen.add(resolved)
        unique.append(item)
    return unique


def create_backup(output=None, root=ROOT, dist=DIST):
    files = operational_files(root, dist)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(output or BACKUP_DIR / f"bosfor-application-backup-{timestamp}.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for item in sorted(files):
        relative = item.relative_to(root).as_posix()
        records.append(
            {
                "path": relative,
                "bytes": item.stat().st_size,
                "sha256": sha256(item),
            }
        )
    manifest = {
        "type": "application_configuration_backup",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "restore_scope": [
            "immutable_release",
            "deployment_configuration",
            "migration_manifest",
            "operational_runbooks",
        ],
        "excluded_scope": [
            "database",
            "WAL",
            "production_media",
            "secrets",
            "CRM data",
        ],
        "file_count": len(records),
        "total_bytes": sum(item["bytes"] for item in records),
        "files": records,
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            archive.write(root / record["path"], record["path"])
        archive.writestr(
            "backup-manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return output, manifest


def safe_target(root, member):
    pure = PurePosixPath(member)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"unsafe_archive_path:{member}")
    target = (root / Path(*pure.parts)).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError(f"unsafe_archive_path:{member}")
    return target


def verify_and_restore(archive_path, restore_dir):
    archive_path = Path(archive_path)
    restore_dir = Path(restore_dir)
    errors = []
    restored = []
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if "backup-manifest.json" not in names:
            raise ValueError("backup_manifest_missing")
        manifest = json.loads(archive.read("backup-manifest.json"))
        expected = {item["path"]: item for item in manifest["files"]}
        unexpected = set(names) - set(expected) - {"backup-manifest.json"}
        if unexpected:
            errors.append(f"unexpected_files:{len(unexpected)}")
        for name in names:
            safe_target(restore_dir, name)
        for relative, record in expected.items():
            if relative not in names:
                errors.append(f"missing:{relative}")
                continue
            if is_secret(Path(relative)):
                errors.append(f"secret_in_backup:{relative}")
                continue
            content = archive.read(relative)
            if len(content) != record["bytes"]:
                errors.append(f"size_mismatch:{relative}")
            if hashlib.sha256(content).hexdigest() != record["sha256"]:
                errors.append(f"checksum_mismatch:{relative}")
            target = safe_target(restore_dir, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            restored.append(relative)
    release_archives = sorted(restore_dir.glob("dist/bosfor-prototype-release-*.zip"))
    if not release_archives:
        errors.append("restored_release_missing")
    else:
        with zipfile.ZipFile(release_archives[-1]) as release:
            release_names = set(release.namelist())
            for required in [
                "release-manifest.json",
                "prototype_server.js",
                "website/index.html",
                "website/sitemap.xml",
            ]:
                if required not in release_names:
                    errors.append(f"restored_release_required_missing:{required}")
    return {
        "ok": not errors,
        "archive": str(archive_path),
        "restored_to": str(restore_dir),
        "restored_files": len(restored),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--output")
    verify = subparsers.add_parser("verify")
    verify.add_argument("archive")
    verify.add_argument("--restore-dir")
    args = parser.parse_args()
    if args.command == "create":
        archive, manifest = create_backup(args.output)
        result = {
            "ok": True,
            "archive": str(archive),
            "file_count": manifest["file_count"],
            "total_bytes": manifest["total_bytes"],
        }
    else:
        if args.restore_dir:
            result = verify_and_restore(args.archive, args.restore_dir)
        else:
            with tempfile.TemporaryDirectory(prefix="bosfor-restore-") as temporary:
                result = verify_and_restore(args.archive, temporary)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
