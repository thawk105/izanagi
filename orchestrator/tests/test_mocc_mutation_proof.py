"""Contracts for the fixed MOCC mutation proof; the compute JSON is mandatory."""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

from orchestrator.campaign import condition_meaning_gate as G
from orchestrator.campaign import materializer_admission
from orchestrator.campaign import s3_mocc_mutation_proof as M

_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = "cc/mocc/transaction.cc"
_PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
_PATCHES = (
    "patches/instr-mocc-lock-coverage.patch",
    "patches/broken-mocc-lockskip-validation.patch",
    "patches/broken-mocc-permutation-erase.patch",
    "patches/broken-mocc-early-unlock.patch",
    "patches/broken-mocc-hot-update-unlock.patch",
)
_CHECK_KEYS = (
    "stock_hot_t1_certified_and_silent",
    "stock_hot_t4_certified_and_silent",
    "stock_cold_t1_certified_and_silent",
    "stock_cold_t4_certified_and_silent",
    "stock_default_t1_certified_and_silent",
    "stock_default_t4_certified_and_silent",
    "stock_u_hot_t1_certified_and_silent",
    "stock_u_hot_t4_certified_and_silent",
    "stock_u_cold_t1_certified_and_silent",
    "stock_u_cold_t4_certified_and_silent",
    "stock_u_default_t1_certified_and_silent",
    "stock_u_default_t4_certified_and_silent",
    "cold_lockskip_t1_three_reasons_cycles_zero",
    "cold_lockskip_t4_x_positive",
    "default_lockskip_t1_three_reasons_cycles_zero",
    "default_lockskip_t4_x_positive",
    "perm_hot_t1_only_size_changed",
    "perm_cold_t1_only_size_changed",
    "early_unlock_hot_t1_retention_without_entry",
    "early_unlock_cold_t1_retention_without_entry",
    "hot_update_unlock_hot_t1_three_reasons_cycles_zero",
    "hot_update_unlock_cold_t1_silent",
    "hot_update_unlock_cold_t4_silent",
    "hot_update_unlock_default_t1_silent",
    "hot_update_unlock_default_t4_silent",
    "matrix_runs_complete_and_terminated",
    "hot_path_evidence_method_is_negative_control",
    "trace0_nm_izanagi_zero",
    "trace0_strings_izanagi_trace_zero",
    "trace0_logical_rows_identical",
    "toolchain_matches_policy",
    "all_broken_patch_touch_sets_are_transaction_only",
)
_NAMES = tuple("""
stock_hot_t1 stock_hot_t4 stock_cold_t1 stock_cold_t4 stock_default_t1 stock_default_t4
stock_u_hot_t1 stock_u_hot_t4 stock_u_cold_t1 stock_u_cold_t4 stock_u_default_t1 stock_u_default_t4
lockskip_hot_t1 lockskip_hot_t4 lockskip_cold_t1 lockskip_cold_t4 lockskip_default_t1 lockskip_default_t4
perm_hot_t1 perm_hot_t4 perm_cold_t1 perm_cold_t4 perm_default_t1 perm_default_t4
early_unlock_hot_t1 early_unlock_hot_t4 early_unlock_cold_t1 early_unlock_cold_t4 early_unlock_default_t1 early_unlock_default_t4
hot_update_unlock_hot_t1 hot_update_unlock_hot_t4 hot_update_unlock_cold_t1 hot_update_unlock_cold_t4 hot_update_unlock_default_t1 hot_update_unlock_default_t4
""".split())
_OBSERVE = frozenset("""
lockskip_hot_t1 lockskip_hot_t4 perm_hot_t4 perm_cold_t4 perm_default_t1 perm_default_t4
early_unlock_hot_t4 early_unlock_cold_t4 early_unlock_default_t1 early_unlock_default_t4
hot_update_unlock_hot_t4
""".split())
_REASONS = ("not-locked-at-entry", "lock-lost-before-write", "lock-lost-before-publish")
_OTHER = (
    "orphan_reads", "version_dups", "dup_txids", "genesis_commits", "missing_txids",
    "write_version_mismatch", "malformed_keys", "framing_violations",
    "framing_violation_details", "write_intent_violations",
)
_EVIDENCE = {
    "method": "negative-control",
    "guarantee": "stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出",
}


