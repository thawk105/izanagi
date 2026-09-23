# -*- coding: utf-8 -*-
"""s8a_trigger_sweep (段 8a D 段: trigger-gating 機械列挙 sweep) の単体テスト。

build/verify/bench を伴わない機械部分のみ (test_s6_sort_sweep.py と対称の様式):
  1. **述語生成の構成的安全** — kUnset 項 (fail-safe 契約) の必在・1 行 (hole が単一行
     のため複数行は検疫で落ちる)・構文契約の禁止トークン (SYNTAX_CONTRACT_FORBIDDEN)
     不使用・enum 等値比較 + OR のみの形をパーサで機械検査 (受理できない形は即 fail、
     fails-closed)。
  2. 列挙の全単射 — 部分集合↔名前↔述語が一意、2^N + ident_all + stock の点数。
  3. 検疫通過 — 全候補が diff 検疫 (フレーム不可触・hole 封じ込め) を write=False で通る。
  4. identity — workload/trial/実効ビット集合が campaign_id に焼かれ分離される。
  5. 頻度実測 (必須前提 (a)) 消費の fails-closed — JSON 不在・部分実行・保存則破れ・
     未知要因で停止する。
  6. floor 判定不能 (fails-closed)・replay 区別・provenance merge (s6 裁定の踏襲)。
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

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

import pytest                                                      # noqa: E402

from orchestrator.campaign import axis_trigger_gating as T                      # noqa: E402
from orchestrator.campaign import campaign_lock, contract_loader_binding        # noqa: E402
from orchestrator.campaign import ident                                         # noqa: E402
from orchestrator.campaign import pipeline                                      # noqa: E402
from orchestrator.campaign import p3_s4_loop as L                               # noqa: E402
from orchestrator.campaign import s8a_trigger_sweep as W                        # noqa: E402
from orchestrator.campaign import s8a_trigger_coverage as coverage               # noqa: E402
from orchestrator.campaign import s8a_trigger_freq as frequency                  # noqa: E402
from orchestrator.campaign import wal                                           # noqa: E402
from orchestrator.campaign.artifact_admission import (                          # noqa: E402
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
from orchestrator.campaign.model import (                                       # noqa: E402
    COMMIT_CONTRACT_SHA256_KEY,
    STAGE_BUILD_START,
)
from orchestrator.campaign.layout import CampaignLayout                         # noqa: E402
from orchestrator.campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from orchestrator.campaign.pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402
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


@pytest.mark.parametrize("module", [coverage, frequency])
def test_trigger_characterization_gate_dominates_first_build(module):
    source = inspect.getsource(module.main)
    assert source.index("_preflight_condition_gates") < source.index("_build(")


@pytest.mark.parametrize(("macro", "default", "directive"), [
    ("IZANAGI_BREAK_TRIGGER_MISATTR", None, "#ifdef IZANAGI_BREAK_TRIGGER_MISATTR"),
    ("BACKOFF_TRIGGER_GATING", 0, "#if BACKOFF_TRIGGER_GATING"),
], ids=["misattr", "gating"])
def test_coverage_condition_gate_passes_exact_factory_pair(monkeypatch, tmp_path, macro, default, directive):
    gate = coverage.condition_meaning_gate
    captured = object()
    record = SimpleNamespace(canonical_json=lambda: "{}")
    admission = SimpleNamespace(admitted=True, canonical_json=lambda: "{}")
    observed = {}

    def capture(source, *, configure_args):
        observed["capture"] = (source, configure_args)
        return captured

    def supply(inputs, **kwargs):
        observed["supply"] = (inputs, kwargs)
        return record

    def meaning(inputs, **kwargs):
        observed["meaning"] = (inputs, kwargs)
        return record

    def family(supplies, meanings, **kwargs):
        observed["family"] = (supplies, meanings, kwargs)
        return admission

    monkeypatch.setattr(gate, "capture_define_inputs", capture)
    monkeypatch.setattr(gate, "evaluate_define_supply_effectuation", supply)
    monkeypatch.setattr(gate, "evaluate_define_runtime_meaning", meaning)
    monkeypatch.setattr(gate, "require_condition_gate_family", family)
    result = coverage._require_condition_gate(
        str(tmp_path), driver_id="coverage-test", macro=macro,
        configure_args=["-DCCBENCH_BACKOFF_TRIGGER_GATING=1"],
    )
    assert result == {"supply": {}, "meaning": {}, "admission": {}}
    assert observed["capture"] == (str(tmp_path), ("-DCCBENCH_BACKOFF_TRIGGER_GATING=1",))
    assert observed["supply"][0] is observed["meaning"][0] is captured
    request = observed["supply"][1]["request"]
    assert observed["meaning"][1]["request"] is request
    assert request.macro == macro
    assert request.requested_value == 1
    assert request.default_value == default
    declaration = observed["meaning"][1]["declaration"]
    assert type(declaration) is gate.ConditionalBranchMeaningDeclaration
    assert declaration.macro == macro
    assert declaration.source_rel == "cc/silo/transaction.cc"
    assert declaration.start_directive == directive
    assert observed["family"] == ([record], [record], {"use_class": "raw-measurement"})


def test_screening_forwards_ident_baseline_genome_protocol():
    source = Path(W.__file__).read_text(encoding="utf-8")
    assert source.count("protocol=_genome(1).protocol") == 1

# 頻度実測の予想結果 (シート導出: YCSB では node/absent 構造ゼロ)。テストは実測に
# 依存しない — 代表として 3 ビットの実効集合で列挙の機械性質を検査する。
EFF3 = ["lock-conflict", "readvali-tid", "readvali-locked"]
_CHARACTERIZATION_GENOME = (
    "silo|ADD_ANALYSIS=1,BACKOFF_TRIGGER_GATING=1,BACK_OFF=1,"
    "NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
)
_CHARACTERIZATION_PIN = "6810666"
_T2304_ADMISSION_POLICY_SHA256 = (
    "db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a"
)
_T816_ADMISSION_POLICY_SHA256 = (
    "949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44"
)
_ADMISSION_POLICY_SHA256 = (
    "baec529678afab7712557eec0b97cb8f0ddc6b8f2f7cc4e7c9fd1eecce3cb941"
)
_PRE_T343_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-c2d838b8",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8",
}
_T343_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-fc683dde",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-5569ad76",
}
_T816_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-82061ef6",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-eaa6d33e",
}
_T2304_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-8ee9d0be",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-49fa575c",
}
_T2858_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-95e18297",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-4766d116",
}
_T530_S8A_CAMPAIGN_IDS = {
    "balanced": "p3-s8a-trigger-sweep-balanced-sweep-0b2966f0",
    "write-heavy": "p3-s8a-trigger-sweep-write-heavy-sweep-27b6af7c",
}

# ==== 述語生成の構成的安全 =====================================================

_TERM_RE = re.compile(
    r"izanagi_abort_reason_ == IzanagiAbortReason::k[A-Za-z]+")


def _parse_predicate(impl: str):
    """生成器が出す形 (1 代入文、enum 等値比較の OR 連鎖) のみ受理し、項の enum 値
    リストを返す。受理できない形は即 fail (fails-closed)。"""
    assert "\n" not in impl, f"述語が複数行 (hole は単一行): {impl!r}"
    m = re.fullmatch(r"izanagi_gate_pass = (.+);", impl)
    assert m, f"代入文の形でない: {impl!r}"
    terms = [t.strip() for t in m.group(1).split("||")]
    for t in terms:
        assert _TERM_RE.fullmatch(t), f"想定外の項: {t!r}"
    return [t.rsplit("::", 1)[1] for t in terms]


def test_predicates_are_single_assignment_with_unset_first():
    for name, _cat, impl in W.candidates(EFF3):
        enums = _parse_predicate(impl)
        assert enums[0] == "kUnset", f"{name}: kUnset 項 (fail-safe 契約) が先頭にない"
        assert len(enums) == len(set(enums)), f"{name}: 項の重複"


def test_predicates_avoid_forbidden_tokens():
    """構文契約の禁止リスト (D48 決定 2 → axis_trigger_gating.SYNTAX_CONTRACT_FORBIDDEN)
    のトークンが機械生成述語に現れない。"""
    for name, _cat, impl in W.candidates(EFF3):
        for tok in T.SYNTAX_CONTRACT_FORBIDDEN:
            assert tok not in impl, f"{name}: 禁止トークン {tok!r} を含む"


def test_predicates_have_no_comments_or_directives():
    """コメント (src_token は preprocess 後ハッシュで消える罠) と生の preprocessor
    directive (render_hole の行頭 # 二次検査) を含まない。"""
    for name, _cat, impl in W.candidates(EFF3):
        assert "//" not in impl and "/*" not in impl, f"{name}: コメント混入"
        assert not impl.lstrip().startswith("#"), f"{name}: 行頭 directive"


def test_empty_subset_is_unset_only():
    """空集合 (退化点) = kUnset のみ true = 実要因全素通し (真の BACK_OFF=0 相当)。"""
    impl = W.predicate_for([])
    assert _parse_predicate(impl) == ["kUnset"]
    name_cat = {n: c for n, c, _i in W.candidates(EFF3)}
    assert name_cat["g_none"] == "degenerate"


# ==== 列挙の全単射と点数 =======================================================

def test_candidates_counts_and_uniqueness():
    cands = W.candidates(EFF3)
    names = [n for n, _c, _i in cands]
    impls = [i for _n, _c, i in cands]
    assert len(names) == 2 ** len(EFF3) + 1          # 2^N + ident_all
    assert len(set(names)) == len(names), "候補名の重複"
    assert len(set(impls)) == len(impls), "述語の重複 (subset↔述語が全単射でない)"
    assert W.candidate_names(EFF3)[0] == W.STOCK_NAME


def test_ident_all_differs_from_effective_full_subset():
    """実効 ⊊ GATEABLE のとき、ident_all (5 要因全列挙) と実効全集合は別述語 =
    別 variant。両者の floor 内一致が不感縮約の健全性検査になる (設計 §3)。"""
    cands = {n: i for n, _c, i in W.candidates(EFF3)}
    eff_all = cands[W.subset_name(EFF3)]
    ident_all = cands[W.IDENT_NAME]
    assert eff_all != ident_all
    assert set(_parse_predicate(ident_all)) > set(_parse_predicate(eff_all))


def test_candidates_preserve_definition_order():
    """実効集合の与え順に依らず GATEABLE_REASONS の定義順に正規化される (列挙の決定論)。"""
    a = [n for n, _c, _i in W.candidates(EFF3)]
    b = [n for n, _c, _i in W.candidates(list(reversed(EFF3)))]
    assert a == b


# ==== 検疫通過 (fixture 骨格、write=False) =====================================
# 実 patch (silo-backoff-trigger-gating-variant.patch) のマーカー構造の忠実な縮小版。
# フィクスチャと実 patch の乖離は sweep 実走の最初の quarantine で露見する
# (fails-closed) — 構造一致の確認は実装レビュー項目。

_TEMPLATE = """#include "include/common.hh"

void TxExecutor::abort() {
#if BACKOFF_TRIGGER_GATING
  bool izanagi_gate_pass = true;
#endif
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
  // izanagi Phase 3 (D48/phase3.md): this conditional-compilation skeleton
  // is the coder (LLM) edit surface -- ONLY the single assignment in the
  // branch selected when BACKOFF_TRIGGER_GATING >= 1 (the gate predicate).
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
}
"""


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s8asweep_")
    full = os.path.join(d, T.SOURCE_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def test_all_candidates_pass_quarantine():
    d = _mk_template_dir()
    for name, _cat, impl in W.candidates(EFF3):
        res, _b, _e, _wd = L.quarantine(d, impl, marker_id=T.MARKER_ID,
                                        source_rel=T.SOURCE_REL, write=False)
        assert res.passed, f"{name}: 機械生成候補が検疫 reject — {res.reason}"


def test_s8a_reject_writer_fails_closed_on_unframed_tail():
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_reject_gate_")
    ).ensure()
    with open(layout.wal_file, "wb") as stream:
        stream.write(b'{"unframed":')
    before = open(layout.wal_file, "rb").read()
    implementation = W.candidates(EFF3)[0][2]
    rejection = L.DiffQuarantineResult(
        passed=False, digest={"subtype": "fixture-reject"},
    )

    try:
        L.record_diff_reject(
            layout, W._genome(1), implementation, rejection, env_tag=W.ENV_TAG,
        )
        assert False, "s8a reject が unframed tail へ追記されてはならない"
    except wal.WalAppendError as exc:
        assert exc.phase == "tail-gate"
        assert isinstance(exc.cause, wal.WalFramingError)

    assert open(layout.wal_file, "rb").read() == before
    assert not any(name.startswith("wal-tail-repair-")
                   for name in os.listdir(layout.runs_dir))


def test_quarantine_scope_does_not_police_hole_content():
    """D96 境界: trigger marker の hole 内容は 32 正準文字列 membership まで検査する。

    非正準な内容は hole 域内でも汎用 sink が拒否する。一方、正準集合内でどの述語を
    選ぶかの意味的な質は auditor が検査する。偵察 sweep は構成的に生成した正準述語を
    渡すため、この membership を通過する。
    """
    d = _mk_template_dir()
    multiline = ("izanagi_gate_pass = true;\n"
                 "  izanagi_gate_pass = izanagi_gate_pass;")
    res, _b, _e, _wd = L.quarantine(d, multiline, marker_id=T.MARKER_ID,
                                    source_rel=T.SOURCE_REL, write=False)
    assert not res.passed
    assert res.digest["subtype"] == "membership"
    assert res.digest["evidence"] == "canonical predicate membership failure"

    canonical = W.predicate_for(EFF3)
    accepted, _b, _e, _wd = L.quarantine(
        d, canonical, marker_id=T.MARKER_ID,
        source_rel=T.SOURCE_REL, write=False,
    )
    assert accepted.passed, accepted.reason


# ==== campaign identity =======================================================

def test_workload_trial_effective_baked_into_identity():
    ca = ident.campaign_id(W.config_for("balanced", EFF3))
    cb = ident.campaign_id(W.config_for("write-heavy", EFF3))
    cr = ident.campaign_id(W.config_for("balanced", EFF3,
                                        trial=f"{W.TRIAL_MAIN}-remeasure1"))
    ce = ident.campaign_id(W.config_for("balanced", EFF3 + ["node-vali"]))
    assert len({str(ca), str(cb), str(cr), str(ce)}) == 4


def test_default_off_campaign_ids_remain_historical_values():
    """pre-T343/T530 を保存し、authority-free current ID を固定する。"""
    workloads = {
        "balanced": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
    }
    historical = {}
    for tag, workload in workloads.items():
        preimage = {
            "spec_content": (
                "P3 段 8a D 段: silo-backoff-trigger-gating 機械列挙 sweep (偵察、D46 型)。"
                "preliminary = 事前登録外カテゴリ、断定 verdict なし、(c) 判定は出さない。"
                "firewall: E 段へは軸の生死二値のみ (D48 条件 7)・段 6 正式 grid へ材料流用"
                "しない。素の sweep は適応 Backoff_ との連成地形 (直交性主張は adaptive-off "
                f"限定)。空間 = reason-subset-v1: 実効要因 {EFF3} の部分集合 2^N "
                f"(kUnset→true 固定) + ident_all + stock。workload={tag}。"
            ),
            "ccbench_commit": "d706650",
            "search_tag": "sweep",
            "search_config": {
                "scale": "silo", "axis": "silo-backoff-trigger-gating",
                "generator": "reason-subset-v1",
                "space": "reason-subsets(effective)+identall+stock",
                "effective_reasons": EFF3,
                "workload": tag, "ycsb": workload,
                "records": 1_000_000, "threads": 48,
                "verify": "legacy+s2",
            },
            "trial": "p3-s8a-trigger-sweep",
        }
        digest = hashlib.sha256(json.dumps(
            preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")).hexdigest()[:8]
        historical[tag] = f"p3-s8a-trigger-sweep-{tag}-sweep-{digest}"
    assert historical == _PRE_T343_S8A_CAMPAIGN_IDS
    explicit_contract = W.env_contract.GENERATIONS["linux-baremetal"][0].contract
    saved_lookup = W.env_contract.lookup
    W.env_contract.lookup = lambda _env_tag: explicit_contract
    try:
        configs = {
            tag: W.config_for(tag, EFF3)
            for tag in workloads
        }
    finally:
        W.env_contract.lookup = saved_lookup
    current = {
        tag: str(ident.campaign_id(cfg)) for tag, cfg in configs.items()
    }
    assert all(
        "environment_contract_sha256" not in cfg.search_config
        and cfg.bound_environment_contract is explicit_contract
        for cfg in configs.values()
    )
    assert current == _T2858_S8A_CAMPAIGN_IDS
    assert set(current.values()).isdisjoint(
        set(_T343_S8A_CAMPAIGN_IDS.values())
        | set(_T530_S8A_CAMPAIGN_IDS.values())
        | set(_T816_S8A_CAMPAIGN_IDS.values())
        | set(_T2304_S8A_CAMPAIGN_IDS.values())
    )


def test_config_wires_s2_verify_and_provenance():
    cfg = W.config_for("balanced", EFF3)
    assert cfg.search_config[SEARCH_CONFIG_VERIFY_KEY] == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config["generator"] == W.SPACE_VERSION
    assert cfg.search_config["effective_reasons"] == EFF3
    assert cfg.search_config["ycsb"] == W.WORKLOADS["balanced"]
    assert cfg.ccbench_commit == W.PIN == T.PIN
    assert "生死二値" in cfg.spec_content       # firewall 文言 (axis-onboarding §7.2)


def test_perf_is_p2_2_operating_point():
    p = W.perf_for("balanced")
    assert (p.records, p.threads, p.extime, p.reps) == (1_000_000, 48, 3, 5)


def test_genome_flags():
    """フラグ 0/1 と BACK_OFF=1 明示 (D48/F6 — hole は #if BACK_OFF 内、CACHE 既定への
    暗黙依存を避ける)。"""
    g1 = W._genome(1).flags
    g0 = W._genome(0).flags
    assert g1["BACKOFF_TRIGGER_GATING"] == 1 and g0["BACKOFF_TRIGGER_GATING"] == 0
    assert g1["BACK_OFF"] == 1 and g0["BACK_OFF"] == 1


def _install_public_reject_sweep_fakes(monkeypatch, layout):
    from orchestrator.campaign import patchharness

    root = tempfile.mkdtemp(prefix="izanagi_s8a_public_sweep_")
    os.makedirs(os.path.join(root, "external", "ccbench"))
    rejection = L.DiffQuarantineResult(
        passed=False, digest={"subtype": "fixture-reject"},
    )
    monkeypatch.setattr(W, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(W, "load_effective_reasons", lambda: EFF3)
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
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_public_resume_")
    ).ensure()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    first, second = [name for name, _category, _impl in W.candidates(EFF3)[:2]]

    first_result = W.run_sweep(
        "balanced", names=[first], isolate=False, log=lambda _line: None,
    )
    assert first_result[first]["outcome"] == "quarantine-reject"
    cfg = W.config_for("balanced", EFF3)
    assert wal.read_lock(layout) == build_v2_lock(ident.canonical_preimage(cfg))

    resumed = W.run_sweep(
        "balanced", names=[second], isolate=False, log=lambda _line: None,
    )
    assert resumed[second]["outcome"] == "quarantine-reject"
    assert len(wal.read_records(layout)) == 4


def test_public_sweep_trigger_crash_tail_fails_before_quarantine_write(monkeypatch):
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_public_crash_tail_")
    ).ensure()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    cfg = W.config_for("balanced", EFF3)
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    wal.log(layout, "trigger-crashed-v", STAGE_BUILD_START, W.ENV_TAG, {
        "build_attempt_id": "trigger-crashed-attempt",
    })
    before = open(layout.wal_file, "rb").read()

    with pytest.raises(wal.InterruptedAttemptRecoveryError) as excinfo:
        W.run_sweep(
            "balanced", names=[W.candidates(EFF3)[0][0]],
            isolate=False, log=lambda _line: None,
        )
    assert excinfo.value.condition == "trigger-campaign"
    assert excinfo.value.variant == "trigger-crashed-v"
    assert excinfo.value.attempt_id == "trigger-crashed-attempt"
    assert open(layout.wal_file, "rb").read() == before


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes(
        monkeypatch):
    """public sweep→実 pipeline admission 境界で exact class 差を固定する。"""
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_admission_")
    ).ensure()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    machine_name = W.candidates(EFF3)[0][0]
    seen = []
    passed = SimpleNamespace(passed=True)
    expected_pin = "6810666"  # repo policy から逆算しない独立 pin

    def evidence_for(genome, commit, source_root):
        assert commit == expected_pin == W.PIN
        machine = genome.flags["BACKOFF_TRIGGER_GATING"] == 1
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
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_admission_error_")
    ).ensure()
    _install_public_reject_sweep_fakes(monkeypatch, layout)

    def fail_admission(*_args, **_kwargs):
        raise BuildAdmissionError("injected admission failure")

    monkeypatch.setattr(W, "_eval_one", fail_admission)
    with pytest.raises(BuildAdmissionError, match="injected admission failure"):
        W.run_sweep("balanced", names=[W.candidates(EFF3)[0][0]], isolate=False,
                    log=lambda _line: None)


