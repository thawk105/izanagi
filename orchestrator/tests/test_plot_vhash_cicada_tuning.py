"""Real-size matplotlib fixture for diagnostic Cicada figure layouts."""
from __future__ import annotations

import sys
import json
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt

from tools.plotting import plot_vhash_cicada_tuning as p
from tools.vhash_cicada_tuning import analysis as a, model as m


def _rows():
    rows = []
    all_genomes = [m.canonical(g) for g in m.genomes()]
    for w in ("W1", "W2", "W3", "W4"):
        for g in all_genomes:
            for gc in ((10, 100, 1000) if w == "W2" else (10,)):
                for rep in range(3):
                    rows.append({"stage": "j1", "perf": False, "exit_code": 0, "workload": w,
                                 "job_id": "j1-0",
                                 "genome": g, "gc_inter_us": gc, "records": 1_000_000,
                                 "throughput_tps": 100_000 + all_genomes.index(g) * 100 + rep * 10,
                                 "maxrss_kb": 500_000})
    selected = all_genomes[:3] + [m.canonical(m.CONTROL)]
    for w in ("W1", "W2", "W3", "W4"):
        for g in selected:
            for gc in ((10, 100, 1000) if w == "W5" else (1, 10, 100, 1000, 10000)):
                for rep in range(3):
                    rows.append({"stage": "j2", "perf": False, "exit_code": 0, "workload": w,
                                 "genome": g, "gc_inter_us": gc, "records": 1_000_000,
                                 "throughput_tps": 100_000 + selected.index(g) * 100 + rep * 10,
                                 "maxrss_kb": 500_000})
    for index, row in enumerate(rows):
        row.setdefault("schema", "vhash-cicada-diagnostic/v1")
        row.setdefault("job_id", "j2-0" if row["stage"] == "j2" else "j1-0")
        row["run_id"] = f"{index:05d}"
    return rows


def _summary(rows, raw=None):
    return {"schema": "vhash-cicada-diagnostic/v1", "input_runs": [str(raw)] if raw else [],
            "calibration": {w: {"records": 1_000_000} for w in m.WORKLOADS},
            "wait_smoke": {"alive": False, "reason": "wait_build_failed"},
            "workload_status": {"W5": {"status": "missing", "reason": "wait_build_failed"}},
            "condition_medians": {stage: a.condition_medians(rows, stage) for stage in ("j1", "j2")}}


def test_real_size_figures_and_overlap_rejection():
    rows = _rows()
    summary_data = _summary(rows)
    for builder in (p.make_j1_figure, p.make_j2_figure):
        fig, axes = builder(rows, summary_data)
        try:
            p.check_figure_layout(fig, axes)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                raw = root / "runs.jsonl"
                summary = root / "summary.json"
                raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
                summary.write_text(json.dumps(summary_data))
                prefix = root / "figure"
                p.publish(fig, axes, prefix, [raw], summary,
                          "j1" if builder is p.make_j1_figure else "j2", rows, summary_data)
                assert all(Path(str(prefix) + suffix).is_file()
                           for suffix in (".png", ".pdf", ".provenance.json"))
                provenance = json.loads(Path(str(prefix) + ".provenance.json").read_text())
                assert provenance["missing_workloads"]["W5"] == "wait_build_failed"
                assert provenance["raw_aggregates"]
                assert all("median_tps" in cell and "mean_tps" not in cell
                           for cell in provenance["raw_aggregates"].values())
            assert len(fig.axes) == (8 if builder is p.make_j1_figure else 4)
            assert ("J1 探索値" if builder is p.make_j1_figure else "J2 確認値") in fig._suptitle.get_text()
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


