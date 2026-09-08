# -*- coding: utf-8 -*-
"""s8b_floor_stats (formula v2) の mutation-killing golden テスト。

**独立 oracle 契約 (β-12/δ-16):** 式の golden は production を import しない stdlib-only の
reference calculator と手導出 literal で固定する (`_ref_*`)。production を走らせて出力を貼る
堕落を避ける。各テストがどの mutant を殺すかはコメントに明記する:
  median↔mean / stdev(n-1)↔pstdev(n) / CV 判定 >↔>= / 異常ゲート除去 / null skip /
  stock anomaly 全 pair 伝播 / pairs キー (configuration_id↔cell_id) 混同。

**閾値の厳密算術 (α-9):** [90,90,100,110,110] は CV ちょうど 10% で異常でない (厳密超過)、
[89,89,100,111,111] は超過。尺度同値 [0.9,0.9,1.0,1.1,1.1] は IEEE-754 の 2 進表現が
名目 10% を僅かに超えるため Fraction 意味論で決定的に異常となる (float 直接比較の非決定ではなく
再現可能な確定値である点を固定する)。

**テストデータは synthetic 軸のみ (δ-15):** holdout 実軸 literal を新規に書かない。
"""
from __future__ import annotations

import inspect
import ast
import copy
import hashlib
import itertools
import json
import math
import os
import sys
import tempfile
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign.s8b_floor_stats import (  # noqa: E402
    ALLOWED_EXCLUDED_REASONS,
    FORMULA_ID,
    CellStats,
    FloorStatsError,
    SessionRecord,
    assess_session,
    cell_cv_exceeds,
    cell_stats,
    holdout_floors,
    session_median,
    verify_floor_artifact as _verify_floor_artifact,
    verify_floor_artifact_with_live_admission,
)
from orchestrator.calibrator import perf_preflight  # noqa: E402
from orchestrator.campaign import attempt_registry_core  # noqa: E402
from orchestrator.campaign import s8b_attempt_profile  # noqa: E402
from orchestrator.campaign import s8b_attempt_registry  # noqa: E402
from orchestrator.campaign import s8b_binary_admission  # noqa: E402
from orchestrator.campaign import s8b_floor_contract  # noqa: E402
from orchestrator.campaign import s8b_floor_stats  # noqa: E402
from orchestrator.campaign import s8b_holdout_admission  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId, ReviewId, build_run_context, derive_build_admission,
)
from orchestrator.campaign.s8b_materialization import reviewed_source_capability  # noqa: E402
from orchestrator.campaign.source_digest import SOURCE_EVIDENCE_SCHEMA, SourceEvidence  # noqa: E402
from orchestrator.tests import test_s8b_attempt_registry as registry_cases  # noqa: E402
from orchestrator.tests import test_s8b_holdout_admission as admission_cases  # noqa: E402
from orchestrator.tests.s8b_floor_evidence_fixture import (  # noqa: E402
    expected_portable_sort_swo_pass_receipt,
)


def verify_floor_artifact(artifact, expected, expected_binaries=None):
    admission = artifact.get("holdout_admission")
    if admission is None:
        expected_cells = [
            f"{holdout}::{configuration}"
            for holdout, configurations in expected["expected_cells"].items()
            for configuration in configurations
        ]
        admission = _admission_receipt(expected_cells)
    return _verify_floor_artifact(
        artifact, expected, expected_binaries=expected_binaries,
        expected_holdout_admission=admission,
        expected_use_perf=True,
    )


# ---------------------------------------------------------------------------
# stdlib-only 独立 reference calculator (production を import しない, β-12)
# ---------------------------------------------------------------------------
def _ref_mean(xs):
    return sum(xs) / len(xs)


def _ref_median(xs):
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _ref_var_n1(xs):
    m = _ref_mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def _ref_stdev_n1(xs):
    return math.sqrt(_ref_var_n1(xs))


def _ref_cv_exceeds(xs, tstr):
    """CV > T を Fraction 厳密で独立判定 (production の _cv_exceeds とは別実装)。"""
    fr = [Fraction(v) for v in xs]
    n = len(fr)
    mean = sum(fr, Fraction(0)) / n
    var = sum((x - mean) ** 2 for x in fr) / (n - 1)
    T = Fraction(tstr)
    return var > T * T * mean * mean


def _ref_u_noise(s_c, s_stock):
    return math.sqrt(s_c ** 2 + s_stock ** 2)


# ---------------------------------------------------------------------------
# テストヘルパ
# ---------------------------------------------------------------------------
_CCBENCH_PIN = "1" * 40
_ENTRY_SHA = hashlib.sha256(b"floor-stats-entry").hexdigest()
_CONTRACT_SHA = hashlib.sha256(b"floor-stats-contract").hexdigest()


def _canonical_bytes(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _perf_receipt(*, available: bool) -> dict:
    events = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]
    return {
        "schema": "izanagi-perf-preflight/v1",
        "status": "available" if available else "unavailable",
        "available": available,
        "probe_argv": [
            "perf", "stat", "-x,", "-o", "<tmp>/perf.csv", "-e",
            ",".join(events), "--", "/bin/true",
        ],
        "rc": 0 if available else None,
        "parsed_events": events if available else [],
        "reason": "available" if available else "perf-not-found",
        "stderr_sha256": hashlib.sha256(b"floor-stats-perf").hexdigest(),
        "candidates": [],
    }


