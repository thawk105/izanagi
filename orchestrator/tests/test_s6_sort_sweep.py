# -*- coding: utf-8 -*-
"""s6_sort_sweep (段6前提タスク (i): sort comparator 機械列挙 sweep) の単体テスト。

build/verify/bench を伴わない機械部分のみ:
  1. **SWO 有限モデル総当たり** — 列挙候補の C++ 比較式を Python モデルへ機械導出し、
     有限空間で SWO 4 公理 (非反射・非対称・推移・同値の推移) を全対検査する。
     「全点 SWO-by-construction」の宣言 (設計 §5 backstop 4) をここで機械化する —
     転写ミス由来の非 SWO (D42: write_set_>=16 でハング) を実走前に落とす。
  2. category (full-order / degenerate) の意味論検査 — 実 workload 制約
     (単一 storage・key 一意・rcdptr 一意) 下で tie の有無と一致するか。
  3. 検疫通過 — 全候補が diff 検疫 (フレーム不可触・hole 封じ込め) を write=False で通る。
  4. identity — workload/trial が campaign_id に焼かれ分離される (機構レンズ should-fix)。
  5. nosort の無名引数形 (-Werror=unused-parameter 対策、機構レンズ must-fix) と
     コメント不在 (src_token は preprocess 後ハッシュでコメントが消える罠)。
"""
from __future__ import annotations

import contextlib
import errno
import hashlib
import inspect
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import ident                                        # noqa: E402
from orchestrator.campaign import campaign_lock, contract_loader_binding       # noqa: E402
from orchestrator.campaign import pipeline                                     # noqa: E402
from orchestrator.campaign import p3_s4_loop as L                              # noqa: E402
from orchestrator.campaign import s6_sort_sweep as W                           # noqa: E402
from orchestrator.campaign import wal                                         # noqa: E402
from orchestrator.campaign.artifact_admission import (                         # noqa: E402
    CampaignNotAdmitted,
    CampaignReadPurpose,
    CampaignVerifierEpochRejected,
    require_admitted_campaign,
)
from orchestrator.campaign.build_admission import (BuildAdmissionError,            # noqa: E402
                                      BuildProvenance, GeneratorId,
                                      attest_generator_output,
                                      build_run_context,
                                      derive_build_admission)
from orchestrator.campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from orchestrator.campaign.pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402
from orchestrator.campaign.model import COMMIT_CONTRACT_SHA256_KEY              # noqa: E402
from orchestrator.campaign.source_digest import (EMPTY_TRACKED_DIFF_SHA256,      # noqa: E402
                                    STOCK, SourceEvidence)
from campaign_lock_test_support import build_v2_lock                 # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402

_REAL_E0_CAMPAIGN = (
    Path(_ORCH).parent
    / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
)


@pytest.fixture(autouse=True)
def _isolate_condition_gate_from_nonbuild_unit_tests(monkeypatch):
    """The real compiler-backed gate is covered by its production API suite."""
    monkeypatch.setattr(
        W, "_preflight_condition_gate",
        lambda _source_root, _patch: {"admission": {"admitted": True}},
    )


def test_condition_gate_preflight_dominates_candidate_evaluation():
    source = inspect.getsource(W.run_sweep)
    assert source.index("_preflight_condition_gate") < source.index("active_screening")


def test_screening_forwards_stock_genome_protocol():
    source = Path(W.__file__).read_text(encoding="utf-8")
    assert source.count("protocol=_genome(0).protocol") == 1

# ==== C++ 比較式 → Python モデルの機械導出 ====================================
# 生成器 (_one/_two/_mk) が出す式形のみ受理する。受理できない式は即 fail
# (パーサが緩いと検査対象がすり替わる — fails-closed)。

_MEMBER_IDX = {"storage_": 0, "key_": 1, "rcdptr_": 2}


def _parse_cmp(expr: str):
    m = re.fullmatch(r"([ab])\.(storage_|key_|rcdptr_) < ([ab])\.(storage_|key_|rcdptr_)",
                     expr.strip())
    assert m, f"想定外の比較式: {expr!r}"
    assert m.group(2) == m.group(4), f"別メンバ間比較は列挙空間にない: {expr!r}"
    idx = _MEMBER_IDX[m.group(2)]
    pair = (m.group(1), m.group(3))
    if pair == ("a", "b"):
        return lambda a, b: a[idx] < b[idx]
    if pair == ("b", "a"):
        return lambda a, b: b[idx] < a[idx]
    raise AssertionError(f"a/b の組が不正: {expr!r}")


