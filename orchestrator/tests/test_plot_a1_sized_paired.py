"""A-1 sized paired leaf, rendered artists, and publication contracts."""
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
        "a1_sized_under_test", REPO / "tools/plotting/plot_a1_sized_paired.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PLOT = _load_module()
RESULTS = REPO / PLOT.CAPTION_SOURCE


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _seal(root):
    p = PLOT
    _write(root / p.COMPLETE_JSON, {
        "schema_version": p.COMPLETE_SCHEMA,
        "files": {name: _hash(root / p.LEAF_DIR / name)
                  for name in ("README.md", "receipt.json", "result.json")}})
    return {path: _hash(root / path) for path in p.PINNED_SHA256}


def _statistics(plan, baseline, variant):
    p = PLOT
    differences = [v - b for v, b in zip(variant, baseline)]
    mean = statistics.fmean(differences)
    variance = sum((d - mean) ** 2 for d in differences) / (p.REPS - 1)
    sd = math.sqrt(variance)
    k = float(plan["k"])
    h = k * sd / math.sqrt(p.REPS)
    baseline_mean = statistics.fmean(baseline)
    boundary = p.FLOOR_FRACTION * baseline_mean
    classification = ("resolved-above-floor" if abs(mean) - h > boundary else
                      "bounded-below-floor" if abs(mean) + h <= boundary else "unresolved")
    return {"n": p.REPS, "df": p.DF, "k": k, "pairing_design": p.PAIRING_DESIGN,
            "contrast": p.CONTRAST, "floor_fraction": p.FLOOR_FRACTION,
            "mean_signed_positional_difference_tps": mean,
            "sample_sd_positional_difference_tps": sd,
            "sample_variance_positional_difference_tps2": variance,
            "descriptive_half_width_tps": h, "descriptive_interval_tps": [mean - h, mean + h],
            "baseline_mean_tps": baseline_mean, "floor_boundary_tps": boundary,
            "planned_sigma_tps": float(plan["planned_sigma_tps"]),
            "variance_plan_breach": sd > float(plan["planned_sigma_tps"]),
            "classification": classification,
            "pairs": [{"pair_index": i, f"{p.VARIANT_ARMS[plan['name']]}_tps": v,
                       f"{p.BASELINE_ARM}_tps": b, "signed_difference_tps": v - b}
                      for i, (v, b) in enumerate(zip(variant, baseline))]}


def _fixture(tmp_path):
    p = PLOT
    root = tmp_path / "repo"
    policy_path = root / p.POLICY_PATH
    policy_path.parent.mkdir(parents=True)
    policy_path.write_bytes((REPO / p.POLICY_PATH).read_bytes())
    policy = json.loads(policy_path.read_text())
    source = root / p.CAPTION_SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("Synthetic caption wording authority.\n")
    generator = root / p.GENERATOR_PATH
    generator.parent.mkdir(parents=True)
    generator.write_bytes(p.GENERATOR.read_bytes())
    result = {"schema_version": p.RESULT_SCHEMA, "study_id": p.STUDY_ID,
              "pairing_design": p.PAIRING_DESIGN, "complete": True, "all_workloads_terminal": True,
              "formal": False, "promotion_prohibited": True, "measurement_error": None,
              "policy_sha256": _hash(policy_path), "workload_reps": dict.fromkeys(p.WORKLOADS, p.REPS),
              "source_binding": {"measurement_source_commit": "a" * 40},
              "limitations": [f"synthetic limitation {i}" for i in range(5)], "workloads": []}
    jobs = []
    for wi, (name, plan) in enumerate(zip(p.WORKLOADS, policy["workloads"])):
        baseline = [float((wi + 2) * 1000000 + i * 50) for i in range(p.REPS)]
        # Asymmetry makes a mean-to-median mutation visible.
        differences = [(1 if wi < 2 else -1) * (400000 + i * i * 30) for i in range(p.REPS)]
        variant = [b + d for b, d in zip(baseline, differences)]
        stat = _statistics(plan, baseline, variant)
        arms = {}
        for arm, values in ((p.VARIANT_ARMS[name], variant), (p.BASELINE_ARM, baseline)):
            flags = next(a["flags"] for a in plan["arms"] if a["name"] == arm)
            arms[arm] = {
                "raw_tps": values, "expected_reps": p.REPS, "observed_reps": p.REPS,
                "actual_rounds": 1, "attempt_count": 1, "unstable": False, "valid": True, "errors": [],
                "genome": "silo|" + ",".join(f"{key}={flags[key]}" for key in sorted(flags)),
                "correctness_evidence": {"certified": [True], "verify_configs": ["legacy"],
                                        "verify_done_frames": [{"raw_sha256": "b" * 64, "stage": "verify_done"}]}}
        result["workloads"].append({"workload": name, "arms": arms, "statistics": stat,
                                    "valid": True, "errors": [],
                                    "terminal_result": {"status": "valid", "classification": stat["classification"]}})
        jobs.append({"workload": name, "request_id": f"fixture-{wi}.nqsv",
                     "reservation_binding": {"host": f"fixture-node-{wi}"}})
    _write(root / p.RESULT_JSON, result)
    _write(root / p.RECEIPT_JSON, {"schema_version": p.RECEIPT_SCHEMA, "study_id": p.STUDY_ID,
                                  "formal": False, "promotion_prohibited": True,
                                  "policy": {"sha256": _hash(policy_path)}, "job_executions": jobs})
    (root / p.LEAF_DIR / "README.md").write_text("Synthetic leaf.\n")
    return root, _seal(root)