def _portable_binary(temp_root: Path, *, cell_id: str, holdout_id: str,
                     configuration_id: str) -> dict:
    genome = json.dumps(
        {"configuration_id": configuration_id}, sort_keys=True,
        separators=(",", ":"),
    )
    src_token = hashlib.sha256(f"source:{configuration_id}".encode()).hexdigest()
    binding = {
        "genome_canonical": genome,
        "src_token": src_token,
        "variant_id": hashlib.sha256(
            f"{genome}|src={src_token}".encode()
        ).hexdigest()[:12],
        "entry_sha256": _ENTRY_SHA,
    }
    binding["binding_sha256"] = hashlib.sha256(_canonical_bytes(binding)).hexdigest()
    source_root = temp_root / cell_id.replace("::", "-")
    source_root.mkdir()
    compiler_input = source_root / "include" / "fixture.hh"
    compiler_input.parent.mkdir()
    compiler_input.write_bytes(f"compiler-input:{cell_id}\n".encode())
    compiler_input_manifest = {
        "schema_version": "s8b-compiler-input/v1",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_fixture.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
        }],
    }
    compiler_input_manifest_sha256 = hashlib.sha256(
        json.dumps(
            compiler_input_manifest, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    source = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=str(source_root.resolve()), ccbench_commit=_CCBENCH_PIN,
        genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=hashlib.sha256(b"source-bytes").hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(b"tracked-diff").hexdigest(),
        tracked_paths=("include/fixture.hh",),
    )
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    review = reviewed_source_capability(
        review_id=ReviewId.S8B_FLOOR, source=source, input_sha256=_ENTRY_SHA,
    )
    admission = derive_build_admission(context, source, review_receipt=review)
    binary = source_root / "binary"
    binary.write_bytes(f"binary:{cell_id}".encode())
    binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipt = s8b_binary_admission.issue_binary_admission_receipt(
        admission=admission, expected_policy=context.policy, source=source,
        cell_id=cell_id, holdout_id=holdout_id,
        configuration_id=configuration_id, binding=binding, binary=binary,
        binary_sha256=binary_sha, contract_sha256=_CONTRACT_SHA, trace=False,
        source_snapshot_sha256=hashlib.sha256(
            f"expected-materialization:{cell_id}".encode()
        ).hexdigest(),
        expected_materialization_sha256=hashlib.sha256(
            f"expected-materialization:{cell_id}".encode()
        ).hexdigest(),
        compiler_input_manifest=compiler_input_manifest,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
    )
    record = {
        "cell_id": cell_id, "holdout_id": holdout_id,
        "configuration_id": configuration_id, "binary": "build/fixture",
        "binary_sha256": binary_sha, "bin_hash_short": binary_sha[:16],
        "binding": binding, "configure_argv": ["cmake", "fixture"],
        "build_argv": ["cmake", "--build", "fixture"], "cached": False,
        "store_path": f"store/{binary_sha}", "admission_receipt": receipt,
    }
    if configuration_id == "sort_best":
        record["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
            cell_id=cell_id, holdout_id=holdout_id,
            configuration_id=configuration_id, entry_sha256=_ENTRY_SHA,
            binary_sha256=binary_sha,
        )
    return record


def _admission_receipt(cell_ids):
    return {
        "schema": "s8b-floor-holdout-admission-receipt/v1",
        "campaign_run_id": "20260816T000000Z-deadbeef",
        "run_relpath": (
            "env/test/calibration/s8b-floor-official/"
            "20260816T000000Z-deadbeef"
        ),
        "mode": "official", "protocol_sha256": "2" * 64,
        "freeze_sha256": "3" * 64, "manifest_sha256": "4" * 64,
        "claim_identities": {
            cell_id: hashlib.sha256(cell_id.encode()).hexdigest()
            for cell_id in sorted(cell_ids)
        },
        "admission_row_count": len(cell_ids), "attempt_row_count": len(cell_ids),
        "ledger_projection_sha256": "5" * 64,
    }


def _sess(cell_id, seq, throughputs, *, reps_expected=5, holdout_id="H",
          configuration_id="cfg", exec_failures=0, excluded_reason=None, retry=False):
    raw_values = list(throughputs) + [None] * max(0, reps_expected - len(throughputs))
    perf_raw = {
        "LLC-load-misses": 1, "LLC-loads": 2, "instructions": 3, "cycles": 4,
    }
    observations = tuple(
        {
            "rep_index": index, "returncode": 0, "counter_status": "complete",
            "execution_failure": False,
            "missing_perf_events": [], "perf_raw": dict(perf_raw),
            "throughput": raw_values[index],
        }
        for index in range(reps_expected)
    )
    return SessionRecord(
        cell_id=cell_id, holdout_id=holdout_id, configuration_id=configuration_id,
        seq=seq, throughputs=tuple(throughputs), reps_expected=reps_expected,
        exec_failures=exec_failures, excluded_reason=excluded_reason, retry=retry,
        rep_observations=observations, rep_integrity_failures=0)


def _flat(cell_id, seq, median_value, **kw):
    """median==median_value・CV=0 の完全 5-rep session (定数列)。"""
    return _sess(cell_id, seq, [median_value] * 5, **kw)


def _cell(cell_id, *, medians, valid=True, holdout_id="H", configuration_id="cfg"):
    """指定 medians から CellStats を組む (m/s/cv は reference calculator で導出)。"""
    medians = tuple(medians)
    n = len(medians)
    m = _ref_median(medians) if n >= 1 else None
    s = _ref_stdev_n1(medians) if n >= 2 else None
    cv = (s / _ref_mean(medians)) if (s is not None and _ref_mean(medians) > 0) else None
    return CellStats(cell_id=cell_id, holdout_id=holdout_id,
                     configuration_id=configuration_id, n_valid=n, medians=medians,
                     m=m, s=s, valid=valid, cv=cv, notes=())


# ---------------------------------------------------------------------------
# FORMULA_ID / 閉表
# ---------------------------------------------------------------------------
def test_formula_id_is_v2():
    # 式の版は v2 (block/delta_c 廃止, F1 裁定)。
    assert FORMULA_ID == "s8b-floor-stats/v2"


def test_formula_v2_preserves_session_outputs_but_counts_post_spawn_integrity_failures():
    """B6: 全 outcome 直積で不変量と post-spawn integrity 増分を固定する。"""

    def observation(index, outcome, *, use_perf):
        perf_raw = {
            event: index + 1 for event in s8b_floor_stats.PERF_EVENTS
        } if use_perf else {
            event: None for event in s8b_floor_stats.PERF_EVENTS
        }
        missing = []
        status = "complete" if use_perf else "not_required"
        returncode = 0
        execution_failure = False
        throughput = float(100 + index)
        if outcome == "nonzero_rc":
            returncode = 7
        elif outcome == "pre_spawn_execution_exception":
            returncode = None
            execution_failure = True
            throughput = None
            if use_perf:
                perf_raw = {event: None for event in s8b_floor_stats.PERF_EVENTS}
                missing = list(s8b_floor_stats.PERF_EVENTS)
                status = "incomplete"
        elif outcome == "post_spawn_execution_exception":
            # run_once() records the completed subprocess rc before parsing its
            # output.  A parse/open failure can therefore be emitted with rc=0
            # and otherwise complete counter evidence, but without throughput.
            execution_failure = True
            throughput = None
        elif outcome == "counter_missing":
            perf_raw["cycles"] = None
            missing = ["cycles"]
            status = "incomplete"
        elif outcome == "nonfinite":
            throughput = float("inf")
        return {
            "rep_index": index,
            "returncode": returncode,
            "execution_failure": execution_failure,
            "counter_status": status,
            "missing_perf_events": missing,
            "perf_raw": perf_raw,
            "throughput": throughput,
        }

    def legacy_projection(observations, *, use_perf, notes):
        qualified = []
        failures = 0
        legacy_keys = s8b_floor_stats._REP_OBSERVATION_KEYS - {"execution_failure"}
        for row in observations:
            old = {key: value for key, value in row.items() if key != "execution_failure"}
            raw_missing = [
                event for event in s8b_floor_stats.PERF_EVENTS
                if type(old["perf_raw"][event]) is not int
                or old["perf_raw"][event] < 0
            ]
            derived_missing = raw_missing if use_perf else []
            derived_status = (
                "not_required" if not use_perf
                else "complete" if not derived_missing else "incomplete"
            )
            complete = (
                set(old) == legacy_keys
                and type(old["returncode"]) is int
                and old["returncode"] == 0
                and old["missing_perf_events"] == derived_missing
                and old["counter_status"] == derived_status
                and derived_status in {"complete", "not_required"}
            )
            if complete:
                if old["throughput"] is not None:
                    qualified.append(old["throughput"])
            else:
                failures += 1
        exec_failures = int(notes[0].split("/", 1)[0]) if notes else 0
        return exec_failures, failures, tuple(qualified)

    def session_result(exec_failures, qualified):
        record = SessionRecord(
            cell_id="H::cfg", holdout_id="H", configuration_id="cfg", seq=0,
            throughputs=qualified, reps_expected=3, exec_failures=exec_failures,
            excluded_reason=None, retry=False,
        )
        median = session_median(record, reps=3, session_cv_max="0.5")
        return median is not None, median

    for use_perf in (False, True):
        outcomes = [
            "success", "nonzero_rc", "pre_spawn_execution_exception",
            "post_spawn_execution_exception", "nonfinite",
        ]
        if use_perf:
            outcomes.append("counter_missing")
        for combination in itertools.product(outcomes, repeat=3):
            observations = [
                observation(index, outcome, use_perf=use_perf)
                for index, outcome in enumerate(combination)
            ]
            exec_count = sum(
                outcome in {
                    "pre_spawn_execution_exception",
                    "post_spawn_execution_exception",
                }
                for outcome in combination
            )
            notes = [f"{exec_count}/3 reps failed to execute"] if exec_count else []
            old_exec, old_integrity, old_qualified = legacy_projection(
                observations, use_perf=use_perf, notes=notes,
            )
            errors, new_integrity, new_exec, new_qualified = \
                s8b_floor_stats._derive_rep_integrity(
                    observations, reps=3, expected_use_perf=use_perf,
                )
            assert errors == []
            assert new_exec == old_exec
            assert new_qualified == old_qualified

            post_spawn_execution_failures = combination.count(
                "post_spawn_execution_exception"
            )
            assert new_integrity == old_integrity + post_spawn_execution_failures

            old_valid, old_median = session_result(old_exec, old_qualified)
            new_valid, new_median = session_result(new_exec, new_qualified)
            assert new_valid == old_valid
            assert new_median == old_median


def test_allowed_reasons_closed_table_order():
    # 閉じた 4 理由 + 固定順 (performance_anomaly は 4 行目)。
    assert ALLOWED_EXCLUDED_REASONS == (
        "competing_process", "launch_failure",
        "nonfinite_or_partial_output", "performance_anomaly")


# ---------------------------------------------------------------------------
# assess_session — Fraction 厳密境界・完全性・構造化エラー
# ---------------------------------------------------------------------------
def test_assess_cv_boundary_exactly_ten_percent_not_anomaly():
    # [90,90,100,110,110]: mean=100, var(n-1)=100, T^2*mean^2=0.01*10000=100。
    # 100 > 100 は偽 → 異常でない。>= mutant はここで赤 (>↔>= を殺す)。
    a = assess_session([90, 90, 100, 110, 110], reps=5, session_cv_max="0.10")
    assert a.required_reason is None
    assert a.median == 100
    assert _ref_cv_exceeds([90, 90, 100, 110, 110], "0.10") is False


def test_assess_cv_just_over_ten_percent_is_anomaly():
    # [89,89,100,111,111]: var(n-1)=121 > 100 → performance_anomaly。ゲート除去 mutant を殺す。
    a = assess_session([89, 89, 100, 111, 111], reps=5, session_cv_max="0.10")
    assert a.required_reason == "performance_anomaly"
    assert a.median is None                      # 異常 session は median を作らない
    assert _ref_cv_exceeds([89, 89, 100, 111, 111], "0.10") is True


def test_assess_scale_equivalent_vector_is_deterministic():
    # 尺度同値 [0.9,0.9,1.0,1.1,1.1] は IEEE-754 表現が名目 10% を僅かに超えるため
    # Fraction 意味論で確定的に異常。float 直接比較の非決定ではなく再現可能な確定値。
    v = [0.9, 0.9, 1.0, 1.1, 1.1]
    a1 = assess_session(v, reps=5, session_cv_max="0.10")
    a2 = assess_session(list(v), reps=5, session_cv_max="0.10")
    assert a1.required_reason == "performance_anomaly"   # 決定的
    assert a2.required_reason == a1.required_reason       # 再現的
    assert _ref_cv_exceeds(v, "0.10") is True


def test_assess_valid_returns_median_and_cv():
    # 完全・低 CV だが右に歪んだ列 [100,100,100,100,105]: median=100, mean=101 (cv≈0.022<10%)。
    a = assess_session([100, 100, 100, 100, 105], reps=5, session_cv_max="0.10")
    assert a.median == 100                         # median (mean=101) — median↔mean を殺す
    assert a.required_reason is None
    assert a.cv is not None and a.cv < 0.10


def test_assess_partial_reps_is_nonfinite_or_partial():
    # 4/5 rep → 完全性欠如 → nonfinite_or_partial_output (CV より優先)。
    a = assess_session([1, 2, 3, 4], reps=5, session_cv_max="0.10")
    assert a.required_reason == "nonfinite_or_partial_output"
    assert a.median is None and a.cv is None


def test_assess_nonfinite_and_nonpositive_are_partial():
    for bad in ([1, 2, 3, 4, math.inf], [1, 2, 3, 4, math.nan],
                [1, 2, 3, 4, 0.0], [1, 2, 3, 4, -5.0]):
        a = assess_session(bad, reps=5, session_cv_max="0.10")
        assert a.required_reason == "nonfinite_or_partial_output"


def test_assess_rejects_bool_and_nonnumeric_as_structured_error():
    # bool は int サブクラスだが型違反 = 構造化エラー (α-7)。
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, True], reps=5, session_cv_max="0.10")
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, "5"], reps=5, session_cv_max="0.10")


def test_assess_rejects_bad_reps_and_threshold():
    with pytest.raises(FloorStatsError):
        assess_session([1, 2], reps=1, session_cv_max="0.10")      # reps<2
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=True, session_cv_max="0.10")  # bool reps
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max=0.10)  # 非文字列閾値
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max="0")   # (0,1] 外
    with pytest.raises(FloorStatsError):
        assess_session([1, 2, 3, 4, 5], reps=5, session_cv_max="1.5")  # >1