def test_measured_throughput_scale_layout():
    """Exercise the measured 16-genome and 3-genome x 4-GC shapes without raw files."""
    genomes = [m.canonical(g) for g in m.genomes()]
    buildable = {g for g in genomes if not (
        "INLINE_VERSION_OPT=1" in g and "INLINE_VERSION_PROMOTION=1" in g)}
    selected = set(genomes[:2]) | {m.canonical(m.CONTROL)}
    assert len(buildable) == 16
    assert len(selected) == 3
    scale = {"W1": 70_000, "W2": 500_000, "W3": 2_000_000, "W4": 4_700_000}
    rows = [r for r in _rows() if (
        r["stage"] == "j1" and r["genome"] in buildable or
        r["stage"] == "j2" and r["genome"] in selected and
        r["gc_inter_us"] in (10, 100, 1000, 10000))]
    for row in rows:
        row["throughput_tps"] = scale[row["workload"]] + (
            genomes.index(row["genome"]) * 100 + row["gc_inter_us"] % 100 +
            int(row["run_id"]) % 3 * 10)
    summary_data = _summary(rows)
    for stage, builder in (("j1", p.make_j1_figure), ("j2", p.make_j2_figure)):
        groups, _ = p._plot_data(rows, summary_data, stage)
        assert len(groups) == (16 * 6 if stage == "j1" else 4 * 3 * 4)
        fig, axes = builder(rows, summary_data)
        try:
            p.check_figure_layout(fig, axes)
            for axis, workload in zip(axes, scale):
                plotted = ([patch.get_height() for patch in axis.patches] if stage == "j1"
                           else [value for line in axis.lines for value in line.get_ydata()
                                 if line.get_marker() == "o"])
                assert plotted
                assert min(plotted) >= scale[workload] / p.TPS_PER_MTPS
                assert max(plotted) < (scale[workload] + 10_000) / p.TPS_PER_MTPS
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                raw, summary = root / "runs.jsonl", root / "summary.json"
                raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
                summary.write_text(json.dumps(summary_data))
                prefix = root / stage
                p.publish(fig, axes, prefix, [raw], summary, stage, rows, summary_data)
                provenance = json.loads(Path(str(prefix) + ".provenance.json").read_text())
                assert provenance["throughput_axis"]["unit"] == "Mtps"
                assert provenance["throughput_axis"]["tps_per_Mtps"] == 1_000_000
                assert all(provenance["raw_aggregates"][key]["median_tps"] ==
                           summary_data["condition_medians"][stage][key]["throughput_tps"]
                           for key in provenance["raw_aggregates"])
        finally:
            plt.close(fig)


def test_partial_workloads_and_input_binding():
    assert p._estimate([10, 30, 100]) == 30
    rows = [r for r in _rows() if r["workload"] in {"W1", "W2"}]
    for row in rows:
        row["exit_code"] = 0
    summary_data = _summary(rows)
    summary_data["workload_status"]["W4"] = {"status": "missing", "reason": "not_selected"}
    bad = {**rows[0], "throughput_tps": 9_999_999, "exit_code": 1}
    perf = {**rows[0], "throughput_tps": 9_999_999, "perf": True}
    measured = rows + [bad, perf]
    for stage, builder in (("j1", p.make_j1_figure), ("j2", p.make_j2_figure)):
        fig, axes = builder(measured, summary_data)
        try:
            p.check_figure_layout(fig, axes)
            assert len(fig.axes) == (4 if stage == "j1" else 2)
            assert "W4 (not_selected)" in [t.get_text() for t in fig.texts][-1]
        finally:
            plt.close(fig)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        raw = root / "runs.jsonl"
        raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        summary_path = root / "summary.json"
        summary_data["input_runs"] = [str(raw)]
        summary_path.write_text(json.dumps(summary_data))
        p.main(["--runs", str(raw), "--summary", str(summary_path),
                "--out-prefix", str(root / "valid")])
        assert (root / "valid-j1.provenance.json").is_file()
        assert (root / "valid-j2.provenance.json").is_file()
        extra = root / "extra.jsonl"
        extra.write_text(raw.read_text())
        try:
            p.main(["--runs", str(extra), "--summary", str(summary_path),
                    "--out-prefix", str(root / "plot")])
        except ValueError as exc:
            assert "input_runs" in str(exc)
        else:
            raise AssertionError("unanalysed runs accepted")