def model_from_impl(impl: str):
    """implementation 文字列から比較関数 (a,b)->bool を導出する。a/b は (S,K,P) タプル。"""
    body = " ".join(impl.split())
    m = re.search(r"return (.+?);", body)
    assert m, f"return 文が見つからない: {impl!r}"
    expr = m.group(1).strip()
    if expr == "false":
        return lambda a, b: False
    tern = re.fullmatch(r"a\.storage_ != b\.storage_ \? (.+?) : (.+)", expr)
    if tern:
        f1, f2 = _parse_cmp(tern.group(1)), _parse_cmp(tern.group(2))
        return lambda a, b: f1(a, b) if a[0] != b[0] else f2(a, b)
    return _parse_cmp(expr)


# 有限モデル空間: S∈{0,1}, K∈{"a","b"}, P∈{1,2,3} の全 12 要素 (重複 (S,K,P) なし —
# 実データでも rcdptr は一意)。SWO 公理は全対 (12^2, 推移は 12^3) を総当たり。
_SPACE = [(s, k, p) for s in (0, 1) for k in ("a", "b") for p in (1, 2, 3)]


def _assert_swo(f, name: str):
    for x in _SPACE:
        assert not f(x, x), f"{name}: 非反射性違反 comp(x,x)=true at {x}"
    for x, y in itertools.product(_SPACE, repeat=2):
        if f(x, y):
            assert not f(y, x), f"{name}: 非対称性違反 at {x},{y}"
    for x, y, z in itertools.product(_SPACE, repeat=3):
        if f(x, y) and f(y, z):
            assert f(x, z), f"{name}: 推移性違反 at {x},{y},{z}"

    def equiv(x, y):
        return not f(x, y) and not f(y, x)
    for x, y, z in itertools.product(_SPACE, repeat=3):
        if equiv(x, y) and equiv(y, z):
            assert equiv(x, z), f"{name}: 同値の推移性違反 at {x},{y},{z}"


def test_all_candidates_are_swo():
    for name, _cat, impl in W.CANDIDATES:
        _assert_swo(model_from_impl(impl), name)


def test_sk_aa_matches_python_tuple_order():
    """sk_aa (coder iter1 同値点 = stock 順序) は (S,K) タプル辞書式と完全一致する
    (導出パーサ自体のクロスチェック)。"""
    f = model_from_impl(next(i for n, _c, i in W.CANDIDATES if n == "sk_aa"))
    for x, y in itertools.product(_SPACE, repeat=2):
        assert f(x, y) == ((x[0], x[1]) < (y[0], y[1]))


# ==== category の意味論 (実 workload 制約下の tie 有無) ========================
# 実 workload 制約: 単一 storage (YCSB)・key 一意・rcdptr 一意。K↔P の対応は
# 単調とは限らない (アドレス順 ≠ キー順) ので P はシャッフルして置く。

_WORKLOAD_SPACE = [(0, "a", 2), (0, "b", 3), (0, "c", 1)]


def test_category_semantics_under_workload_constraints():
    for name, cat, impl in W.CANDIDATES:
        f = model_from_impl(impl)
        has_tie = any(not f(x, y) and not f(y, x)
                      for x, y in itertools.combinations(_WORKLOAD_SPACE, 2))
        if cat == "full-order":
            assert not has_tie, f"{name}: full-order なのに tie が残る"
        else:
            assert has_tie, f"{name}: degenerate なのに tie が無い"


# ==== 列挙の構造 ==============================================================

def test_candidate_names_unique_and_counts():
    names = [n for n, _c, _i in W.CANDIDATES]
    assert len(names) == len(set(names)) == 15
    assert len([n for n, c, _i in W.CANDIDATES if c == "degenerate"]) == 3
    assert W.STOCK_NAME not in names
    assert W.CODER_EQUIV in names
    assert W.candidate_names()[0] == W.STOCK_NAME
    assert len(W.candidate_names()) == 16


def test_nosort_uses_anonymous_params():
    """nosort は引数名を持たない (-Werror=unused-parameter でビルド不能になるため。
    機構レンズ must-fix、GCC13 実測)。"""
    impl = next(i for n, _c, i in W.CANDIDATES if n == "nosort")
    assert "return false;" in impl
    assert re.search(r"WriteElement<Tuple>&\s*[ab]\b", impl) is None, \
        "nosort に引数名が付いている (未使用引数警告でビルドが落ちる)"