def _data(tmp_path):
    root, hashes = _fixture(tmp_path)
    return PLOT.load_leaf(root, expected_hashes=hashes)


def _change(root, change):
    path = root / PLOT.RESULT_JSON
    result = json.loads(path.read_text())
    change(result)
    _write(path, result)
    return _seal(root)


def _reject(call, phrase=None):
    try:
        call()
    except PLOT.FigureDataError as exc:
        if phrase is not None:
            assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("invalid evidence was accepted")


def _reject_changed(tmp_path, change, phrase):
    root, _ = _fixture(tmp_path)
    hashes = _change(root, change)
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes), phrase)


def _provenance(data, tmp_path):
    outputs = [tmp_path / "fig9_test.png", tmp_path / "fig9_test.pdf"]
    for path in outputs:
        path.write_bytes(b"synthetic output bytes")
    return PLOT.build_provenance(data, outputs, ["python3", PLOT.GENERATOR_PATH])


def test_fixture_has_production_shape_and_recomputes_statistics(tmp_path):
    root, hashes = _fixture(tmp_path)
    data = PLOT.load_leaf(root, expected_hashes=hashes)
    result = json.loads((root / PLOT.RESULT_JSON).read_text())
    assert tuple(c["workload"] for c in data["workloads"]) == PLOT.WORKLOADS
    for c, w in zip(data["workloads"], result["workloads"]):
        assert len(c["pairs"]) == PLOT.REPS
        assert all(len(a["raw_tps"]) == PLOT.REPS for a in w["arms"].values())
        differences = [p["variant_tps"] - p["baseline_tps"] for p in c["pairs"]]
        assert c["mean"] == statistics.fmean(differences)
        assert math.isclose(c["sd"], statistics.stdev(differences), rel_tol=1e-12)
        assert c["h"] == c["k"] * c["sd"] / math.sqrt(PLOT.REPS)
        assert c["B"] == .03 * statistics.fmean(p["baseline_tps"] for p in c["pairs"])
        assert c["mean"] != statistics.median(differences)


