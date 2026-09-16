# -*- coding: utf-8 -*-
"""SS2PL lock-study gates with paired positive and mutation-sensitive cases."""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
DRIVER_PATH = ROOT / "tools/pegasus/run_ss2pl_lock_study.py"
PLOT_PATH = ROOT / "tools/plotting/plot_ss2pl_lock_study.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


driver = _load("ss2pl_lock_study_driver_test", DRIVER_PATH)
plot = _load("ss2pl_lock_study_plot_test", PLOT_PATH)


def test_condition_family_dominates_first_study_configure_and_covers_all_axes():
    build_source = inspect.getsource(driver.build_target)
    gate_source = (
        inspect.getsource(driver._require_condition_gates)
        + inspect.getsource(driver._condition_request_inputs)
    )
    assert build_source.index("_require_condition_gates") < build_source.index("_configure")
    assert build_source.count("expected_cache=requested_cache") == 2
    assert "stock_source=stock_source" in build_source
    for macro in (
        "SS2PL_LOCK_IMPL", "SS2PL_LOCK_KIND", "SS2PL_DLR", "SS2PL_WFG_DIAG",
    ):
        assert macro in gate_source


def test_condition_requests_are_derived_from_each_actual_arm_cache():
    macro_by_axis = {
        "impl": "SS2PL_LOCK_IMPL",
        "kind": "SS2PL_LOCK_KIND",
        "dlr": "SS2PL_DLR",
        "wfg": "SS2PL_WFG_DIAG",
    }
    for arm, axes in driver.ARM_CONFIG.items():
        expected_cache = driver._expected_cache(arm, backoff=1)
        rows = driver._condition_request_inputs(expected_cache)
        assert {macro: requested for _axis, macro, requested, _default in rows} == {
            macro_by_axis[axis]: value for axis, value in axes.items()
        }


def test_condition_request_derivation_rejects_the_old_fixed_four_value_shape():
    expected_cache = driver._expected_cache("S", backoff=1)
    rows = driver._condition_request_inputs(expected_cache)
    assert tuple(requested for _axis, _macro, requested, _default in rows) == (
        0, 1, 1, 0,
    )
    mutated = dict(expected_cache)
    mutated[driver.AXIS_CACHE_KEYS["dlr"]] = "2"
    mutated_rows = driver._condition_request_inputs(mutated)
    assert tuple(requested for _axis, _macro, requested, _default in mutated_rows) == (
        0, 1, 2, 0,
    )


def _preprocess_cost(text: str = "int fixture;") -> dict:
    encoded = text.encode()
    _token_sha, token_count = driver._token_hash(encoded)
    return {
        "preprocessed_bytes": len(encoded),
        "token_count": token_count,
        "preprocess_duration_s": 0.001,
        "tokenize_duration_s": 0.001,
        "request_duration_s": 0.002,
        "cache_hit": False,
    }


def _stock_lock_evidence(
    sources: list[str], *, injected_source: str | None = None
) -> dict:
    identifiers = [
        "Ss2plStudyLock", "init", "load", "max", "study_state_", "try_study_lock",
    ]
    baseline_scan = driver._scan_cpp_tokens_for_study_lock(
        b"void init(); int load; int max;", identifiers,
    )
    baseline_identifier_hits = sorted(
        baseline_scan["study_lock_identifier_counts"]
    )
    receptor_identifiers = sorted(set(identifiers) - set(baseline_identifier_hits))
    rows = []
    for source in sources:
        text = (
            'void ShowOptParameters() { print(": SS2PL_LOCK_IMPL "); } '
            "void init(); int load; int max;"
            if source.endswith("/util.cc")
            else "void init(); int load; int max; int ordinary_translation_unit;"
        )
        if source == injected_source:
            text += " Ss2plStudyLock leaked_lock;"
        scan = driver._scan_cpp_tokens_for_study_lock(
            text.encode(), receptor_identifiers,
        )
        rows.append({
            "source": source,
            "sha256": scan["preprocessed_sha256"],
            "token_scan": scan,
        })
    return {
        "source_list": sources,
        "header": {
            "path": driver.STUDY_LOCK_HEADER,
            "sha256": "a" * 64,
            "identifiers": identifiers,
            "type_identifiers": ["Ss2plStudyLock"],
            "derivation": "fixture",
        },
        "baseline_identifier_hits": baseline_identifier_hits,
        "receptor_identifiers": receptor_identifiers,
        "preprocessed": rows,
        "checked_translation_units": len(sources),
    }