def test_no_comments_in_implementations():
    """src_token は preprocess 後ハッシュ (コメント除去) — コメントだけ違う 2 候補は
    同一 variant に潰れて WAL replay で誤 skip される (機構レンズ nit)。"""
    for name, _cat, impl in W.CANDIDATES:
        assert "//" not in impl and "/*" not in impl, f"{name}: コメントを含む"


def test_implementations_reference_only_allowed_members():
    """closed-region 契約: 参照可能メンバは storage_/key_/rcdptr_ のみ (a./b. 経由)。"""
    for name, _cat, impl in W.CANDIDATES:
        for m in re.finditer(r"\b([ab])\.(\w+)", impl):
            assert m.group(2) in _MEMBER_IDX, f"{name}: 契約外メンバ {m.group(0)}"


# ==== 検疫通過 (fixture 骨格、write=False) =====================================

_TEMPLATE = """#pragma once
#include "storage.hh"

class TxExecutor {
 public:
  bool validationPhase() {
#ifndef SORT_VARIANT
#error "SORT_VARIANT must be defined"
#endif
    // EVOLVE-BLOCK-BEGIN silo-writeset-sort
    // izanagi Phase 3 (D41/phase3.md): coder の編集面はこの #if 枝のみ。
#if SORT_VARIANT
    sort(write_set_.begin(), write_set_.end());
#else
    sort(write_set_.begin(), write_set_.end());
#endif
    // EVOLVE-BLOCK-END silo-writeset-sort
    return true;
  }
};
"""


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s6sweep_")
    full = os.path.join(d, W.S.SOURCE_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def test_all_candidates_pass_quarantine():
    d = _mk_template_dir()
    for name, _cat, impl in W.CANDIDATES:
        res, _b, _e, _wd = L.quarantine(d, impl, marker_id=W.S.MARKER_ID,
                                        source_rel=W.S.SOURCE_REL, write=False)
        assert res.passed, f"{name}: 機械生成候補が検疫 reject — {res.reason}"


def test_s6_reject_writer_fails_closed_on_unframed_tail():
    layout = _tmp_layout()
    with open(layout.wal_file, "wb") as stream:
        stream.write(b'{"unframed":')
    before = open(layout.wal_file, "rb").read()
    implementation = W.CANDIDATES[0][2]
    rejection = L.DiffQuarantineResult(
        passed=False, digest={"subtype": "fixture-reject"},
    )

    try:
        L.record_diff_reject(
            layout, W._genome(1), implementation, rejection, env_tag=W.ENV_TAG,
        )
        assert False, "s6 reject が unframed tail へ追記されてはならない"
    except wal.WalAppendError as exc:
        assert exc.phase == "tail-gate"
        assert isinstance(exc.cause, wal.WalFramingError)

    assert open(layout.wal_file, "rb").read() == before
    assert not any(name.startswith("wal-tail-repair-")
                   for name in os.listdir(layout.runs_dir))


# ==== campaign identity =======================================================

def test_workload_and_trial_baked_into_identity():
    """balanced / write-heavy / remeasure が別 campaign_id に解決される (identity の
    ハッシュ分離。spec_slug ラベルだけに依存しない — 機構レンズ should-fix)。"""
    ca = ident.campaign_id(W.config_for("balanced"))
    cb = ident.campaign_id(W.config_for("write-heavy"))
    cr = ident.campaign_id(W.config_for("balanced", trial=f"{W.TRIAL_MAIN}-remeasure1"))
    assert len({str(ca), str(cb), str(cr)}) == 3


def test_config_wires_s2_verify_and_space_provenance():
    cfg = W.config_for("balanced")
    assert cfg.search_config[SEARCH_CONFIG_VERIFY_KEY] == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config["generator"] == W.SPACE_VERSION
    assert cfg.search_config["ycsb"] == W.WORKLOADS["balanced"]
    assert cfg.ccbench_commit == W.PIN


def test_perf_is_p2_2_operating_point():
    """計測規模は p2_2 確定動作点 (配線規模 t4/100k ではない — 読解 2026-07-10 の
    決定的事実: 配線規模では contention が弱く施錠順序の影響が観測できない)。"""
    p = W.perf_for("balanced")
    assert (p.records, p.threads, p.extime, p.reps) == (1_000_000, 48, 3, 5)


def test_genome_flags():
    assert W._genome(0).flags["SORT_VARIANT"] == 0
    assert W._genome(1).flags["SORT_VARIANT"] == 1
    assert W._genome(1).flags["BACK_OFF"] == 1


# ==== 実装後レビューの是正 (2026-07-10) =======================================

def _tmp_layout():
    from orchestrator.campaign.layout import CampaignLayout
    return CampaignLayout(root=tempfile.mkdtemp(prefix="izanagi_s6sweep_lay_")).ensure()


def _install_public_reject_sweep_fakes(monkeypatch, layout):
    from orchestrator.campaign import patchharness

    root = tempfile.mkdtemp(prefix="izanagi_s6_public_sweep_")
    os.makedirs(os.path.join(root, "external", "ccbench"))
    rejection = L.DiffQuarantineResult(
        passed=False, digest={"subtype": "fixture-reject"},
    )
    monkeypatch.setattr(W, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(W, "_repo_root", lambda: root)
    monkeypatch.setattr(W, "campaign_layout", lambda _campaign_id: layout)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_args: None)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        L, "quarantine", lambda *_args, **_kwargs: (rejection, "", "", ""),
    )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_fresh_reject_then_next_candidate_resumes(monkeypatch):
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    first, second = [name for name, _category, _impl in W.CANDIDATES[:2]]

    first_result = W.run_sweep(
        "balanced", names=[first], isolate=False, log=lambda _line: None,
    )
    assert first_result[first]["outcome"] == "quarantine-reject"
    cfg = W.config_for("balanced")
    assert wal.read_lock(layout) == build_v2_lock(ident.canonical_preimage(cfg))

    resumed = W.run_sweep(
        "balanced", names=[second], isolate=False, log=lambda _line: None,
    )
    assert resumed[second]["outcome"] == "quarantine-reject"
    assert len(wal.read_records(layout)) == 4


