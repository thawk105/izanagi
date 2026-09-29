"""Real-size matplotlib fixture for diagnostic Cicada figure layouts."""
from __future__ import annotations

import sys
import json
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt

from tools.plotting import plot_vhash_cicada_tuning as p
from tools.vhash_cicada_tuning import model as m


def _rows():
    rows = []
    all_genomes = [m.canonical(g) for g in m.genomes()]
    for w in ("W1", "W2", "W3", "W4"):
        for g in all_genomes:
            for gc in ((10, 100, 1000) if w == "W2" else (10,)):
                for rep in range(3):
                    rows.append({"stage": "j1", "perf": False, "workload": w,
                                 "job_id": "j1-0",
                                 "genome": g, "gc_inter_us": gc, "records": 1_000_000,
                                 "throughput_tps": 100_000 + all_genomes.index(g) * 100 + rep * 10,
                                 "maxrss_kb": 500_000})
    selected = all_genomes[:3] + [m.canonical(m.CONTROL)]
    for w in m.WORKLOADS:
        for g in selected:
            for gc in ((10, 100, 1000) if w == "W5" else (1, 10, 100, 1000, 10000)):
                for rep in range(3):
                    rows.append({"stage": "j2", "perf": False, "workload": w,
                                 "genome": g, "gc_inter_us": gc, "records": 1_000_000,
                                 "throughput_tps": 100_000 + selected.index(g) * 100 + rep * 10,
                                 "maxrss_kb": 500_000})
    return rows


def test_real_size_figures_and_overlap_rejection():
    rows = _rows()
    for builder in (p.make_j1_figure, p.make_j2_figure):
        fig, axes = builder(rows, {"schema": "vhash-cicada-diagnostic/v1"})
        try:
            p.check_figure_layout(fig, axes)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                raw = root / "runs.jsonl"
                summary = root / "summary.json"
                raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
                summary.write_text(json.dumps({"schema": "vhash-cicada-diagnostic/v1"}))
                prefix = root / "figure"
                p.publish(fig, axes, prefix, [raw], summary,
                          "j1" if builder is p.make_j1_figure else "j2", rows, {})
                assert all(Path(str(prefix) + suffix).is_file()
                           for suffix in (".png", ".pdf", ".provenance.json"))
            axes[0].text(0.5, 0.5, "forced overlap", transform=axes[0].transAxes)
            axes[0].text(0.5, 0.5, "forced overlap", transform=axes[0].transAxes)
            try:
                p.check_figure_layout(fig, axes)
            except p.FigureLayoutError:
                pass
            else:
                raise AssertionError("overlap was not rejected")
        finally:
            plt.close(fig)


def _run():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:
                failed += 1
                print("FAIL", name, repr(exc))
    return failed


if __name__ == "__main__":
    sys.exit(_run())