# ---------------------------------------------------------------------------
# session_median — assess_session への一元化 (α-8)
# ---------------------------------------------------------------------------
def test_session_median_valid_and_invalidations():
    good = _flat("c", 0, 100)
    assert session_median(good, reps=5, session_cv_max="0.10") == 100
    # excluded_reason / exec_failures / CV 異常はいずれも None。
    assert session_median(_flat("c", 0, 100, excluded_reason="competing_process"),
                          reps=5, session_cv_max="0.10") is None
    assert session_median(_flat("c", 0, 100, exec_failures=1),
                          reps=5, session_cv_max="0.10") is None
    anomaly = _sess("c", 0, [89, 89, 100, 111, 111])  # CV>10%
    assert session_median(anomaly, reps=5, session_cv_max="0.10") is None


# ---------------------------------------------------------------------------
# cell_stats — median/stdev golden・有効性・座標一貫性
# ---------------------------------------------------------------------------
def test_cell_stats_golden_median_and_stdev():
    # 4 session medians = [100,100,100,200] (定数列で CV=0)。
    #   m = median = 100  (mean=125; median↔mean を殺す)
    #   s = stdev(n-1): mean=125, dev=[-25,-25,-25,75], Σsq=7500, /3=2500, sqrt=50
    #       (pstdev(n) なら sqrt(7500/4)=43.30…; stdev(n-1)↔pstdev(n) を殺す)
    #   cv = 50/125 = 0.4
    recs = [_flat("c", 0, 100), _flat("c", 1, 100),
            _flat("c", 2, 100), _flat("c", 3, 200)]
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is True and cs.n_valid == 4
    assert cs.m == _ref_median([100, 100, 100, 200]) == 100
    assert math.isclose(cs.s, _ref_stdev_n1([100, 100, 100, 200])) and math.isclose(cs.s, 50.0)
    assert math.isclose(cs.cv, 0.4)
    assert cs.medians == (100, 100, 100, 200)
    assert cs.holdout_id == "H" and cs.configuration_id == "cfg"


def test_cell_stats_invalid_when_valid_count_short():
    # anomaly session を 1 本混ぜ有効数を減らす → n_valid(3) != n_sessions(4) → 無効。
    recs = [_flat("c", 0, 100), _flat("c", 1, 100), _flat("c", 2, 100),
            _sess("c", 3, [89, 89, 100, 111, 111])]  # CV 異常 → 除外
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is False
    assert cs.n_valid == 3
    # 異常 session の median 101 は母集団に入らない (fail-closed)。
    assert 101 not in cs.medians


def test_cell_stats_invalid_when_configuration_mixed():
    # 同一 cell_id に別 configuration_id が混入 → 座標不一致 → 無効 (混入検知)。
    recs = [_flat("c", 0, 100, configuration_id="cfgA"),
            _flat("c", 1, 100, configuration_id="cfgB"),
            _flat("c", 2, 100, configuration_id="cfgA"),
            _flat("c", 3, 100, configuration_id="cfgA")]
    cs = cell_stats(recs, n_sessions=4, reps=5, session_cv_max="0.10")
    assert cs.valid is False


# ---------------------------------------------------------------------------
# cell_cv_exceeds — machine_anomaly 判定の Fraction 厳密境界
# ---------------------------------------------------------------------------
def test_cell_cv_boundary_exactly_fifteen_percent_not_anomaly():
    # [85,100,115]: var(n-1)=225, T^2*mean^2=0.0225*10000=225 → 225>225 偽 → 非異常。
    assert cell_cv_exceeds([85, 100, 115], "0.15") is False
    assert _ref_cv_exceeds([85, 100, 115], "0.15") is False


def test_cell_cv_just_over_fifteen_percent_is_anomaly():
    # [84,100,116]: var(n-1)=256 > 225 → 異常。
    assert cell_cv_exceeds([84, 100, 116], "0.15") is True
    assert _ref_cv_exceeds([84, 100, 116], "0.15") is True


# ---------------------------------------------------------------------------
# holdout_floors — formula v2 支配関係・fail-closed・machine_anomaly
# ---------------------------------------------------------------------------
def test_floor_u_noise_dominates():
    # stock medians [97,100,103] → s=3, m=100 (cv=0.03<15%)。
    # c medians [96,100,104] → s=4 (cv=0.04)。u_noise=sqrt(16+9)=5, rel=0.01*100=1 → floor=5。
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], _ref_u_noise(4.0, 3.0)) and math.isclose(
        hf.pairs["variant_A"], 5.0)
    # pairs のキーは configuration_id であって cell_id ではない (key 混同 mutant を殺す)。
    assert "variant_A" in hf.pairs and "c" not in hf.pairs
    assert math.isclose(hf.scalar_alt, 5.0)
    assert hf.scale_ref == 100


def test_floor_wired_min_dominates():
    # u_noise 小・rel 大: stock/c medians [99,100,101] → s=1。u_noise=sqrt(2)=1.414。
    # wired=0.05, m_stock=100 → rel=5 → floor=max(1.414,5)=5。
    stock = _cell("stock", medians=[99, 100, 101], configuration_id="stock_common")
    c = _cell("c", medians=[99, 100, 101], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.05, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], 5.0)


def test_floor_stock_invalid_nulls_whole_holdout():
    stock = _cell("stock", medians=[97, 100, 103], valid=False,
                  configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.scalar_alt is None and hf.scale_ref is None


def test_floor_cell_invalid_nulls_only_its_pair():
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c1 = _cell("c1", medians=[96, 100, 104], configuration_id="variant_A")   # floor 5
    c2 = _cell("c2", medians=[96, 100, 104], valid=False, configuration_id="variant_B")
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], 5.0)
    assert hf.pairs["variant_B"] is None
    # scalar_alt は c2 の null で veto (null skip mutant を殺す)。
    assert hf.scalar_alt is None
    assert hf.scale_ref == 100