def _inert_witness_fixture() -> dict:
    sources = [*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"]
    units = []
    for index, source in enumerate(sources):
        before = f"int baseline_{index};"
        after = f"int patched_{index};" if source in driver.INERT_DECLARED_DIFFERENCES else before
        before_sha, before_count = driver._token_hash(before.encode())
        after_sha, after_count = driver._token_hash(after.encode())
        units.append({
            "translation_unit": source,
            "compile_command_sha256": "b" * 64,
            "baseline_cpp_token_sha256": before_sha,
            "patched_cpp_token_sha256": after_sha,
            "baseline_token_count": before_count,
            "patched_token_count": after_count,
            "baseline_preprocessing": _preprocess_cost(before),
            "patched_preprocessing": _preprocess_cost(after),
            "match": (before_sha, before_count) == (after_sha, after_count),
            "declared_difference_reason": driver.INERT_DECLARED_DIFFERENCES.get(source),
        })
    return {
        "collected": True,
        "configuration": {"impl": 0, "kind": 1, "dlr": 1, "wfg": 0},
        "normalization": "fixture",
        "translation_units": units,
        "checked_translation_units": len(units),
        "declared_translation_unit_differences": driver._declared_difference_rows(),
        "observed_differing_translation_units": sorted(driver.INERT_DECLARED_DIFFERENCES),
        "observed_differences_match_declaration": True,
        "all_undeclared_translation_units_match": True,
        "default_stock_lock_gate": driver.validate_default_stock_lock_absence(
            _stock_lock_evidence(sources)
        ),
        "claim": driver._inert_witness_claim(),
    }


def _run(arm: str, thread: int, block: int, tps: float = 100.0) -> dict:
    return {
        "arm": arm,
        "thread_num": thread,
        "block_id": block,
        "experiment": "sweep",
        "metrics": {"throughput_tps": tps, "abort_rate": 0.1},
    }


def _complete_sweep_document() -> dict:
    identity = {"occasion_id": "o1", "pbs_jobid": "1.nqsv", "node": "bnode001"}
    runs = [
        {**_run(arm, thread, block), **identity}
        for block in range(driver.SWEEP_BLOCKS)
        for thread in driver.THREADS
        for arm in driver.PERFORMANCE_ARMS
    ]
    return {
        "mode": "sweep",
        "occasion": identity,
        "performance_runs": runs,
        "phase_runs": [],
        "isolation_observations": [_isolation("job_before")],
        "inert_witness": _inert_witness_fixture(),
        "builds": [
            {
                "arm": arm,
                "wfg_absence": {"preprocessed": [_preprocess_cost()]},
            }
            for arm in driver.PERFORMANCE_ARMS
        ],
    }


def _wfg_evidence() -> dict:
    sources = [
        "/clone/cc/ss2pl/ycsb_ss2pl.cc",
        "/clone/cc/ss2pl/transaction.cc",
        "/clone/cc/ss2pl/util.cc",
        "/clone/cc/ss2pl/bomb_ss2pl.cc",
        "/clone/cc/ss2pl/tpcc_ss2pl.cc",
    ]
    texts = {
        source: (
            'void ShowOptParameters() { print(": SS2PL_WFG_DIAG "); }'
            if source.endswith("/util.cc") else "int ordinary_translation_unit;"
        )
        for source in sources
    }
    return {
        "source_list": sources,
        "symbols": [],
        "strings": [driver.WFG_AXIS_BINARY_STRING],
        "preprocessed": [
            {
                "source": source,
                "text": texts[source],
                "sha256": driver._sha256_bytes(texts[source].encode()),
                **_preprocess_cost(texts[source]),
            }
            for source in sources
        ],
        "checked_translation_units": len(sources),
    }


def _isolation(scope: str, block: str | None = None) -> dict:
    return {
        "scope": scope,
        "block_attempt_id": block,
        "uptime": "up fixture",
        "proc_loadavg": "0.10 0.20 0.30 1/1 1",
        "other_user_cpu_processes": [],
        "competing_ycsb_processes": [],
        "disturbed": False,
    }


def _complete_phase_matrix() -> list[dict]:
    runs = []
    for phase in ("phase1", "phase2"):
        for point in ("high-contention", "headline"):
            for trial in range(3):
                run = {
                    "phase": phase,
                    "point": point,
                    "trial": trial,
                    "timed_out": phase == "phase1" and trial == 0,
                    "returncode": -15 if phase == "phase1" and trial == 0 else 0,
                    "accepted_cycle": None,
                    "cycle_observed": False,
                    "conflict_count": trial + 1,
                    "phase2_counters": None,
                }
                if phase == "phase2":
                    run["phase2_counters"] = {
                        "conflict_count": 3,
                        "no_wait_failure_count": 2,
                        "acquisition_paths": {"exclusive_try": 3},
                    }
                runs.append(run)
    return runs


def _admission_fixture(tmp_path: Path, *, arm: str = "D") -> tuple[Path, dict, str]:
    binary = tmp_path / "ycsb_ss2pl.exe"
    binary.write_bytes(b"fixture-binary")
    requested_cache = driver._expected_cache(arm, backoff=1)
    definitions = {
        driver.CACHE_TO_DEFINE[key]: value
        for key, value in requested_cache.items()
        if key in driver.CACHE_TO_DEFINE
    }
    build = {
        "requested_cache": requested_cache,
        "observed_cache": dict(requested_cache),
        "compile_definitions": [{"file": "fixture.cc", "definitions": definitions}],
        "binary_sha256": driver.sha256_file(binary),
    }
    axes = driver.ARM_CONFIG[arm]
    lines = [
        "#ShowOptParameters(): "
        f"IMPL {axes['impl']}: KIND {axes['kind']}: DLR {axes['dlr']}: WFG {axes['wfg']}",
        *[f"#FLAGS_{key}: {value}" for key, value in driver.WORKLOAD_DEFAULT.items()],
        "abort_counts_: 10", "commit_counts_: 90", "abort_rate: 0.1",
        "throughput[tps]: 100", "actual_extime: 10",
        json.dumps({
            "ss2pl_layout": {
                "sizeof_lock": 64, "alignof_lock": 64, "offsetof_state": 0,
            },
        }),
    ]
    return binary, build, "\n".join(lines)


_CCBENCH_METRIC_OUTPUT = """abort_counts_:  871363
batch_abort_counts_:    0
commit_counts_: 3545176
batch_commit_counts_:   0
abort_rate:     0.1973
batch_abort_rate:       -nan
latency[ns]:    40618.5872
throughput[tps]:        1181725
"""


def test_u1_ccbench_metrics_use_exact_unprefixed_labels():
    assert driver._metric(_CCBENCH_METRIC_OUTPUT, "abort_counts_", int) == 871363
    assert driver._metric(_CCBENCH_METRIC_OUTPUT, "commit_counts_", int) == 3545176
    assert driver._metric(_CCBENCH_METRIC_OUTPUT, "abort_rate", float) == pytest.approx(0.1973)
    assert driver._metric(_CCBENCH_METRIC_OUTPUT, "throughput[tps]", float) == 1181725


def test_u1_batch_metric_lines_cannot_replace_required_unprefixed_lines():
    for label, line in (
        ("abort_counts_", "abort_counts_:  871363\n"),
        ("commit_counts_", "commit_counts_: 3545176\n"),
        ("abort_rate", "abort_rate:     0.1973\n"),
    ):
        with pytest.raises(driver.ContractError, match=rf"missing: {label}"):
            driver._metric(_CCBENCH_METRIC_OUTPUT.replace(line, ""), label, float)


@pytest.mark.parametrize("token", ("-nan", "nan", "inf"))
def test_u1_required_nonfinite_metric_is_rejected(token: str):
    stdout = _CCBENCH_METRIC_OUTPUT.replace(
        "abort_rate:     0.1973", f"abort_rate:     {token}",
    )
    with pytest.raises(driver.ContractError, match="not a finite number"):
        driver._metric(stdout, "abort_rate", float)


def test_u1_duplicate_metric_lines_are_ambiguous():
    stdout = _CCBENCH_METRIC_OUTPUT + "throughput[tps]: 1\n"
    with pytest.raises(driver.ContractError, match="ambiguous: throughput"):
        driver._metric(stdout, "throughput[tps]", float)


def test_u1_missing_metric_line_is_rejected():
    stdout = _CCBENCH_METRIC_OUTPUT.replace("throughput[tps]:        1181725\n", "")
    with pytest.raises(driver.ContractError, match="missing: throughput"):
        driver._metric(stdout, "throughput[tps]", float)


def test_z1_compiled_scanner_preserves_legacy_tokens_hash_and_blanking():
    fixture = (
        "int alpha = 0x1p+2;\\\n"
        'auto raw = u8R"tag(line "quoted" // not comment\n)tag"; '
        "char c='x'; char q='\\''; "
        "alpha >>= 1; value...member; 12e-3\n"
    )
    expected_tokens = [
        "int", "alpha", "=", "0x1p+2", ";", "\\", "auto", "raw", "=",
        'u8R"tag(line "quoted" // not comment\n)tag"', ";", "char", "c", "=",
        "'x'", ";", "char", "q", "=", "'\\''", ";", "alpha", ">>=", "1",
        ";", "value", "...", "member", ";", "12e-3",
    ]
    assert list(driver._cpp_tokens(fixture)) == expected_tokens
    assert driver._token_hash(fixture.encode()) == (
        "0ca0e2301f09e13f17e999352d1a8c7e28625b76f7a41d1b9dcc70abbb332f72",
        30,
    )
    strip_fixture = (
        'int x = "/*literal*/"; // line\n'
        "char c = '}'; /* block\ncomment */ return {x};\n"
    )
    assert driver._strip_cpp_comments_and_literals(strip_fixture) == (
        "int x =              ;        \n"
        "char c =    ;         \n"
        "           return {x};\n"
    )


@pytest.mark.parametrize(
    ("source", "message"),
    (("\"unterminated", "unterminated C++ literal"),
     ('R"tag(unterminated', "unterminated raw C++ string")),
)
def test_z1_compiled_scanner_preserves_unterminated_literal_rejection(
    source: str, message: str,
):
    with pytest.raises(driver.ContractError, match=re.escape(message)):
        list(driver._cpp_tokens(source))


def test_z2_preprocess_cache_keys_command_content_and_source_state(
    monkeypatch, tmp_path: Path,
):
    source = tmp_path / "fixture.cc"
    source.write_text("int value = 1;\n", encoding="utf-8")
    entry = {
        "file": str(source),
        "directory": str(tmp_path),
        "arguments": ["c++", "-DVALUE=1", str(source)],
    }
    calls: list[tuple[str, ...]] = []

    def fake_preprocess(observed):
        argv = tuple(driver._entry_argv(observed))
        calls.append(argv)
        return source.read_bytes() + "\0".join(argv).encode()

    monkeypatch.setattr(driver, "_preprocess", fake_preprocess)
    cache = driver.PreprocessCache()
    first = cache.preprocess(entry, source_state_sha256="1" * 64)
    repeated = cache.preprocess(entry, source_state_sha256="1" * 64)
    assert first["scan"] == repeated["scan"]
    assert first["receipt"]["cache_hit"] is False
    assert repeated["receipt"]["cache_hit"] is True
    assert len(calls) == 1

    source.write_text("int value = 2;\n", encoding="utf-8")
    changed_content = cache.preprocess(entry, source_state_sha256="1" * 64)
    assert changed_content["scan"] != first["scan"]

    changed_entry = {**entry, "arguments": ["c++", "-DVALUE=2", str(source)]}
    changed_argv = cache.preprocess(changed_entry, source_state_sha256="1" * 64)
    assert changed_argv["scan"] != changed_content["scan"]

    changed_state = cache.preprocess(changed_entry, source_state_sha256="2" * 64)
    assert changed_state["receipt"]["cache_hit"] is False
    assert len(calls) == 4
    assert cache.summary() == {
        "requests": 5,
        "hits": 1,
        "entries": 4,
        "avoided_preprocessed_bytes": first["receipt"]["preprocessed_bytes"],
    }


def test_z3_missing_per_tu_preprocessing_cost_is_rejected():
    document = _complete_sweep_document()
    del document["builds"][0]["wfg_absence"]["preprocessed"][0]["token_count"]
    with pytest.raises(driver.ContractError, match="preprocessing cost receipt is incomplete"):
        driver.validate_preprocessing_receipts(document)


# M1: workload binding.
def test_m1_correct_workload_binding_is_accepted():
    requested = dict(driver.WORKLOAD_DEFAULT)
    observed = {key: str(value) for key, value in requested.items()}
    driver.validate_workload_binding(requested, observed)


def test_m1_mutated_admission_rejects_wrong_runtime_record_count(tmp_path: Path):
    binary, build, stdout = _admission_fixture(tmp_path)
    stdout = stdout.replace(
        "#FLAGS_ycsb_tuple_num: 1000000", "#FLAGS_ycsb_tuple_num: 100000",
    )
    with pytest.raises(driver.ContractError, match="workload binding mismatch"):
        driver._admit_output(
            stdout, arm="D", workload=driver.WORKLOAD_DEFAULT, build=build,
            binary=binary, thread_num=1, require_thread_commits=False,
        )


# M2: build/runtime binding.
def test_m2_correct_runtime_build_axes_are_accepted():
    driver.validate_build_binding(driver.ARM_CONFIG["D"], {
        "impl": "1", "kind": "1", "dlr": "2", "wfg": "0",
    })


def test_m2_mutated_admission_rejects_phase_label_forgery(tmp_path: Path):
    binary, build, stdout = _admission_fixture(tmp_path)
    stdout = stdout.replace("KIND 1", "KIND 0")
    with pytest.raises(driver.ContractError, match="build binding mismatch"):
        driver._admit_output(
            stdout, arm="D", workload=driver.WORKLOAD_DEFAULT, build=build,
            binary=binary, thread_num=1, require_thread_commits=False,
        )


# M3: exact, nonempty four-surface WFG absence gate.
def test_m3_correct_wfg_free_performance_evidence_is_accepted():
    result = driver.validate_wfg_absence(_wfg_evidence())
    assert result["checked_translation_units"] == 5
    assert result["allowed_axis_label"]["token_count"] == 1


@pytest.mark.parametrize(
    "mutation",
    (
        "empty", "watchdog", "second-label", "header-inline", "binary-string",
    ),
)
def test_m3_mutated_wfg_surfaces_are_rejected(mutation: str):
    evidence = _wfg_evidence()
    if mutation == "empty":
        evidence = {
            "source_list": [], "symbols": [], "strings": [], "preprocessed": [],
            "checked_translation_units": 0,
        }
    elif mutation == "watchdog":
        evidence["strings"].append("SS2PL_WFG_DIAG_watchdog")
    elif mutation == "second-label":
        row = evidence["preprocessed"][2]
        row["text"] += ' void diagnostic_logger() { print(": SS2PL_WFG_DIAG "); }'
        row["sha256"] = driver._sha256_bytes(row["text"].encode())
    elif mutation == "header-inline":
        row = evidence["preprocessed"][4]
        row["text"] += " inline void ss2pl_wfg_snapshot() {}"
        row["sha256"] = driver._sha256_bytes(row["text"].encode())
    else:
        evidence["strings"].append("wait_for_graph")
    with pytest.raises(driver.ContractError, match="WFG absence gate failed"):
        driver.validate_wfg_absence(evidence)


def test_m3_mutated_preprocessed_collector_is_rejected(monkeypatch, tmp_path: Path):
    evidence = _wfg_evidence()
    entries = [
        {"file": row["source"], "directory": "/clone", "arguments": ["c++", row["source"]]}
        for row in evidence["preprocessed"]
    ]
    texts = {row["source"]: row["text"] for row in evidence["preprocessed"]}
    texts[entries[0]["file"]] += " inline void ss2pl_wfg_snapshot() {}"

    def fake_checked(argv, **_kwargs):
        output = "" if argv[0] == "nm" else driver.WFG_AXIS_BINARY_STRING + "\n"
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr="")

    monkeypatch.setattr(driver, "_run_checked", fake_checked)
    monkeypatch.setattr(
        driver, "_preprocess", lambda entry: texts[entry["file"]].encode(),
    )
    with pytest.raises(driver.ContractError, match="preprocessed_hits"):
        driver._wfg_absence_evidence(tmp_path / "binary", entries)


