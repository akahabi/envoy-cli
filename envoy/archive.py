"""Archive (export bundle) support: pack multiple profiles into a zip archive and unpack them."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Dict, List

from envoy.sync import _profile_path, push_profile, pull_profile


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


def pack(
    profiles: List[str],
    profiles_dir: Path,
    passphrase: str,
) -> bytes:
    """Pack *profiles* from *profiles_dir* into an in-memory zip archive.

    Returns raw bytes of the zip file.
    Raises ArchiveError if a profile file is missing.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest: Dict[str, str] = {}
        for name in profiles:
            path = _profile_path(profiles_dir, name)
            if not path.exists():
                raise ArchiveError(f"Profile not found: {name!r}")
            zf.write(path, arcname=f"{name}.enc")
            manifest[name] = f"{name}.enc"
        zf.writestr("manifest.json", json.dumps(manifest))
    return buf.getvalue()


def unpack(
    data: bytes,
    profiles_dir: Path,
    passphrase: str,
    overwrite: bool = False,
) -> List[str]:
    """Unpack profiles from *data* (zip bytes) into *profiles_dir*.

    Returns list of restored profile names.
    Raises ArchiveError on malformed archive or existing profile when
    *overwrite* is False.
    """
    profiles_dir.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO(data)
    restored: List[str] = []
    with zipfile.ZipFile(buf, mode="r") as zf:
        if "manifest.json" not in zf.namelist():
            raise ArchiveError("Archive is missing manifest.json")
        manifest: Dict[str, str] = json.loads(zf.read("manifest.json"))
        for name, arcname in manifest.items():
            dest = _profile_path(profiles_dir, name)
            if dest.exists() and not overwrite:
                raise ArchiveError(
                    f"Profile {name!r} already exists; use overwrite=True to replace."
                )
            dest.write_bytes(zf.read(arcname))
            restored.append(name)
    return restored