def test_floor_scalar_alt_is_max_when_all_valid():
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    c1 = _cell("c1", medians=[92, 100, 108], configuration_id="variant_A")  # s=8 u_noise=sqrt(64+9)
    c2 = _cell("c2", medians=[96, 100, 104], configuration_id="variant_B")  # s=4 u_noise=5
    hf = holdout_floors({"stock": stock, "c1": c1, "c2": c2}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert math.isclose(hf.pairs["variant_A"], _ref_u_noise(8.0, 3.0))
    assert math.isclose(hf.pairs["variant_B"], 5.0)
    assert math.isclose(hf.scalar_alt, _ref_u_noise(8.0, 3.0))   # max


def test_floor_machine_anomaly_nulls_nonstock_pair():
    # c のセル間 CV>15% → 当該 pair null + diagnostics.machine_anomaly_cells に載る。
    stock = _cell("stock", medians=[97, 100, 103], configuration_id="stock_common")
    anom = _cell("c", medians=[70, 100, 130], configuration_id="variant_A")  # cv=0.3
    hf = holdout_floors({"stock": stock, "c": anom}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.diagnostics["machine_anomaly_cells"] == ["c"]
    assert hf.diagnostics["cells"]["c"]["machine_anomaly"] is True


def test_floor_stock_machine_anomaly_nulls_whole_holdout():
    # stock のセル間 CV>15% → 全 pair / scalar_alt / scale_ref すべて null (α-11, stock 伝播)。
    stock = _cell("stock", medians=[70, 100, 130], configuration_id="stock_common")
    c = _cell("c", medians=[96, 100, 104], configuration_id="variant_A")
    hf = holdout_floors({"stock": stock, "c": c}, stock_id="stock",
                        wired_min_rel_floor=0.01, cell_cv_max="0.15")
    assert hf.pairs["variant_A"] is None
    assert hf.scalar_alt is None
    assert hf.scale_ref is None                        # scale_ref も消える (異常 stock 値を消費させない)
    assert "stock" in hf.diagnostics["machine_anomaly_cells"]


# ---------------------------------------------------------------------------
# verify_floor_artifact — 内部整合再計算 + expected_protocol 照合 + 改竄検出
# ---------------------------------------------------------------------------
def _honest_artifact():
    """honest な生成器を模した整合 artifact と対応する expected_protocol を組む (synthetic 軸)。"""
    holdout = "H1"
    stock_cfg = "stock_common"
    va, vb = "sort_best", "variant_B"
    stock_cell = f"{holdout}::{stock_cfg}"
    va_cell = f"{holdout}::{va}"
    vb_cell = f"{holdout}::{vb}"
    n_sessions, reps = 4, 5

    def mk(cell, cfg, seq, median):
        return _sess(cell, seq, [median] * reps, holdout_id=holdout,
                     configuration_id=cfg, reps_expected=reps)

    records = []
    for seq, mval in enumerate([98, 100, 100, 102]):        # stock medians, s>0, cv 低
        records.append(mk(stock_cell, stock_cfg, seq, mval))
    for seq, mval in enumerate([148, 150, 150, 152]):        # variant_A
        records.append(mk(va_cell, va, seq, mval))
    for seq, mval in enumerate([118, 120, 120, 122]):        # variant_B
        records.append(mk(vb_cell, vb, seq, mval))

    by_cell = {}
    for r in records:
        by_cell.setdefault(r.cell_id, []).append(r)
    cells = {cid: asdict(cell_stats(recs, n_sessions=n_sessions, reps=reps,
                                    session_cv_max="0.10"))
             for cid, recs in by_cell.items()}

    cell_objs = {cid: cell_stats(recs, n_sessions=n_sessions, reps=reps,
                                 session_cv_max="0.10")
                 for cid, recs in by_cell.items()}
    hf = holdout_floors(cell_objs, stock_id=stock_cell, wired_min_rel_floor=0.01,
                        cell_cv_max="0.15")
    floors = {holdout: asdict(hf)}

    config = {"formula": FORMULA_ID, "n_sessions": n_sessions, "reps": reps,
              "stock_configuration": stock_cfg, "wired_min_rel_floor": 0.01,
              "session_cv_max": "0.10", "cell_cv_max": "0.15"}
    sessions = [asdict(r) for r in records]
    for row in sessions:
        row["rep_observations"] = [dict(item) for item in row["rep_observations"]]
        row["exclusion_class"] = None
    with tempfile.TemporaryDirectory() as temp_dir:
        binaries = {
            cell_id: _portable_binary(
                Path(temp_dir), cell_id=cell_id, holdout_id=holdout,
                configuration_id=configuration_id,
            )
            for cell_id, configuration_id in (
                (stock_cell, stock_cfg), (va_cell, va), (vb_cell, vb)
            )
        }
    artifact = {
        "schema": "s8b-floor-result/v4", "formula": FORMULA_ID,
        "mode": "official", "eligible_for_refreeze": True,
        "env_tag": "test", "ccbench_pin": _CCBENCH_PIN,
        "protocol_sha256": "2" * 64, "freeze_sha256": "3" * 64,
        "manifest_sha256": "4" * 64,
        "stock_configuration": stock_cfg, "wired_min_rel_floor": 0.01,
        "reps": reps, "n_sessions": n_sessions,
        "scale_adequacy_rel_tolerance": "0.10",
        "holdouts": [holdout], "configurations": [stock_cfg, va, vb],
        "config": config, "sessions": sessions, "cells": cells, "floors": floors,
        "binaries": binaries,
        "holdout_admission": _admission_receipt(binaries),
        "wall_ledger": [], "excluded": [], "attempts": [],
    }
    expected = {"formula": FORMULA_ID, "n_sessions": n_sessions, "reps": reps,
                "stock_configuration": stock_cfg, "wired_min_rel_floor": 0.01,
                "session_cv_max": "0.10", "cell_cv_max": "0.15",
                "expected_cells": {holdout: [stock_cfg, va, vb]}}
    return artifact, expected, holdout, stock_cell, va_cell, va


def _attempt_registry_proof(artifact) -> dict[str, object]:
    return {
        "schema": attempt_registry_core.ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA,
        "registry_schema": (
            attempt_registry_core.ATTEMPT_REGISTRY_PREFIX_REGISTRY_SCHEMA
        ),
        "freeze_sha256": artifact["freeze_sha256"],
        "protocol_sha256": artifact["protocol_sha256"],
        "schedule_sha256": "6" * 64,
        "row_count": 3,
        "chain_head_sha256": "7" * 64,
    }


def _v5_artifact():
    artifact, expected, *rest = _honest_artifact()
    proof = _attempt_registry_proof(artifact)
    assert attempt_registry_core.validate_attempt_registry_prefix_proof(
        proof
    ) == proof
    artifact["schema"] = s8b_floor_contract.RESULT_SCHEMA_V5
    artifact["attempt_registry"] = copy.deepcopy(proof)
    return artifact, expected, proof, rest


def _assert_v5_control_gates_accept(
    artifact, expected, proof,
) -> dict[str, object]:
    independent = copy.deepcopy(proof)
    assert independent is not proof
    assert _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=independent,
    ) == []
    return independent


def test_pure_verifier_accepts_v5_with_independent_prefix_proof(monkeypatch):
    artifact, expected, proof, _ = _v5_artifact()
    production_validator = (
        attempt_registry_core.validate_attempt_registry_prefix_proof
    )
    assert production_validator(proof) == proof
    for field, invalid in (
        ("row_count", True),
        ("chain_head_sha256", "0" * 64),
        ("schema", "s8b-floor-attempt-registry-proof/wrong"),
    ):
        malformed = copy.deepcopy(proof)
        malformed[field] = invalid
        with pytest.raises(attempt_registry_core.AttemptRegistryCoreError):
            production_validator(malformed)

    validator_calls = []

    def validator_spy(value):
        validator_calls.append(value)
        return production_validator(value)

    monkeypatch.setattr(
        attempt_registry_core,
        "validate_attempt_registry_prefix_proof",
        validator_spy,
    )
    independent = _assert_v5_control_gates_accept(artifact, expected, proof)
    assert len(validator_calls) == 2
    assert validator_calls[0] is artifact["attempt_registry"]
    assert validator_calls[1] is independent


def test_pure_verifier_rejects_v4_attempt_registry_as_extra_key():
    artifact, expected, *_ = _honest_artifact()
    assert verify_floor_artifact(artifact, expected) == []
    artifact["attempt_registry"] = _attempt_registry_proof(artifact)
    errors = verify_floor_artifact(artifact, expected)
    assert errors == [
        "artifact result v4 exact key 集合が不一致 "
        "(欠落=[] 余分=['attempt_registry'])"
    ]


def test_pure_verifier_rejects_v4_expected_attempt_registry():
    artifact, expected, *_ = _honest_artifact()
    assert verify_floor_artifact(artifact, expected) == []
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=_attempt_registry_proof(artifact),
    )
    assert errors == ["v4 artifact に expected_attempt_registry を指定できない"]


def test_pure_verifier_rejects_v5_without_expected_attempt_registry():
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=None,
    )
    assert errors == ["v5 artifact の expected_attempt_registry が必須"]


def test_v5_rejects_missing_attempt_registry_proof():
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    del artifact["attempt_registry"]
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=proof,
    )
    assert errors == [
        "artifact result v5 exact key 集合が不一致 "
        "(欠落=['attempt_registry'] 余分=[])"
    ]


def test_v5_rejects_reported_prefix_head_tamper():
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    artifact["attempt_registry"]["chain_head_sha256"] = "8" * 64
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=proof,
    )
    assert errors == ["attempt_registry が独立 inspector の期待値と不一致"]


def test_v5_rejects_artifact_header_freeze_tamper():
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    artifact["freeze_sha256"] = "8" * 64
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=proof,
    )
    assert errors == [
        "attempt_registry.freeze_sha256 が artifact.freeze_sha256 と不一致"
    ]


def test_v5_rejects_artifact_header_protocol_tamper():
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    artifact["protocol_sha256"] = "8" * 64
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=proof,
    )
    assert errors == [
        "attempt_registry.protocol_sha256 が artifact.protocol_sha256 と不一致"
    ]


@pytest.mark.parametrize("field", ["freeze", "protocol", "schedule"])
def test_v5_rejects_proof_binding_mismatch(field):
    """freeze/protocol は診断 node。reason 順序 pin で変異観測には使わない。"""

    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    artifact["attempt_registry"][f"{field}_sha256"] = "8" * 64
    errors = _verify_floor_artifact(
        artifact,
        expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
        expected_attempt_registry=proof,
    )
    if field in {"freeze", "protocol"}:
        assert errors == [
            f"attempt_registry.{field}_sha256 が "
            f"artifact.{field}_sha256 と不一致"
        ]
    else:
        assert errors == ["attempt_registry が独立 inspector の期待値と不一致"]


def test_live_v4_does_not_call_attempt_registry_inspector(tmp_path, monkeypatch):
    artifact, expected, *_ = _honest_artifact()
    valid_proof = _attempt_registry_proof(artifact)
    production_validator = (
        attempt_registry_core.validate_attempt_registry_prefix_proof
    )
    validator_calls = []

    def accept_absent_proof(value):
        validator_calls.append(value)
        if value is None:
            return copy.deepcopy(valid_proof)
        return production_validator(value)

    monkeypatch.setattr(
        attempt_registry_core,
        "validate_attempt_registry_prefix_proof",
        accept_absent_proof,
    )
    monkeypatch.setattr(
        s8b_attempt_registry,
        "inspect_attempt_registry_prefix",
        lambda *_args, **_kwargs: pytest.fail(
            "v4 must not inspect the attempt registry"
        ),
    )
    monkeypatch.setattr(
        s8b_holdout_admission,
        "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact["holdout_admission"], derived_eligible_for_refreeze=True,
        ),
    )
    assert verify_floor_artifact_with_live_admission(
        artifact,
        expected,
        repo_root=tmp_path,
        protocol={},
        verified_freeze_document={},
        freeze_sha256=artifact["freeze_sha256"],
        manifest_sha256=artifact["manifest_sha256"],
        campaign_run_id="run",
        run_relpath="env/test/run",
        mode="official",
        cells=[],
        schedule=[],
        sessions=[],
        expected_use_perf=True,
    ) == []
    assert validator_calls == []


def test_live_v5_absent_proof_validator_seam_is_reachable(
        tmp_path, monkeypatch):
    artifact, expected, proof, _ = _v5_artifact()
    artifact["attempt_registry"] = None
    production_validator = (
        attempt_registry_core.validate_attempt_registry_prefix_proof
    )
    validator_calls = []

    def accept_absent_proof(value):
        validator_calls.append(value)
        if value is None:
            return copy.deepcopy(proof)
        return production_validator(value)

    inspector_calls = []

    def fake_inspector(*_args, **_kwargs):
        inspector_calls.append(_kwargs)
        return copy.deepcopy(proof)

    monkeypatch.setattr(
        attempt_registry_core,
        "validate_attempt_registry_prefix_proof",
        accept_absent_proof,
    )
    monkeypatch.setattr(
        s8b_attempt_registry,
        "inspect_attempt_registry_prefix",
        fake_inspector,
    )
    monkeypatch.setattr(
        s8b_holdout_admission,
        "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact["holdout_admission"], derived_eligible_for_refreeze=True,
        ),
    )

    assert verify_floor_artifact_with_live_admission(
        artifact,
        expected,
        repo_root=tmp_path,
        protocol={},
        verified_freeze_document={},
        freeze_sha256=artifact["freeze_sha256"],
        manifest_sha256=artifact["manifest_sha256"],
        campaign_run_id="run",
        run_relpath="env/test/run",
        mode="official",
        cells=[],
        schedule=[],
        sessions=[],
        expected_use_perf=True,
    ) == []
    assert len(inspector_calls) == 1
    assert validator_calls[:2] == [None, None]
    assert len(validator_calls) == 3
    assert validator_calls[2] == proof