def test_wfg_population_gate_rejects_duplicate_sources_and_count_drift():
    duplicate = _wfg_evidence()
    duplicate["source_list"][1] = duplicate["source_list"][0]
    with pytest.raises(driver.ContractError, match="not unique"):
        driver.validate_wfg_absence(duplicate)
    drift = _wfg_evidence()
    drift["checked_translation_units"] = 4
    with pytest.raises(driver.ContractError, match="counts differ"):
        driver.validate_wfg_absence(drift)


# M4: patched source ownership, independent of displayed counters.
def _write_abort_sources(clone: Path, transaction_increment: bool = False) -> None:
    transaction = clone / "cc/ss2pl/transaction.cc"
    workload = clone / "include/ycsb.hh"
    transaction.parent.mkdir(parents=True)
    workload.parent.mkdir(parents=True)
    increment = "++result_->local_abort_counts_;" if transaction_increment else "status_ = aborted;"
    transaction.write_text(
        f"void TxExecutor::abort() {{ {increment} }}\n", encoding="utf-8",
    )
    workload.write_text(
        "void run() { ++result_->local_abort_counts_; result_->local_abort_counts_++; }\n",
        encoding="utf-8",
    )


def test_m4_correct_patched_source_abort_ownership_is_accepted(tmp_path: Path):
    _write_abort_sources(tmp_path)
    result = driver.validate_abort_counter_ownership(tmp_path)
    assert result["txexecutor_abort_increment_count"] == 0
    assert result["workload_abort_increment_count"] == 2


def test_m4_mutated_txexecutor_abort_increment_is_rejected(tmp_path: Path):
    _write_abort_sources(tmp_path, transaction_increment=True)
    with pytest.raises(driver.ContractError, match="TxExecutor::abort increments=1"):
        driver.validate_abort_counter_ownership(tmp_path)


# M5: exact (arm, thread, block) coverage.
def test_m5_complete_performance_matrix_is_accepted():
    driver.validate_mode_document(_complete_sweep_document(), "sweep")


def test_m5_mutated_performance_matrix_rejects_missing_cell():
    document = _complete_sweep_document()
    document["performance_runs"].pop()
    with pytest.raises(driver.ContractError, match="matrix mismatch"):
        driver.validate_mode_document(document, "sweep")


# M6: strict 3.0 percent floor rule.
def test_m6_correct_above_floor_effect_is_accepted_as_directional():
    assert plot.floor_verdict(1.030) == "above_floor_positive"
    assert plot.floor_verdict(0.970) == "above_floor_negative"


def test_m6_mutated_below_floor_effect_is_not_reported_as_winner():
    runs = []
    for block in range(5):
        runs.extend((_run("B", 24, block, 100.0), _run("D", 24, block, 102.9)))
    effect = plot.paired_log_effect(runs, "B", "D", 24)
    assert effect["floor_verdict"] == "below_floor_no_reproducible_difference_established"


# M7: blockwise paired log ratio, not independent arm means.
def test_m7_correct_constant_paired_log_effect_is_accepted():
    runs = []
    for block, base in enumerate((100.0, 300.0, 900.0)):
        runs.extend((_run("B", 24, block, base), _run("D", 24, block, base * 1.1)))
    effect = plot.paired_log_effect(runs, "B", "D", 24)
    assert effect["ratio"] == pytest.approx(1.1)
    assert effect["mean_log_ratio"] == pytest.approx(math.log(1.1))


def test_m7_mutated_independent_mean_ratio_differs_from_paired_estimator():
    x = (10.0, 100.0, 1000.0)
    y = (20.0, 90.0, 1100.0)
    runs = []
    for block, (left, right) in enumerate(zip(x, y)):
        runs.extend((_run("B", 24, block, left), _run("D", 24, block, right)))
    effect = plot.paired_log_effect(runs, "B", "D", 24)
    expected = math.exp(sum(math.log(right / left) for left, right in zip(x, y)) / 3)
    independent = (sum(y) / len(y)) / (sum(x) / len(x))
    assert effect["ratio"] == pytest.approx(expected)
    assert not math.isclose(effect["ratio"], independent, rel_tol=1e-5)


# M8: one occasion and one node per receipt.
def test_m8_correct_single_occasion_receipt_is_accepted():
    identity = {"occasion_id": "o1", "pbs_jobid": "1.nqsv", "node": "bnode001"}
    document = {
        "occasion": identity,
        "performance_runs": [{**identity, "arm": "B"}],
        "phase_runs": [{**identity, "phase": "phase1"}],
    }
    driver.validate_single_occasion(document)


def test_m8_mutated_cross_node_receipt_is_rejected():
    document = _complete_sweep_document()
    document["performance_runs"][0]["node"] = "bnode002"
    with pytest.raises(driver.ContractError, match="crosses occasion or node"):
        driver.validate_mode_document(document, "sweep")


# M9: exact input SHA256 in figure provenance.
def test_m9_correct_figure_provenance_is_accepted(tmp_path: Path):
    source = tmp_path / "input.json"
    source.write_text('{"fixture":true}\n', encoding="utf-8")
    provenance = plot._base_provenance(
        "fixture", [source], {"threads": [1], "environment": {"node": "plot001"}},
        {"point": 1},
    )
    plot.validate_provenance(provenance, [source])
    assert provenance["inputs"][0]["sha256"] == plot.sha256_file(source)


def test_m9_mutated_figure_provenance_rejects_wrong_sha256(tmp_path: Path):
    source = tmp_path / "input.json"
    source.write_text('{"fixture":true}\n', encoding="utf-8")
    provenance = plot._base_provenance(
        "fixture", [source], {"environment": {"node": "plot001"}}, {"point": 1},
    )
    provenance["inputs"][0]["sha256"] = "0" * 64
    with pytest.raises(plot.PlotContractError, match="SHA256 mismatch"):
        plot.validate_provenance(provenance, [source])