def test_public_sweep_recovers_real_wal_start_before_quarantine_write(monkeypatch):
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    cfg = W.config_for("balanced")
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    wal.log(layout, "crashed-v", "build_start", W.ENV_TAG, {
        "build_attempt_id": "crashed-attempt",
    })
    candidate = W.CANDIDATES[0][0]

    result = W.run_sweep(
        "balanced", names=[candidate], isolate=False, log=lambda _line: None,
    )
    assert result[candidate]["outcome"] == "quarantine-reject"
    records = wal.read_records(layout)
    assert records[0].payload["build_attempt_id"] == "crashed-attempt"
    assert records[1].stage == "abort"
    assert records[1].payload == {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": "crashed-attempt",
    }


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes(
        monkeypatch):
    """public sweep→実 pipeline admission 境界で exact class 差を固定する。"""
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    machine_name = W.CANDIDATES[0][0]
    seen = []
    passed = SimpleNamespace(passed=True)
    expected_pin = "6810666"  # repo policy から逆算しない独立 pin

    def evidence_for(genome, commit, source_root):
        assert commit == expected_pin == W.PIN
        machine = genome.flags["SORT_VARIANT"] == 1
        return SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(source_root),
            ccbench_commit=expected_pin,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="6" * 64 if machine else STOCK,
            source_bytes_sha256="7" * 64,
            tracked_clean=not machine,
            tracked_diff_sha256=(
                "8" * 64 if machine else EMPTY_TRACKED_DIFF_SHA256
            ),
            tracked_paths=("cc/silo/transaction.cc",) if machine else (),
        )

    def resolve(genome, commit, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir).src_token

    def resolve_evidence(genome, commit, *, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir)

    def stop_at_build(_genome, _commit, trace, **kwargs):
        assert trace is True
        receipt = kwargs["admission"].as_wal_receipt()
        seen.append((
            kwargs["admission"].provenance,
            receipt["generator_receipt"] is not None,
            kwargs["build_context"],
        ))
        raise RuntimeError("stop after admission boundary")

    def run_through_pipeline(cfg, genomes, perf, env_tag, clocks_per_us, **kwargs):
        result = pipeline.evaluate(
            genomes[0], layout, env_tag, cfg.ccbench_commit, perf,
            clocks_per_us, do_bench=False, log=lambda _line: None,
            numactl=kwargs["numactl"],
            authorization_contract=kwargs["authorization_contract"],
            ccbench_dir=kwargs["ccbench_dir"],
            cache_root=kwargs["cache_root"],
            build_context=kwargs["build_context"],
            capability_resolver=kwargs["capability_resolver"],
        )
        return SimpleNamespace(results=[result])

    monkeypatch.setattr(L, "quarantine", lambda *_a, **_k: (passed, "", "", ""))
    monkeypatch.setattr(W.source_digest, "resolve", resolve)
    monkeypatch.setattr(pipeline.source_digest, "resolve_evidence", resolve_evidence)
    monkeypatch.setattr(pipeline.buildcache, "build", stop_at_build)
    monkeypatch.setattr(W, "run_campaign", run_through_pipeline)
    W.run_sweep("balanced", names=[W.STOCK_NAME, machine_name], isolate=False,
                log=lambda _line: None)
    assert [(provenance, has_generator) for provenance, has_generator, _ in seen] == [
        (BuildProvenance.STOCK_BASELINE, False),
        (BuildProvenance.MACHINE_GENERATED, True),
    ]
    assert seen[0][2] is seen[1][2]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_does_not_turn_admission_error_into_driver_error(monkeypatch):
    """F4: admission 配線失敗は候補隔離の broad except を通過して停止する。"""
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)

    def fail_admission(*_args, **_kwargs):
        raise BuildAdmissionError("injected admission failure")

    monkeypatch.setattr(W, "_eval_one", fail_admission)
    with pytest.raises(BuildAdmissionError, match="injected admission failure"):
        W.run_sweep("balanced", names=[W.CANDIDATES[0][0]], isolate=False,
                    log=lambda _line: None)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_driver_error_provenance_never_reflects_candidate_bytes(monkeypatch):
    """固定化された上流例外を S6 の error・log・永続 JSON まで通して非反射を固定する。"""
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    name = W.CANDIDATES[0][0]
    sentinel = "SENTINEL_S6_CANDIDATE_BYTES_7f39"

    def fail_with_sanitized_candidate_error(*_args, **_kwargs):
        coder = L.CoderProposal(
            axis=L.MARKER_ID,
            value=17.0,
            implementation=f"double now_backoff = compute_{sentinel}();",
        )
        # Candidate bytes enter the real attribution validator, whose exception
        # projection is fixed before S6's broad per-candidate isolation sees it.
        L.assert_value_literal_consistent(coder)
        raise AssertionError("fixed validator was expected to stop")

    monkeypatch.setattr(W, "_eval_one", fail_with_sanitized_candidate_error)
    log_lines = []
    result = W.run_sweep(
        "balanced", names=[name], isolate=False, log=log_lines.append,
    )
    provenance_path = Path(
        layout.root, "reports", "s6_sort_sweep_provenance.json",
    )
    persisted = provenance_path.read_text(encoding="utf-8")

    assert result[name]["outcome"] == "driver-error"
    assert result[name]["error"]
    for projection in (result[name]["error"], "\n".join(log_lines), persisted):
        assert sentinel not in projection