def test_live_v5_calls_inspector_and_compares_reported_to_independent_proof(
        tmp_path, monkeypatch):
    artifact, expected, proof, _ = _v5_artifact()
    _assert_v5_control_gates_accept(artifact, expected, proof)
    protocol = {"external": "protocol"}
    schedule = [{"seq": 4, "cell_id": "synthetic"}]
    external_freeze_sha256 = "9" * 64
    external_protocol_sha256 = "8" * 64
    expected_schedule_sha256 = hashlib.sha256(
        _canonical_bytes(list(schedule))
    ).hexdigest()
    calls = []

    def fake_canonical_protocol_sha256(value):
        assert value is protocol
        return external_protocol_sha256

    def fake_inspector(
            repo_root, *, expected_binding, row_count, chain_head_sha256):
        calls.append({
            "repo_root": repo_root,
            "expected_binding": expected_binding,
            "row_count": row_count,
            "chain_head_sha256": chain_head_sha256,
        })
        independent = copy.deepcopy(proof)
        independent.update({
            "freeze_sha256": expected_binding.freeze_sha256,
            "protocol_sha256": expected_binding.protocol_sha256,
            "schedule_sha256": expected_binding.schedule_sha256,
        })
        return independent

    monkeypatch.setattr(
        s8b_floor_contract,
        "canonical_protocol_sha256",
        fake_canonical_protocol_sha256,
    )
    monkeypatch.setattr(
        s8b_attempt_registry,
        "inspect_attempt_registry_prefix",
        fake_inspector,
    )
    monkeypatch.setattr(
        s8b_holdout_admission,
        "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact["holdout_admission"], derived_eligible_for_refreeze=True,
        ),
    )

    errors = verify_floor_artifact_with_live_admission(
        artifact,
        expected,
        repo_root=tmp_path,
        protocol=protocol,
        verified_freeze_document={},
        freeze_sha256=external_freeze_sha256,
        manifest_sha256=artifact["manifest_sha256"],
        campaign_run_id="external-run",
        run_relpath="env/test/external-run",
        mode="official",
        cells=[],
        schedule=schedule,
        sessions=[],
        expected_use_perf=True,
    )

    assert errors == ["attempt_registry が独立 inspector の期待値と不一致"]
    accepted = copy.deepcopy(artifact)
    accepted["freeze_sha256"] = external_freeze_sha256
    accepted["protocol_sha256"] = external_protocol_sha256
    accepted["attempt_registry"].update({
        "freeze_sha256": external_freeze_sha256,
        "protocol_sha256": external_protocol_sha256,
        "schedule_sha256": expected_schedule_sha256,
    })
    assert verify_floor_artifact_with_live_admission(
        accepted,
        expected,
        repo_root=tmp_path,
        protocol=protocol,
        verified_freeze_document={},
        freeze_sha256=external_freeze_sha256,
        manifest_sha256=accepted["manifest_sha256"],
        campaign_run_id="external-run",
        run_relpath="env/test/external-run",
        mode="official",
        cells=[],
        schedule=schedule,
        sessions=[],
        expected_use_perf=True,
    ) == []

    assert len(calls) == 2
    assert calls[0] == {
        "repo_root": tmp_path,
        "expected_binding": s8b_attempt_profile.S8BAttemptBinding(
            freeze_sha256=external_freeze_sha256,
            protocol_sha256=external_protocol_sha256,
            schedule_sha256=expected_schedule_sha256,
        ),
        "row_count": proof["row_count"],
        "chain_head_sha256": proof["chain_head_sha256"],
    }
    assert calls[1] == calls[0]


def _create_reserved_v2_generation(case):
    generation_claim = s8b_holdout_admission._read_canonical_document(
        case["claim_path"]
    )
    generation_key = generation_claim["key"]
    schedule = list(case["state"].schedule)
    binding = s8b_attempt_profile.S8BAttemptBinding(
        freeze_sha256=str(generation_key["freeze_sha256"]),
        protocol_sha256=str(generation_claim["protocol_sha256"]),
        schedule_sha256=hashlib.sha256(
            attempt_registry_core.canonical_json_bytes(schedule)
        ).hexdigest(),
    )
    identity = {
        "freeze_holdout_key": str(case["marker"]["freeze_holdout_key"]),
        "configuration_id": str(case["marker"]["configuration_id"]),
        "repetition": int(case["use_kwargs"]["repetition"]),
        "measurement_ordinal": int(case["use_kwargs"]["attempt_ordinal"]),
        "attempt_ordinal": 0,
    }
    slot = s8b_attempt_profile.S8BV2AttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            attempt_registry_core.canonical_json_bytes(identity)
        ).hexdigest(),
    )
    profile = registry_cases._v2_authority_profile()
    s8b_attempt_registry.create_attempt_registry(
        case["repo_root"], profile=profile, slots=[slot], binding=binding,
    )
    registry_cases._reserve_v2(case, profile, binding, slot)
    proof = s8b_attempt_registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    assert proof["row_count"] == 3
    protocol = json.loads(
        (case["repo_root"] / "output/s8b-freeze/floor_protocol.json").read_bytes()
    )
    assert s8b_floor_contract.canonical_protocol_sha256(protocol) == (
        binding.protocol_sha256
    )
    return binding, proof, protocol, schedule


def _issued_cell_for_campaign_identity(root, protocol, freeze, *, run_id):
    cells, schedule = admission_cases._cells_and_schedule(protocol, freeze)
    reservation = admission_cases._reserve(
        root, protocol, freeze, run_id=run_id,
    )
    admitted = s8b_holdout_admission.finalize_floor_holdout_admissions(
        reservation
    )
    cell = cells[0]
    seq = next(
        row["seq"] for row in schedule if row["cell_id"] == cell["cell_id"]
    )
    attempt_id = f"{cell['cell_id']}::seq{seq}"
    run_dir = root / (
        f"out/env/{protocol['env_tag']}/calibration/s8b-floor-pilot/{run_id}"
    )
    (run_dir / "journal.jsonl").write_text(json.dumps({
        "event": "session-start",
        "seq": seq,
        "round": next(row["round"] for row in schedule if row["seq"] == seq),
        "kind": "planned",
        "cell_id": cell["cell_id"],
        "attempt_id": attempt_id,
        "trigger": None,
    }, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha256 = hashlib.sha256(
        (run_dir / "manifest.json").read_bytes()
    ).hexdigest()
    return (
        root, protocol, cell, admitted[cell["cell_id"]], attempt_id,
        manifest_sha256,
    )


def test_live_v5_real_registry_rejects_reported_other_generation(
        tmp_path, monkeypatch):
    case_a_root = tmp_path / "a"
    case_a_root.mkdir()
    case_a = admission_cases._consumed_marker_capability_case(case_a_root)
    repo_a = case_a["repo_root"]
    linked = tmp_path / "linked"
    admission_cases._git(
        repo_a, "worktree", "add", "--detach", str(linked), "HEAD",
    )
    protocol_b, freeze_b = admission_cases._fixture_documents("seed-b")
    admission_cases._write_fixed_documents(linked, protocol_b, freeze_b)
    admission_cases._git(linked, "add", "output/s8b-freeze")
    admission_cases._git(
        linked,
        "-c", "user.name=fixture",
        "-c", "user.email=f@example.invalid",
        "commit", "-m", "fixture generation b",
    )
    with monkeypatch.context() as patcher:
        patcher.setattr(
            admission_cases,
            "_issued_cell",
            lambda _path: _issued_cell_for_campaign_identity(
                linked, protocol_b, freeze_b, run_id="run-b",
            ),
        )
        case_b = admission_cases._consumed_marker_capability_case(
            tmp_path / "b"
        )

    assert case_a["marker"]["campaign_run_id"] == "run-a"
    assert case_b["marker"]["campaign_run_id"] == "run-b"
    assert case_a["claim_path"].parent == case_b["claim_path"].parent
    assert case_a["claim_path"] != case_b["claim_path"]
    assert case_a["claim_path"].is_file()
    assert case_b["claim_path"].is_file()
    assert s8b_holdout_admission.shared_admission_root(repo_a) == (
        s8b_holdout_admission.shared_admission_root(linked)
    )
    binding_a, proof_a, protocol_a, schedule_a = (
        _create_reserved_v2_generation(case_a)
    )
    binding_b, proof_b, _protocol_b, _schedule_b = (
        _create_reserved_v2_generation(case_b)
    )
    assert binding_a.freeze_sha256 == binding_b.freeze_sha256
    assert binding_a.protocol_sha256 != binding_b.protocol_sha256
    assert proof_a["chain_head_sha256"] != proof_b["chain_head_sha256"]

    artifact_b, expected, *_ = _honest_artifact()
    artifact_b["schema"] = s8b_floor_contract.RESULT_SCHEMA_V5
    artifact_b["freeze_sha256"] = binding_b.freeze_sha256
    artifact_b["protocol_sha256"] = binding_b.protocol_sha256
    artifact_b["attempt_registry"] = copy.deepcopy(proof_b)
    monkeypatch.setattr(
        s8b_holdout_admission,
        "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact_b["holdout_admission"],
            derived_eligible_for_refreeze=True,
        ),
    )
    live_kwargs = {
        "repo_root": repo_a,
        "protocol": protocol_a,
        "verified_freeze_document": freeze_b,
        "freeze_sha256": binding_a.freeze_sha256,
        "manifest_sha256": artifact_b["manifest_sha256"],
        "campaign_run_id": "external-run",
        "run_relpath": "env/test/external-run",
        "mode": "official",
        "cells": [],
        "schedule": schedule_a,
        "sessions": [],
        "expected_use_perf": True,
    }
    with pytest.raises(
        s8b_holdout_admission.FloorHoldoutEvidenceError,
    ) as exc_info:
        verify_floor_artifact_with_live_admission(
            artifact_b, expected, **live_kwargs,
        )
    assert exc_info.value.category == "mismatch"
    assert exc_info.value.reason == "attempt-registry-prefix-head-mismatch"

    artifact_a = copy.deepcopy(artifact_b)
    artifact_a["freeze_sha256"] = binding_a.freeze_sha256
    artifact_a["protocol_sha256"] = binding_a.protocol_sha256
    artifact_a["attempt_registry"] = copy.deepcopy(proof_a)
    assert verify_floor_artifact_with_live_admission(
        artifact_a, expected, **live_kwargs,
    ) == []


def test_verify_accepts_consistent_artifact():
    artifact, expected, *_ = _honest_artifact()
    assert verify_floor_artifact(artifact, expected) == []


def _degraded_honest_artifact():
    artifact, expected, *rest = _honest_artifact()
    receipt = _perf_receipt(available=False)
    for session in artifact["sessions"]:
        session["run_cmd"] = [artifact["binaries"][session["cell_id"]]["binary"]]
        for observation in session["rep_observations"]:
            observation["counter_status"] = "not_required"
            observation["perf_raw"] = {
                event: None for event in (
                    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
                )
            }
    artifact["perf_preflight"] = receipt
    artifact["perf_observation"] = {
        "use_perf": False,
        "counter_status": "not_required",
        "missing_leading_indicators": [],
        "preflight": receipt,
        "claim_scope": {
            "throughput": "eligible",
            "perf_required": "unsupported",
        },
    }
    return (artifact, expected, *rest)


def test_pilot_degraded_preserves_legacy_shape_without_perf_observation():
    artifact, expected, *_ = _degraded_honest_artifact()
    artifact["mode"] = "pilot"
    del artifact["perf_observation"]

    errors = _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    )

    assert errors == []