def test_m9_generation_execution_writes_validated_provenance(monkeypatch, tmp_path: Path):
    sweep = _complete_sweep_document()
    for run in sweep["performance_runs"]:
        run["workload"] = dict(driver.WORKLOAD_DEFAULT)
    sweep["environment"] = {"node": "bnode001", "cpu_model": "fixture"}
    controls = {
        "occasion": {"occasion_id": "c", "pbs_jobid": "2.nqsv", "node": "bnode002"},
        "performance_runs": [{
            **_run("B", 24, 0), "workload": dict(driver.WORKLOAD_DEFAULT),
        }],
        "environment": {"node": "bnode002", "cpu_model": "fixture"},
    }
    sweep_path = tmp_path / "sweep.json"
    controls_path = tmp_path / "controls.json"
    sweep_path.write_text("{}\n", encoding="utf-8")
    controls_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(plot, "ensure_plot_host_allowed", lambda: None)
    monkeypatch.setattr(
        plot, "load_receipt", lambda _path, mode: sweep if mode == "sweep" else controls,
    )
    for name in (
        "scalability_figure", "abort_figure", "paired_figure", "controls_figure",
        "deadlock_figure",
    ):
        monkeypatch.setattr(plot, name, lambda _document, _prefix: {"fixture": True})
    output_dir = tmp_path / "figures"
    plot.generate(sweep_path, controls_path, output_dir)
    provenance_paths = sorted(output_dir.glob("*.provenance.json"))
    assert len(provenance_paths) == 5
    for path in provenance_paths:
        provenance = json.loads(path.read_text(encoding="utf-8"))
        plot.validate_provenance(provenance, [sweep_path, controls_path])
        assert provenance["figure_values"]["control_experiment_input"]["provided"] is True


def test_generation_without_controls_omits_only_control_figures_and_records_absence(
    monkeypatch, tmp_path: Path,
):
    sweep = _complete_sweep_document()
    for run in sweep["performance_runs"]:
        run["workload"] = dict(driver.WORKLOAD_DEFAULT)
    sweep["environment"] = {"node": "bnode001", "cpu_model": "fixture"}
    sweep_path = tmp_path / "sweep.json"
    sweep_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(plot, "ensure_plot_host_allowed", lambda: None)
    monkeypatch.setattr(plot, "load_receipt", lambda _path, mode: sweep)
    for name in ("scalability_figure", "abort_figure", "paired_figure"):
        monkeypatch.setattr(plot, name, lambda _document, _prefix: {"fixture": True})
    monkeypatch.setattr(
        plot, "controls_figure",
        lambda *_args: (_ for _ in ()).throw(AssertionError("controls figure called")),
    )
    monkeypatch.setattr(
        plot, "deadlock_figure",
        lambda *_args: (_ for _ in ()).throw(AssertionError("deadlock figure called")),
    )

    output_dir = tmp_path / "figures"
    outputs = plot.generate(sweep_path, None, output_dir)

    assert len(outputs) == 9
    provenance_paths = sorted(output_dir.glob("*.provenance.json"))
    assert len(provenance_paths) == 3
    for path in provenance_paths:
        provenance = json.loads(path.read_text(encoding="utf-8"))
        plot.validate_provenance(provenance, [sweep_path])
        observation = provenance["figure_values"]["control_experiment_input"]
        assert observation["provided"] is False
        assert "was not provided" in observation["statement"]


def test_controls_cli_argument_is_optional():
    args = plot._parser().parse_args(["--sweep", "sweep.json", "--output-dir", "figures"])
    assert args.controls is None


# M10: non-tick bbox overlap is fatal; tick/tick overlap is outside this gate.
def test_m10_correct_nonoverlapping_bboxes_are_accepted():
    boxes = [
        ("axis label", (0.0, 0.0, 10.0, 10.0), False),
        ("legend", (20.0, 20.0, 30.0, 30.0), False),
        ("tick-a", (40.0, 40.0, 50.0, 50.0), True),
        ("tick-b", (45.0, 45.0, 55.0, 55.0), True),
    ]
    assert plot.find_non_tick_overlaps(boxes) == []


def test_m10_mutated_bbox_gate_detects_non_tick_overlap(monkeypatch):
    boxes = [
        ("title", (0.0, 0.0, 10.0, 10.0), False),
        ("legend", (5.0, 5.0, 12.0, 12.0), False),
    ]
    assert plot.find_non_tick_overlaps(boxes) == [("title", "legend")]

    class FakeFigure:
        def __init__(self):
            self.saved = []
            self.axes = []
            self.canvas = type("FakeCanvas", (), {"draw": lambda _self: None})()

        def savefig(self, path):
            self.saved.append(Path(path).suffix)

    figure = FakeFigure()
    monkeypatch.setattr(
        plot, "_figure_overlap_check",
        lambda _figure: (_ for _ in ()).throw(plot.PlotContractError("bbox overlap")),
    )
    with pytest.raises(plot.PlotContractError, match="bbox overlap"):
        plot._save_checked(figure, Path("fixture"))
    assert figure.saved == []


# M11: job-before and paired block isolation records.
def test_m11_correct_isolation_ledger_is_accepted():
    records = [
        _isolation("job_before"),
        _isolation("block_before", "b0-a0"),
        _isolation("block_after", "b0-a0"),
    ]
    driver.validate_isolation_records(records)


def test_m11_mutated_execution_receipt_rejects_missing_job_before_collection():
    document = _complete_sweep_document()
    document["isolation_observations"] = []
    with pytest.raises(driver.ContractError, match="job-before"):
        driver.validate_mode_document(document, "sweep")


# M12: reverse plus empty status is required.
def test_m12_correct_patch_reverse_cleanup_is_accepted():
    document = _complete_sweep_document()
    document["cleanup"] = {
        "reverse_attempted": True,
        "reverse_succeeded": True,
        "git_status_porcelain": "",
    }
    driver.validate_completed_receipt(document, "sweep")


def test_m12_mutated_patch_reverse_cleanup_rejects_dirty_tree():
    document = _complete_sweep_document()
    document["cleanup"] = {
        "reverse_attempted": True,
        "reverse_succeeded": True,
        "git_status_porcelain": " M cc/ss2pl/transaction.cc\n",
    }
    with pytest.raises(driver.ContractError, match="dirty"):
        driver.validate_completed_receipt(document, "sweep")


def test_runtime_axis_parser_requires_show_opt_parameters_line_name():
    axes = "IMPL 1: KIND 1: DLR 2: WFG 0"
    with pytest.raises(driver.ContractError, match="ShowOptParameters"):
        driver.parse_runtime_axes("#forged: " + axes)
    prefixed = (
        "batch_CCBENCH_SS2PL_LOCK_IMPL 1: batch_CCBENCH_SS2PL_LOCK_KIND 1: "
        "batch_CCBENCH_SS2PL_DLR 2: batch_CCBENCH_SS2PL_WFG_DIAG 0"
    )
    with pytest.raises(driver.ContractError, match="ShowOptParameters"):
        driver.parse_runtime_axes("#ShowOptParameters(): " + prefixed)
    observed, line = driver.parse_runtime_axes("#ShowOptParameters(): " + axes)
    assert observed == {"impl": 1, "kind": 1, "dlr": 2, "wfg": 0}
    assert line.startswith("#ShowOptParameters()")


def test_runtime_workload_parser_accepts_equal_duplicates_and_rejects_conflicts():
    equal = "#FLAGS_ycsb_tuple_num: 100\n#FLAGS_ycsb_tuple_num: 100\n"
    flags, lines = driver.parse_runtime_flags(equal)
    assert flags == {"ycsb_tuple_num": "100"}
    assert len(lines) == 2
    assert driver.parse_runtime_flags("batch_#FLAGS_ycsb_tuple_num: 999\n") == ({}, [])
    with pytest.raises(driver.ContractError, match="conflicting duplicate"):
        driver.parse_runtime_flags(
            "#FLAGS_ycsb_tuple_num: 10\n#FLAGS_ycsb_tuple_num: 100\n"
        )


def test_layout_record_is_preserved_when_collected():
    layout = driver._parse_layout([{
        "ss2pl_layout": {"sizeof_lock": 64, "alignof_lock": 64, "offsetof_state": 0},
    }])
    assert layout["collected"] is True
    assert layout["sizeof_lock"] == 64


@pytest.mark.parametrize(
    "events",
    ([], [{"ss2pl_layout": {"sizeof_lock": 64}}], [{
        "ss2pl_layout": {
            "sizeof_lock": 0, "alignof_lock": 64, "offsetof_state": 0,
        },
    }]),
)
def test_layout_collection_failure_is_recorded_without_rejection(events: list[dict]):
    layout = driver._parse_layout(events)
    assert layout["collected"] is False
    assert layout["failure"]["type"] == "ContractError"
    assert layout["failure"]["message"]


def test_admission_continues_without_layout_record(tmp_path: Path):
    binary, build, stdout = _admission_fixture(tmp_path)
    stdout = "\n".join(
        line for line in stdout.splitlines() if not line.startswith("{")
    )
    admitted = driver._admit_output(
        stdout, arm="D", workload=driver.WORKLOAD_DEFAULT, build=build,
        binary=binary, thread_num=1, require_thread_commits=False,
    )
    assert admitted["layout"]["collected"] is False
    assert admitted["metrics"]["throughput_tps"] == 100