def test_artist_series_equal_provenance_cells_and_leaf_statistics(tmp_path):
    root, hashes = _fixture(tmp_path)
    data = PLOT.load_leaf(root, expected_hashes=hashes)
    leaf = json.loads((root / PLOT.RESULT_JSON).read_text())
    fig, axes = PLOT.make_figure(data)
    try:
        prov = _provenance(data, tmp_path)
        assert fig._a1_artist_series == prov["artist_series"]
        for ax, s, c, w in zip(axes.flat, prov["artist_series"], prov["workloads"], leaf["workloads"]):
            for key, field in PLOT.STAT_FIELDS.items():
                assert math.isclose(c[key], w["statistics"][field], rel_tol=1e-12)
            assert s["mean"] == c["mean"] / 1e6
            assert s["interval"] == [v / 1e6 for v in c["interval"]]
            assert s["floor"] == [-c["B"] / 1e6, c["B"] / 1e6]
            assert s["zero"] == 0
            lines = {line.get_gid(): line for line in ax.lines if line.get_gid() != "floor"}
            assert list(lines["mean"].get_ydata()) == [c["mean"] / 1e6] * 2
            assert list(lines["zero"].get_ydata()) == [0, 0]
            assert [float(line.get_ydata()[0]) for line in ax.lines if line.get_gid() == "floor"] == s["floor"]
            assert list(lines["pairs"].get_xdata()) == s["x"] == list(range(PLOT.REPS))
            assert list(lines["pairs"].get_ydata()) == s["y"] == [p["signed_difference"] / 1e6 for p in c["pairs"]]
            assert lines["pairs"].get_markerfacecolor() == "none"
            assert lines["pairs"].get_linestyle() == "None"
            patch, = [p for p in ax.patches if p.get_gid() == "interval"]
            bbox = patch.get_extents().transformed(ax.transData.inverted())
            assert math.isclose(bbox.y0, s["interval"][0], abs_tol=1e-12)
            assert math.isclose(bbox.y1, s["interval"][1], abs_tol=1e-12)
            assert list(ax.get_xticks()) == list(range(0, PLOT.REPS, 5))
    finally:
        PLOT.plt.close(fig)


def test_real_figure_passes_layout_check(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        assert axes.shape == (1, 3)
        PLOT.check_figure_layout(fig, axes)
    finally:
        PLOT.plt.close(fig)


def test_bbox_overlap_is_a_failure(tmp_path):
    fig, axes = PLOT.make_figure(_data(tmp_path))
    try:
        PLOT.check_figure_layout(fig, axes)
        fig.text(.5, .5, "overlap alpha")
        fig.text(.5, .5, "overlap beta")
        _reject(lambda: PLOT.check_figure_layout(fig, axes), "overlap")
    finally:
        PLOT.plt.close(fig)


def test_layout_failure_publishes_nothing(tmp_path):
    data = _data(tmp_path)
    fig, axes = PLOT.make_figure(data)
    prefix = tmp_path / "fig9_overlap"
    try:
        fig.text(.5, .5, "overlap one")
        fig.text(.5, .5, "overlap two")
        _reject(lambda: PLOT._publish_outputs(fig, axes, prefix, data, []), "overlap")
        assert not list(tmp_path.glob("*fig9_overlap*"))
    finally:
        PLOT.plt.close(fig)


def test_caption_contains_fixed_literals_and_lane(tmp_path):
    caption = PLOT._caption(_data(tmp_path), "fig9_test")
    literals = [
        "formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only",
        "This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts.",
        "Panel y scales are workload-local and must not be compared across panels.",
        "not a performance certification", "fixture-0.nqsv, fixture-1.nqsv, fixture-2.nqsv",
        "fixture-node-0, fixture-node-1, fixture-node-2", "sign positive, positive and negative",
        "no perf", "legacy", "all 6 arms", "Pilot observations did not enter the estimate",
    ]
    for literal in literals:
        assert literal in caption
    ordered = ["Figure 9.", "Columns:", "What is drawn:", "Values:", "The interval and the classification",
               "This figure reports", "Conditions:", "Correctness comes", "Panel y scales", "Pilot observations"]
    assert [caption.index(part) for part in ordered] == sorted(caption.index(part) for part in ordered)


def test_caption_avoids_forbidden_claims(tmp_path):
    caption = PLOT._caption(_data(tmp_path), "fig9_test")
    source = PLOT.GENERATOR.read_text()
    for phrase in ("headline result", "reproduces C1", "reproduction of C1 confirmed",
                   "statistically significant", "significant improvement", "significant regression",
                   "certified performance", "performance certified", "A-1 is satisfied", "formal result"):
        assert phrase.lower() not in caption.lower()
        assert phrase.lower() not in source.lower()
    assert not re.search(r"\b(improvement|regression)\b", caption, re.I)


def test_caption_figure_number_comes_from_prefix(tmp_path):
    data = _data(tmp_path)
    assert PLOT._caption(data, "fig9_test").startswith("Figure 9.")
    assert PLOT._caption(data, "fig27_test").startswith("Figure 27.")
    _reject(lambda: PLOT._caption(data, "figX_test"))


def test_formal_true_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r.update(formal=True), "formal must")