def test_official_degraded_requires_and_consumes_perf_observation():
    artifact, expected, *_ = _degraded_honest_artifact()

    assert _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    ) == []

    del artifact["perf_observation"]
    assert _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    ) == [
        "artifact result v4 exact key 集合が不一致 "
        "(欠落=['perf_observation'] 余分=[])"
    ]


def test_official_degraded_keeps_all_five_internal_consistency_conditions():
    artifact, expected, *_ = _degraded_honest_artifact()

    noncanonical_receipt = copy.deepcopy(artifact)
    noncanonical_receipt["perf_preflight"]["reason"] = "available"
    assert _verify_floor_artifact(
        noncanonical_receipt, expected,
        expected_holdout_admission=noncanonical_receipt["holdout_admission"],
        expected_use_perf=False,
    )[0].startswith("artifact perf_preflight が不正: ")

    for field, invalid in (
        ("counter_status", "complete"),
        ("missing_leading_indicators", ["ipc"]),
    ):
        mutated = copy.deepcopy(artifact)
        mutated["perf_observation"][field] = invalid
        errors = _verify_floor_artifact(
            mutated, expected,
            expected_holdout_admission=mutated["holdout_admission"],
            expected_use_perf=False,
        )
        assert errors == [
            "artifact perf_observation が不正: "
            "degraded perf observation の counter 状態が不整合"
        ]

    perf_prefixed = copy.deepcopy(artifact)
    perf_prefixed["sessions"][0]["run_cmd"] = [
        "perf", "stat", "--", perf_prefixed["sessions"][0]["run_cmd"][0],
    ]
    assert _verify_floor_artifact(
        perf_prefixed, expected,
        expected_holdout_admission=perf_prefixed["holdout_admission"],
        expected_use_perf=False,
    ) == [
        "artifact perf_observation が不正: "
        "degraded measurement run_cmd に perf stat prefix がある"
    ]

    non_null_counter = copy.deepcopy(artifact)
    non_null_counter["sessions"][0]["rep_observations"][0]["perf_raw"][
        "cycles"
    ] = 1
    assert _verify_floor_artifact(
        non_null_counter, expected,
        expected_holdout_admission=non_null_counter["holdout_admission"],
        expected_use_perf=False,
    ) == [
        "artifact perf_observation が不正: "
        "leading_indicators.session.rep_observations[0].perf_raw "
        "に non-null perf raw 値がある"
    ]

    invalid_claim_scope = copy.deepcopy(artifact)
    invalid_claim_scope["perf_observation"]["claim_scope"][
        "perf_required"
    ] = "eligible"
    assert _verify_floor_artifact(
        invalid_claim_scope, expected,
        expected_holdout_admission=invalid_claim_scope["holdout_admission"],
        expected_use_perf=False,
    ) == [
        "artifact perf_observation が不正: "
        "degraded perf observation.claim_scope が不一致"
    ]


def test_official_perf_present_keeps_legacy_exact_shape():
    artifact, expected, *_ = _honest_artifact()

    assert _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
    ) == []

    artifact["perf_observation"] = _degraded_honest_artifact()[0][
        "perf_observation"
    ]
    assert _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=True,
    ) == [
        "artifact result v4 exact key 集合が不一致 "
        "(欠落=[] 余分=['perf_observation'])"
    ]


def test_expected_use_perf_cannot_disagree_with_artifact_receipt():
    """M3: caller の裸 False は available receipt の authority を上書きできない。"""
    artifact, expected, *_ = _honest_artifact()
    artifact["mode"] = "pilot"
    artifact["perf_preflight"] = _perf_receipt(available=True)

    errors = _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    )

    assert errors == [
        "expected_use_perf が artifact receipt の再導出値と不一致 "
        "(caller=False, artifact=True)"
    ]


def test_degraded_floor_stats_require_consumed_throughput_claim(monkeypatch):
    """consumer-side M2: valid observation の claim 判定だけ deny して呼出しを pin。"""
    artifact, expected, *_ = _degraded_honest_artifact()
    monkeypatch.setattr(
        perf_preflight, "_claim_decision",
        lambda _claim_scope, _claim: False,
    )

    errors = _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    )

    assert errors == [
        "artifact perf_observation が不正: "
        "floor artifact は 'throughput' claim を許可しない"
    ]


def test_degraded_floor_stats_bind_run_cmd_from_same_result():
    artifact, expected, *_ = _degraded_honest_artifact()
    artifact["sessions"][0]["run_cmd"] = [
        "perf", "stat", "--", artifact["sessions"][0]["run_cmd"][0],
    ]

    errors = _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    )

    assert errors == [
        "artifact perf_observation が不正: "
        "degraded measurement run_cmd に perf stat prefix がある"
    ]


def test_degraded_floor_stats_bind_raw_counters_from_same_result():
    artifact, expected, *_ = _degraded_honest_artifact()
    artifact["sessions"][0]["rep_observations"][0]["perf_raw"]["cycles"] = 1

    errors = _verify_floor_artifact(
        artifact, expected,
        expected_holdout_admission=artifact["holdout_admission"],
        expected_use_perf=False,
    )

    assert errors == [
        "artifact perf_observation が不正: "
        "leading_indicators.session.rep_observations[0].perf_raw "
        "に non-null perf raw 値がある"
    ]


def test_verify_requires_expected_use_perf_keyword_argument():
    artifact, expected, *_ = _honest_artifact()
    parameter = inspect.signature(_verify_floor_artifact).parameters["expected_use_perf"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match="expected_use_perf"):
        _verify_floor_artifact(
            artifact, expected,
            expected_holdout_admission=artifact["holdout_admission"],
        )


def test_verify_requires_expected_holdout_admission_keyword_argument():
    artifact, expected, *_ = _honest_artifact()
    parameter = inspect.signature(_verify_floor_artifact).parameters[
        "expected_holdout_admission"
    ]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError, match="expected_holdout_admission"):
        _verify_floor_artifact(artifact, expected, expected_use_perf=True)


def test_live_verifier_signature_forbids_caller_supplied_expected_admission():
    parameters = inspect.signature(
        verify_floor_artifact_with_live_admission
    ).parameters
    assert "expected_holdout_admission" not in parameters


def test_live_refreeze_comparison_is_centralized_once_and_has_three_callers():
    source = inspect.getsource(verify_floor_artifact_with_live_admission)
    comparisons = [
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Compare)
        and any(
            isinstance(item, ast.Attribute)
            and item.attr == "derived_eligible_for_refreeze"
            for item in ast.walk(node)
        )
    ]
    assert len(comparisons) == 1

    campaign_root = Path(__file__).resolve().parents[1] / "campaign"
    callers = {
        path.name
        for path in campaign_root.glob("*.py")
        if path.name != "s8b_floor_stats.py"
        and "verify_floor_artifact_with_live_admission(" in path.read_text(
            encoding="utf-8"
        )
    }
    assert callers == {
        "s8b_floor_campaign.py",
        "s8b_holdout_freeze.py",
        "s8b_ratified_freeze.py",
    }


@pytest.mark.parametrize(
    "reported,derived",
    [(True, False), (False, True)],
    ids=["reported-true-derived-false", "reported-false-derived-true"],
)
def test_live_verifier_rejects_both_refreeze_mismatch_directions(
    tmp_path, monkeypatch, reported, derived,
):
    artifact, expected, *_ = _honest_artifact()
    artifact["eligible_for_refreeze"] = reported
    monkeypatch.setattr(
        s8b_holdout_admission, "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact["holdout_admission"],
            derived_eligible_for_refreeze=derived,
        ),
    )

    with pytest.raises(
        s8b_holdout_admission.FloorHoldoutEvidenceError,
    ) as exc_info:
        verify_floor_artifact_with_live_admission(
            artifact, expected, repo_root=tmp_path, protocol={},
            verified_freeze_document={}, freeze_sha256="3" * 64,
            manifest_sha256="4" * 64, campaign_run_id="run",
            run_relpath="env/test/run", mode="official", cells=[], schedule=[],
            sessions=[], expected_use_perf=True,
        )
    assert exc_info.value.category == "mismatch"
    assert exc_info.value.reason == "refreeze-eligibility-mismatch"