def _collect_inert_fixture(
    monkeypatch, tmp_path: Path, differing: set[str],
) -> dict:
    clone = tmp_path / "clone"
    sources = [*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"]
    entries = []
    for index, source in enumerate(sources):
        path = clone / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"int baseline_{index};\n", encoding="utf-8")
        entries.append({
            "file": str(path), "directory": str(clone),
            "arguments": ["c++", str(path)],
        })
    header = clone / driver.STUDY_LOCK_HEADER
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text(
        "class Ss2plStudyLock {\n"
        " public: bool try_study_lock(); void init(); int load(); int max();\n"
        " private: int study_state_;\n"
        "};\n",
        encoding="utf-8",
    )
    state = {"applied": True}
    monkeypatch.setattr(driver, "_tracked_at_head", lambda *_args: True)
    monkeypatch.setattr(driver, "_apply_patch", lambda *_args, **_kwargs: None)
    def preprocess(entry):
        source = Path(entry["file"]).resolve().relative_to(clone.resolve()).as_posix()
        baseline = Path(entry["file"]).read_bytes() + b" void init(); int load; int max;"
        if not state["applied"] or source not in differing:
            return baseline
        if source == "cc/ss2pl/util.cc":
            return b'void ShowOptParameters() { print(": SS2PL_LOCK_IMPL "); } int patched_util;'
        return baseline + f" int patched_{Path(source).stem};".encode()

    monkeypatch.setattr(driver, "_preprocess", preprocess)
    state["applied"] = True
    return driver.collect_inert_witness(
        clone, tmp_path / "study.patch", entries, state,
    )


def test_w1_declared_differences_exactly_are_accepted(monkeypatch, tmp_path: Path):
    witness = _collect_inert_fixture(
        monkeypatch, tmp_path, set(driver.INERT_DECLARED_DIFFERENCES),
    )
    assert witness["observed_differences_match_declaration"] is True
    assert witness["all_undeclared_translation_units_match"] is True
    reasons = {
        row["translation_unit"]: row["declared_difference_reason"]
        for row in witness["translation_units"]
    }
    assert reasons == {
        **driver.INERT_DECLARED_DIFFERENCES,
        "cc/ss2pl/tpcc_ss2pl.cc": None,
    }
    gate = witness["default_stock_lock_gate"]
    assert gate["baseline_identifier_hits"] == ["init", "load", "max"]
    assert gate["receptor_identifiers"] == [
        "Ss2plStudyLock", "study_state_", "try_study_lock",
    ]


def test_w1_undeclared_difference_is_rejected(monkeypatch, tmp_path: Path):
    differing = {*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"}
    witness = _collect_inert_fixture(monkeypatch, tmp_path, differing)
    assert witness["collected"] is True
    assert witness["observed_differences_match_declaration"] is False
    assert witness["all_undeclared_translation_units_match"] is False
    assert "cc/ss2pl/tpcc_ss2pl.cc" in witness["observed_differing_translation_units"]


def test_w1_declared_but_matching_translation_unit_is_rejected(
    monkeypatch, tmp_path: Path,
):
    differing = set(driver.INERT_DECLARED_DIFFERENCES) - {"cc/ss2pl/transaction.cc"}
    witness = _collect_inert_fixture(monkeypatch, tmp_path, differing)
    assert witness["collected"] is True
    assert witness["observed_differences_match_declaration"] is False
    assert witness["all_undeclared_translation_units_match"] is True
    assert "cc/ss2pl/transaction.cc" not in witness["observed_differing_translation_units"]


def test_inert_witness_collection_failure_is_recorded_without_rejection(
    monkeypatch, tmp_path: Path,
):
    monkeypatch.setattr(
        driver, "collect_inert_witness",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            driver.ContractError("preprocessing unavailable")
        ),
    )
    receipt = driver.collect_inert_witness_observation(
        tmp_path / "clone", tmp_path / "study.patch", [], {"applied": True},
    )
    assert receipt["collected"] is False
    assert receipt["failure"] == {
        "type": "ContractError", "message": "preprocessing unavailable",
    }
    assert receipt["default_stock_lock_gate"]["collected"] is False
    driver.validate_inert_witness_receipt(receipt)


def test_uncollected_inert_witness_is_accepted_by_final_preprocessing_check():
    document = _complete_sweep_document()
    document["inert_witness"] = driver._uncollected_inert_witness(
        driver.ContractError("preprocessing unavailable")
    )
    driver.validate_preprocessing_receipts(document)