def test_promotion_prohibited_false_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r.update(promotion_prohibited=False), "promotion_prohibited must")


def test_statistics_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r["workloads"][0]["statistics"].update(
        mean_signed_positional_difference_tps=1), "numeric crosscheck")


def test_classification_mismatch_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r["workloads"][0]["statistics"].update(
        classification="unresolved"), "classification mismatch")


def test_pair_difference_mismatch_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    def change(r):
        w = r["workloads"][0]
        # Alter arm and pair together: only the signed-difference identity fails.
        arm = PLOT.VARIANT_ARMS[w["workload"]]
        w["arms"][arm]["raw_tps"][0] += 100
        w["statistics"]["pairs"][0][arm + "_tps"] += 100
    hashes = _change(root, change)
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes), "pair difference")


def test_leaf_hash_drift_is_rejected(tmp_path):
    root, hashes = _fixture(tmp_path)
    path = root / PLOT.COMPLETE_JSON
    path.write_text(path.read_text() + "\n")
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes), "SHA-256")


def test_policy_hash_mismatch_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    path = root / PLOT.RECEIPT_JSON
    receipt = json.loads(path.read_text())
    receipt["policy"]["sha256"] = "c" * 64
    _write(path, receipt)
    hashes = _change(root, lambda r: r.update(policy_sha256="c" * 64))
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes), "policy SHA-256")


def test_uncertified_arm_is_rejected(tmp_path):
    _reject_changed(tmp_path, lambda r: r["workloads"][0]["arms"][PLOT.VARIANT_ARMS[PLOT.WORKLOADS[0]]][
        "correctness_evidence"].update(certified=[False]), "uncertified")


def test_variance_plan_breach_true_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    policy_path = root / PLOT.POLICY_PATH
    policy = json.loads(policy_path.read_text())
    policy["workloads"][0]["planned_sigma_tps"] = "1"
    _write(policy_path, policy)
    digest = _hash(policy_path)
    receipt_path = root / PLOT.RECEIPT_JSON
    receipt = json.loads(receipt_path.read_text())
    receipt["policy"]["sha256"] = digest
    _write(receipt_path, receipt)
    def change(r):
        r["policy_sha256"] = digest
        r["workloads"][0]["statistics"].update(planned_sigma_tps=1.0, variance_plan_breach=True)
    hashes = _change(root, change)
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes), "outside scope")


def test_provenance_binds_caption_source(tmp_path):
    root, hashes = _fixture(tmp_path)
    data = PLOT.load_leaf(root, expected_hashes=hashes)
    prov = _provenance(data, tmp_path)
    rows = [r for r in prov["tracked_inputs"] if r["kind"] == "caption_source"]
    assert rows == [{"kind": "caption_source", "path": PLOT.CAPTION_SOURCE,
                     "sha256": _hash(root / PLOT.CAPTION_SOURCE),
                     "authority_scope": "wording of limitations and conditions only; not measurement values or classification"}]
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    (root / PLOT.CAPTION_SOURCE).write_text("Changed wording.\n")
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), "tracked_inputs")
    (root / PLOT.CAPTION_SOURCE).unlink()
    _reject(lambda: PLOT.load_leaf(root, expected_hashes=hashes))


