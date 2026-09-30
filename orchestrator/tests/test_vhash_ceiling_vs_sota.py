"""Independent positive and negative examples for preregistered ceiling gates."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from orchestrator.campaign import vhash_ceiling_vs_sota as C


def row(point="P2", arm="R", gc=10, round_no=1, node="n1", job=None,
        tps=100, batch=10, mode="prelim", run_id=None):
    tree, key = C._build_for_arm(arm)
    patches = [{"name": p.name, "sha256": "a"*64} for p in C.TREE_PATCHES[tree]]
    binary_sha = "b"*64
    return {"mode": mode, "point": point, "arm": arm, "gc_inter_us": gc,
            "round": round_no, "node": node, "job_id": job or f"job-{point}-{gc}-{round_no}",
            "run_id": run_id or f"{mode}-{point}-{arm}-{gc}-{round_no}-{node}",
            "flags": {"tuple_num": 1_000_000},
            "throughput_tps": tps, "normal_commits": tps*10, "duration_s": 10,
            "batch_commits": batch, "manifest": {"tree": tree, "arm": key,
                "pin": C.PIN, "patches": patches, "binary_sha256": binary_sha},
            "binary_sha256": binary_sha, "patch_sha256": patches,
            "build_macro": list(C.variants(tree)[key])}


class CeilingTests(unittest.TestCase):
    def test_workload_exact_output(self):
        values = {"schema": 1, "thread_num": 47, "batch_threads": 1,
                  "batch_ops": 1000, "ronly_pct": 0, "normal_commits": 100,
                  "batch_commits": 2}
        line = C.WORKLOAD_PREFIX + json.dumps(values)
        self.assertEqual(C.parse_workload(line)["normal_commits"], 100)
        for bad in ("", line+"\n"+line, line.replace("100", "-1", 1),
                    line.replace('"batch_commits": 2', '"batch_commits": 2, "batch_commits": 3'),
                    line.replace('"normal_commits": 100, ', "")):
            with self.subTest(bad=bad[:30]), self.assertRaises(ValueError):
                C.parse_workload(bad)
        with self.assertRaises(ValueError):
            C.parse_workload(line, {"thread_num": 48, "batch_th_num": 1,
                "batch_max_ope": 1000, "izanagi_ceiling_ronly_pct": 0})

    def test_patch_order_and_genome(self):
        self.assertEqual([p.name for p in C.TREE_PATCHES["hot"]], [
            "cicada-ro-gcflag-variant.patch", "cicada-vhash-hot-block-variant.patch",
            "cicada-vhash-hot-block-post.patch", "cicada-ceiling-workload.patch"])
        self.assertEqual(C.V.TUNED_GENOME, {"BACK_OFF": 0, "INLINE_VERSION_OPT": 1,
            "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1, "WRITE_LATEST_ONLY": 0})
        self.assertEqual(C._build_for_arm("igc1"), C._build_for_arm("igc3"))

    def test_m1_perf_defines(self):
        expected = C.expected_perf_defines("hot8") | {k: str(v) for k, v in C.V.TUNED_GENOME.items()}
        rows = [{"file": f"/x/{name}", "command": "c++ " + " ".join(
            f"-D{k}={v}" for k, v in expected.items()) +
            " CMakeFiles/ycsb_cicada.exe.dir/ -c " + name} for name in
            ("transaction.cc", "util.cc", "ycsb_cicada.cc")]
        C.check_perf_defines(rows, "hot8")
        for macro in ("CICADA_VHASH_COUNT", "IZANAGI_CICADA_VLIFE", "UNRELATED_DEFINE"):
            bad = copy.deepcopy(rows)
            bad[0]["command"] += f" -D{macro}=1"
            with self.subTest(macro=macro), self.assertRaises(ValueError):
                C.check_perf_defines(bad, "hot8")

    def test_m8_manifest_all_fields(self):
        with tempfile.TemporaryDirectory() as td:
            binary = Path(td) / "binary"
            binary.write_bytes(b"binary")
            v = Path(td) / "V.patch"
            w = Path(td) / "W.patch"
            v.write_bytes(b"v")
            w.write_bytes(b"w")
            old = C.TREE_PATCHES["base"]
            C.TREE_PATCHES["base"] = (v, w)
            try:
                manifest = {"schema": 1, "pin": C.PIN, "tree": "base", "arm": "R",
                    "patches": C.patch_manifest("base"), "macros": list(C.variants("base")["R"]),
                    "binary_sha256": C.base.sha(binary),
                    "compile_commands_sha256": "c"*64, "compiler_version_sha256": "d"*64}
                C.check_manifest(manifest, binary, "base", "R")
                for key, replacement in (("patches", list(reversed(manifest["patches"]))),
                                         ("macros", []), ("pin", "wrong")):
                    bad = {**manifest, key: replacement}
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        C.check_manifest(bad, binary, "base", "R")
            finally:
                C.TREE_PATCHES["base"] = old

    def test_m2_paired_same_round_node_job(self):
        good = [row(), row(arm="hot1", tps=150)]
        self.assertEqual(C.paired(good, "hot1", "P2", 10, "prelim")[0]["ratio"], 1.5)
        for change in ({"round": 2}, {"node": "n2"}, {"job_id": "other"},
                       {"gc_inter_us": 100}):
            bad = copy.deepcopy(good)
            bad[1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                C.paired(bad, "hot1", "P2", 10, "prelim")

    def test_m3_gc_only_R(self):
        rows = [row(gc=gc, round_no=i, tps=100 if gc == 10 else 90) for gc in (10, 100)
                for i in range(1, 4)]
        rows += [row(arm="hot1", gc=gc, round_no=i,
                     tps=100 if gc == 10 else 10000) for gc in (10, 100)
                 for i in range(1, 4)]
        self.assertEqual(C.select_gc(rows, "P2"), 10)
        for r in rows:
            if r["arm"] == "R" and r["gc_inter_us"] == 100: r["throughput_tps"] = 110
        self.assertEqual(C.select_gc(rows, "P2"), 100)

    def test_m4_m5_m6_selection_and_witness(self):
        summary = {"P2": {"hot1": {"ratio": 1.4, "eligible": True},
                          "igc1": {"ratio": 99, "eligible": True}},
                   "P1": {"hot8": {"ratio": 1.6, "eligible": True},
                          "S": {"ratio": 100, "eligible": True}}}
        self.assertEqual(C.choose_representative(summary), ("P1", "hot8"))
        pairs = [{"completion_ratio": 0.8}, {"completion_ratio": 0.9}]
        self.assertTrue(C.completion_ok(pairs, "P2"))
        self.assertFalse(C.completion_ok([{"completion_ratio": 0.79}], "P2"))
        self.assertTrue(C.witness_ok("hot1", {"batch_c_lines": 1, "hot_hits": 1}))
        self.assertFalse(C.witness_ok("hot1", {"batch_c_lines": 1, "hot_hits": 0}))
        self.assertTrue(C.certified_witness("hot1", {"status": "certified",
            "counts": {"batch_c_lines": 1, "hot_hits": 1}}))
        self.assertFalse(C.certified_witness("hot1", {"status": C.verdict_label(3),
            "counts": {"batch_c_lines": 1, "hot_hits": 1}}))

    def test_m7_c_lines_two_independent_equalities(self):
        C.check_c_lines(12, 12, 2, 2)
        for values in ((12, 2, 2, 2), (12, 12, 2, 1)):
            with self.assertRaises(ValueError): C.check_c_lines(*values)

    def test_m9_order_and_m10_neighbor(self):
        arms = ("S", "R", "hot1", "hot8")
        orders = [C.arm_order(arms, i) for i in range(1, 5)]
        self.assertEqual(set(orders[0]), set(arms))
        self.assertEqual(len(set(orders)), 4)
        self.assertEqual(C.continuation({"P2": {"hot1": {"ratio": 2, "eligible": True}}},
                                        "P2", "P3", "hot1"), "判定不能")
        compare = {"P2": {"hot1": {"ratio": 1.5, "eligible": True}},
                   "P3": {"hot1": {"ratio": 1.3, "eligible": True}}}
        self.assertEqual(C.continuation(compare, "P2", "P3", "hot1"), "継続の材料")

    def test_m11_m12_and_perf_separation(self):
        C._unique_runs([row(), row(arm="hot1")])
        with self.assertRaises(ValueError):
            C._unique_runs([row(), row(arm="hot1", mode="compare",
                                      run_id=row()["run_id"])])
        self.assertEqual(C.verdict_label(0), "certified")
        self.assertEqual(C.verdict_label(3), "no-cycle (upper bound indeterminate)")
        bad = row()
        bad["mode"] = "diag"
        with self.assertRaises(ValueError): C._eligible_raw(bad)

    def test_full_preliminary_choice_and_budget_flags(self):
        rows = []
        for point in ("P1", "P2", "P3", "P4"):
            for gc in (10, 100):
                for round_no in range(1, 4):
                    for arm in C.prelim_arms(point):
                        score = 100 if arm == "R" else 120
                        if point == "P2" and arm == "hot1": score = 140
                        if point == "P4" and arm == "hot8": score = 135
                        rows.append(row(point, arm, gc, round_no, tps=score,
                                        batch=0 if arm == "R-noLR" else 10))
        witnesses = {arm: {"status": "certified", "accepted": True, "verifier_rc": 0,
            "counts": {"batch_c_lines": 1,
            "hot_hits": 1, "forward_success": 1}} for arm in C.M_ARMS}
        result = C.aggregate(rows, witnesses)
        self.assertEqual(result["representative"], {"point": "P2", "arm": "hot1"})
        self.assertEqual(result["neighbor"], "P3")
        self.assertEqual(result["continuation"], "判定不能")
        self.assertTrue(result["add_P4_and_P4prime"])
        estimate = C.job_estimate({"base": 299}, 11)
        self.assertFalse(estimate["build_over_5_minutes"])
        self.assertIn("base", C.job_estimate({"base": 301}, 11)["build_over_5_minutes"])
        self.assertTrue(C.job_estimate({"base": 7201}, 11)["over_2_node_hours"])

    def test_m6_accepted_rc3_and_single_witness_gate(self):
        good = {"accepted": True, "verifier_rc": 3,
                "status": C.verdict_label(3),
                "counts": {"batch_c_lines": 1, "hot_hits": 1}}
        self.assertTrue(C.accepted_witness("hot1", good))
        self.assertFalse(C.accepted_witness("hot1", {**good,
            "counts": {"batch_c_lines": 1, "hot_hits": 0}}))
        self.assertFalse(C.accepted_witness("hot1", {**good, "accepted": False}))

    def test_m13_broken_positive_reaches_mode_one_flags(self):
        self.assertEqual(C.flags("P2", "igc-broken", 10, 1)["cicada_igc_debug_mode"], 1)
        self.assertEqual(C.flags("P2", "igc3", 10, 1)["cicada_igc_debug_mode"], 3)
        with self.assertRaises(ValueError):
            C.flags("P2", "igc-invalid", 10, 1)

    def test_m13_broken_run_reaches_verifier(self):
        with tempfile.TemporaryDirectory() as td:
            scratch = Path(td)
            seen = []
            def fake_run(_binary, run_flags, _scratch, trace_dir):
                seen.append(run_flags["cicada_igc_debug_mode"])
                trace_dir.mkdir()
                (trace_dir / "trace_4.log").write_text("C 0 4\n")
                payload = {"schema": 1, "thread_num": 4, "batch_threads": 1,
                           "batch_ops": 1000, "ronly_pct": 0,
                           "normal_commits": 0, "batch_commits": 1}
                return {"stdout": C.WORKLOAD_PREFIX + json.dumps(payload), "stderr": "", "rc": 0}
            report = {"runs": 1, "non_serializable": 1,
                      "results": [{"total_cycles": 1}]}
            with mock.patch.object(C, "_run_one", side_effect=fake_run), \
                 mock.patch.object(C.subprocess, "run", return_value=SimpleNamespace(
                     returncode=1, stdout=json.dumps(report)) ) as verifier:
                result = C._verify_once(scratch, scratch / "binary", {},
                                        "igc-broken", scratch, 1)
            self.assertEqual(seen, [1])
            self.assertEqual(result["report"]["non_serializable"], 1)
            verifier.assert_called_once()

    def test_m14_final_decision_from_30_second_comparison(self):
        compare = {"P2": {"hot1": {"ratio": 1.6, "eligible": True}},
                   "P3": {"hot1": {"ratio": 1.3, "eligible": True}}}
        self.assertEqual(C.final_recommendation(compare, "P2", "P3", "hot1", {}),
                         "継続の材料")
        compare["P2"]["hot1"]["ratio"] = 1.1
        self.assertIn("主論文候補から外す", C.final_recommendation(compare, "P2", "P3", "hot1", {}))
        self.assertIn("予備のみ", C.final_recommendation({}, "P2", "P3", "hot1", {}))
        self.assertIn("判定不能", C.final_recommendation({"P2": compare["P2"]},
                                                   "P2", "P3", "hot1", {}))

    def test_m14_aggregate_uses_comparison_not_preliminary(self):
        rows = []
        for point in ("P1", "P2", "P3", "P4"):
            for gc in (10, 100):
                for round_no in range(1, 4):
                    for arm in C.prelim_arms(point):
                        rows.append(row(point, arm, gc, round_no,
                                        tps=100 if arm == "R" else 130,
                                        batch=0 if arm == "R-noLR" else 10))
        witnesses = {"hot1": {"accepted": True, "verifier_rc": 3,
                    "counts": {"batch_c_lines": 1, "hot_hits": 1}}}
        self.assertIn("予備のみ", C.aggregate(rows, witnesses)["research_decision"])
        for point in ("P2", "P3"):
            for round_no in range(1, 7):
                for arm in ("R", "hot1"):
                    item = row(point, arm, 10, round_no, mode="compare",
                               tps=100 if arm == "R" else 160)
                    item["duration_s"] = 30
                    item["normal_commits"] = item["throughput_tps"] * 30
                    rows.append(item)
        self.assertEqual(C.aggregate(rows, witnesses)["research_decision"], "継続の材料")

    def test_m15_build_shards_and_budget_gate(self):
        plan = C.job_estimate({"hot:hot1": 170, "hot:hot8": 170}, 11)
        builds = [j for j in plan["jobs"] if j["kind"] == "build"]
        self.assertEqual([j["conditions"] for j in builds], [1, 1])
        self.assertTrue(all(j["estimated_s"] <= 300 for j in builds))
        self.assertIs(C.require_budget(plan), plan)
        over = C.job_estimate({"base:S": 7201}, 11)
        with self.assertRaises(ValueError):
            C.require_budget(over)
        self.assertIs(C.require_budget(over, allow_over_budget=True), over)

    def test_m17_max_eligible_even_below_one(self):
        summary = {"P1": {"hot1": {"ratio": 0.99, "eligible": True}},
                   "P2": {"hot1": {"ratio": 0.8, "eligible": True}}}
        self.assertEqual(C.choose_representative(summary), ("P1", "hot1"))
        self.assertEqual(C.choose_representative({"P1": {"hot1": {
            "ratio": 0.99, "eligible": False}}})[0], "P2")

    def test_m16_runner_up_requires_eligible_witness(self):
        rows = []
        for point in ("P1", "P2", "P3", "P4"):
            for gc in (10, 100):
                for round_no in range(1, 4):
                    for arm in C.prelim_arms(point):
                        scores = {"R": 100, "hot1": 140, "hot8": 135, "fwd": 130}
                        rows.append(row(point, arm, gc, round_no,
                                        tps=scores.get(arm, 105),
                                        batch=0 if arm == "R-noLR" else 10))
        valid = lambda key: {"accepted": True, "verifier_rc": 3,
                             "counts": {"batch_c_lines": 1, key: 1}}
        witnesses = {"hot1": valid("hot_hits"), "hot8": valid("hot_hits"),
                     "fwd": valid("forward_success")}
        self.assertEqual(C.aggregate(rows, witnesses)["comparison_arms"],
                         ["S", "R", "hot1", "hot8"])
        witnesses["hot8"]["counts"]["hot_hits"] = 0
        self.assertEqual(C.aggregate(rows, witnesses)["comparison_arms"],
                         ["S", "R", "hot1", "fwd"])
        witnesses["fwd"]["counts"]["forward_success"] = 0
        self.assertEqual(C.aggregate(rows, witnesses)["comparison_arms"],
                         ["S", "R", "hot1"])

    def test_m18_hot_count_precedes_workload(self):
        for tree in ("diag-hot", "trace-hot"):
            C.check_patch_order(tree)
            original = C.TREE_PATCHES[tree]
            C.TREE_PATCHES[tree] = tuple(p for p in original if p != C.HOT_COUNT) + (C.HOT_COUNT,)
            try:
                with self.assertRaises(ValueError):
                    C.check_patch_order(tree)
            finally:
                C.TREE_PATCHES[tree] = original

    def test_interval_mode_three_diagnostics_are_extracted(self):
        payload = {"schema": 1, "debug_mode": 3, "chain_versions": 42,
                   "threads": [{"pruned": 0}]}
        record = {"mode": "diag", "arm": "igc3", "point": "P2",
                  "stdout": "CICADA_INTERVAL_V1 " + json.dumps(payload)}
        self.assertEqual(C.aggregate_diagnostics([record])["P2"]["igc3"],
                         {"pruned": 0, "chain_versions": 42})
        payload["debug_mode"] = 1
        record["stdout"] = "CICADA_INTERVAL_V1 " + json.dumps(payload)
        with self.assertRaises(ValueError):
            C.aggregate_diagnostics([record])


def _run():
    unittest.main()


if __name__ == "__main__":
    _run()