def test_eval_one_propagates_context_and_source_capability_to_build_entry(monkeypatch):
    """検疫通過後の build は policy context と source-bound resolver を受ける。"""
    from orchestrator.campaign import patchharness
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_eval_admission_")
    ).ensure()
    name = W.candidates(EFF3)[0][0]
    context = W.build_run_context(generator_id=W.GeneratorId.S8A_TRIGGER_SWEEP)
    passed = SimpleNamespace(passed=True)
    seen = []
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        L, "quarantine", lambda *_a, **_k: (passed, "", "", "fixture"),
    )
    monkeypatch.setattr(W.source_digest, "resolve", lambda *_a, **_k: "b" * 64)

    def build_entry(*_args, **kwargs):
        seen.append((kwargs["build_context"], kwargs["capability_resolver"]))
        return SimpleNamespace(
            results=[SimpleNamespace(certified=True, aborted=False)]
        )

    monkeypatch.setattr(W, "run_campaign", build_entry)
    result = W._eval_one(
        name, EFF3, W.config_for("balanced", EFF3), W.perf_for("balanced"),
        layout, "/fixture/sub", "/fixture/template.patch", "",
        build_context=context, log=lambda _line: None,
    )
    assert result["outcome"] == "certified"
    assert seen[0][0] is context
    assert callable(seen[0][1])


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_public_sweep_full_frame_fsync_eio_stops_before_next_candidate(
        monkeypatch):
    from orchestrator.campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8a_public_fsync_")
    ).ensure()
    _install_public_reject_sweep_fakes(monkeypatch, layout)
    names = [name for name, _category, _impl in W.candidates(EFF3)[:2]]
    real_fsync = wal.os.fsync
    wal_fsyncs = []

    def fail_wal_fsync(fd):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        if path == layout.wal_file:
            wal_fsyncs.append(fd)
            raise OSError(errno.EIO, "injected full-frame WAL fsync EIO")
        return real_fsync(fd)

    monkeypatch.setattr(wal.os, "fsync", fail_wal_fsync)
    with pytest.raises(wal.WalAppendError) as excinfo:
        W.run_sweep(
            "balanced", names=names, isolate=False, log=lambda _line: None,
        )
    assert excinfo.value.phase == "fsync"
    assert excinfo.value.written_bytes == excinfo.value.total_bytes
    assert len(wal_fsyncs) == 1
    records, truncated = wal.read_records_checked(layout)
    assert truncated is False and len(records) == 1
    assert records[0].stage == STAGE_BUILD_START