@contextmanager
def _source_root(*patches):
    with tempfile.TemporaryDirectory(prefix="mocc-mutation-proof-") as temporary:
        root = Path(temporary)
        archive = subprocess.run(
            ["git", "-C", str(_ROOT / "external/ccbench"), "archive", _PIN, _SOURCE],
            check=True, capture_output=True,
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for relative in patches:
            for operation in (("--check",), ()):
                subprocess.run(["git", "-C", str(root), "apply", *operation,
                                str(_ROOT / relative)], check=True, capture_output=True)
        yield root


def _lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def test_mocc_hot_unlock_is_balanced_on_commit_and_abort():
    with _source_root(_PATCHES[0], _PATCHES[4]) as root:
        source = (root / _SOURCE).read_text()
    assert source.count("#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK") == 1
    declaration = """#line 17
#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK
[[maybe_unused]] static constexpr bool izanagi_break_mocc_hot_update_unlock = TRACE != 0;
[[maybe_unused]] static thread_local Tuple* izanagi_hot_update_pending = nullptr;
#else
[[maybe_unused]] static constexpr bool izanagi_break_mocc_hot_update_unlock = false;
[[maybe_unused]] static thread_local Tuple* izanagi_hot_update_pending = nullptr;
#endif
#line 17
"""
    assert declaration in source
    use = "if constexpr (izanagi_break_mocc_hot_update_unlock) {"
    assert source.count(use) == 3
    update = source.split("Status TxExecutor::update(", 1)[1].split("Status TxExecutor::insert(", 1)[0]
    expected = """if (loadepot.temp >= FLAGS_temp_threshold) {
lock(tuple, true);
if constexpr (izanagi_break_mocc_hot_update_unlock) {
if (this->status_ != TransactionStatus::aborted &&
izanagi_hot_update_pending == nullptr) {
tuple->rwlock_.w_unlock();
izanagi_hot_update_pending = tuple;
}
}
}
#line 460"""
    assert "\n".join(_lines(expected)) in "\n".join(_lines(update))
    abort = source.split("void TxExecutor::abort() {", 1)[1].split("void TxExecutor::unlockCLL()", 1)[0]
    abort_site = """if constexpr (izanagi_break_mocc_hot_update_unlock) {
if (izanagi_hot_update_pending != nullptr) {
izanagi_hot_update_pending->rwlock_.w_lock();
izanagi_hot_update_pending = nullptr;
}
}
#line 1069
unlockCLL();"""
    assert "\n".join(_lines(abort_site)) in "\n".join(_lines(abort))
    publish = source.split('"lock-lost-before-publish");', 1)[1]
    publish_site = """#endif
#line 1195
if constexpr (izanagi_break_mocc_hot_update_unlock) {
if (izanagi_hot_update_pending == (*itr).rcdptr_) {
izanagi_hot_update_pending->rwlock_.w_lock();
izanagi_hot_update_pending = nullptr;
}
}
#line 1195
__atomic_store_n(&((*itr).rcdptr_->tidword_.obj_), maxtid.obj_,"""
    assert _lines(publish)[:len(_lines(publish_site))] == _lines(publish_site)
    assert source.count("izanagi_hot_update_pending->rwlock_.w_lock();") == 2
    assert source.count("izanagi_hot_update_pending = nullptr;") == 4
    assert re.findall(r"(?m)^#line (\d+)$", source) == [
        "17", "17", "460", "990", "991", "1069", "1158", "1169", "1187", "1195", "1195",
    ]
    assert "lock(izanagi_hot_update_pending" not in source
    assert re.findall(r"(?m)^diff --git (.+)$", (_ROOT / _PATCHES[4]).read_text()) == [
        "a/cc/mocc/transaction.cc b/cc/mocc/transaction.cc",
    ]


def test_mocc_hot_unlock_has_unique_condition_witness():
    macro = "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK"
    assert G.CONDITIONAL_BRANCH_WITNESSES[macro] == (_SOURCE, f"#if {macro}")
    assert G.DEFINE_SPECS[macro].patch_rel == _PATCHES[4]
    declaration = G.ConditionalBranchMeaningDeclaration(
        macro=macro, source_rel=_SOURCE, start_directive=f"#if {macro}",
    )
    with _source_root(_PATCHES[0], _PATCHES[4]) as root:
        source = (root / _SOURCE).read_text()
    assert G._instrument_declared_owner_source(source, declaration) != source
    try:
        G._instrument_declared_owner_source(source + f"\n#if {macro}\n#endif\n", declaration)
    except G.ConditionMeaningGateError as exc:
        assert exc.reason_code == "compile-time-branch-start-not-unique"
    else:
        raise AssertionError("duplicate condition witness was accepted")


def test_mocc_mutation_matrix_is_exact():
    assert tuple(cell["run_name"] for cell in M.MATRIX) == _NAMES
    assert len(set(_NAMES)) == 36
    assert Counter(cell["acceptance"] for cell in M.MATRIX) == {"required": 25, "observe": 11}
    assert {cell["run_name"] for cell in M.MATRIX if cell["acceptance"] == "observe"} == _OBSERVE
    assert M.REGIMES == {"hot": "0", "cold": "21", "default": "10"}
    builds = []
    for cell in M.MATRIX:
        name = cell["run_name"]
        label, regime, thread = name.rsplit("_", 2)
        assert (cell["regime"], cell["thread"]) == (regime, int(thread[1:]))
        assert cell["build"] == {"stock": "S", "stock_u": "S", "lockskip": "L",
                                  "perm": "P", "early_unlock": "E", "hot_update_unlock": "H"}[label]
        update = label in {"stock_u", "hot_update_unlock"}
        assert cell["workload"] == ("U" if update else "W")
        assert M._cell_flags(cell) == {
            "ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "0",
            "ycsb_rmw": "false" if update else "true", "ycsb_max_ope": "1" if update else "5",
            "thread_num": thread[1:], "extime": "1", "temp_threshold": M.REGIMES[regime],
        }
        builds.append(cell["build"])
    assert builds == ["S"] * 12 + ["L"] * 6 + ["P"] * 6 + ["E"] * 6 + ["H"] * 6
    assert M.SINGLE_FLAGS == M.legacy.SINGLE_FLAGS and M.SINGLE_FLAGS is not M.legacy.SINGLE_FLAGS
    assert M.HIGH_FLAGS == M.legacy.HIGH_FLAGS and M.HIGH_FLAGS is not M.legacy.HIGH_FLAGS
    admission = materializer_admission.non_admissible_materializer(
        "orchestrator.campaign.s3_mocc_mutation_proof._build_variant")
    assert admission


def test_mocc_mutation_check_keys_are_exact():
    assert type(M.CHECK_KEYS) is tuple
    assert M.CHECK_KEYS == _CHECK_KEYS
    assert len(set(_CHECK_KEYS)) == 32


def _baseline():
    runs = {}
    for cell in M.MATRIX:
        flags = M._cell_flags(cell)
        name = cell["run_name"]
        run = {k: v for k, v in cell.items() if k != "run_name"}
        run.update(flags=flags, argv=["/synthetic/ycsb_mocc.exe", *(f"-{k}={v}" for k, v in flags.items()), "-clocks_per_us=2100"],
                   terminated=True, returncode=0, timed_out=False, error=None,
                   verdict="serializable", certified=True, total_cycles=0, txns=1,
                   lock_coverage_violations=0, permutation_violations=0,
                   x_reasons={}, p_reasons={}, non_insert_writes=1, read_rows=0)
        if cell["build"] != "S" and not (cell["build"] == "H" and cell["regime"] != "hot"):
            run.update(verdict="indeterminate", certified=False)
            if cell["build"] == "P":
                run.update(permutation_violations=1, p_reasons={"size-changed": 1})
            else:
                reasons = _REASONS[1:] if cell["build"] == "E" else _REASONS
                run.update(lock_coverage_violations=len(reasons), x_reasons=dict.fromkeys(reasons, 1))
        raw = {k: run[k] for k in ("verdict", "certified", "total_cycles")}
        raw.update(stats={"txns": 1}, integrity={**dict.fromkeys(_OTHER, 0),
                   "lock_coverage_violations": run["lock_coverage_violations"],
                   "permutation_violations": run["permutation_violations"]})
        run["verifier"] = {"argv": [sys.executable, "-m", "verifier", "/synthetic/trace", "--json", "--quiet",
                                    "--protocol", "mocc", "--ccbench-root", "/synthetic/source"],
                           "terminated": True, "returncode": 0 if run["certified"] else 3,
                           "timed_out": False, "error": None, "record": raw}
        runs[name] = run
    digest = "1" * 64
    return {
        "runs": runs,
        "trace0": {"nm_izanagi_count": 0, "strings_izanagi_trace_count": 0,
                   "strings_izanagi_macro_count": 0, "logical_rows_identical": True,
                   "base_logical_rows_count": 1, "patched_logical_rows_count": 1,
                   "base_logical_rows_sha256": digest, "patched_logical_rows_sha256": digest},
        "touch_sets": {path: [_SOURCE] for path in _PATCHES}, "patch_relatives": _PATCHES,
        "toolchain": {"version_body_sha256": {"gcc": digest, "g++": digest}},
        "policy": {"expected_compiler_version_body_sha256": {"gcc": digest, "g++": digest}},
        "hot_path_evidence": dict(_EVIDENCE),
    }


def test_mocc_mutation_checks_are_input_derived():
    baseline = _baseline()
    assert tuple(M.compute_checks(**baseline)) == _CHECK_KEYS
    assert all(M.compute_checks(**baseline).values())
    assert M._empty_process([])["wall_seconds"] is None
    for elapsed in (None, 0.25):
        timed = copy.deepcopy(baseline)
        for run in timed["runs"].values():
            run["wall_seconds"] = elapsed
            run["verifier"]["wall_seconds"] = elapsed
        assert M.compute_checks(**timed) == M.compute_checks(**baseline)
    required = [name for name in _NAMES if name not in _OBSERVE]
    assert len(required) == 25
    mutations = []
    for key, name in zip(_CHECK_KEYS[:25], required):
        mutations.append((key, lambda b, name=name: b["runs"][name].__setitem__("non_insert_writes", 0)))
    mutations.extend((
        (_CHECK_KEYS[25], lambda b: b["runs"]["hot_update_unlock_hot_t4"].__setitem__("timed_out", True)),
        (_CHECK_KEYS[26], lambda b: b["hot_path_evidence"].__setitem__("method", "counter")),
        (_CHECK_KEYS[27], lambda b: b["trace0"].__setitem__("nm_izanagi_count", 1)),
        (_CHECK_KEYS[28], lambda b: b["trace0"].__setitem__("strings_izanagi_macro_count", 1)),
        (_CHECK_KEYS[29], lambda b: b["trace0"].__setitem__("logical_rows_identical", False)),
        (_CHECK_KEYS[30], lambda b: b["toolchain"]["version_body_sha256"].__setitem__("g++", "2" * 64)),
        (_CHECK_KEYS[31], lambda b: b["touch_sets"].__setitem__(_PATCHES[4], ["cc/silo/transaction.cc"])),
    ))
    assert tuple(key for key, _ in mutations) == _CHECK_KEYS
    for key, mutate in mutations:
        changed = copy.deepcopy(baseline)
        mutate(changed)
        assert {k for k, v in M.compute_checks(**changed).items() if not v} == {key}, key
    # R1 is an explicit set: seven single-thread negative controls, not all negatives.
    for name in required:
        changed = copy.deepcopy(baseline)
        changed["runs"][name]["verifier"]["record"]["integrity"]["version_dups"] = 1
        checks = M.compute_checks(**changed)
        exempt = name in {"lockskip_cold_t4", "lockskip_default_t4"}
        assert all(checks.values()) == exempt, name
    for name in _OBSERVE:
        changed = copy.deepcopy(baseline)
        run = changed["runs"][name]
        run.update(certified=False, verdict="non-serializable", total_cycles=12,
                   lock_coverage_violations=0, permutation_violations=17,
                   txns=0, non_insert_writes=0, read_rows=8)
        run["verifier"]["record"]["integrity"]["version_dups"] = 1
        assert all(M.compute_checks(**changed).values()), name
    for field in ("runs", "trace0", "touch_sets", "toolchain", "policy", "hot_path_evidence"):
        changed = copy.deepcopy(baseline)
        changed[field] = {}
        assert not all(M.compute_checks(**changed).values()), field
    for key, value in (("argv", []), ("flags", {}), ("build", "H"), ("acceptance", "required"),
                       ("terminated", False), ("returncode", 1), ("timed_out", True)):
        changed = copy.deepcopy(baseline)
        changed["runs"]["perm_default_t4"][key] = value
        assert not M.compute_checks(**changed)[_CHECK_KEYS[25]], key
    for key, value in (("terminated", False), ("returncode", 2), ("timed_out", True), ("record", None)):
        changed = copy.deepcopy(baseline)
        changed["runs"]["perm_default_t4"]["verifier"][key] = value
        assert not M.compute_checks(**changed)[_CHECK_KEYS[25]], key


def test_mocc_mutation_proof_json_is_complete_and_bound():
    path = _ROOT / "output/env/pegasus/calibration/s3_mocc_mutation_proof.json"
    payload = json.loads(path.read_text())  # Absence is red, never a skip.
    assert set(payload) == {
        "schema_version", "env_tag", "site", "ccbench_commit", "genome", "clocks_per_us",
        "toolchain", "patches", "workloads", "regimes", "trace0", "legacy_proof",
        "condition_gates", "diagnostic_build_admission", "hot_path_evidence", "touch_sets",
        "runs", "checks", "all_pass",
    }
    assert payload["schema_version"] == "s3-mocc-mutation-proof/v1"
    assert payload["ccbench_commit"] == _PIN == M.PIN
    assert payload["env_tag"] == "pegasus"
    assert payload["genome"] == M.STOCK_G.canonical()
    assert payload["clocks_per_us"] == 2100
    assert payload["regimes"] == {"hot": "0", "cold": "21", "default": "10"}
    assert payload["hot_path_evidence"] == _EVIDENCE
    assert payload["workloads"] == {"W": {"single": M.SINGLE_FLAGS, "high": M.HIGH_FLAGS},
                                     "U": {"single": M.U_SINGLE_FLAGS, "high": M.U_HIGH_FLAGS}}
    patches = payload["patches"]
    assert len(patches) == 5
    assert {record["path"] for record in patches.values()} == set(_PATCHES)
    for record in patches.values():
        assert record["sha256"] == hashlib.sha256((_ROOT / record["path"]).read_bytes()).hexdigest()
    legacy_path = "output/env/pegasus/calibration/s3_mocc_lock_coverage.json"
    assert payload["legacy_proof"] == {"path": legacy_path, "sha256": hashlib.sha256((_ROOT / legacy_path).read_bytes()).hexdigest()}
    assert payload["touch_sets"] == {path: [_SOURCE] for path in _PATCHES}
    assert payload["diagnostic_build_admission"] == materializer_admission.non_admissible_materializer(
        "orchestrator.campaign.s3_mocc_mutation_proof._build_variant")
    assert {gate["macro"] for gate in payload["condition_gates"]} == {
        "IZANAGI_BREAK_MOCC_LOCK_COVERAGE", "IZANAGI_BREAK_MOCC_PERMUTATION",
        "IZANAGI_BREAK_MOCC_EARLY_UNLOCK", "IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK",
    }
    assert len(payload["condition_gates"]) == 4
    for gate in payload["condition_gates"]:
        for arm in ("supply", "meaning"):
            assert gate[arm]["terminal_status"] == "green"
            assert gate[arm]["driver_id"] == "orchestrator.campaign.s3_mocc_mutation_proof"
        assert gate["admission"]["admitted"] is True
    assert set(payload["runs"]) == set(_NAMES)
    for run in payload["runs"].values():
        assert "integrity" not in run
        raw = run["verifier"]["record"]
        assert {key: run[key] for key in M.SUMMARY_KEYS} == M._summary(raw)
        assert sum(run["x_reasons"].values()) == raw["integrity"]["lock_coverage_violations"]
        assert sum(run["p_reasons"].values()) == raw["integrity"]["permutation_violations"]
        argv = run["verifier"]["argv"]
        assert argv[argv.index("--protocol") + 1] == "mocc"
        assert Path(argv[argv.index("--ccbench-root") + 1]).is_absolute()
    policy = M._load_policy(_ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    checks = M.compute_checks(payload["runs"], payload["trace0"], payload["touch_sets"], _PATCHES,
                              payload["toolchain"], policy, hot_path_evidence=payload["hot_path_evidence"])
    assert tuple(checks) == _CHECK_KEYS
    assert payload["checks"] == checks and all(value is True for value in checks.values())
    assert payload["all_pass"] is True


def test_mocc_mutation_run_records_failure_and_timeout():
    cell = M.MATRIX[-5]  # observation-only H/hot/t4
    flags = M._cell_flags(cell)
    for outcome, rc, timeout, terminated in (
        (subprocess.CompletedProcess([], 7, stdout="", stderr="failed"), 7, False, True),
        (subprocess.TimeoutExpired(["benchmark"], 120), None, True, False),
        (FileNotFoundError("missing binary"), None, False, False),
    ):
        kwargs = {"side_effect": outcome} if isinstance(outcome, Exception) else {"return_value": outcome}
        with mock.patch.object(M.subprocess, "run", **kwargs) as run:
            directory, record = M._run_trace(Path("/synthetic/ycsb_mocc.exe"), flags)
        try:
            assert isinstance(record["wall_seconds"], float) and record["wall_seconds"] >= 0
            assert record["returncode"] == rc and record["timed_out"] is timeout
            assert record["terminated"] is terminated and record["error"]
            assert record["argv"] == run.call_args.args[0]
            assert run.call_args.kwargs["timeout"] == 120.0
            assert run.call_args.kwargs["env"]["IZANAGI_TRACE_DIR"] == str(directory)
            baseline = _baseline()
            baseline["runs"][cell["run_name"]].update(record)
            assert not M.compute_checks(**baseline)["matrix_runs_complete_and_terminated"]
        finally:
            shutil.rmtree(directory)


def test_mocc_mutation_verify_binds_protocol_root_and_timeout():
    raw = _baseline()["runs"]["stock_hot_t1"]["verifier"]["record"]
    raw["integrity"]["details"] = ["preserved"]
    for rc in (0, 1, 3):
        completed = subprocess.CompletedProcess([], rc, stdout=json.dumps({"results": [raw]}), stderr="")
        with mock.patch.object(M, "_run_checked", return_value=completed) as run:
            result = M._verify(Path("/trace"), Path("/bound-source"))
        argv = run.call_args.args[0]
        assert argv == result["argv"]
        assert argv[argv.index("--protocol") + 1] == "mocc"
        assert argv[argv.index("--ccbench-root") + 1] == "/bound-source"
        assert run.call_args.kwargs["timeout"] == 900.0
        assert run.call_args.kwargs["cwd"] == _ROOT / "orchestrator"
        assert {-15, 0, 1, 2, 3} <= run.call_args.kwargs["allowed_returncodes"]
        assert isinstance(result["wall_seconds"], float) and result["wall_seconds"] >= 0
        assert result["record"] == raw
        assert result["returncode"] == rc and result["terminated"] is True
        assert result["timed_out"] is False and result["error"] is None
    for error, timeout in ((subprocess.TimeoutExpired(["verifier"], 900), True),
                           (FileNotFoundError("verifier"), False)):
        wrapped = RuntimeError("command could not be executed")
        wrapped.__cause__ = error
        with mock.patch.object(M, "_run_checked", side_effect=wrapped):
            result = M._verify(Path("/trace"), Path("/bound-source"))
        assert result["timed_out"] is timeout and result["terminated"] is False
        assert result["record"] is None and result["error"]
        assert result["returncode"] is None
        assert isinstance(result["wall_seconds"], float) and result["wall_seconds"] >= 0
    for rc in (2, -15):
        completed = subprocess.CompletedProcess([], rc, stdout=json.dumps({"results": [raw]}), stderr="bad")
        with mock.patch.object(M, "_run_checked", return_value=completed):
            result = M._verify(Path("/trace"), Path("/bound-source"))
        assert result["terminated"] is True and result["returncode"] == rc
        assert result["record"] is None and result["error"]
        assert result["timed_out"] is False
        assert isinstance(result["wall_seconds"], float) and result["wall_seconds"] >= 0
        baseline = _baseline()
        baseline["runs"]["stock_hot_t1"]["verifier"] = result
        assert not M.compute_checks(**baseline)["matrix_runs_complete_and_terminated"]


def test_mocc_mutation_condition_gate_uses_new_driver_id():
    # Inspect the real call's literal arguments, then exercise the real registry
    # and production instrumenter against each applied control, without gate stubs.
    tree = ast.parse(Path(M.__file__).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_require_condition_gate")
    call = next(node for node in ast.walk(function) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and node.func.attr == "make_define_request")
    values = {arg.arg: ast.literal_eval(arg.value) for arg in call.keywords if arg.arg != "macro"}
    assert values == {"driver_id": "orchestrator.campaign.s3_mocc_mutation_proof", "requested_value": 1, "default_value": 0}
    assert next(arg.value.id for arg in call.keywords if arg.arg == "macro") == "macro"
    assert M._require_condition_gate(_ROOT, None, [], "g++") is None
    for macro, patch in zip((M.LOCKSKIP_DEFINE, M.PERMUTATION_DEFINE, M.EARLY_UNLOCK_DEFINE, M.HOT_UPDATE_DEFINE), _PATCHES[1:]):
        request = G.make_define_request(macro=macro, **values)
        assert request.driver_id == values["driver_id"]
        assert request.requested_value == 1 and request.default_value == 0
        assert G.DEFINE_SPECS[macro].patch_rel == patch
        declaration = G.declare_define_runtime_meaning(request)
        with _source_root(_PATCHES[0], patch) as root:
            source = (root / _SOURCE).read_text()
        assert G._instrument_declared_owner_source(source, declaration) != source


def test_mocc_mutation_trace0_logical_rows_are_input_derived():
    cxx = shutil.which("g++")
    assert cxx is not None, "g++ is required"
    with _source_root() as root:
        base = (root / _SOURCE).read_text()
    with _source_root(_PATCHES[0]) as root:
        instrumented = (root / _SOURCE).read_text()
    rows = M._preprocess_trace_zero(base, cxx)
    identical = M._preprocess_trace_zero(instrumented, cxx)
    assert rows == identical and rows
    assert M._logical_rows_record(rows, identical)["logical_rows_identical"] is True
    for offset in (-1, 1):
        changed = instrumented.replace("#line 991\n", f"#line {991 + offset}\n")
        observed = M._logical_rows_record(rows, M._preprocess_trace_zero(changed, cxx))
        assert observed["logical_rows_identical"] is False
        bundle = _baseline()
        bundle["trace0"].update(observed)
        assert not M.compute_checks(**bundle)["trace0_logical_rows_identical"]


def test_mocc_mutation_u_trace_counts_reads():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        path = root / "trace_0.log"
        path.write_text("C 1 0 1 1 0 1\nW 1 0000000000000001 U 1 1\nE 1\n")
        assert M._trace_counts(root) == {"x_reasons": {}, "p_reasons": {}, "non_insert_writes": 1, "read_rows": 0}
        with path.open("a") as handle:
            handle.write("R 1 0000000000000001 0 0\n")
        counts = M._trace_counts(root)
        assert counts["read_rows"] == 1 and counts["non_insert_writes"] == 1
    for name in ("stock_u_hot_t1", "hot_update_unlock_hot_t1", "hot_update_unlock_cold_t4"):
        bundle = _baseline()
        bundle["runs"][name]["read_rows"] = counts["read_rows"]
        assert bundle["runs"][name]["non_insert_writes"] == bundle["runs"][name]["txns"]
        assert not all(M.compute_checks(**bundle).values()), name


def _run() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