def test_live_verifier_rejects_result_v4_unexpected_top_level_key(
        tmp_path, monkeypatch):
    artifact, expected, *_ = _honest_artifact()
    artifact["unexpected"] = "must be rejected"
    monkeypatch.setattr(
        s8b_holdout_admission, "inspect_floor_holdout_admission_evidence",
        lambda **_kwargs: s8b_holdout_admission.FloorHoldoutEvidenceInspection(
            artifact["holdout_admission"], derived_eligible_for_refreeze=True,
        ),
    )

    errors = verify_floor_artifact_with_live_admission(
        artifact, expected, repo_root=tmp_path, protocol={},
        verified_freeze_document={}, freeze_sha256="3" * 64,
        manifest_sha256="4" * 64, campaign_run_id="run",
        run_relpath="env/test/run", mode="official", cells=[], schedule=[],
        sessions=[], expected_use_perf=True,
    )

    assert errors == [
        "artifact result v4 exact key 集合が不一致 (欠落=[] 余分=['unexpected'])"
    ]


def test_verify_rejects_integrity_violation_with_valid_claim():
    """M8: rc 違反を count 0・全 tps 採用のまま隠すと拒否する。"""
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["rep_observations"][2]["returncode"] = 7
    errors = verify_floor_artifact(artifact, expected)
    assert any("rep_integrity_failures 齟齬" in error for error in errors)
    assert any("integrity-qualified throughputs 齟齬" in error for error in errors)


def test_derive_rep_integrity_counts_execution_exception_in_both_quantities():
    observations = list(_sess("c", 0, [100, 101, 102], reps_expected=3).rep_observations)
    observations[1] = {
        **observations[1],
        "returncode": None,
        "execution_failure": True,
        "throughput": None,
    }
    errors, integrity_failures, exec_failures, qualified = \
        s8b_floor_stats._derive_rep_integrity(
            observations, reps=3, expected_use_perf=True,
        )
    assert errors == []
    assert exec_failures == 1
    assert integrity_failures == 1
    assert qualified == (100, 102)


def test_derive_rep_integrity_keeps_nonzero_rc_out_of_exec_failures():
    observations = list(_sess("c", 0, [100, 101, 102], reps_expected=3).rep_observations)
    observations[1] = {**observations[1], "returncode": 7}
    errors, integrity_failures, exec_failures, qualified = \
        s8b_floor_stats._derive_rep_integrity(
            observations, reps=3, expected_use_perf=True,
        )
    assert errors == []
    assert exec_failures == 0
    assert integrity_failures == 1
    assert qualified == (100, 102)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero"),
        pytest.param(1, id="one"),
        pytest.param(None, id="none"),
        pytest.param("false", id="string"),
    ],
)
def test_derive_rep_integrity_rejects_non_bool_execution_failure(value):
    observations = list(_sess("c", 0, [100, 101, 102], reps_expected=3).rep_observations)
    observations[0] = {**observations[0], "execution_failure": value}
    errors, _integrity, _exec, _qualified = \
        s8b_floor_stats._derive_rep_integrity(
            observations, reps=3, expected_use_perf=True,
        )
    assert any("execution_failure が exact bool でない" in error for error in errors)


def test_execution_failure_true_with_throughput_has_specific_rejection():
    observations = list(_sess("c", 0, [100, 101, 102], reps_expected=3).rep_observations)
    observations[1] = {**observations[1], "execution_failure": True}
    errors, integrity_failures, exec_failures, qualified = \
        s8b_floor_stats._derive_rep_integrity(
            observations, reps=3, expected_use_perf=True,
        )
    assert errors == [
        "rep_observations[1]: execution_failure=True なのに throughput が非 null"
    ]
    assert (integrity_failures, exec_failures, qualified) == (1, 1, (100, 102))


def test_verify_rejects_exec_count_mismatch_independently_of_integrity_count():
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["exec_failures"] = 1
    errors = verify_floor_artifact(artifact, expected)
    assert any("exec_failures 齟齬" in error for error in errors)
    assert not any("rep_integrity_failures 齟齬" in error for error in errors)


def test_old_six_key_rep_observation_is_rejected():
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["rep_observations"][0].pop("execution_failure")
    errors = verify_floor_artifact(artifact, expected)
    assert any("exact key 不一致" in error for error in errors)


def test_verify_rejects_false_rep_integrity_exclusion():
    """M9: 全 rep 完備なのに failure count を自己申告しても信用しない。"""
    artifact, expected, *_ = _honest_artifact()
    row = artifact["sessions"][0]
    row["rep_integrity_failures"] = 1
    row["exclusion_class"] = "rep_integrity_failure"
    errors = verify_floor_artifact(artifact, expected)
    assert any("rep_integrity_failures 齟齬" in error for error in errors)
    assert any("偽除外" in error for error in errors)


@pytest.mark.parametrize("reason", [
    pytest.param("competing_process", id="competing"),
    pytest.param("launch_failure", id="launch"),
])
def test_verify_rejects_exempt_session_exclusion_class_tamper(reason):
    """R1: 証跡免除 session でも exclusion_class の改変を拒否する。"""
    artifact, expected, *_ = _honest_artifact()
    row = artifact["sessions"][0]
    row.update({
        "throughputs": [], "rep_observations": [],
        "rep_integrity_failures": None, "run_cmd": None,
        "excluded_reason": reason, "exclusion_class": reason,
        "exec_failures": 0 if reason == "competing_process" else row["reps_expected"],
        "probe_before": {"competing": reason == "competing_process"},
        "probe_after": None if reason == "competing_process" else {"competing": False},
    })
    before = verify_floor_artifact(artifact, expected)
    assert not any("exclusion_class 齟齬" in error for error in before)
    row["exclusion_class"] = "rep_integrity_failure"
    after = verify_floor_artifact(artifact, expected)
    assert any("exclusion_class 齟齬" in error for error in after)


def test_verify_rejects_completed_measure_disguised_as_unmeasured_exemption():
    """R2: post-probe 済み session は自己申告だけで証跡免除へ偽装できない。"""
    artifact, expected, *_ = _honest_artifact()
    row = artifact["sessions"][0]
    row.update({
        "throughputs": [], "rep_observations": [],
        "rep_integrity_failures": None, "run_cmd": None,
        "excluded_reason": "competing_process",
        "exclusion_class": "competing_process", "exec_failures": 0,
        "probe_before": {"competing": False},
        "probe_after": {"competing": False},
    })
    errors = verify_floor_artifact(artifact, expected)
    assert any("rep_observations 件数" in error for error in errors)
    assert any("rep_integrity_failures が非負 exact int" in error for error in errors)


@pytest.mark.parametrize("field,value", [
    pytest.param("seq", "5", id="seq-string"),
    pytest.param("reps_expected", 5.9, id="reps-float"),
    pytest.param("exec_failures", "0", id="failures-string"),
    pytest.param("retry", 0.9, id="retry-float"),
])
def test_verify_rejects_normalizable_session_scalar_types(field, value):
    """R3: int/bool へ正規化できても保存型が exact でなければ拒否する。"""
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0][field] = value
    errors = verify_floor_artifact(artifact, expected)
    assert any(field in error and "変換不能" in error for error in errors)


def test_verify_rejects_perf_required_not_required_claim():
    """M10: perf-required 文脈で not_required を良好値にできない。"""
    artifact, expected, *_ = _honest_artifact()
    observation = artifact["sessions"][0]["rep_observations"][0]
    observation["counter_status"] = "not_required"
    observation["perf_raw"] = {event: None for event in (
        "LLC-load-misses", "LLC-loads", "instructions", "cycles",
    )}
    observation["missing_perf_events"] = [
        "LLC-load-misses", "LLC-loads", "instructions", "cycles",
    ]
    errors = verify_floor_artifact(artifact, expected)
    assert any("counter_status 齟齬" in error for error in errors)


def test_verify_rejects_counter_status_missing_contradiction():
    """M11: missing 列からの status 再導出と申告が矛盾すれば拒否する。"""
    artifact, expected, *_ = _honest_artifact()
    observation = artifact["sessions"][0]["rep_observations"][0]
    observation["perf_raw"]["cycles"] = None
    observation["missing_perf_events"] = ["cycles"]
    observation["counter_status"] = "complete"
    errors = verify_floor_artifact(artifact, expected)
    assert any("counter_status 齟齬" in error for error in errors)


@pytest.mark.parametrize("field,value", [
    ("returncode", False),
    ("rep_index", False),
])
def test_verify_rejects_bool_in_rep_observation(field, value):
    """M12: bool を exact int として受け入れない。"""
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["rep_observations"][0][field] = value
    errors = verify_floor_artifact(artifact, expected)
    assert any(field in error for error in errors)


def test_verify_rejects_negative_perf_counter():
    """M5: 負 counter は取得済みでなく欠損として扱う。"""
    artifact, expected, *_ = _honest_artifact()
    observation = artifact["sessions"][0]["rep_observations"][0]
    observation["perf_raw"]["cycles"] = -1
    errors = verify_floor_artifact(artifact, expected)
    assert any("missing_perf_events 齟齬" in error for error in errors)


@pytest.mark.parametrize("mutation", ["unknown", "missing_observation"])
def test_verify_rejects_unknown_or_missing_rep_evidence(mutation):
    """M6: unknown・証跡欠落を違反なしへ補わない。"""
    artifact, expected, *_ = _honest_artifact()
    if mutation == "unknown":
        artifact["sessions"][0]["rep_observations"][0]["counter_status"] = "unknown"
    else:
        artifact["sessions"][0]["rep_observations"].pop()
    errors = verify_floor_artifact(artifact, expected)
    assert errors
    assert any(
        "counter_status 齟齬" in error or "rep_observations 件数" in error
        for error in errors
    )