def test_pinned_hashes_are_used_when_no_override(tmp_path):
    root, _ = _fixture(tmp_path)
    _reject(lambda: PLOT.load_leaf(root), "SHA-256 mismatch")


def test_pinned_input_hashes_match_results_document():
    table = RESULTS.read_text().split("### 5.1", 1)[1].split("### 5.2", 1)[0]
    for path, digest in PLOT.PINNED_SHA256.items():
        rows = [line for line in table.splitlines() if f"\u0060{path}\u0060" in line]
        assert len(rows) == 1
        assert re.findall(r"\u0060([0-9a-f]{64})\u0060", rows[0]) == [digest]


def test_cli_writes_three_outputs_and_provenance_closure(tmp_path):
    root, hashes = _fixture(tmp_path)
    prefix = root / "fig9_fixture"
    assert PLOT.main(["--repo-root", str(root), str(prefix)], expected_hashes=hashes) == 0
    paths = [Path(f"{prefix}{s}") for s in (".png", ".pdf", ".provenance.json")]
    assert all(path.is_file() for path in paths)
    prov = json.loads(paths[2].read_text())
    PLOT.validate_repo_closure(prov, root, expected_hashes=hashes)
    assert prov["reproduction"]["argv"] == ["python3", PLOT.GENERATOR_PATH, "--repo-root", str(root), prefix.name]
    assert prov["limitations"] == json.loads((root / PLOT.RESULT_JSON).read_text())["limitations"]
    for key, change, phrase in (
        ("artist_series", lambda v: v[0].update(mean=1), "artist"),
        ("workloads", lambda v: v[0].update(mean=1), "workloads"),
        ("caption", None, "caption"),
    ):
        changed = copy.deepcopy(prov)
        if change is None:
            changed[key] += " drift"
        else:
            change(changed[key])
        _reject(lambda: PLOT.validate_repo_closure(changed, root, expected_hashes=hashes), phrase)
    paths[0].write_bytes(paths[0].read_bytes() + b"drift")
    _reject(lambda: PLOT.validate_repo_closure(prov, root, expected_hashes=hashes), "output closure")


def test_cli_rejects_prefix_without_fig_number(tmp_path):
    root, hashes = _fixture(tmp_path)
    prefix = tmp_path / "figX_invalid"
    assert PLOT.main(["--repo-root", str(root), str(prefix)], expected_hashes=hashes) == 2
    assert not list(tmp_path.glob("figX_invalid*"))


def test_real_leaf_loads_and_matches_results_document():
    data = PLOT.load_leaf(REPO)
    table = RESULTS.read_text().split("### 2.1", 1)[1].split("### 2.2", 1)[0]
    for c in data["workloads"]:
        row, = [line for line in table.splitlines() if line.startswith(f"| {c['workload']} |")]
        columns = [v.strip().strip("\u0060") for v in row.split("|")[1:-1]]
        for key, index in (("mean", 3), ("h", 4), ("B", 6), ("baseline_mean", 7), ("sd", 8), ("planned_sigma", 9)):
            assert math.isclose(c[key], float(columns[index]), rel_tol=1e-9, abs_tol=1e-6)
        assert c["classification"] == columns[10]
        assert c["variance_plan_breach"] is False and columns[11] == "false"


def test_landed_fig9_repo_closure_and_caption_when_present():
    prefix = REPO / "docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1"
    paths = [Path(f"{prefix}{s}") for s in (".png", ".pdf", ".provenance.json")]
    readme = (prefix.parent / "README.md").read_text()
    if not any(path.exists() for path in paths) and prefix.name not in readme:
        skip("fig9 integration artifacts are parent-owned and not landed yet")
    assert all(path.is_file() for path in paths), "fig9 integration bundle is incomplete"
    prov = json.loads(paths[2].read_text())
    PLOT.validate_repo_closure(prov, REPO)
    assert prov["caption"] in readme


def _run():
    passed = failed = skipped = errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        node = f"{Path(__file__).name}::{test.__name__}"
        try:
            with tempfile.TemporaryDirectory(prefix="a1-sized-test-") as directory:
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