def test_eval_one_propagates_context_and_source_capability_to_build_entry(monkeypatch):
    """検疫通過後の build は policy context と source-bound resolver を受ける。"""
    from orchestrator.campaign import patchharness

    layout = _tmp_layout()
    name = W.CANDIDATES[0][0]
    context = W.build_run_context(generator_id=W.GeneratorId.S6_SORT_SWEEP)
    passed = SimpleNamespace(passed=True)
    seen = []
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        L, "quarantine", lambda *_a, **_k: (passed, "", "", "fixture"),
    )
    monkeypatch.setattr(W.source_digest, "resolve", lambda *_a, **_k: "a" * 64)

    def build_entry(*_args, **kwargs):
        seen.append((kwargs["build_context"], kwargs["capability_resolver"]))
        return SimpleNamespace(
            results=[SimpleNamespace(certified=True, aborted=False)]
        )

    monkeypatch.setattr(W, "run_campaign", build_entry)
    result = W._eval_one(
        name, W.config_for("balanced"), W.perf_for("balanced"), layout,
        "/fixture/sub", "/fixture/template.patch", "", build_context=context,
        log=lambda _line: None,
    )
    assert result["outcome"] == "certified"
    assert seen[0][0] is context
    assert callable(seen[0][1])


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_partial_write_eio_stops_before_next_candidate(
        monkeypatch):
    layout = _tmp_layout()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    names = [name for name, _category, _impl in W.CANDIDATES[:2]]
    real_write = wal.os.write
    wal_calls = []

    def partial_then_eio(fd, data):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        if path == layout.wal_file:
            wal_calls.append(len(data))
            if len(wal_calls) == 1:
                return real_write(fd, data[:7])
            raise OSError(errno.EIO, "injected partial WAL write EIO")
        return real_write(fd, data)

    monkeypatch.setattr(wal.os, "write", partial_then_eio)
    with pytest.raises(wal.WalAppendError) as excinfo:
        W.run_sweep(
            "balanced", names=names, isolate=False, log=lambda _line: None,
        )
    assert excinfo.value.phase == "write"
    assert excinfo.value.written_bytes == 7 < excinfo.value.total_bytes
    assert len(wal_calls) == 2
    assert Path(layout.wal_file).read_bytes() and b"\n" not in Path(layout.wal_file).read_bytes()


