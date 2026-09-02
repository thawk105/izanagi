from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.py"
PBS = ROOT / "tools" / "pegasus" / "probes" / "t2187_adaptive_const_probe.pbs"
PATCH = ROOT / "patches" / "cicada-adaptive-params.patch"
CCBENCH = ROOT / "external" / "ccbench"
PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"

SPEC = importlib.util.spec_from_file_location(
    "t2187_adaptive_const_probe_under_test", DRIVER
)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)

VALID_CELLS = (
    "none:0:100:1000:10,"
    "step0.5-upd10:1:0.5:1000:10,"
    "stock:1:100:1000:10"
)


def test_cells_parser_accepts_three_cells_and_normalizes_milliunits() -> None:
    assert probe.parse_cells(VALID_CELLS) == (
        probe.Cell("none", 0, 100.0, 1000, 10),
        probe.Cell("step0.5-upd10", 1, 0.5, 1000, 10),
        probe.Cell("stock", 1, 100.0, 1000, 10),
    )
    assert [cell.incr_milli for cell in probe.parse_cells(VALID_CELLS)] == [
        100_000,
        500,
        100_000,
    ]


@pytest.mark.parametrize(
    "cells",
    (
        "bad:1:0:1000:10",
        "bad:1:-0.5:1000:10",
        "bad:1:1:0:10",
        "bad:1:1:-1:10",
        "bad:1:1:1000:0",
        "bad:1:1:1000:-1",
    ),
    ids=(
        "zero-step",
        "negative-step",
        "zero-ceiling",
        "negative-ceiling",
        "zero-update",
        "negative-update",
    ),
)
def test_cells_parser_rejects_nonpositive_constants(cells: str) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(cells)


@pytest.mark.parametrize(
    "cells",
    (
        "dup:1:1:1000:10,dup:1:2:1000:10",
        "short:1:1:1000",
        "",
        "submilli:1:0.0001:1000:10",
    ),
    ids=("duplicate-label", "missing-field", "empty", "rounding-loss"),
)
def test_cells_parser_rejects_malformed_or_lossy_grids(cells: str) -> None:
    with pytest.raises(ValueError):
        probe.parse_cells(cells)


def test_is_stock_control_requires_exact_three_constants_and_backoff() -> None:
    stock = probe.Cell("stock", 1, 100.0, 1000, 10)
    assert probe.is_stock_control(stock)
    assert stock.is_stock_control

    assert not probe.is_stock_control(probe.Cell("step-drift", 1, 99.999, 1000, 10))
    assert not probe.is_stock_control(probe.Cell("ceiling-drift", 1, 100.0, 999, 10))
    assert not probe.is_stock_control(probe.Cell("update-drift", 1, 100.0, 1000, 11))
    assert not probe.is_stock_control(probe.Cell("disabled", 0, 100.0, 1000, 10))


def test_existing_out_is_rejected_before_site_or_measurement(tmp_path: Path) -> None:
    out = tmp_path / "already-there.json"
    out.write_text("do not overwrite\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        probe.main(["--cells", VALID_CELLS, "--out", str(out)])

    assert out.read_text(encoding="utf-8") == "do not overwrite\n"


def test_patch_applies_to_exact_pin_and_has_three_fail_closed_macros() -> None:
    assert PATCH.is_file()
    patch = PATCH.read_text(encoding="utf-8")
    assert re.search(r"\bIZANAGI_[A-Z0-9_]+\b", patch) is None

    head = subprocess.run(
        ["git", "-C", str(CCBENCH), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == PIN_FULL
    subprocess.run(
        ["git", "-C", str(CCBENCH), "apply", "--check", str(PATCH)],
        check=True,
        capture_output=True,
        text=True,
    )

    for macro in (
        "BACKOFF_INCR_MILLI",
        "BACKOFF_MAX_US",
        "BACKOFF_UPDATE_US",
    ):
        assert re.search(
            rf"^\+#ifndef {macro}\n\+#error ", patch, flags=re.MULTILINE
        )
        assert f"CCBENCH_{macro}" in patch
    assert patch.count("static_assert(") == 3


def test_pbs_restores_plus_lists_and_is_compute_only() -> None:
    subprocess.run(
        ["bash", "-n", str(PBS)],
        check=True,
        capture_output=True,
        text=True,
    )
    text = PBS.read_text(encoding="utf-8")
    assert "#PBS -l elapstim_req=00:40:00" in text
    assert (
        "# qsub -v 'IZANAGI_T2187_CELLS="
        "none:0:100:1000:10+stock:1:100:1000:10"
    ) in text
    assert "${CELLS_RAW//+/,}" in text
    assert "${WORKLOADS_RAW//+/,}" in text
    assert "${THREADS_RAW//+/,}" in text
    assert "write-heavy+balanced+read-heavy" in text
    assert "^bnode[0-9]+" in text
    assert "--cells \"$CELLS\"" in text
    assert "--workloads \"$WORKLOADS\"" in text
    assert "--threads \"$THREADS\"" in text


def test_pbs_rejects_legacy_semicolon_list_delimiter() -> None:
    text = PBS.read_text(encoding="utf-8")
    assert '"$CELLS_RAW" == *";"*' in text
    assert '"$WORKLOADS_RAW" == *";"*' in text
    assert r'^[0-9]+(\+[0-9]+)*$' in text
    assert "${CELLS_RAW//;/,}" not in text
    assert "${WORKLOADS_RAW//;/,}" not in text
    assert "${THREADS_RAW//;/,}" not in text


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
