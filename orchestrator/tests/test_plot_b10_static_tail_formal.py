"""Formal B-10 tail evidence, rendered artists, and publication contracts."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import statistics
import sys
import tempfile
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from skiputil import Skip, skip


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "b10_tail_under_test", REPO / "tools/plotting/plot_b10_static_tail_formal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLOT = _load_module()
RESULTS = REPO / "docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md"


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seal(root):
    """Rehash synthetic bytes, including completion; never inject production hashes."""
    p = PLOT
    complete_path = root / p.COMPLETE_JSON
    complete = json.loads(complete_path.read_text())
    complete["artifacts"] = {Path(key).name: _hash(root / key) for key in (p.REPORT_JSON, p.REPORT_DAT)}
    complete_path.write_text(json.dumps(complete))
    return {key: _hash(root / key) for key in p.PINNED_SHA256}


def _fixture(tmp_path, **overrides):
    p = PLOT
    root = tmp_path / "measurements"
    (root / p.REPORT_JSON).parent.mkdir(parents=True)
    report = {"schema_version": p.REPORT_SCHEMA, "run_kind": p.RUN_KIND,
              "verdict": p.EXPECTED_VERDICT, "performance_certified": False,
              "spec_sha256": "a" * 64, "failures": [], "campaigns": [], "workloads": []}
    dat = [p.DAT_HEADER]
    for wi, workload in enumerate(p.WORKLOADS):
        lock = str(wi + 1) * 64
        campaign = {"workload": workload, "campaign_id": f"fixture-{workload}", "campaign_lock_digest": lock,
                    "admission": {"admission_status": "admitted",
                                  "campaign_path": f"/fixture/{p.GROUP_ID}-{workload}/campaigns/test"},
                    "identity": {"threads": 48, "records": 1000000, "extime_s": 3,
                                 "measurement_env": "pegasus",
                                 "workload_coordinates": {"ycsb_rratio": str(sorted(p.RRATIOS)[wi]),
                                     "ycsb_zipf_skew": "0.9", "ycsb_rmw": "0", "ycsb_max_ope": "10"},
                                 "grid": [{"backoff_us": x} for x in reversed(p.GRID_US)],
                                 "performance_reps_per_cell": p.REPS_PER_CELL,
                                 "build_admission": {"repo_stock_pin": "511c953"}},
                    "completion": {"status": "complete", "campaign_lock_sha256": lock,
                                   "wal_sha256": "b" * 64, "scheduler": {"job_id": f"fixture-{wi}.nqsv"}},
                    "points": []}
        stats = {}
        for xi, x in enumerate(p.GRID_US):
            reps = []
            for ri in range(p.REPS_PER_CELL):
                aborts = 20000 - xi * 2000 + ri * 3
                commits = 800000 + wi * 100000 + ri * 100
                tps = (wi + 1) * 1000000 - xi * 75000 + (ri - 2) * 1000
                rate = aborts / (aborts + commits)
                reps.append({"rep_index": ri, "abort_counts_": aborts, "commit_counts_": commits,
                             "throughput_tps": tps, "abort_rate_recomputed": rate})
                dat.append(f"{workload} {x} {ri} {aborts} {commits} {rate:.17g} {tps}")
            ts = [r["throughput_tps"] for r in reps]
            rates = [r["abort_counts_"] / (r["abort_counts_"] + r["commit_counts_"]) for r in reps]
            campaign["points"].append({"backoff_us": x, "use_perf": False, "reps": reps, "tps": ts,
                                       "correctness": [{"payload": {"certified": True, "anomalies": 0}}
                                                       for _ in range(p.REPS_PER_CELL)]})
            stats[str(x)] = {"throughput_tps_mean": statistics.mean(ts), "mean": statistics.mean(rates),
                             "throughput_tps_cv": statistics.stdev(ts) / statistics.mean(ts),
                             "abort_rate_cv": statistics.stdev(rates) / statistics.mean(rates),
                             "sample_sd": statistics.stdev(rates), "gate_passed": True}
        report["campaigns"].append(campaign)
        report["workloads"].append({"workload": workload, "state": "not-observed", "saturation_location": None,
            "local_flat_intervals": [], "statistics": stats,
            "intervals": [{"left_us": left, "right_us": right, "state": "declining", "qhat": -.5,
                           "qL": -.6, "qU": -.4, "L": 1 - 2**(-.4), "U": 1 - 2**(-.6), "U_flat": .03}
                          for left, right in zip(p.TAIL_GRID_US, p.TAIL_GRID_US[1:])]})
    report.update(overrides)
    (root / p.REPORT_JSON).write_text(json.dumps(report))
    (root / p.REPORT_DAT).write_text("\n".join(dat) + "\n")
    prereg = {"preregistration_commit": "c" * 40, "preregistration_document_blob_sha256": "d" * 64,
              "spec_sha256": report["spec_sha256"]}
    (root / p.COMPLETE_JSON).write_text(json.dumps({"spec_sha256": report["spec_sha256"],
                                                  "preregistrations": [prereg.copy() for _ in p.WORKLOADS]}))
    return root, _seal(root)


def _data(tmp_path):
    root, hashes = _fixture(tmp_path)
    return PLOT.load_measurements(root, expected_hashes=hashes)


def _change_report(root, change):
    path = root / PLOT.REPORT_JSON
    report = json.loads(path.read_text())
    change(report)
    path.write_text(json.dumps(report))
    return _seal(root)


def _reject(call, phrase=None):
    try:
        call()
    except PLOT.FigureDataError as exc:
        if phrase is not None:
            assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("invalid evidence was accepted")


def test_fixture_has_production_shape_and_recomputes_statistics(tmp_path):
    root, hashes = _fixture(tmp_path)
    data = PLOT.load_measurements(root, expected_hashes=hashes)
    assert len((root / PLOT.REPORT_DAT).read_text().splitlines()) == 121
    assert len(data["workloads"]) == 3
    assert sum(len(w["cells"]) for w in data["workloads"]) == 24
    assert data["correctness"] == {"records": 120, "certified": 120, "anomalies": 0}
    for w in data["workloads"]:
        assert len(w["intervals"]) == 6
        for c in w["cells"]:
            assert len(c["reps"]) == 5
            rates = [r["abort_counts_"] / (r["abort_counts_"] + r["commit_counts_"]) for r in c["reps"]]
            ts = [r["throughput_tps"] for r in c["reps"]]
            assert c["abort_rates"] == rates
            for key, vals in (("tps", ts), ("abort", rates)):
                assert math.isclose(c[key + "_mean"], statistics.mean(vals), rel_tol=1e-12)
                assert math.isclose(c[key + "_ci95_half"], 2.7764451051977987 * statistics.stdev(vals) / math.sqrt(5), rel_tol=1e-12)
                assert math.isclose(c[key + "_cv"], statistics.stdev(vals) / statistics.mean(vals), rel_tol=1e-12)
        assert w["tail_throughput_ratio"] == w["cells"][-1]["tps_mean"] / w["cells"][1]["tps_mean"]


def test_artist_series_have_exact_x_and_boundary_reference_is_separate(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    try:
        for s in fig._b10_tail_artist_series:
            if s["kind"] == "tail":
                assert s["x"] == [1250, 1768, 2500, 3535, 5000, 7070, 9999]
            elif s["kind"] == "boundary-reference":
                assert s["x"] == [1000]
        for ax in axes.flat:
            assert ax.get_xscale() == "log"
            assert list(ax.get_xticks()) == list(PLOT.GRID_US)
            tail, = [line for line in ax.lines if line.get_gid() == "tail"]
            boundary, = [line for line in ax.lines if line.get_gid() == "boundary-reference"]
            assert list(tail.get_xdata()) == [1250, 1768, 2500, 3535, 5000, 7070, 9999]
            assert list(boundary.get_xdata()) == [1000]
            assert boundary.get_markerfacecolor() == "none"
            assert boundary.get_linestyle() == "None"
            for line in ax.lines:
                assert not (1000 in line.get_xdata() and 1250 in line.get_xdata())
    finally:
        PLOT.plt.close(fig)


def test_interval_states_are_copied_not_recomputed(tmp_path):
    root, _ = _fixture(tmp_path)
    hashes = _change_report(root, lambda r: r["workloads"][0]["intervals"][0].update(state="indeterminate"))
    data = PLOT.load_measurements(root, expected_hashes=hashes)
    original = json.loads((root / PLOT.REPORT_JSON).read_text())["workloads"][0]["intervals"]
    assert data["workloads"][0]["intervals"] == original
    assert original[0]["L"] > .05
    fig, axes = PLOT.make_figure(data)
    try:
        assert any("1 indeterminate" in t.get_text() for t in axes[1, 0].texts)
        assert any(l.get_gid() == "interval-indeterminate" and l.get_linestyle() == ":" for l in axes[1, 0].lines)
        PLOT.check_figure_layout(fig, axes)
        outputs = [tmp_path / "fig9_test.png", tmp_path / "fig9_test.pdf"]
        for path in outputs:
            path.write_bytes(b"synthetic bytes for projection test")
        prov = PLOT.build_provenance(data, outputs, ["python3"])
        assert prov["workloads"][0]["intervals"] == original
        assert prov["artist_series"][4]["intervals"] == original
    finally:
        PLOT.plt.close(fig)


def test_real_figure_passes_layout_check(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        assert len(fig.axes) == 6
        PLOT.check_figure_layout(fig, axes)
    finally:
        PLOT.plt.close(fig)


def test_bbox_overlap_is_a_failure(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        PLOT.check_figure_layout(fig, axes)
        fig.text(.5, .5, "overlap alpha")
        fig.text(.5, .5, "overlap beta")
        try:
            PLOT.check_figure_layout(fig, axes)
        except PLOT.FigureLayoutError as exc:
            assert "overlap" in str(exc)
        else:
            raise AssertionError("layout overlap accepted")
    finally:
        PLOT.plt.close(fig)


def test_caption_contains_fixed_expression_and_certification_literal(tmp_path):
    caption = PLOT._caption(_data(tmp_path), "fig8_test")
    assert "Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of the current encoding." in caption
    assert "performance_certified: false" in caption
    assert PLOT.GROUP_ID in caption
    assert PLOT.COMPARISON_WARNING in caption
    assert "18/18 intervals" in caption
    assert "Pegasus compute nodes" in caption
    assert "t2418-explore" in caption
    assert "nothing beyond" in caption
    assert "fixture-0.nqsv, fixture-1.nqsv, fixture-2.nqsv" in caption


def test_caption_avoids_forbidden_saturation_claims(tmp_path):
    caption = PLOT._caption(_data(tmp_path), "fig8_test")
    source = PLOT.GENERATOR.read_text()
    for phrase in ("does not saturate", "no saturation point", "never saturates", "saturation-free", "saturates"):
        assert phrase not in caption.lower()
        assert phrase not in source.lower()


def test_caption_figure_number_comes_from_prefix(tmp_path):
    data = _data(tmp_path)
    assert PLOT._caption(data, "fig8_test").startswith("Figure 8.")
    assert PLOT._caption(data, "fig9_test").startswith("Figure 9.")
    _reject(lambda: PLOT._caption(data, "figX_test"))


def test_external_input_hash_drift_is_rejected(tmp_path):
    root, hashes = _fixture(tmp_path)
    # Whitespace keeps semantics intact, so only the byte pin detects this drift.
    path = root / PLOT.COMPLETE_JSON
    path.write_text(path.read_text() + "\n")
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "SHA-256")


def test_pinned_hashes_are_used_when_no_override(tmp_path):
    root, _ = _fixture(tmp_path)
    # completion record は production pin を名乗り、byte 比較だけが拒否する単一理由 fixture。
    complete_path = root / PLOT.COMPLETE_JSON
    complete = json.loads(complete_path.read_text())
    complete["artifacts"] = {
        Path(path).name: PLOT.PINNED_SHA256[path]
        for path in (PLOT.REPORT_JSON, PLOT.REPORT_DAT)
    }
    complete_path.write_text(json.dumps(complete))
    _reject(lambda: PLOT.load_measurements(root), "SHA-256 mismatch")


def test_performance_certified_true_is_rejected(tmp_path):
    root, hashes = _fixture(tmp_path, performance_certified=True)
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "performance_certified")


def test_verdict_mismatch_is_rejected(tmp_path):
    root, hashes = _fixture(tmp_path, verdict="fixture-invalid")
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "verdict")


def test_dat_with_missing_row_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    path = root / PLOT.REPORT_DAT
    path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
    hashes = _seal(root)
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "120 rows")


def test_dat_abort_rate_disagreeing_with_counters_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    path = root / PLOT.REPORT_DAT
    lines = path.read_text().splitlines()
    fields = lines[1].split()
    fields[5] = "0.4"
    lines[1] = " ".join(fields)
    path.write_text("\n".join(lines) + "\n")
    hashes = _seal(root)
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "numeric crosscheck")


def test_boundary_reference_inside_interval_set_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    hashes = _change_report(root, lambda r: r["workloads"][0]["intervals"][0].update(left_us=1000))
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "interval grid")


def test_uncertified_correctness_record_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    hashes = _change_report(root, lambda r: r["campaigns"][0]["points"][0]["correctness"][0]["payload"].update(certified=False))
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "uncertified")


def test_group_id_absent_from_campaign_path_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    hashes = _change_report(root, lambda r: r["campaigns"][0]["admission"].update(campaign_path="/other/campaigns/test"))
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "group binding")


def test_statistics_mismatch_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    hashes = _change_report(root, lambda r: r["workloads"][0]["statistics"]["1250"].update(throughput_tps_mean=1))
    _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes), "numeric crosscheck")


def test_pinned_input_hashes_match_results_document():
    text = RESULTS.read_text()
    table = text.split("### 4.1", 1)[1].split("### 4.2", 1)[0]
    for path, digest in PLOT.PINNED_SHA256.items():
        rows = [line for line in table.splitlines() if f"`{path}`" in line]
        assert len(rows) == 1
        assert re.findall(r"`([0-9a-f]{64})`", rows[0]) == [digest]


def test_cli_writes_three_outputs_and_provenance_closure(tmp_path):
    root, hashes = _fixture(tmp_path)
    prefix = tmp_path / "fig9_fixture"
    assert PLOT.main(["--measurement-root", str(root), str(prefix)], expected_hashes=hashes) == 0
    paths = [Path(f"{prefix}{s}") for s in (".png", ".pdf", ".provenance.json")]
    assert all(path.is_file() for path in paths)
    prov = json.loads(paths[2].read_text())
    PLOT.validate_external_sources(prov, root)
    _reject(lambda: PLOT.validate_repo_closure(prov, REPO), "external pins")
    PLOT.validate_repo_closure(prov, REPO, expected_hashes=hashes)
    argv = prov["reproduction"]["argv"]
    assert argv[:3] == ["python3", PLOT.GENERATOR_PATH, "--measurement-root"]
    assert Path(argv[3]) == root.resolve()
    assert not Path(argv[4]).is_absolute()
    assert (REPO / argv[4]).resolve() == prefix
    assert prov["caption"].startswith("Figure 9.")
    changed = copy.deepcopy(prov)
    changed["artist_series"][0]["y"][0] += 1
    _reject(lambda: PLOT.validate_repo_closure(changed, REPO, expected_hashes=hashes), "artist")
    changed = copy.deepcopy(prov)
    changed["caption"] += " drift"
    _reject(lambda: PLOT.validate_repo_closure(changed, REPO, expected_hashes=hashes), "caption")
    paths[0].write_bytes(paths[0].read_bytes() + b"drift")
    _reject(lambda: PLOT.validate_repo_closure(prov, REPO, expected_hashes=hashes), "output closure")


def test_cli_rejects_prefix_without_fig_number(tmp_path):
    root, hashes = _fixture(tmp_path)
    prefix = tmp_path / "figX_invalid"
    assert PLOT.main(["--measurement-root", str(root), str(prefix)], expected_hashes=hashes) == 2
    assert not list(tmp_path.glob("figX_invalid*"))


def test_layout_failure_publishes_nothing(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    prefix = tmp_path / "fig8_overlap"
    try:
        fig.text(.5, .5, "overlap one")
        fig.text(.5, .5, "overlap two")
        _reject(lambda: PLOT._publish_outputs(fig, axes, prefix, data, []), "overlap")
        assert not list(tmp_path.glob("*fig8_overlap*"))
    finally:
        PLOT.plt.close(fig)


def test_malformed_fields_and_counterpart_mismatches_are_rejected(tmp_path):
    mutations = [
        lambda r: r.pop("performance_certified"),
        lambda r: r.update(performance_certified=0),
        lambda r: r.update(failures=["failed"]),
        lambda r: r["campaigns"][0]["points"][0]["reps"][0].update(abort_counts_=True),
        lambda r: r["campaigns"][0]["points"][0]["reps"][0].update(throughput_tps=float("nan")),
        lambda r: r["campaigns"][0]["points"][0]["correctness"][0]["payload"].update(anomalies=1),
        lambda r: r["campaigns"][0]["points"][0]["reps"][0].update(rep_index=1),
        lambda r: r["campaigns"][0]["points"][0].update(backoff_us=1250),
        lambda r: r["workloads"][0]["intervals"][0].update(L=.9),
        lambda r: r["workloads"][0]["statistics"]["1250"].update(abort_rate_cv=10),
        lambda r: r["workloads"][0]["statistics"]["1250"].update(gate_passed=False),
    ]
    for index, mutation in enumerate(mutations):
        root, _ = _fixture(tmp_path / str(index))
        hashes = _change_report(root, mutation)
        _reject(lambda: PLOT.load_measurements(root, expected_hashes=hashes))


def test_real_root_loads_and_matches_results_document_when_present():
    if not PLOT.DEFAULT_ROOT.exists():
        skip("formal measurement root is unavailable")
    data = PLOT.load_measurements(PLOT.DEFAULT_ROOT)
    assert data["report"]["verdict"] == "not-observed-in-any-workload"
    assert sum(len(w["cells"]) for w in data["workloads"]) == 24
    assert data["workloads"][0]["cells"][0]["tps_mean"] == 993106.4
    ratios = [f"{w['tail_throughput_ratio']:.3f}" for w in data["workloads"]]
    assert ratios == ["0.444", "0.481", "0.400"]
    text = RESULTS.read_text()
    assert "993,106.4" in text and all(ratio in text for ratio in ratios)


def test_landed_fig8_repo_closure_and_caption_when_present():
    prefix = REPO / "docs/paper-story/figures/fig8_b10_static_tail_not_observed"
    paths = [Path(f"{prefix}{s}") for s in (".png", ".pdf", ".provenance.json")]
    readme = (prefix.parent / "README.md").read_text()
    if not any(path.exists() for path in paths) and prefix.name not in readme:
        skip("fig8 integration artifacts are parent-owned and not landed yet")
    assert all(path.is_file() for path in paths), "fig8 integration bundle is incomplete"
    prov = json.loads(paths[2].read_text())
    PLOT.validate_repo_closure(prov, REPO)
    assert prov["caption"] in readme


def _run():
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        node = f"{Path(__file__).name}::{test.__name__}"
        try:
            with tempfile.TemporaryDirectory(prefix="b10-tail-test-") as directory:
                kwargs = {"tmp_path": Path(directory)} if "tmp_path" in inspect.signature(test).parameters else {}
                test(**kwargs)
            print(f"PASS {node}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {node}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {node}: {exc}")
            traceback.print_exc()
            failed += 1
        except Exception as exc:
            print(f"ERROR {node}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
            errors += 1
    print(f"{passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
    return 1 if failed or errors else 0


if __name__ == "__main__":
    sys.exit(_run())