def test_replay_outcome_distinguishes_commit_and_abort(monkeypatch):
    """WAL replay skip 時、前 run の commit/abort を区別する (一律 'replayed' だと abort 点
    が完了サマリ/exit code から消える — 実装後レビュー should-fix)。"""
    context = W.build_run_context(generator_id=W.GeneratorId.S6_SORT_SWEEP)
    states = {
        "v-commit": SimpleNamespace(
            committed=True, aborted=False, last_terminal=object()),
        "v-abort": SimpleNamespace(
            committed=False, aborted=True, last_terminal=object()),
    }
    records = [SimpleNamespace(variant="v-commit", stage=W.STAGE_COMMIT)]
    monkeypatch.setattr(
        W, "_replay_snapshot",
        lambda _layout, observed: (
            records, states if observed.policy == context.policy else {}, "a" * 64,
        ),
    )
    monkeypatch.setattr(
        W, "require_persisted_certified_commit",
        lambda records, commit, *, campaign_lock_sha256: commit,
    )
    assert W._replay_outcome(None, "v-commit", context) == "replayed-certified"
    assert W._replay_outcome(None, "v-abort", context) == "replayed-aborted"
    assert W._replay_outcome(None, "v-none", context) == "replayed-unknown"


@pytest.mark.parametrize("consumer", ["s6"], ids=["s6"])
def test_replay_outcome_requires_persisted_certification(
        monkeypatch, consumer):
    layout = _tmp_layout()
    Path(layout.lock_file).write_text(
        json.dumps({"fixture": "s6 replay"}), encoding="utf-8",
    )
    attempt_id = "s6-replay-attempt"
    W.wal.log(layout, "v", "verify_done", W.ENV_TAG, {
        "build_attempt_id": attempt_id,
        "verdict": "serializable",
        "certified": True,
        "anomalies": 1,
        "workload": {"tag": "legacy"},
    })
    receipt_support.log_receipted_commit(
        layout, "v", W.ENV_TAG, {"build_attempt_id": attempt_id},
        operation_identity=attempt_id,
    )
    records = W.wal.read_records(layout)
    states = W.wal.replay_admitted_records(records)
    lock_sha256 = hashlib.sha256(Path(layout.lock_file).read_bytes()).hexdigest()
    monkeypatch.setattr(
        W, "_replay_snapshot",
        lambda _layout, _context: (records, states, lock_sha256),
    )
    context = W.build_run_context(generator_id=W.GeneratorId.S6_SORT_SWEEP)

    with pytest.raises(W.ArtifactAdmissionError, match="anomalies"):
        W._replay_outcome(layout, "v", context)

    assert consumer == "s6"


def test_provenance_merges_existing_entries():
    """部分 --names 実行が既存の name→variant_id 対応を truncate しない (merge)。"""
    lay = _tmp_layout()
    W._write_provenance(lay, "balanced", W.TRIAL_MAIN,
                        {"k_asc": {"variant_id": "v1", "category": "full-order",
                                   "src_token": "s1", "outcome": "certified"}})
    W._write_provenance(lay, "balanced", W.TRIAL_MAIN,
                        {"stock": {"variant_id": "v0", "category": "stock",
                                   "src_token": "stock", "outcome": "certified"}})
    import json as _json
    with open(os.path.join(lay.root, "reports", "s6_sort_sweep_provenance.json"),
              encoding="utf-8") as f:
        doc = _json.load(f)
    assert set(doc["entries"]) == {"k_asc", "stock"}
    assert doc["entries"]["k_asc"]["variant_id"] == "v1"
    # stock の実効 comparator が自蔵される (PIN+patch を辿らなくても監査できる)
    assert "operator<" in doc["entries"]["stock"]["implementation"]


