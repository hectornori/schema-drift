"""Central registration of all sub-commands.

Import this module and call ``register_all`` to attach every known
subcommand to an :class:`argparse._SubParsersAction` object.
"""
from __future__ import annotations

import argparse
from typing import List, Callable

from schema_drift.commands import (
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    lint_cmd,
    validate_cmd,
)
from schema_drift.commands import summary_cmd

# Ordered list of (module_with_add_subparser,) tuples.
_COMMAND_MODULES: List = [
    baseline_cmd,
    compare_cmd,
    diff_cmd,
    export_cmd,
    history_cmd,
    lint_cmd,
    validate_cmd,
    summary_cmd,
]


def register_all(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach every sub-command to *subparsers*."""
    for mod in _COMMAND_MODULES:
        mod.add_subparser(subparsers)


def command_names() -> List[str]:
    """Return the list of registered command names in registration order."""
    # Build a temporary parser just to collect names.
    tmp = argparse.ArgumentParser()
    subs = tmp.add_subparsers()
    register_all(subs)
    return [action.dest if hasattr(action, 'dest') else ''
            for action in subs._group_actions]  # noqa: SLF001