# ==== 頻度実測 (必須前提 (a)) 消費の fails-closed ==============================

def _canonical_sha(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()


def _characterization_receipt():
    source = {
        "schema": "source-evidence/v1",
        "source_root": "/tmp/izanagi-s8a-characterization",
        "ccbench_commit": _CHARACTERIZATION_PIN,
        "genome_sha256": hashlib.sha256(
            _CHARACTERIZATION_GENOME.encode("utf-8")
        ).hexdigest(),
        "src_token": "2" * 64,
        "source_bytes_sha256": "3" * 64,
        "tracked_clean": False,
        "tracked_diff_sha256": "4" * 64,
        "tracked_paths": ["cc/silo/transaction.cc"],
    }
    generator_input = {
        "schema": "s8a-trigger-characterization-input/v1",
        "genome": _CHARACTERIZATION_GENOME,
        "trace": True,
        "extra_cxx_define": "",
    }
    input_sha = _canonical_sha(generator_input)
    generator = {
        "schema": "generator-receipt/v1",
        "generator_id": "s8a-trigger-sweep",
        "source": source,
        "generator_input_sha256": input_sha,
    }
    generator["receipt_sha256"] = _canonical_sha(generator)
    receipt = {
        "schema": "build-admission/v1",
        "class": "machine-generated",
        "policy_sha256": _ADMISSION_POLICY_SHA256,
        "source": source,
        "generator_id": "s8a-trigger-sweep",
        "review_id": None,
        "input_sha256": input_sha,
        "generator_receipt": generator,
        "review_receipt": None,
        "authority_kind": None,
    }
    receipt["receipt_sha256"] = _canonical_sha(receipt)
    return receipt


def _freq_doc(effective, conservation_ok=True, partial=False):
    doc = {
        "ccbench_commit": _CHARACTERIZATION_PIN,
        "genome": _CHARACTERIZATION_GENOME,
        "build_admissions": [_characterization_receipt()],
        "workloads": {
            t: {"conservation_ok": conservation_ok}
            for t in ("read-heavy", "balanced", "write-heavy")
        },
    }
    if not partial:
        doc["effective_reasons"] = effective
    return doc


def _with_freq(monkeypatch, doc):
    d = tempfile.mkdtemp(prefix="izanagi_s8afreq_")
    path = os.path.join(d, "s8a_trigger_freq_t48.json")
    if doc is not None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
    monkeypatch.setattr(W, "freq_json_path", lambda: path)
    return path


def test_load_effective_reasons_ok(monkeypatch):
    _with_freq(monkeypatch, _freq_doc(EFF3))
    assert W.load_effective_reasons() == EFF3


def test_load_effective_reasons_missing_json(monkeypatch):
    _with_freq(monkeypatch, None)
    with pytest.raises(RuntimeError, match="頻度実測が無い"):
        W.load_effective_reasons()


def test_load_effective_reasons_partial_run(monkeypatch):
    _with_freq(monkeypatch, _freq_doc(EFF3, partial=True))
    with pytest.raises(RuntimeError, match="部分実行"):
        W.load_effective_reasons()


def test_load_effective_reasons_broken_conservation(monkeypatch):
    _with_freq(monkeypatch, _freq_doc(EFF3, conservation_ok=False))
    with pytest.raises(RuntimeError, match="保存則"):
        W.load_effective_reasons()


def test_load_effective_reasons_unknown_reason(monkeypatch):
    _with_freq(monkeypatch, _freq_doc(EFF3 + ["insert-node"]))
    with pytest.raises(RuntimeError, match="gate 不能"):
        W.load_effective_reasons()


def test_load_effective_reasons_rejects_receiptless_characterization(monkeypatch):
    doc = _freq_doc(EFF3)
    del doc["build_admissions"]
    _with_freq(monkeypatch, doc)
    with pytest.raises(RuntimeError, match="receipt が exact に必要"):
        W.load_effective_reasons()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda doc: doc["build_admissions"][0].update(
            policy_sha256="0" * 64), "schema/policy"),
        (lambda doc: doc["build_admissions"][0]["source"].update(
            ccbench_commit="wrong-pin"), "outer SHA"),
        (lambda doc: doc.update(genome="silo|WAL=1"), "producer と不一致"),
    ],
)
def test_load_effective_reasons_rejects_mismatched_receipts(
        monkeypatch, mutation, message):
    doc = _freq_doc(EFF3)
    mutation(doc)
    _with_freq(monkeypatch, doc)
    with pytest.raises(RuntimeError, match=message):
        W.load_effective_reasons()


