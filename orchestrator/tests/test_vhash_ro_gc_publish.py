"""Read-only GC publication patch, ordering, and acceptance contracts."""
from __future__ import annotations

import ast
import inspect
import json
import shutil
import subprocess

import pytest

from orchestrator.campaign import vhash_ro_gc_publish as P
from orchestrator.campaign import vhash_cicada_vlife as V


def test_condition_grid_and_balanced_order():
    assert len(P.CONDITIONS) == 12
    assert {c["genome"] for c in P.CONDITIONS.values()} == {"default", "tuned"}
    assert {c["ro_pct"] for c in P.CONDITIONS.values()} == {0, 50, 95}
    assert {c["wait_us"] for c in P.CONDITIONS.values()} == {0, 10000}
    plan = P.pair_plan(tuple(P.CONDITIONS))
    assert len(plan) == 72
    assert P._flags(P.CONDITIONS["S50-none-gc10"], records=200, extime=1,
                    clocks_per_us=2100, workers=4, seed=3)["izanagi_rogc_seed"] == 3
    for cid in P.CONDITIONS:
        rows = [row for row in plan if row["condition"] == cid]
        assert [row["order"] for row in rows] == [
            ["stock", "variant"], ["variant", "stock"],
            ["stock", "variant"], ["variant", "stock"],
            ["stock", "variant"], ["variant", "stock"],
        ]
        assert sum(row["order"][0] == "stock" for row in rows) == 3


@pytest.mark.parametrize("records,extime,workers", ((1000000, 3, 48), (200, 1, 4)))
def test_vlife_flags_match_build_macros(records, extime, workers):
    # The main measure and smoke-vlife builds both use these macros. LONGTX is
    # absent, so its guarded izanagi_long_kind flag is unavailable at runtime.
    main = next(node for node in ast.parse(inspect.getsource(P)).body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    macro_literals = {node.value for node in ast.walk(main)
                      if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert "IZANAGI_CICADA_VLIFE" in macro_literals
    assert "IZANAGI_CICADA_LONGTX" not in macro_literals
    assert sum(isinstance(node, ast.AugAssign)
               and isinstance(node.target, ast.Name) and node.target.id == "macros"
               and any(isinstance(value, ast.Constant)
                       and value.value == "IZANAGI_CICADA_VLIFE"
                       for value in ast.walk(node.value))
               for node in ast.walk(main)) == 2
    cell = {**P.CONDITIONS["S95-wait10msR-gc10"], "vlife": True}
    flags = P._flags(cell, records=records, extime=extime,
                     clocks_per_us=2100, workers=workers)
    assert flags["izanagi_ronly_pct"] == -1
    assert flags["worker1_insert_delay_rphase_us"] == 0
    assert "izanagi_long_kind" not in flags


def test_each_source_copy_prepares_ungated_build_before_condition_gates(monkeypatch, tmp_path):
    calls = []

    def observe_build(source, build, genome, macros, *, trace, toolchain, dependencies):
        calls.append((source, build, genome, macros, trace))
        return build / "cc/cicada/ycsb_cicada.exe", {"elapsed_s": 1.25}

    monkeypatch.setattr(P, "_build_variant", observe_build)
    for label in ("primary", "trace", "vlife"):
        source = tmp_path / label
        receipt = P._prepare_build_dependencies(
            source, tmp_path / f"build-{label}", {"cxx_path": "/fake/c++"}, {})
        assert receipt["elapsed_s"] == 1.25
    assert [(source.name, genome, macros, trace)
            for source, _, genome, macros, trace in calls] == [
        ("primary", "default", (), False),
        ("trace", "default", (), False),
        ("vlife", "default", (), False),
    ]

    # Inspect the real driver call sites: both fresh-copy paths prepare before
    # the real _build_variant reaches its _gates call.
    tree = ast.parse(inspect.getsource(P))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "main")
    ordered = [(node.lineno, node.func.id) for node in ast.walk(main)
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id in {"_source_copy", "_apply",
                                    "_prepare_build_dependencies", "_build_variant"}]
    ordered.sort()
    assert [name for _, name in ordered] == [
        "_source_copy", "_apply", "_prepare_build_dependencies", "_build_variant",
        "_source_copy", "_apply", "_prepare_build_dependencies", "_build_variant",
    ]
    build = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "_build_variant")
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
               and node.func.id == "_gates" for node in ast.walk(build))


@pytest.mark.parametrize("forbidden", (
    "IZANAGI_CICADA_VLIFE", "TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT"))
def test_throughput_rejects_instrumentation(forbidden):
    with pytest.raises(ValueError, match="forbids"):
        P.check_throughput_macros(("IZANAGI_CICADA_ROGC_WORKLOAD", forbidden))
    P.check_throughput_macros(("IZANAGI_CICADA_ROGC_WORKLOAD",
                               "IZANAGI_CICADA_RO_GCFLAG"))


