"""現行 2 層の snapshot であり, 未知の保留層の自動発見は保証しない.

This inventory covers registered layers only. It does not guarantee automatic
discovery of unknown hold layers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign.freeze_verification_hold import (  # noqa: E402
    HELD,
    HELD_CHECK_ID_COUNT,
    HELD_CHECK_IDS,
    HELD_CHECK_IDS_SHA256,
    REASON,
)
from orchestrator.tests.growth_test_holds import (  # noqa: E402
    RELEASE_EXPLICIT_USER_COMMAND_ONLY,
    RUN_GROWTH_HELD_TESTS_ENV,
    RUN_GROWTH_HELD_TESTS_TOKEN,
    RULING_2026_08_12_BUNDLE_3,
    growth_test_hold_inventory,
)


SCHEMA = "izanagi-hold-inventory/v1"
COMPLETENESS = "registered-layers-only"
_SNAPSHOT_HEADING = (
    "現行 2 層の snapshot であり, 未知の保留層の自動発見は保証しない"
)


def _production_layer() -> dict[str, object]:
    check_ids = sorted(HELD_CHECK_IDS)
    status = "held" if HELD else "active"
    return {
        "id": "production",
        "what": {
            "kind": "check-id-set",
            "check_ids": check_ids,
            "count": HELD_CHECK_ID_COUNT,
            "sha256": HELD_CHECK_IDS_SHA256,
        },
        "ruling": REASON["ruling"],
        "reason": dict(REASON),
        "release": {
            "condition": REASON["release_condition"],
            "mechanism": "manual-source-edit",
            "target": (
                "orchestrator/campaign/freeze_verification_hold.py:HELD"
            ),
        },
        "configured_status": status,
        "effective_status": status,
        "effective_status_assumption": (
            "source flag is authoritative for registered consumers"
        ),
        "bypass_surface": [],
    }


def _test_effective_status() -> str:
    value = os.environ.get(RUN_GROWTH_HELD_TESTS_ENV)
    if value in (None, ""):
        return "held"
    if value == RUN_GROWTH_HELD_TESTS_TOKEN:
        return "released-by-explicit-user-command"
    return "invalid-opt-in-rejected"


def _test_layer() -> dict[str, object]:
    source_inventory = growth_test_hold_inventory()
    holds = source_inventory["holds"]
    assert isinstance(holds, list)
    return {
        "id": "test",
        "what": {
            "kind": "node-id-set",
            "node_ids": [row["node_id"] for row in holds],
            "count": source_inventory["count"],
            "sha256": source_inventory["key_sha256"],
            "holds": holds,
        },
        "ruling": RULING_2026_08_12_BUNDLE_3,
        "reason": "Repository-growth-proportional tests are held by ruling.",
        "release": {
            "condition": RELEASE_EXPLICIT_USER_COMMAND_ONLY,
            "mechanism": "environment-exact-token",
            "target": RUN_GROWTH_HELD_TESTS_ENV,
            "env": RUN_GROWTH_HELD_TESTS_ENV,
            "token": RUN_GROWTH_HELD_TESTS_TOKEN,
        },
        "configured_status": "held-by-default",
        "effective_status": _test_effective_status(),
        "effective_status_assumption": (
            "pytest runner loads orchestrator/tests/conftest.py"
        ),
        "bypass_surface": [
            {
                "id": "plain-python-runner",
                "classification": "known-unresolved-bypass",
                "command_pattern": "python3 test_*.py",
                "effect": "bypasses-test-hold",
                "reason": "pytest conftest collection hook is not invoked",
                "tracking": "T-930",
            },
            {
                "id": "pytest-noconftest",
                "classification": "known-unresolved-bypass",
                "option": "--noconftest",
                "effect": "bypasses-test-hold",
                "reason": "pytest suite conftest is not loaded",
                "tracking": "T-930",
            },
            {
                "id": "pytest-confcutdir-below-suite",
                "classification": "known-unresolved-bypass",
                "option_pattern": (
                    "--confcutdir=<path-below-orchestrator/tests>"
                ),
                "effect": "bypasses-test-hold",
                "reason": "pytest stops conftest discovery below suite root",
                "tracking": "T-930",
            },
            {
                "id": "direct-test-function-call",
                "classification": "known-unresolved-bypass",
                "invocation": "import-test-module-and-call-function",
                "effect": "bypasses-test-hold",
                "reason": "pytest collection hook is not invoked",
                "tracking": "T-930",
            },
            {
                "id": "pegasus-dispatch-env-allowlist",
                "classification": "release-transport",
                "effect": "transports-test-release-opt-in",
                "env": RUN_GROWTH_HELD_TESTS_ENV,
                "target": "tools/pegasus/dispatch_compute.py:tests.env_allowlist",
            },
            {
                "id": "pegasus-pytest-addopts-transport",
                "classification": "bypass-transport",
                "effect": "transports-conftest-suppression-options",
                "env": "PYTEST_ADDOPTS",
                "options": ["--noconftest", "--confcutdir"],
                "target": "tools/pegasus/dispatch_compute.py:tests.env_allowlist",
            },
        ],
    }


def hold_inventory() -> dict[str, object]:
    """Return the deterministic snapshot of the two registered hold layers."""
    return {
        "schema": SCHEMA,
        "completeness": COMPLETENESS,
        "layers": [_production_layer(), _test_layer()],
    }


def render_human(inventory: dict[str, object]) -> str:
    lines = [
        _SNAPSHOT_HEADING,
        f"schema: {inventory['schema']}",
        f"completeness: {inventory['completeness']}",
    ]
    layers = inventory["layers"]
    assert isinstance(layers, list)
    for layer in layers:
        assert isinstance(layer, dict)
        lines.extend((
            "",
            f"layer: {layer['id']}",
            f"configured_status: {layer['configured_status']}",
            f"effective_status: {layer['effective_status']}",
            (
                "effective_status_assumption: "
                f"{layer['effective_status_assumption']}"
            ),
            f"ruling: {layer['ruling']}",
            "reason: " + json.dumps(
                layer["reason"], ensure_ascii=False, sort_keys=True,
            ),
            "release: " + json.dumps(
                layer["release"], ensure_ascii=False, sort_keys=True,
            ),
            "bypass_surface: " + json.dumps(
                layer["bypass_surface"], ensure_ascii=False, sort_keys=True,
            ),
        ))
        what = layer["what"]
        assert isinstance(what, dict)
        if layer["id"] == "production":
            lines.extend(f"check_id: {check_id}" for check_id in what["check_ids"])
        else:
            lines.append(
                "observed_seconds_note: observation only; not hold rationale"
            )
            for hold in what["holds"]:
                lines.append(
                    "node_id: {node_id} | reason: {reason} | ruling: {ruling} | "
                    "release_condition: {release_condition} | "
                    "hold_axis: {hold_axis} | "
                    "correctness_gate: {correctness_gate} | "
                    "observed_seconds: {measured_seconds} | "
                    "collateral_note: {collateral_note}".format(**hold)
                )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=_SNAPSHOT_HEADING)
    parser.add_argument(
        "--format", choices=("human", "json"), default="human",
    )
    args = parser.parse_args(argv)
    inventory = hold_inventory()
    if args.format == "json":
        print(json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_human(inventory), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