# ==== replay / provenance / floor (s6 裁定の踏襲) ==============================

def test_replay_outcome_distinguishes_commit_and_abort(monkeypatch):
    context = W.build_run_context(generator_id=W.GeneratorId.S8A_TRIGGER_SWEEP)
    states = {
        "c": SimpleNamespace(
            committed=True, aborted=False, last_terminal=object()),
        "a": SimpleNamespace(
            committed=False, aborted=True, last_terminal=object()),
    }
    records = [SimpleNamespace(variant="c", stage=W.STAGE_COMMIT)]
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
    assert W._replay_outcome(None, "c", context) == "replayed-certified"
    assert W._replay_outcome(None, "a", context) == "replayed-aborted"
    assert W._replay_outcome(None, "u", context) == "replayed-unknown"


@pytest.mark.parametrize("consumer", ["s8a"], ids=["s8a"])
def test_replay_outcome_requires_persisted_certification(
        tmp_path, monkeypatch, consumer):
    layout = CampaignLayout(str(tmp_path / "s8a-replay")).ensure()
    Path(layout.lock_file).write_text(
        json.dumps({"fixture": "s8a replay"}), encoding="utf-8",
    )
    attempt_id = "s8a-replay-attempt"
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
    context = W.build_run_context(generator_id=W.GeneratorId.S8A_TRIGGER_SWEEP)

    with pytest.raises(W.ArtifactAdmissionError, match="anomalies"):
        W._replay_outcome(layout, "v", context)

    assert consumer == "s8a"