def test_floor_uncalibrated_fails_closed():
    """退化点は stock 非依存で無条件 True。比較材料欠損も True (fails-closed)。"""
    degen = {"category": "degenerate", "abort_rate": 0.01}
    ok = {"category": "full-order", "abort_rate": 0.10}
    calm = {"category": "full-order", "abort_rate": 0.05}
    stock = {"category": "stock", "abort_rate": 0.04}
    assert W._floor_uncalibrated(degen, None)          # stock 欠落でも退化点は True
    assert W._floor_uncalibrated(degen, stock)
    assert W._floor_uncalibrated(ok, stock)            # 0.10 > 2.0 * 0.04
    assert not W._floor_uncalibrated(calm, stock)      # 0.05 <= 0.08
    assert W._floor_uncalibrated(ok, None)             # stock 欠落 → fails-closed
    assert W._floor_uncalibrated({"category": "full-order", "abort_rate": None}, stock)


def _fixture_git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("git is required for verifier epoch fixtures")
    completed = subprocess.run(
        [executable, "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        pytest.fail(
            "git fixture command failed: "
            f"args={args!r} rc={completed.returncode} "
            f"stderr={completed.stderr.decode('utf-8', errors='replace')!r}"
        )
    return completed.stdout


def _install_fixed_e1_closure(
    root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """単位 A と同じ固定 bytes の exact 14-path closure を用意する。"""
    repo = root / "closure-repo"
    repo.mkdir()
    _fixture_git(repo, "init", "-q")
    for index, relative in enumerate(
        campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS, start=1,
    ):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"epoch closure fixture {index}\n".encode("ascii"))
    _fixture_git(
        repo, "add", "--", *campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
    )
    _fixture_git(
        repo,
        "-c", "user.email=epoch-fixture@example.invalid",
        "-c", "user.name=epoch fixture",
        "commit", "-q", "-m", "record closure A",
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)


def _install_post_policy_screen_fixture(layout, root, monkeypatch):
    """固定 E1 closure と receipt に束縛した合成 sweep WAL を作る。"""
    context = build_run_context(generator_id=GeneratorId.S6_SORT_SWEEP)
    identity_preimage = campaign_lock.canonical_json({
        "ccbench_commit": W.PIN,
        "search_config": {
            "records": 1,
            "threads": 1,
            "build_admission": dict(context.policy.as_preimage()),
        },
        "search_tag": "test",
        "spec_content": "test",
        "trial": "test",
    })
    _install_fixed_e1_closure(root, monkeypatch)
    lock_text = build_v2_lock(identity_preimage)
    Path(layout.lock_file).write_text(lock_text, encoding="utf-8")
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    assert decoded.authority is not None
    variants = {}
    for ordinal, label in enumerate(("screen", "certified"), start=1):
        genome = W._genome(1)
        src_token = str(ordinal) * 64
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(layout.root),
            ccbench_commit=W.PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token=src_token,
            source_bytes_sha256=str(ordinal + 2) * 64,
            tracked_clean=False,
            tracked_diff_sha256=str(ordinal + 4) * 64,
            tracked_paths=("cc/silo/transaction.cc",),
        )
        generator = attest_generator_output(
            context,
            evidence,
            generator_input_sha256=hashlib.sha256(
                label.encode("utf-8")
            ).hexdigest(),
        )
        receipt = derive_build_admission(
            context, evidence, generator_receipt=generator,
        ).as_wal_receipt()
        variant = pipeline.variant_id(genome, src_token)
        attempt = f"screen-fixture-{label}"
        variants[label] = (variant, attempt, receipt)
        W.wal.log(layout, variant, "build_start", W.ENV_TAG, {
            "genome": genome.canonical(),
            "src_token": src_token,
            "build_attempt_id": attempt,
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })
        W.wal.log(layout, variant, "build_done", W.ENV_TAG, {
            "build_attempt_id": attempt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })
    return variants, decoded.authority.environment_contract_sha256