def test_w2_default_stock_lock_gate_accepts_only_the_positioned_axis_label():
    sources = [*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"]
    receipt = driver.validate_default_stock_lock_absence(_stock_lock_evidence(sources))
    assert receipt["collected"] is True
    assert receipt["passed"] is True
    assert receipt["checked_identifiers"] == [
        "Ss2plStudyLock", "study_state_", "try_study_lock",
    ]
    assert receipt["baseline_identifier_hits"] == ["init", "load", "max"]
    assert receipt["receptor_identifiers"] == receipt["checked_identifiers"]
    assert receipt["allowed_axis_label"] == {
        "literal": driver.STUDY_LOCK_AXIS_LITERAL,
        "source": "cc/ss2pl/util.cc",
        "function": "ShowOptParameters",
        "token_count": 1,
    }


def test_w2_default_stock_lock_observation_records_identifier_and_axis_hits():
    sources = [*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"]
    identifier_receipt = driver.validate_default_stock_lock_absence(
        _stock_lock_evidence(sources, injected_source="cc/ss2pl/transaction.cc")
    )
    assert identifier_receipt["collected"] is True
    assert identifier_receipt["passed"] is False
    assert identifier_receipt["findings"]["identifier_hits"]
    misplaced = _stock_lock_evidence(sources)
    row = next(
        item for item in misplaced["preprocessed"]
        if item["source"] == "cc/ss2pl/transaction.cc"
    )
    text = 'void forged() { print(": SS2PL_LOCK_IMPL "); }'
    row["token_scan"] = driver._scan_cpp_tokens_for_study_lock(
        text.encode(), misplaced["receptor_identifiers"],
    )
    row["sha256"] = row["token_scan"]["preprocessed_sha256"]
    axis_receipt = driver.validate_default_stock_lock_absence(misplaced)
    assert axis_receipt["collected"] is True
    assert axis_receipt["passed"] is False
    assert axis_receipt["findings"]["allowed_locations"] != axis_receipt["findings"][
        "expected_location"
    ]


def test_w2_default_stock_lock_collection_failure_is_recorded():
    sources = [*driver.INERT_DECLARED_DIFFERENCES, "cc/ss2pl/tpcc_ss2pl.cc"]
    evidence = _stock_lock_evidence(sources)
    evidence["baseline_identifier_hits"] = list(evidence["header"]["identifiers"])
    evidence["receptor_identifiers"] = []
    receipt = driver.validate_default_stock_lock_absence(evidence)
    assert receipt["collected"] is False
    assert "could not calibrate" in receipt["failure"]["message"]


def test_w2_stock_lock_inspection_exception_does_not_discard_inert_witness(
    monkeypatch, tmp_path: Path,
):
    monkeypatch.setattr(
        driver, "validate_default_stock_lock_absence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            driver.ContractError("identifier scan unavailable")
        ),
    )
    witness = _collect_inert_fixture(
        monkeypatch, tmp_path, set(driver.INERT_DECLARED_DIFFERENCES),
    )
    assert witness["collected"] is True
    assert witness["default_stock_lock_gate"]["collected"] is False
    assert witness["default_stock_lock_gate"]["failure"] == {
        "type": "ContractError", "message": "identifier scan unavailable",
    }


def test_w3_missing_inert_witness_claim_is_rejected():
    document = _complete_sweep_document()
    del document["inert_witness"]["claim"]
    with pytest.raises(driver.ContractError, match="claim is missing"):
        driver.validate_preprocessing_receipts(document)


def test_phase2_counter_gate_rejects_empty_conflict_observation():
    accepted = driver._phase2_counters([{
        "conflict_count": 3,
        "no_wait_failure_count": 2,
        "acquisition_paths": {"exclusive_try": 3},
    }])
    assert accepted["conflict_count"] == 3
    with pytest.raises(driver.ContractError, match="positive conflict"):
        driver._phase2_counters([{
            "conflict_count": 0,
            "no_wait_failure_count": 0,
            "acquisition_paths": {"exclusive_try": 0},
        }])


def test_phase1_matrix_accepts_timeout_and_normal_completion_observations():
    driver.validate_phase_matrix(_complete_phase_matrix())


def test_phase1_natural_completion_records_cycle_and_conflict_observations(
    monkeypatch, tmp_path: Path,
):
    binary = tmp_path / "phase1.exe"
    binary.write_bytes(b"fixture")
    observed_expectations = []

    def fake_run_process(argv, *, timeout_s, expected_timeout):
        observed_expectations.append(expected_timeout)
        return 0, "fixture stdout", "", False, "natural"

    monkeypatch.setattr(driver, "_run_process", fake_run_process)
    monkeypatch.setattr(
        driver, "_admit_output",
        lambda *_args, **_kwargs: {
            "json_events": [{"conflict_count": 17}],
            "runtime_axes": dict(driver.ARM_CONFIG["phase1"]),
        },
    )

    run = driver._run_phase_trial(
        phase="phase1", build={"binary": str(binary)},
        workload=driver.WORKLOAD_DEFAULT, trial=0, point="headline",
        clocks_per_us=2100,
        occasion={"occasion_id": "o", "pbs_jobid": "1.nqsv", "node": "bnode001"},
    )

    assert observed_expectations == [None]
    assert run["timed_out"] is False
    assert run["cycle_observed"] is False
    assert run["conflict_count"] == 17
    assert run["conflict_observation"] == {
        "collected": True,
        "count": 17,
        "statement": "Observed conflict count: 17.",
    }


def test_phase1_zero_cycles_is_recorded_as_valid_observation(monkeypatch):
    document = {"phase_runs": [], "phase_timings": {}}

    def fake_trial(*, phase, workload, trial, point, **_kwargs):
        return {
            "phase": phase,
            "point": point,
            "trial": trial,
            "duration_s": 0.1,
            "timed_out": False,
            "accepted_cycle": None,
            "cycle_observed": False,
            "conflict_count": 4,
        }

    monkeypatch.setattr(driver, "_run_phase_trial", fake_trial)
    driver._run_controls_phases(
        document, {"phase1": {}, "phase2": {}}, 2100,
        {"occasion_id": "o", "pbs_jobid": "1.nqsv", "node": "bnode001"},
    )

    observation = document["phase1_observation"]
    assert observation["trials"] == 6
    assert observation["cycles_observed"] == 0
    assert observation["cycle_observation"] == "0 of 6 phase1 trials"
    assert observation["no_cycle_observed_in_window"] is True


@pytest.mark.parametrize("value", (0.0, -1.0, float("inf"), float("nan")))
def test_throughput_gate_rejects_nonpositive_or_nonfinite_values(value: float):
    with pytest.raises(driver.ContractError, match="finite and positive"):
        driver.validate_positive_throughputs([_run("B", 1, 0, value)])


def test_parallel_efficiency_uses_ratio_of_medians():
    runs = []
    for block, value in enumerate((1.0, 100.0, 100.0)):
        runs.append(_run("B", 1, block, value))
    for block, value in enumerate((2.0, 2.0, 200.0)):
        runs.append(_run("B", 2, block, value))
    assert plot.parallel_efficiency_from_medians(runs, "B", 2) == pytest.approx(0.01)


def test_replication_requires_distinct_node_job_and_occasion():
    sweep = {"occasion": {"occasion_id": "s", "pbs_jobid": "1.nqsv", "node": "bnode001"}}
    replication = {
        "occasion": {"occasion_id": "r", "pbs_jobid": "2.nqsv", "node": "bnode002"},
    }
    plot.validate_replication_independence(sweep, replication)
    for field in ("occasion_id", "pbs_jobid", "node"):
        mutated = json.loads(json.dumps(replication))
        mutated["occasion"][field] = sweep["occasion"][field]
        with pytest.raises(plot.PlotContractError, match="replication must use"):
            plot.validate_replication_independence(sweep, mutated)


def test_plot_host_gate_rejects_measurement_node():
    plot.ensure_plot_host_allowed("analysis001")
    with pytest.raises(plot.PlotContractError, match="forbidden"):
        plot.ensure_plot_host_allowed("bnode044")


def test_figure_caption_expands_conditions_environment_and_warmup():
    document = _complete_sweep_document()
    for run in document["performance_runs"]:
        run["workload"] = dict(driver.WORKLOAD_DEFAULT)
    document["environment"] = {"node": "bnode001", "cpu_model": "fixture"}
    caption = plot._condition_caption(document, blocks=5)
    for needle in (
        "records=1000000", "skew=0.9", "rratio=50", "threads=1,2,4",
        "env=bnode001", "process-internal warmup=none",
    ):
        assert needle in caption
    assert plot.ARM_LABELS["B"] == "exclusive Wound-Wait"


def test_five_block_rotation_is_exactly_position_balanced():
    orders = [driver.rotated_arm_order(driver.PERFORMANCE_ARMS, block) for block in range(5)]
    for arm in driver.PERFORMANCE_ARMS:
        assert [order.index(arm) for order in orders] == [
            (driver.PERFORMANCE_ARMS.index(arm) - block) % 5 for block in range(5)
        ]
        assert sorted(order.index(arm) for order in orders) == list(range(5))
    assert driver.SWEEP_BLOCKS == 5
    assert plot.T975[4] == pytest.approx(2.776)


@pytest.mark.parametrize("stage", ("build", "run", "collection"))
def test_stage_deadline_independently_stops_a_child_command(stage: str):
    document = {"stage_deadlines": {}}
    with pytest.raises(driver.ContractError, match=rf"{stage} stage deadline exceeded"):
        with driver._stage_deadline(document, stage, 0.03):
            driver._run_checked(
                [sys.executable, "-c", "import time; time.sleep(0.2)"], timeout=1,
            )
    assert document["stage_deadlines"][stage]["within_deadline"] is False


def test_saturation_predicate_uses_median_and_first_3_percent_knee():
    runs = []
    medians = {1: 100.0, 2: 150.0, 4: 153.0, 8: 250.0}
    for thread, median in medians.items():
        for block, delta in enumerate((-1.0, 0.0, 1.0)):
            runs.append(_run("B", thread, block, median + delta))
    original = plot.THREADS
    plot.THREADS = (1, 2, 4, 8)
    try:
        result = plot.saturation_point(runs, "B")
    finally:
        plot.THREADS = original
    assert result["n_star"] == 2


def test_owned_job_policy_and_shell_syntax_contract():
    policy = json.loads((ROOT / "tools/pegasus/policy.json").read_text(encoding="utf-8"))["ss2pl_lock_study"]
    assert policy["walltime_s"] == 10800
    assert policy["build_and_witness_cap_s"] == 2100
    for mode, run_cap in policy["mode_run_cap_s"].items():
        inner = (
            policy["dependency_build_cap_s"] + policy["build_and_witness_cap_s"]
            + run_cap + policy["collection_cap_s"] + policy["finalize_reserve_s"]
        )
        assert inner < policy["walltime_s"], mode
    shell = ROOT / "tools/pegasus/ss2pl_lock_study.sh"
    checked = subprocess.run(["bash", "-n", str(shell)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr


def test_shell_sanitized_path_conditionally_adds_scheduler_bins():
    shell = (ROOT / "tools/pegasus/ss2pl_lock_study.sh").read_text(encoding="utf-8")
    assert "for candidate in /opt/nec/nqsv/bin /system/tool/bin; do" in shell
    assert '[[ -d "$candidate" ]] || continue' in shell
    assert 'SANITIZED_PATH="${SANITIZED_PATH}:$candidate"' in shell
    assert "REQUIRED_COMMANDS=(git cmake cc c++ make as ld ar ranlib nm strings timeout date)" in shell


@pytest.mark.parametrize("failure", ("missing", "command", "format"))
def test_qstat_failure_is_recorded_and_does_not_raise(monkeypatch, failure: str):
    monkeypatch.setattr(
        driver.shutil, "which",
        lambda command, path=None: None if failure == "missing" else "/fixture/qstat",
    )
    if failure == "command":
        monkeypatch.setattr(
            driver, "_run_checked",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                driver.ContractError("qstat command failed")
            ),
        )
    elif failure == "format":
        monkeypatch.setattr(
            driver, "_run_checked",
            lambda argv, **_kwargs: subprocess.CompletedProcess(
                argv, 0, stdout="changed scheduler output\n", stderr="",
            ),
        )
    record = driver._qstat_elapse("0:123.nqsv")
    assert record["collected"] is False
    assert record["failure"]["type"] in {"FileNotFoundError", "ContractError"}


def test_driver_run_continues_when_qstat_is_unavailable(monkeypatch, tmp_path: Path):
    repo = tmp_path / "repo"
    scratch = tmp_path / "scratch"
    gflags = tmp_path / "gflags"
    glog = tmp_path / "glog"
    thirdparty = tmp_path / "thirdparty"
    canonical = tmp_path / "canonical"
    for directory in (scratch, gflags, glog, thirdparty, canonical):
        directory.mkdir()
    (repo / "tools/pegasus").mkdir(parents=True)
    (repo / "tools/pegasus/policy.json").write_text("{}\n", encoding="utf-8")
    patch = tmp_path / "study.patch"
    patch.write_text("fixture\n", encoding="utf-8")
    output = tmp_path / "receipt.json"
    args = driver.argparse.Namespace(
        repo_root=repo,
        patch=patch,
        output=output,
        scratch_root=scratch,
        gflags_prefix=gflags,
        glog_prefix=glog,
        thirdparty_root=thirdparty,
        clocks_per_us=2100,
        mode="sweep",
        max_block_retries=0,
        jobs=1,
        occasion_id="fixture",
        build_cap_s=30,
        run_cap_s=30,
        collection_cap_s=30,
    )
    measurements: list[str] = []
    monkeypatch.setenv("PBS_JOBID", "0:123.nqsv")
    monkeypatch.setattr(driver.socket, "gethostname", lambda: "bnode001")
    monkeypatch.setattr(
        driver.shutil, "which",
        lambda command, path=None: None if command == "qstat" else f"/fixture/{command}",
    )
    monkeypatch.setattr(driver, "_validate_thirdparty", lambda *_args: [])
    monkeypatch.setattr(
        driver, "verify_canonical_submodule",
        lambda _root: {"path": str(canonical), "head": "a" * 40},
    )
    monkeypatch.setattr(driver, "clone_network_free", lambda _source, destination: destination.mkdir())
    monkeypatch.setattr(driver, "_apply_patch", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(driver, "validate_abort_counter_ownership", lambda _clone: {})
    monkeypatch.setattr(
        driver, "_configure",
        lambda _source, build_dir, **_kwargs: (
            (_ for _ in ()).throw(driver.ContractError("inert configure unavailable"))
            if build_dir.name == "inert-witness" else {}
        ),
    )
    monkeypatch.setattr(driver, "_target_compile_entries", lambda *_args: [])
    monkeypatch.setattr(driver, "_validate_compile_definitions", lambda *_args: [])
    monkeypatch.setattr(driver, "collect_inert_witness", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        driver, "build_target",
        lambda *_args, **kwargs: {"arm": kwargs["arm"]},
    )
    monkeypatch.setattr(driver, "observe_isolation", lambda **_kwargs: _isolation("job_before"))
    monkeypatch.setattr(
        driver, "_run_blocks",
        lambda **kwargs: measurements.append(str(kwargs["experiment"])),
    )
    monkeypatch.setattr(driver, "validate_matrix", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(driver, "validate_preprocessing_receipts", lambda *_args: None)
    monkeypatch.setattr(driver, "validate_mode_document", lambda *_args: None)
    monkeypatch.setattr(
        driver, "_run_checked",
        lambda argv, **_kwargs: subprocess.CompletedProcess(argv, 0, stdout="", stderr=""),
    )

    rc, document = driver.run(args)

    assert rc == 0
    assert measurements == ["sweep"]
    assert document["status"] == "complete"
    assert document["inert_witness"]["collected"] is False
    assert document["inert_witness"]["failure"] == {
        "type": "ContractError", "message": "inert configure unavailable",
    }
    assert document["pbs_elapse"]["start"]["collected"] is False
    assert document["pbs_elapse"]["end"]["collected"] is False


def test_missing_required_command_stops_before_study_start(monkeypatch):
    monkeypatch.setattr(
        driver.shutil, "which",
        lambda command, path=None: None if command == "cmake" else f"/fixture/{command}",
    )
    with pytest.raises(driver.ContractError, match="before study start.*cmake"):
        driver.validate_required_commands()


def test_uptime_absence_is_recorded_without_losing_isolation_data(monkeypatch):
    monkeypatch.setattr(driver.shutil, "which", lambda _command, path=None: None)
    monkeypatch.setattr(driver, "_read_proc_ticks", lambda: {})
    observation = driver.observe_isolation(scope="job_before", sample_seconds=0)
    assert observation["uptime"] is None
    assert observation["uptime_collection"]["collected"] is False
    assert observation["proc_loadavg"]


def _persistent_cycle_snapshots() -> list[dict]:
    snapshot = {
        "nodes": [
            {
                "thread_id": 0, "attempt": 7, "wait_lock_id": "L1",
                "request_mode": "write", "commit_count": 10, "abort_count": 2,
            },
            {
                "thread_id": 1, "attempt": 9, "wait_lock_id": "L0",
                "request_mode": "write", "commit_count": 20, "abort_count": 3,
            },
        ],
        "edges": [
            {
                "waiter_thread_id": 0, "holder_thread_id": 1,
                "lock_id": "L1", "request_mode": "write", "holder_mode": "write",
                "holder_holds_lock": True, "compatible": False,
            },
            {
                "waiter_thread_id": 1, "holder_thread_id": 0,
                "lock_id": "L0", "request_mode": "write", "holder_mode": "write",
                "holder_holds_lock": True, "compatible": False,
            },
        ],
    }
    return [json.loads(json.dumps(snapshot)) for _ in range(3)]


def test_deadlock_evidence_accepts_three_stable_actual_holder_snapshots():
    evidence = driver.validate_deadlock_evidence(
        _persistent_cycle_snapshots(), timed_out=True,
    )
    assert evidence is not None
    assert evidence["snapshot_indexes"] == [0, 1, 2]


def test_deadlock_evidence_rejects_attempt_drift_and_nontimeout():
    snapshots = _persistent_cycle_snapshots()
    snapshots[1]["nodes"][0]["attempt"] += 1
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is None
    assert driver.validate_deadlock_evidence(_persistent_cycle_snapshots(), timed_out=False) is None


def test_deadlock_evidence_rejects_edge_topology_drift_with_stable_nodes():
    snapshots = _persistent_cycle_snapshots()
    extra_node = {
        "thread_id": 2, "attempt": 11, "wait_lock_id": "L2",
        "request_mode": "write", "commit_count": 30, "abort_count": 4,
    }
    for snapshot in snapshots:
        snapshot["nodes"].append(dict(extra_node))
        snapshot["edges"] = [
            {
                "waiter_thread_id": 0, "holder_thread_id": 1,
                "lock_id": "L1", "request_mode": "write", "holder_mode": "write",
                "holder_holds_lock": True, "compatible": False,
            },
            {
                "waiter_thread_id": 1, "holder_thread_id": 2,
                "lock_id": "L0", "request_mode": "write", "holder_mode": "write",
                "holder_holds_lock": True, "compatible": False,
            },
            {
                "waiter_thread_id": 2, "holder_thread_id": 0,
                "lock_id": "L2", "request_mode": "write", "holder_mode": "write",
                "holder_holds_lock": True, "compatible": False,
            },
        ]
    snapshots[1]["edges"] = [
        {**snapshots[1]["edges"][0], "holder_thread_id": 2},
        {**snapshots[1]["edges"][1], "holder_thread_id": 0},
        {**snapshots[1]["edges"][2], "holder_thread_id": 1},
    ]
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is None


def _wfg_stdout_fixture() -> str:
    """計算ノード 1 走 (request 0:2339.nqsv、bnode007、2026-09-17) の実 stdout を逐語で写した fixture。

    sha256 c98ea15b033a54c55dca34b77bd0d4a236f51609aac7dbf0ce4bd3c418784bf4。合成ではない。
    """
    return """#FLAGS_clocks_per_us:\t2100
#FLAGS_extime:\t\t10
#FLAGS_thread_num:\t48
#ShowOptParameters(): ADD_ANALYSIS 0: BACK_OFF 1: DLR0 : SS2PL_LOCK_IMPL 1: SS2PL_LOCK_KIND 0: SS2PL_DLR 0: SS2PL_WFG_DIAG 1: MASSTREE_USE 1: KEY_SIZE 8: KEY_SORT 0: VAL_SIZE 8
#FLAGS_ycsb_max_ope:\t10
#FLAGS_ycsb_rmw:\t0
#FLAGS_ycsb_rratio:\t50
#FLAGS_ycsb_tuple_num:\t100
#FLAGS_ycsb_zipf_skew:\t0
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":5,"cycle_found":true,"conflict_count":41,"no_wait_failure_count":0,"nodes":[{"thread_id":16,"attempt":1,"wait_lock_id":"0x14d33800a740","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d33800b1c0","mode":"write"}]},{"thread_id":21,"attempt":1,"wait_lock_id":"0x14d33800b1c0","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d338008280","mode":"write"},{"lock_id":"0x14d33800a740","mode":"write"},{"lock_id":"0x14d338007d40","mode":"write"},{"lock_id":"0x14d33800e480","mode":"write"},{"lock_id":"0x14d3380056c0","mode":"write"}]}],"edges":[{"waiter_thread_id":16,"holder_thread_id":21,"lock_id":"0x14d33800a740","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":21,"holder_thread_id":16,"lock_id":"0x14d33800b1c0","request_mode":"write","holder_mode":"write","compatible":false}]}
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":6,"cycle_found":true,"conflict_count":41,"no_wait_failure_count":0,"nodes":[{"thread_id":16,"attempt":1,"wait_lock_id":"0x14d33800a740","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d33800b1c0","mode":"write"}]},{"thread_id":21,"attempt":1,"wait_lock_id":"0x14d33800b1c0","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d338008280","mode":"write"},{"lock_id":"0x14d33800a740","mode":"write"},{"lock_id":"0x14d338007d40","mode":"write"},{"lock_id":"0x14d33800e480","mode":"write"},{"lock_id":"0x14d3380056c0","mode":"write"}]}],"edges":[{"waiter_thread_id":16,"holder_thread_id":21,"lock_id":"0x14d33800a740","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":21,"holder_thread_id":16,"lock_id":"0x14d33800b1c0","request_mode":"write","holder_mode":"write","compatible":false}]}
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":7,"cycle_found":true,"conflict_count":41,"no_wait_failure_count":0,"nodes":[{"thread_id":16,"attempt":1,"wait_lock_id":"0x14d33800a740","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d33800b1c0","mode":"write"}]},{"thread_id":21,"attempt":1,"wait_lock_id":"0x14d33800b1c0","request_mode":"write","commit_count":0,"abort_count":0,"held_locks":[{"lock_id":"0x14d338008280","mode":"write"},{"lock_id":"0x14d33800a740","mode":"write"},{"lock_id":"0x14d338007d40","mode":"write"},{"lock_id":"0x14d33800e480","mode":"write"},{"lock_id":"0x14d3380056c0","mode":"write"}]}],"edges":[{"waiter_thread_id":16,"holder_thread_id":21,"lock_id":"0x14d33800a740","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":21,"holder_thread_id":16,"lock_id":"0x14d33800b1c0","request_mode":"write","holder_mode":"write","compatible":false}]}
"""


def _wfg_fixture_snapshots() -> list[dict]:
    return driver._extract_snapshots(driver._json_events(_wfg_stdout_fixture()))


def _wfg_fixture_workload() -> dict:
    return {**driver.WORKLOAD_DEFAULT, "ycsb_tuple_num": 100, "ycsb_zipf_skew": 0}


def test_wfg_stdout_fixture_accepts_actual_holders():
    assert hashlib.sha256(_wfg_stdout_fixture().encode("utf-8")).hexdigest() == (
        "c98ea15b033a54c55dca34b77bd0d4a236f51609aac7dbf0ce4bd3c418784bf4"
    )
    events = driver._json_events(_wfg_stdout_fixture())
    snapshots = driver._extract_snapshots(events)
    assert len(events) == len(snapshots) == 3
    assert "holder_holds_lock" not in json.dumps(events)
    evidence = driver.validate_deadlock_evidence(snapshots, timed_out=True)
    assert evidence is not None
    assert evidence["snapshot_indexes"] == [0, 1, 2]
    assert driver.validate_deadlock_evidence(snapshots, timed_out=False) is None


@pytest.mark.parametrize("field", ["wait_lock_id", "waiter_thread_id", "holder_thread_id"])
def test_wfg_stdout_legacy_fields_are_rejected(field):
    snapshots = _wfg_fixture_snapshots()
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is not None
    legacy = {
        "wait_lock_id": "waiting_lock_id",
        "waiter_thread_id": "waiter", "holder_thread_id": "holder",
    }
    for snapshot in snapshots:
        for item in snapshot["nodes" if field == "wait_lock_id" else "edges"]:
            item[legacy[field]] = item.pop(field)
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is None


@pytest.mark.parametrize("mutation", ["missing", "lock_id", "mode"])
def test_wfg_stdout_missing_held_locks_is_rejected(mutation):
    snapshots = _wfg_fixture_snapshots()
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is not None
    for snapshot in snapshots:
        for node in snapshot["nodes"]:
            if mutation == "missing":
                del node["held_locks"]
            else:
                edge = next(
                    edge for edge in snapshot["edges"]
                    if edge["holder_thread_id"] == node["thread_id"]
                )
                held = next(
                    held for held in node["held_locks"]
                    if held["lock_id"] == edge["lock_id"]
                )
                held[mutation] = "0xdead" if mutation == "lock_id" else "read"
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is None


def test_wfg_startup_axes_without_terminal_output(tmp_path):
    binary, build, _ = _admission_fixture(tmp_path, arm="phase1")
    build["binary"] = str(binary)
    stdout = "\n".join(
        line for line in _wfg_stdout_fixture().splitlines() if not line.startswith("{")
    ) + "\n"
    axes, _ = driver.parse_runtime_axes(stdout)
    assert axes == driver.ARM_CONFIG["phase1"]
    admitted = driver._admit_output(
        stdout, arm="phase1", workload=_wfg_fixture_workload(), build=build,
        binary=binary, thread_num=48, require_metrics=False, require_thread_commits=False,
    )
    assert admitted["runtime_axes"] == axes
    assert admitted["json_events"] == []


def test_phase_trial_passes_unique_wfg_output_and_collects_file(tmp_path, monkeypatch):
    """Exercise argv/receipt wiring; subprocess timeout and flush are not simulated."""
    binary, build, _ = _admission_fixture(tmp_path.resolve(), arm="phase1")
    build["binary"] = str(binary)
    stdout = _wfg_stdout_fixture()
    final_bytes = (stdout.splitlines()[-1] + "\n").encode("utf-8")
    final_json = json.loads(final_bytes)
    paths = []
    output_kind = "present"

    def fake(argv, *, timeout_s, expected_timeout):
        flags = [arg for arg in argv if arg.startswith("-ss2pl_wfg_output=")]
        assert len(flags) == 1, "required unique -ss2pl_wfg_output flag missing"
        path = Path(flags[0].split("=", 1)[1])
        assert path.is_absolute()
        assert path.name == "final.json"
        assert path.parent.parent == binary.parent
        assert path.parent.name.startswith("ss2pl-wfg-phase1-high-contention-t0-")
        assert path not in paths
        paths.append(path)
        assert timeout_s == 60 and expected_timeout is None
        if output_kind == "present":
            path.write_bytes(final_bytes)
        elif output_kind == "invalid_json":
            path.write_bytes(b"{")
        elif output_kind == "invalid_utf8":
            path.write_bytes(b"\xff")
        elif output_kind == "read_error":
            path.mkdir()
        return (0, stdout, "", True, "term")

    monkeypatch.setattr(driver, "_run_process", fake)
    for output_kind in ("present", "present", "missing", "invalid_json", "invalid_utf8", "read_error"):
        result = driver._run_phase_trial(
            phase="phase1", build=build, workload=_wfg_fixture_workload(),
            trial=0, point="high-contention", clocks_per_us=2100, occasion={},
        )
        receipt = result["wfg_output"]
        assert set(receipt) == {"path", "status", "sha256", "json", "error"}
        assert receipt["path"] == str(paths[-1])
        assert receipt["status"] == ("invalid_json" if output_kind == "invalid_utf8" else output_kind)
        assert Path(result["stdout_path"]).read_text(encoding="utf-8") == stdout
        assert Path(result["stderr_path"]).read_text(encoding="utf-8") == ""
        assert driver.sha256_file(Path(result["stdout_path"])) == result["stdout_sha256"]
        assert driver.sha256_file(Path(result["stderr_path"])) == result["stderr_sha256"]
        assert Path(result["stdout_path"]).parent == paths[-1].parent
        assert Path(result["stderr_path"]).parent == paths[-1].parent
        assert result["timed_out"] is True and result["termination"] == "term"
        assert result["accepted_cycle"]["snapshot_indexes"] == [0, 1, 2]
        assert len(result["wfg_snapshots"]) == 3
        assert sum(arg.startswith("-ss2pl_wfg_output=") for arg in result["argv"]) == 1
        if output_kind == "present":
            assert receipt["json"] == final_json
            assert receipt["sha256"] == driver._sha256_bytes(final_bytes)
            assert receipt["error"] is None
        else:
            assert receipt["json"] is None
            if output_kind in ("invalid_json", "invalid_utf8"):
                assert receipt["sha256"] == driver.sha256_file(paths[-1])
            else:
                assert receipt["sha256"] is None
            if output_kind == "missing":
                assert receipt["error"] is None
            else:
                assert isinstance(receipt["error"], str) and receipt["error"]
        json.dumps(result)
    assert len(set(paths)) == 6

    perf_binary, perf_build, perf_stdout = _admission_fixture(tmp_path.resolve(), arm="D")
    perf_build["binary"] = str(perf_binary)
    perf_stdout += "\n#ss2pl_thread_commit_counts: 90\n"
    perf_argv = []

    def fake_performance(argv, *, timeout_s, expected_timeout):
        assert not any(arg.startswith("-ss2pl_wfg_output=") for arg in argv)
        assert timeout_s == 120 and expected_timeout is False
        perf_argv.extend(argv)
        return (0, perf_stdout, "", False, "natural")

    monkeypatch.setattr(driver, "_run_process", fake_performance)
    performance = driver._run_performance_once(
        build=perf_build, arm="D", workload=driver.WORKLOAD_DEFAULT,
        thread_num=1, clocks_per_us=2100, block_id=0, block_attempt=0,
        order_index=0, experiment="fixture", occasion={},
    )
    assert perf_argv
    assert performance["argv"] == perf_argv[1:]


def test_wfg_exclusive_mode_write_is_accepted_and_read_read_is_rejected():
    snapshots = _wfg_fixture_snapshots()
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is not None
    for snapshot in snapshots:
        for node in snapshot["nodes"]:
            node["request_mode"] = "read"
            for held in node["held_locks"]:
                held["mode"] = "read"
        for edge in snapshot["edges"]:
            edge["request_mode"] = edge["holder_mode"] = "read"
    assert driver.validate_deadlock_evidence(snapshots, timed_out=True) is None



if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