def test_j1_stock_buildable_genomes_and_missing_cells():
    all_genomes = [m.canonical(g) for g in m.genomes()]
    buildable = [g for g in all_genomes if not (
        "INLINE_VERSION_OPT=1" in g and "INLINE_VERSION_PROMOTION=1" in g)]
    assert len(buildable) == 16
    rows = [r for r in _rows() if r["stage"] == "j2" or r["genome"] in buildable]
    summary_data = _summary(rows)
    fig, axes = p.make_j1_figure(rows, summary_data)
    try:
        p.check_figure_layout(fig, axes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, summary = root / "runs.jsonl", root / "summary.json"
            raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            summary.write_text(json.dumps(summary_data))
            prefix = root / "j1"
            p.publish(fig, axes, prefix, [raw], summary, "j1", rows, summary_data)
            provenance = json.loads(Path(str(prefix) + ".provenance.json").read_text())
            assert provenance["missing_genome_count"] == 8
            assert provenance["missing_genomes"] == [g for g in all_genomes if g not in buildable]
            assert provenance["missing_cells"] == []
            assert len(provenance["raw_aggregates"]) == 16 * 6
            assert "J1 で測れなかった genome: 8 件" in provenance["caption"]
    finally:
        plt.close(fig)

    # A measured genome with one missing GC condition must remain a gap.
    omitted = buildable[0]
    partial = [r for r in rows if not (r["stage"] == "j1" and r["workload"] == "W2"
                                        and r["genome"] == omitted and r["gc_inter_us"] == 1000)]
    partial_summary = _summary(partial)
    groups, _ = p._plot_data(partial, partial_summary, "j1")
    _, missing_cells = p._j1_missing(groups, ["W1", "W2", "W3", "W4"])
    assert {"workload": "W2", "genome": omitted, "gc_inter_us": 1000} in missing_cells
    assert ("W2", omitted, 1000, 1_000_000) not in groups
    fig, axes = p.make_j1_figure(partial, partial_summary)
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, summary = root / "runs.jsonl", root / "summary.json"
            raw.write_text("\n".join(json.dumps(r) for r in partial) + "\n")
            summary.write_text(json.dumps(partial_summary))
            prefix = root / "partial"
            p.publish(fig, axes, prefix, [raw], summary, "j1", partial, partial_summary)
            provenance = json.loads(Path(str(prefix) + ".provenance.json").read_text())
            assert {"workload": "W2", "genome": omitted, "gc_inter_us": 1000} in provenance["missing_cells"]
            assert f"W2|{omitted}|1000|1000000" not in provenance["raw_aggregates"]
    finally:
        plt.close(fig)


def test_j2_summary_missing_condition_is_not_drawn():
    rows = _rows()
    summary_data = _summary(rows)
    candidate = next(r for r in rows if r["stage"] == "j2" and r["workload"] == "W1")
    key = f"W1|{candidate['genome']}|{candidate['gc_inter_us']}|{candidate['records']}"
    listed = summary_data["condition_medians"]["j2"]
    del listed[key]
    removed_genome = next(r["genome"] for r in rows if r["stage"] == "j2"
                          and r["workload"] == "W2" and r["genome"] != candidate["genome"])
    removed = {k for k in listed if k.startswith("W4|") or
               k.startswith(f"W2|{removed_genome}|") or k.startswith("W3|") and "|10000|" in k}
    for condition in removed:
        del listed[condition]
    fig, axes = p.make_j2_figure(rows, summary_data)
    try:
        p.check_figure_layout(fig, axes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, summary = root / "runs.jsonl", root / "summary.json"
            raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            summary.write_text(json.dumps(summary_data))
            prefix = root / "j2"
            p.publish(fig, axes, prefix, [raw], summary, "j2", rows, summary_data)
            provenance = json.loads(Path(str(prefix) + ".provenance.json").read_text())
            assert key not in provenance["raw_aggregates"]
            assert not removed.intersection(provenance["raw_aggregates"])
            assert provenance["missing_workloads"]["W4"] == "not_selected"
            assert {"workload": "W1", "genome": candidate["genome"],
                    "gc_inter_us": candidate["gc_inter_us"]} in provenance["missing_cells"]
            unavailable = {f"{c['workload']}|{c['genome']}|{c['gc_inter_us']}|{c['records']}"
                           for c in provenance["unavailable_conditions"]
                           if c["reason"] == "summary_missing"}
            assert {key, *removed} <= unavailable
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