def test_verify_accepts_zero_perf_counters():
    """P4: counter 0 は取得済みの exact int であり complete。"""
    artifact, expected, *_ = _honest_artifact()
    for observation in artifact["sessions"][0]["rep_observations"]:
        observation["perf_raw"] = {
            "LLC-load-misses": 0, "LLC-loads": 0,
            "instructions": 0, "cycles": 0,
        }
    assert verify_floor_artifact(artifact, expected) == []


def test_verify_detects_tampered_floor_pair():
    # freeze 向き pair (configuration_id キー) を +1 改竄 → 再計算不一致。
    artifact, expected, holdout, _, _, va = _honest_artifact()
    artifact["floors"][holdout]["pairs"][va] += 1.0
    errs = verify_floor_artifact(artifact, expected)
    assert any("pairs" in e for e in errs)


def test_verify_rejects_ghost_holdout_floor():
    # sessions に現れない幽霊 holdout の floors 注入を拒否 (fail-closed 対称性、
    # レビュー所見: 以前は素通りしていた)。
    artifact, expected, *_ = _honest_artifact()
    artifact["floors"]["ghost-holdout"] = {
        "pairs": {"variant_a": 0.0001}, "scalar_alt": 0.0001, "scale_ref": 1.0,
        "diagnostics": {"machine_anomaly_cells": []},
    }
    errs = verify_floor_artifact(artifact, expected)
    assert any("期待にない holdout" in e for e in errs)


def test_verify_detects_diagnostics_cells_tamper_and_injected_key():
    # diagnostics の cells 内訳改竄・任意キー注入を拒否 (レビュー所見: machine_anomaly_cells
    # だけの照合では素通りしていた)。
    artifact, expected, holdout, *_ = _honest_artifact()
    tampered = dict(artifact["floors"][holdout]["diagnostics"])
    tampered["injected"] = "malicious note"
    artifact["floors"][holdout]["diagnostics"] = tampered
    errs = verify_floor_artifact(artifact, expected)
    assert any("diagnostics" in e for e in errs)


def test_verify_rejects_extra_key_in_floors_entry():
    # floors[h] 直下への余分キー注入を拒否。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["floors"][holdout]["bonus"] = 1
    errs = verify_floor_artifact(artifact, expected)
    assert any("期待にないキー" in e for e in errs)


def test_verify_detects_swapped_throughputs():
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["throughputs"] = [999999.0] * 5
    assert verify_floor_artifact(artifact, expected) != []


# --- 改竄 positive control 群 (verifier mutant を殺す) ---
def test_verify_rejects_empty_artifact():
    # 空 sessions/cells/floors + config だけ → expected_cells 不一致で恒真化を拒否 (α-2)。
    empty, expected, *_ = _honest_artifact()
    empty["sessions"] = []
    empty["cells"] = {}
    empty["floors"] = {}
    errs = verify_floor_artifact(empty, expected)
    assert any("expected_cells" in e for e in errs)


def test_verify_rejects_missing_holdout_cell():
    # variant_B のセッションを丸ごと削除 → expected_cells 欠落で拒否。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["sessions"] = [s for s in artifact["sessions"]
                            if s["configuration_id"] != "variant_B"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("expected_cells" in e for e in errs)


def test_verify_rejects_threshold_selfreport_mismatch():
    # config の閾値を緩めても expected_protocol (凍結値) と不一致で拒否 (α-3)。
    artifact, expected, *_ = _honest_artifact()
    artifact["config"]["cell_cv_max"] = "1.0"
    errs = verify_floor_artifact(artifact, expected)
    assert any("cell_cv_max" in e for e in errs)


def test_verify_rejects_reps_selfreport_downgrade():
    # 4/5 rep の session を reps_expected=4 と自己申告しても expected.reps=5 と不一致で拒否 (α-4)。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["throughputs"] = [100.0, 100.0, 100.0, 100.0]
    artifact["sessions"][0]["reps_expected"] = 4
    errs = verify_floor_artifact(artifact, expected)
    assert any("reps_expected" in e for e in errs)


def test_verify_detects_false_exclusion():
    # 良い session (CV 0) を performance_anomaly と偽ラベル → 生値と理由が食い違う (偽除外, α-5)。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["excluded_reason"] = "performance_anomaly"
    errs = verify_floor_artifact(artifact, expected)
    assert any("理由すり替え" in e for e in errs)


def test_verify_detects_anomaly_hiding():
    # CV 異常な生値を持つ session を有効 (excluded_reason=None) と主張 → 異常隠蔽 (α-5)。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    for s in artifact["sessions"]:
        if s["seq"] == 0 and s["cell_id"] == stock_cell:
            s["throughputs"] = [89.0, 89.0, 100.0, 111.0, 111.0]  # CV>10%
            s["excluded_reason"] = None
    errs = verify_floor_artifact(artifact, expected)
    assert any("異常隠蔽" in e for e in errs)


def test_verify_detects_reason_swap_to_partial():
    # CV 異常 (完全 5-rep) を nonfinite_or_partial_output と誤ラベル → throughput 導出理由と不一致。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    for s in artifact["sessions"]:
        if s["seq"] == 0 and s["cell_id"] == stock_cell:
            s["throughputs"] = [89.0, 89.0, 100.0, 111.0, 111.0]
            s["excluded_reason"] = "nonfinite_or_partial_output"
    errs = verify_floor_artifact(artifact, expected)
    assert any("理由すり替え" in e for e in errs)


def test_verify_rejects_unknown_reason():
    # 閉表外の理由は拒否。
    artifact, expected, *_ = _honest_artifact()
    artifact["sessions"][0]["excluded_reason"] = "orphan_detected"
    errs = verify_floor_artifact(artifact, expected)
    assert any("閉表" in e for e in errs)


def test_verify_detects_diagnostics_machine_anomaly_tamper():
    # diagnostics の machine_anomaly_cells を捏造 → 再計算と不一致 (α-11 改竄 positive control)。
    artifact, expected, holdout, *_ = _honest_artifact()
    artifact["floors"][holdout]["diagnostics"]["machine_anomaly_cells"] = ["H1::variant_A"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("machine_anomaly_cells" in e for e in errs)


def test_verify_detects_cell_stat_tamper():
    # 申告 cell の m を書き換え → 再計算と不一致。
    artifact, expected, holdout, stock_cell, *_ = _honest_artifact()
    artifact["cells"][stock_cell]["m"] += 7.0
    errs = verify_floor_artifact(artifact, expected)
    assert any(stock_cell in e and "m" in e for e in errs)


def test_verify_rejects_cellid_collision_across_coords():
    # 同一 cell_id を別 (holdout, configuration) に再利用 → global 衝突拒否 (α-10)。
    artifact, expected, holdout, stock_cell, va_cell, va = _honest_artifact()
    # variant_A の 1 セッションの座標だけ別 holdout に変え cell_id は据え置き。
    for s in artifact["sessions"]:
        if s["cell_id"] == va_cell:
            s["holdout_id"] = "H2"
            break
    errs = verify_floor_artifact(artifact, expected)
    assert any("衝突" in e or "不一致" in e for e in errs)


def test_verify_rejects_missing_expected_protocol_key():
    artifact, expected, *_ = _honest_artifact()
    del expected["cell_cv_max"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("expected_protocol" in e for e in errs)


def test_verify_rejects_missing_config():
    artifact, expected, *_ = _honest_artifact()
    del artifact["config"]
    errs = verify_floor_artifact(artifact, expected)
    assert any("config" in e for e in errs)


def test_verify_rejects_duplicate_binary_for_existing_pair_without_expected_binaries():
    artifact, expected, *_ = _honest_artifact()
    duplicate = copy.deepcopy(artifact["binaries"]["H1::variant_B"])
    artifact["binaries"]["duplicate-cell-id"] = duplicate
    errors = verify_floor_artifact(artifact, expected, expected_binaries=None)
    assert any("canonical cell_id 集合/件数" in error for error in errors)


def test_verify_rejects_unknown_binary_cell_id_without_expected_binaries():
    artifact, expected, *_ = _honest_artifact()
    record = artifact["binaries"].pop("H1::variant_B")
    artifact["binaries"]["H1::unknown"] = record
    errors = verify_floor_artifact(artifact, expected, expected_binaries=None)
    assert any("canonical cell_id 集合/件数" in error for error in errors)


def test_verify_rejects_binary_cell_id_bound_to_different_pair_without_expected_binaries():
    artifact, expected, *_ = _honest_artifact()
    stock = artifact["binaries"]["H1::stock_common"]
    stock["holdout_id"] = "H1"
    stock["configuration_id"] = "variant_B"
    errors = verify_floor_artifact(artifact, expected, expected_binaries=None)
    assert any("canonical cell identity" in error or "admission receipt" in error
               for error in errors)


def test_verify_rejects_empty_binaries_without_expected_binaries():
    artifact, expected, *_ = _honest_artifact()
    artifact["binaries"] = {}
    errors = verify_floor_artifact(artifact, expected, expected_binaries=None)
    assert errors == ["binaries: section が無い/空"]


def test_verify_rejects_expected_holdout_without_exactly_one_sort_best():
    artifact, expected, *_ = _honest_artifact()
    expected["expected_cells"]["H1"].remove("sort_best")
    errors = verify_floor_artifact(artifact, expected)
    assert any("sort_best が 0 個" in error for error in errors)


def test_pure_verifier_rejects_admission_different_from_external_expected():
    artifact, expected, *_ = _honest_artifact()
    live = copy.deepcopy(artifact["holdout_admission"])
    live["ledger_projection_sha256"] = "6" * 64
    errors = _verify_floor_artifact(
        artifact, expected, expected_holdout_admission=live,
        expected_use_perf=True,
    )
    assert errors == ["holdout_admission が live inspector の期待値と不一致"]


def test_pure_verifier_rejects_legacy_result_schema():
    artifact, expected, *_ = _honest_artifact()
    artifact["schema"] = "s8b-floor-result/v3"
    errors = verify_floor_artifact(artifact, expected)
    assert errors == ["artifact.schema が 's8b-floor-result/v4' でない"]
