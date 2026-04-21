"""Pipeline support for envoy-cli.

Allows chaining multiple envoy operations into a named, repeatable
pipeline that can be stored and executed in sequence.  Each step
describes an operation (set, delete, import, export, rotate, …) and
its arguments; the pipeline runner executes them in order, rolling
back completed steps on failure when possible.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PipelineError(Exception):
    """Raised when a pipeline operation fails."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class PipelineStep:
    """A single step inside a pipeline definition."""

    operation: str          # e.g. "set", "delete", "import", "export"
    args: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class PipelineResult:
    """Result of running a pipeline."""

    name: str
    steps_total: int
    steps_ok: int
    steps_failed: int
    errors: list[str] = field(default_factory=list)
    rolled_back: bool = False

    @property
    def ok(self) -> bool:
        return self.steps_failed == 0

    def summary(self) -> str:
        status = "OK" if self.ok else "FAILED"
        parts = [f"{self.name}: {status} ({self.steps_ok}/{self.steps_total} steps)"]
        if self.errors:
            parts += [f"  - {e}" for e in self.errors]
        if self.rolled_back:
            parts.append("  (rolled back)")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def _pipelines_dir(base_dir: Path) -> Path:
    d = base_dir / ".envoy" / "pipelines"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pipeline_path(base_dir: Path, name: str) -> Path:
    return _pipelines_dir(base_dir) / f"{name}.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def save_pipeline(base_dir: Path, name: str, steps: list[PipelineStep]) -> Path:
    """Persist a pipeline definition to disk.

    Returns the path of the saved file.
    """
    if not name or not name.isidentifier():
        raise PipelineError(f"Invalid pipeline name: {name!r}")
    if not steps:
        raise PipelineError("Pipeline must contain at least one step.")

    payload = {
        "name": name,
        "created_at": time.time(),
        "steps": [asdict(s) for s in steps],
    }
    path = _pipeline_path(base_dir, name)
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_pipeline(base_dir: Path, name: str) -> list[PipelineStep]:
    """Load a saved pipeline definition.

    Raises PipelineError if the pipeline does not exist.
    """
    path = _pipeline_path(base_dir, name)
    if not path.exists():
        raise PipelineError(f"Pipeline not found: {name!r}")
    raw = json.loads(path.read_text())
    return [
        PipelineStep(
            operation=s["operation"],
            args=s.get("args", {}),
            description=s.get("description", ""),
        )
        for s in raw.get("steps", [])
    ]


def list_pipelines(base_dir: Path) -> list[str]:
    """Return the names of all saved pipelines."""
    return sorted(p.stem for p in _pipelines_dir(base_dir).glob("*.json"))


def delete_pipeline(base_dir: Path, name: str) -> None:
    """Remove a saved pipeline.

    Raises PipelineError if the pipeline does not exist.
    """
    path = _pipeline_path(base_dir, name)
    if not path.exists():
        raise PipelineError(f"Pipeline not found: {name!r}")
    path.unlink()


def run_pipeline(
    base_dir: Path,
    name: str,
    executor: Any,  # callable(step: PipelineStep) -> None
    *,
    rollback: Any | None = None,  # callable(completed: list[PipelineStep]) -> None
) -> PipelineResult:
    """Execute every step of a pipeline in order.

    Parameters
    ----------
    base_dir:
        Root directory used to locate the pipeline definition.
    name:
        Name of the pipeline to run.
    executor:
        A callable that accepts a :class:`PipelineStep` and performs
        the described operation.  It should raise on failure.
    rollback:
        Optional callable that receives the list of successfully
        completed steps so the caller can undo them on failure.
    """
    steps = load_pipeline(base_dir, name)
    completed: list[PipelineStep] = []
    errors: list[str] = []
    rolled_back = False

    for step in steps:
        try:
            executor(step)
            completed.append(step)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Step '{step.operation}': {exc}")
            if rollback is not None:
                try:
                    rollback(completed)
                    rolled_back = True
                except Exception as rb_exc:  # noqa: BLE001
                    errors.append(f"Rollback failed: {rb_exc}")
            break

    return PipelineResult(
        name=name,
        steps_total=len(steps),
        steps_ok=len(completed),
        steps_failed=len(errors),
        errors=errors,
        rolled_back=rolled_back,
    )