def test_verify_acceptance_requires_real_flag_and_no_cycle():
    integrity = {key: 0 for key in (
        "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
        "missing_txids", "write_version_mismatch", "malformed_keys",
        "framing_violations", "lock_coverage_violations",
        "write_intent_violations", "permutation_violations",
        "existence_violations",
    )}
    integrity["clean"] = False  # Cicada lacks the proof surfaces for certification.
    report = {"runs": 1, "non_serializable": 0, "indeterminate": 1,
              "results": [{"total_cycles": 0, "integrity": integrity,
                           "stats": {"txns": 20}}]}
    count = {"ro_commits": 10, "flag_raises": 2}
    assert P.verify_acceptance(3, report, 0, count, 20)
    assert P.verdict_label(0) == "certified"
    assert P.verdict_label(3) == "no-cycle (upper bound indeterminate)"
    assert P.verdict_label(1) == "rejected"
    assert not P.verify_acceptance(1, report, 0, count, 20)
    assert not P.verify_acceptance(3, {**report, "non_serializable": 1}, 0, count, 20)
    assert not P.verify_acceptance(3, report, 1, count, 20)
    assert not P.verify_acceptance(3, report, 0, {**count, "flag_raises": 0}, 20)
    assert not P.verify_acceptance(3, {**report, "indeterminate": 2}, 0, count, 20)
    assert not P.verify_acceptance(3, {**report, "results": [
        {**report["results"][0], "total_cycles": 1}]}, 0, count, 20)


@pytest.mark.parametrize("field", (
    "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
    "missing_txids", "write_version_mismatch", "malformed_keys",
    "framing_violations", "lock_coverage_violations",
    "write_intent_violations", "permutation_violations", "existence_violations",
))
def test_verify_acceptance_rejects_each_integrity_violation(field):
    integrity = {key: 0 for key in (
        "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
        "missing_txids", "write_version_mismatch", "malformed_keys",
        "framing_violations", "lock_coverage_violations",
        "write_intent_violations", "permutation_violations", "existence_violations",
    )}
    integrity[field] = 1
    report = {"runs": 1, "non_serializable": 0, "indeterminate": 1,
              "results": [{"total_cycles": 0, "integrity": integrity,
                           "stats": {"txns": 20}}]}
    assert not P.verify_acceptance(3, report, 0,
                                   {"ro_commits": 10, "flag_raises": 2}, 20)


def test_verify_acceptance_rejects_txn_mismatch():
    integrity = {key: 0 for key in (
        "orphan_reads", "version_dups", "dup_txids", "genesis_commits",
        "missing_txids", "write_version_mismatch", "malformed_keys",
        "framing_violations", "lock_coverage_violations",
        "write_intent_violations", "permutation_violations",
    )}
    report = {"runs": 1, "non_serializable": 0, "indeterminate": 1,
              "results": [{"total_cycles": 0, "integrity": integrity,
                           "stats": {"txns": 19}}]}
    assert not P.verify_acceptance(3, report, 0,
                                   {"ro_commits": 10, "flag_raises": 2}, 20)


def test_counter_parsers_reject_missing_duplicate_and_inconsistent():
    good = P.parse_workload(P.WORKLOAD_PREFIX +
        '{"schema":1,"attempts":10,"ro_attempts":5,"commits":8,"long_ro_attempts":1}')
    assert good["realized_ro_attempt_rate"] == .5
    with pytest.raises(ValueError):
        P.parse_workload(P.WORKLOAD_PREFIX +
            '{"schema":1,"attempts":10,"ro_attempts":11,"commits":8,"long_ro_attempts":1}')
    with pytest.raises(ValueError):
        P.parse_count(P.COUNT_PREFIX +
            '{"schema":1,"ro_commits":1,"flag_raises":2}')
    with pytest.raises(ValueError):
        P.parse_count(P.COUNT_PREFIX +
            '{"schema":1,"ro_commits":1,"ro_commits":1,"flag_raises":0}')


