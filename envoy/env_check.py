"""Check for missing or extra env vars by comparing a store against a reference .env.example file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from envoy.import_ import from_dotenv
from envoy.store import get_env_vars


class EnvCheckError(Exception):
    pass


@dataclass
class EnvCheckResult:
    missing: List[str] = field(default_factory=list)   # in example, not in store
    extra: List[str] = field(default_factory=list)     # in store, not in example
    present: List[str] = field(default_factory=list)   # in both

    @property
    def ok(self) -> bool:
        return not self.missing and not self.extra

    def summary(self) -> str:
        lines = []
        if self.missing:
            lines.append(f"Missing ({len(self.missing)}): " + ", ".join(sorted(self.missing)))
        if self.extra:
            lines.append(f"Extra   ({len(self.extra)}): " + ", ".join(sorted(self.extra)))
        if self.present:
            lines.append(f"Present ({len(self.present)}): " + ", ".join(sorted(self.present)))
        return "\n".join(lines) if lines else "All vars match."


def check_against_example(
    store_path: Path,
    passphrase: str,
    example_path: Path,
    *,
    ignore_extra: bool = False,
) -> EnvCheckResult:
    """Compare store vars to keys defined in an .env.example file."""
    if not example_path.exists():
        raise EnvCheckError(f"Example file not found: {example_path}")
    if not store_path.exists():
        raise EnvCheckError(f"Store file not found: {store_path}")

    example_text = example_path.read_text(encoding="utf-8")
    example_vars: Dict[str, str] = from_dotenv(example_text)
    example_keys: Set[str] = set(example_vars.keys())

    store_vars: Dict[str, str] = get_env_vars(store_path, passphrase)
    store_keys: Set[str] = set(store_vars.keys())

    missing = sorted(example_keys - store_keys)
    extra = sorted(store_keys - example_keys) if not ignore_extra else []
    present = sorted(example_keys & store_keys)

    return EnvCheckResult(missing=missing, extra=extra, present=present)