class _FakeLayout:
    def __init__(self, root):
        self.root = root


def test_provenance_merges_existing_entries():
    d = tempfile.mkdtemp(prefix="izanagi_s8aprov_")
    layout = _FakeLayout(d)
    W._write_provenance(layout, "balanced", W.TRIAL_MAIN, EFF3,
                        {"g_none": {"variant_id": "v1", "category": "degenerate",
                                    "src_token": "s1", "outcome": "certified"}})
    W._write_provenance(layout, "balanced", W.TRIAL_MAIN, EFF3,
                        {"g_lc": {"variant_id": "v2", "category": "subset",
                                  "src_token": "s2", "outcome": "certified"}})
    with open(os.path.join(d, "reports", "s8a_trigger_sweep_provenance.json"),
              encoding="utf-8") as f:
        doc = json.load(f)
    assert set(doc["entries"]) == {"g_none", "g_lc"}     # merge (truncate しない)
    assert doc["entries"]["g_none"]["implementation"] == W.predicate_for([])
    assert "生死二値" in doc["firewall"]


def test_remeasure_requires_ident_all(monkeypatch, capsys):
    """--remeasure の --names に基準 ident_all が無ければ fails-closed (return 2) —
    common-mode 誤差を抜けない再測で生死を確定させない (実装レビュー F2、MS-2/STAT-3)。"""
    _with_freq(monkeypatch, _freq_doc(EFF3))
    rc = W.main(["balanced", "--remeasure", "--names", "g_lc"])
    assert rc == 2
    assert "ident_all" in capsys.readouterr().out
    rc2 = W.main(["balanced", "--remeasure"])          # --names 自体の欠落も 2
    assert rc2 == 2