def test_screen_reject_row_and_report_hide_uncertified_bench_values(
    monkeypatch, tmp_path,
):
    """BENCH_DONE は certified の証拠ではない。screen 数値は WAL にだけ保持する。"""
    historical = require_admitted_campaign(
        _REAL_E0_CAMPAIGN,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert historical.campaign_verifier_epoch.state == "E0"
    assert historical.records
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        W._load_rows(_REAL_E0_CAMPAIGN, {})

    layout = _tmp_layout()
    variants, contract_sha256 = _install_post_policy_screen_fixture(
        layout, tmp_path, monkeypatch,
    )
    screen_variant, screen_attempt, screen_receipt = variants["screen"]
    certified_variant, certified_attempt, certified_receipt = (
        variants["certified"]
    )
    W.wal.log(layout, screen_variant, W.STAGE_BENCH_DONE, W.ENV_TAG, {
        "median_tps": 12345,
        "cv": 0.01,
        "unstable": True,
        "leading_indicators": {
            "abort_rate": 0.12,
            "ipc": 1.23,
            "llc_miss_rate": 0.34,
        },
    })
    W.wal.log(layout, screen_variant, W.STAGE_ABORT, W.ENV_TAG, {
        "reason": pipeline.SCREEN_REJECTION_REASON,
        "screen": {"median_tps": 12345},
        "build_attempt_id": screen_attempt,
        "build_admission_receipt_sha256": screen_receipt["receipt_sha256"],
    })
    W.wal.log(layout, certified_variant, W.STAGE_BENCH_DONE, W.ENV_TAG, {
        "median_tps": 6789,
        "cv": 0.02,
        "unstable": False,
        "leading_indicators": {
            "abort_rate": 0.05,
            "ipc": 0.98,
            "llc_miss_rate": 0.21,
        },
    })
    W.wal.log(layout, certified_variant, "verify_done", W.ENV_TAG, {
        "build_attempt_id": certified_attempt,
        "verdict": "serializable",
        "certified": True,
        "anomalies": 0,
        "workload": {"tag": "legacy"},
    })
    # post-policy COMMIT は attempt と receipt SHA を必須にする。
    receipt_support.log_receipted_commit(
        layout, certified_variant, W.ENV_TAG, {
        "build_attempt_id": certified_attempt,
        "build_admission_receipt_sha256": certified_receipt["receipt_sha256"],
        COMMIT_CONTRACT_SHA256_KEY: contract_sha256,
        }, operation_identity=certified_attempt,
    )

    entries = {
        "screened-out": {"variant_id": screen_variant, "category": "full-order"},
        "certified": {"variant_id": certified_variant, "category": "full-order"},
    }
    rows = {r["name"]: r for r in W._load_rows(layout, entries)}
    rejected = rows["screened-out"]
    assert rejected["certified"] is False
    assert rejected["abort_reason"] == pipeline.SCREEN_REJECTION_REASON
    assert {
        key: rejected[key]
        for key in ("median_tps", "cv", "abort_rate", "ipc", "llc_miss_rate")
    } == {
        "median_tps": None,
        "cv": None,
        "abort_rate": None,
        "ipc": None,
        "llc_miss_rate": None,
    }
    assert rejected["unstable"] is False
    assert rows["certified"]["certified"] is True
    assert rows["certified"]["median_tps"] == 6789

    abort_payload = next(
        r.payload for r in W.wal.read_records(layout)
        if r.variant == screen_variant and r.stage == W.STAGE_ABORT
    )
    assert abort_payload["screen"]["median_tps"] == 12345

    reports = os.path.join(layout.root, "reports")
    os.makedirs(reports, exist_ok=True)
    with open(os.path.join(reports, "s6_sort_sweep_provenance.json"),
              "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f)
    monkeypatch.setattr(W, "campaign_layout", lambda _campaign_id: layout)

    path = W.report("balanced", log=lambda _line: None)
    assert path is not None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    assert "受理目的**: `CERTIFIED_ACCEPTANCE`" in text
    assert "campaign_verifier_epoch**: `E1:" in text
    assert "screening 正常棄却" in text
    assert pipeline.SCREEN_REJECTION_REASON in text
    assert "12345" not in text.replace(",", "")


def test_real_legacy_sort_campaign_cannot_be_certified_by_commit_only():
    campaign = (Path(_ORCH).parent / "output" / "campaigns" /
                "p3-s5-sort-loop-s5-sort-autonomous-3be89e0d")
    with pytest.raises(CampaignNotAdmitted, match="legacy-unclassified"):
        W._load_rows(str(campaign), {})