@pytest.mark.parametrize("preimage", ("pin", "trace", "vlife"))
def test_both_patches_apply_without_fuzz_on_real_preimages(tmp_path, preimage):
    source = tmp_path / "ccbench"
    shutil.copytree(P.ROOT / "external/ccbench", source,
                    ignore=shutil.ignore_patterns(".git", "build*"))
    if preimage != "pin":
        prior = P.TRACE if preimage == "trace" else P.VLIFE
        subprocess.run(["git", "apply", str(prior)], cwd=source, check=True)
    for patch in (P.WORKLOAD, P.VARIANT):
        subprocess.run(["git", "apply", "--check", str(patch)],
                       cwd=source, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
    transaction = (source / "cc/cicada/transaction.cc").read_text()
    ro = transaction.index("if (this->is_ronly_)", transaction.index("bool TxExecutor::commit()"))
    clear = transaction.index("node_map_.clear();", ro)
    call = transaction.index("mainte();", clear)
    ret = transaction.index("return true;", call)
    assert ro < clear < call < ret
    guard = transaction.rfind("#if IZANAGI_CICADA_RO_GCFLAG\n", clear, call)
    close = transaction.find("#endif\n", call)
    assert clear < guard < call < close < ret
    assert "#line 937" in transaction[call:ret]
    workload = (source / "include/ycsb.hh").read_text()
    assert "if (!has_write) tx.pro_set_.front().ope_" in workload
    assert workload.index("makeProcedure(tx.pro_set_", workload.index("void run(")) < (
        workload.index("const bool chosen_ro", workload.index("void run(")))


def test_patch_size_and_owner_paths():
    assert len(P.VARIANT.read_text().splitlines()) <= 200
    assert len(P.WORKLOAD.read_text().splitlines()) <= 200
    assert [line for line in P.VARIANT.read_text().splitlines()
            if line.startswith("diff --git ")] == [
        "diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc"]
    assert {line for line in P.WORKLOAD.read_text().splitlines()
            if line.startswith("diff --git ")} == {
        "diff --git a/include/ycsb.hh b/include/ycsb.hh",
        "diff --git a/cc/cicada/ycsb_cicada.cc b/cc/cicada/ycsb_cicada.cc"}


def test_full_size_figure_layout_fixture():
    from tools.plotting.plot_vhash_ro_gc_publish import make_figure, check_figure_layout
    import matplotlib.pyplot as plt
    # Production grid: 12 conditions, six paired repetitions, three metrics.
    publication = {cid: [float(rep + i) for rep in range(6)]
                   for i, cid in enumerate(P.CONDITIONS)}
    boundary = {cid: [float(rep - i) for rep in range(6)]
                for i, cid in enumerate(P.CONDITIONS)}
    throughput = {cid: [1 + .01 * (rep - i) for rep in range(6)]
                  for i, cid in enumerate(P.CONDITIONS)}
    figures = make_figure(publication, boundary, throughput)
    try:
        for fig in figures:
            check_figure_layout(fig)
    finally:
        for fig in figures:
            plt.close(fig)


def test_figure_layout_rejects_overlapping_real_text():
    from tools.plotting.plot_vhash_ro_gc_publish import check_figure_layout
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    try:
        ax.text(.5, .5, "overlap", transform=ax.transAxes)
        ax.text(.5, .5, "overlap", transform=ax.transAxes)
        with pytest.raises(ValueError, match="overlapping"):
            check_figure_layout(fig)
    finally:
        plt.close(fig)


def _vlife_fixture(publications: int, age: int, ro_units: int) -> dict:
    worker = {"hops": [[0] * 18 for _ in V.SITES],
              "position": [[0] * 18 for _ in V.SITES]}
    for field in ("readonly_attempt", "readonly_commit", "install", "detach",
                  "gc_negative", "readonly_reads", "gc_boundary_sum_us",
                  "gc_boundary_count", "gc_publish_sum_us", "gc_publish_count",
                  "gc_publish_negative", "gc_boundary_overflow", "gc_publish_overflow",
                  "ro_snapshot_age_sum_us", "ro_snapshot_age_count",
                  "ro_snapshot_age_negative", "ro_snapshot_age_overflow", "gc_same",
                  "dc_cf_wait_sum_us", "dc_ro_gap_sum_us", "dc_leader_wait_sum_us",
                  "dc_interval_sum_us", "dc_count", "dc_first", "dc_missing",
                  "dc_generation", "dc_negative", "dc_epoch_mismatch", "dc_late_epoch",
                  "dc_leader_count", "holder_count", "holder_unresolved"):
        worker[field] = 0
    for field, n in {"no_scan": 8, "deep": 5, "candidate": 5,
                     "readonly_deep": 5, "deep_read_zero": 5,
                     "candidate_read_zero": 5, "gc_boundary_us": 42,
                     "gc_publish_us": 42, "age_create_us": 42,
                     "age_overwrite_us": 42, "attempts": 2, "commits": 2,
                     "aborts": 2, "operations": 2, "cycles": 2,
                     "readonly_candidate": 5, "ro_snapshot_age_us": 42,
                     "dc_cf_kind_count": 5, "dc_cf_kind_sum_us": 5,
                     "holder_units": 5}.items():
        worker[field] = [0] * n
    if publications:
        worker["gc_boundary_count"] = publications
        worker["gc_boundary_sum_us"] = publications * age
        worker["gc_boundary_us"][age - 1] = publications
        worker["holder_count"] = publications
        worker["holder_units"][0] = publications * (1000000 - ro_units)
        worker["holder_units"][3] = publications * ro_units
    return {"schema_version": 2, "clocks_per_us": 2100,
            "bucket_bounds": [0,1,2,3,4,5,6,7,8,16,32,64,128,256,512,1024,2048,
                              18446744073709551615],
            "time_bucket_bounds": V.TIME_BOUNDS, "position_origin": V.POSITION_ORIGIN,
            "sites": list(V.SITES),
            "build": {"reuse_version": 1, "inline_version_opt": 0, "longtx": 1,
                      "izanagi_ronly_pct": -1, "izanagi_long_kind": 0},
            "workers": [worker]}


def test_record_raw_round_trip_into_plot_and_boundary_table(tmp_path):
    from tools.plotting import plot_vhash_ro_gc_publish as plot
    paths = {}
    for command in ("measure", "throughput"):
        raw = {"command": command, "conditions": P.CONDITIONS,
               "ccbench_commit": P.PIN, "records": 1000000, "extime": 3,
               "workers": 48, "site": "compute",
               "measurement_env": {"records": 1000000, "extime": 3,
                                   "workers": 48, "site": "compute"},
               "patch_sha256": {p.name: P.sha(p) for p in
                   (P.VARIANT, P.WORKLOAD, P.VLIFE, P.TRACE)}, "runs": []}
        for item in P.pair_plan(tuple(P.CONDITIONS)):
            cid, rep = item["condition"], item["rep"]
            for arm in item["order"]:
                wait = P.CONDITIONS[cid]["delay"] == "wait10msR"
                payload = _vlife_fixture(0 if arm == "stock" else 1,
                                          2 if wait else 1, 750000)
                stdout = (P.WORKLOAD_PREFIX +
                          '{"schema":1,"attempts":10,"ro_attempts":5,"commits":8,"long_ro_attempts":1}\n')
                if command == "measure":
                    stdout += V.PREFIX + json.dumps(payload) + "\n"
                else:
                    stdout += "throughput[tps]:\t100\n"
                build = {"trace": False, "vlife": command == "measure",
                         "macro": ["IZANAGI_CICADA_ROGC_WORKLOAD"],
                         "genome": {"genome": P.CONDITIONS[cid]["genome"]}}
                run = {"rc": 0, "stdout": stdout, "stderr": "",
                       "argv": ["binary", "-extime=3"],
                       "started_at": "start", "ended_at": "end", "wall_s": 3.0}
                raw["runs"].append(P._record(run, condition=cid, arm=arm, rep=rep,
                    order=item["order"], build=build, command=command))
        path = tmp_path / f"{command}.json"
        path.write_text(json.dumps(raw))
        paths[command] = path
    measure = plot.load_raw([paths["measure"]], "measure")
    throughput = plot.load_raw([paths["throughput"]], "throughput")
    malformed = json.loads(paths["measure"].read_text())
    malformed["measurement_env"]["workers"] = 4
    paths["measure"].write_text(json.dumps(malformed))
    with pytest.raises(ValueError, match="measurement environment"):
        plot.load_raw([paths["measure"]], "measure")
    malformed["measurement_env"]["workers"] = 48
    paths["measure"].write_text(json.dumps(malformed))
    assert plot.paired_values(throughput, "throughput", "throughput_tps")[
        "S95-wait10msR-gc10"] == [1.0] * 6
    table = plot.boundary_context(measure)
    assert table["S95-wait10msR-gc10"]["stock"][0] == {
        "publications": 0, "publication_label": "公開 0 回",
        "boundary_age_us": None, "boundary_age_label": "未定義"}
    assert table["S95-wait10msR-gc10"]["variant"][0]["ro_holder_fraction"] == .75
    assert table["S95-wait10msR-gc10"]["variant_ro_holder_fraction"] == {
        "repetitions": [.75] * 6, "mean": .75}
    assert table["S95-wait10msR-gc10"]["variant_wait_minus_none_boundary_age_us"] == {
        "repetitions": [1.0] * 6, "mean": 1.0}
    prefix = tmp_path / "paired"
    assert plot.main(["--measure", str(paths["measure"]),
                      "--throughput", str(paths["throughput"]),
                      "--out-prefix", str(prefix)]) == 0
    emitted = json.loads((tmp_path / "paired-boundary-table.json").read_text())
    assert emitted["conditions"]["S95-wait10msR-gc10"]["variant_ro_holder_fraction"]["mean"] == .75
    swapped = json.loads(json.dumps(measure))
    for row in swapped["runs"]:
        row["arm"] = "variant" if row["arm"] == "stock" else "stock"
    assert plot.boundary_context(swapped)["S95-wait10msR-gc10"]["stock"][0][
        "publication_label"] != "公開 0 回"