def test_floor_uncalibrated_fails_closed():
    ident_row = {"abort_rate": 0.10}
    assert W._floor_uncalibrated({"category": "degenerate", "abort_rate": 0.10},
                                 ident_row)                       # 退化点は無条件
    assert W._floor_uncalibrated({"category": "subset", "abort_rate": 0.21},
                                 ident_row)                       # 2 倍超
    assert not W._floor_uncalibrated({"category": "subset", "abort_rate": 0.19},
                                     ident_row)
    assert W._floor_uncalibrated({"category": "subset", "abort_rate": None},
                                 ident_row)                       # 材料欠落
    assert W._floor_uncalibrated({"category": "subset", "abort_rate": 0.1}, None)
    assert W._floor_uncalibrated({"category": "subset", "abort_rate": 0.1},
                                 {"abort_rate": 0})               # 基準 0 も判定不能


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
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
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
    from orchestrator.campaign.layout import CampaignLayout

    historical = require_admitted_campaign(
        _REAL_E0_CAMPAIGN,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert historical.campaign_verifier_epoch.state == "E0"
    assert historical.records
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        W._load_rows(_REAL_E0_CAMPAIGN, {})

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8ascreen_")
    ).ensure()
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
        "screened-out": {"variant_id": screen_variant, "category": "subset"},
        "certified": {"variant_id": certified_variant, "category": "subset"},
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
    with open(os.path.join(reports, "s8a_trigger_sweep_provenance.json"),
              "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f)
    monkeypatch.setattr(W, "load_effective_reasons", lambda: EFF3)
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


def test_real_legacy_trigger_campaign_cannot_be_certified_by_commit_only():
    campaign = (Path(_ORCH).parent / "output" / "campaigns" /
                "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5")
    with pytest.raises(CampaignNotAdmitted, match="legacy-unclassified"):
        W._load_rows(str(campaign), {})
