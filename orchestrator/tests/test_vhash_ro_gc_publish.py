"""Read-only GC publication patch, ordering, and acceptance contracts."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from orchestrator.campaign import vhash_ro_gc_publish as P


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
        assert [row["order"] for row in rows] == [list(x) for x in P.ORDER]
        assert sum(row["order"][0] == "stock" for row in rows) == 3


@pytest.mark.parametrize("forbidden", (
    "IZANAGI_CICADA_VLIFE", "TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT"))
def test_throughput_rejects_instrumentation(forbidden):
    with pytest.raises(ValueError, match="forbids"):
        P.check_throughput_macros(("IZANAGI_CICADA_ROGC_WORKLOAD", forbidden))
    P.check_throughput_macros(("IZANAGI_CICADA_ROGC_WORKLOAD",
                               "IZANAGI_CICADA_RO_GCFLAG"))


def test_verify_acceptance_requires_real_flag_and_no_cycle():
    report = {"runs": 1, "non_serializable": 0, "indeterminate": 1,
              "results": [{"total_cycles": 0, "integrity": {"clean": True}}]}
    count = {"ro_commits": 10, "flag_raises": 2}
    assert P.verify_acceptance(3, report, 0, count)
    assert not P.verify_acceptance(1, report, 0, count)
    assert not P.verify_acceptance(3, {**report, "non_serializable": 1}, 0, count)
    assert not P.verify_acceptance(3, report, 1, count)
    assert not P.verify_acceptance(3, report, 0, {**count, "flag_raises": 0})
    assert not P.verify_acceptance(3, {**report, "indeterminate": 2}, 0, count)
    assert not P.verify_acceptance(3, {**report, "results": [
        {"total_cycles": 1, "integrity": {"clean": True}}]}, 0, count)


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
