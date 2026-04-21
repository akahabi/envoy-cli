"""Integration helper: wire schedule_cmd into the main CLI group.

This module is imported by envoy/main.py to register the `schedule`
command group alongside the other top-level groups.
"""

from __future__ import annotations

from envoy.cli_schedule import schedule_cmd

__all__ = ["schedule_cmd"]
