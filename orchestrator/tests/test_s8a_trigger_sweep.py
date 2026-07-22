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
import itertools
import json
import os
import re
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

import pytest                                                      # noqa: E402

from campaign import axis_trigger_gating as T                      # noqa: E402
from campaign import ident                                         # noqa: E402
from campaign import pipeline                                      # noqa: E402
from campaign import p3_s4_loop as L                               # noqa: E402
from campaign import s8a_trigger_sweep as W                        # noqa: E402
from campaign import wal                                           # noqa: E402
from campaign.model import STAGE_BUILD_START                       # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY             # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                # noqa: E402

# 頻度実測の予想結果 (シート導出: YCSB では node/absent 構造ゼロ)。テストは実測に
# 依存しない — 代表として 3 ビットの実効集合で列挙の機械性質を検査する。
EFF3 = ["lock-conflict", "readvali-tid", "readvali-locked"]


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
    from campaign.layout import CampaignLayout

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
    """検疫の守備範囲の固定 (実測 2026-07-11): DiffQuarantine は hole 域の封じ込め
    (フレーム・hole 外の改変拒否) を守るのであって、hole 域**内**の内容の質 (1 行性・
    副作用なし・構文契約) は守らない — 複数行 implementation も hole 域内なら通る。
    質の守りの主体は、偵察では述語生成器の構成的保証 + 本テスト群の機械検査
    (test_predicates_*)、E 段では auditor 目視 (D48 決定 2/F5 — 構文恒真検査を第一
    防壁にしない)。この分担を忘れて検疫に質の防御を期待しないこと。"""
    d = _mk_template_dir()
    multiline = ("izanagi_gate_pass = true;\n"
                 "  izanagi_gate_pass = izanagi_gate_pass;")
    res, _b, _e, _wd = L.quarantine(d, multiline, marker_id=T.MARKER_ID,
                                    source_rel=T.SOURCE_REL, write=False)
    assert res.passed, ("hole 域内の複数行が検疫で落ちるなら、質の守りの分担 "
                        "(生成器/auditor) の前提が変わっている — 本テストの docstring "
                        "と設計ドラフトを再訪すること")


# ==== campaign identity =======================================================

def test_workload_trial_effective_baked_into_identity():
    ca = ident.campaign_id(W.config_for("balanced", EFF3))
    cb = ident.campaign_id(W.config_for("write-heavy", EFF3))
    cr = ident.campaign_id(W.config_for("balanced", EFF3,
                                        trial=f"{W.TRIAL_MAIN}-remeasure1"))
    ce = ident.campaign_id(W.config_for("balanced", EFF3 + ["node-vali"]))
    assert len({str(ca), str(cb), str(cr), str(ce)}) == 4


def test_default_off_campaign_ids_remain_historical_values():
    assert str(ident.campaign_id(W.config_for("balanced", EFF3))) == \
        "p3-s8a-trigger-sweep-balanced-sweep-c2d838b8"
    assert str(ident.campaign_id(W.config_for("write-heavy", EFF3))) == \
        "p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8"


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
    from campaign import patchharness

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


def test_public_sweep_fresh_reject_then_next_candidate_resumes(monkeypatch):
    from campaign.layout import CampaignLayout

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
    assert wal.read_lock(layout) == ident.canonical_preimage(cfg)

    resumed = W.run_sweep(
        "balanced", names=[second], isolate=False, log=lambda _line: None,
    )
    assert resumed[second]["outcome"] == "quarantine-reject"
    assert len(wal.read_records(layout)) == 4


def test_public_sweep_full_frame_fsync_eio_stops_before_next_candidate(
        monkeypatch):
    from campaign.layout import CampaignLayout

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

def _freq_doc(effective, conservation_ok=True, partial=False):
    doc = {"workloads": {t: {"conservation_ok": conservation_ok}
                         for t in ("read-heavy", "balanced", "write-heavy")}}
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


# ==== replay / provenance / floor (s6 裁定の踏襲) ==============================

def test_replay_outcome_distinguishes_commit_and_abort(monkeypatch):
    from campaign.model import STAGE_ABORT, STAGE_COMMIT

    def fake(layout, vid):
        return {"c": {STAGE_COMMIT: {}, STAGE_ABORT: None},
                "a": {STAGE_COMMIT: None, STAGE_ABORT: {}},
                "u": {STAGE_COMMIT: None, STAGE_ABORT: None}}[vid]
    monkeypatch.setattr(W.wal, "records_by_stage", fake)
    assert W._replay_outcome(None, "c") == "replayed-certified"
    assert W._replay_outcome(None, "a") == "replayed-aborted"
    assert W._replay_outcome(None, "u") == "replayed-unknown"


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


def test_screen_reject_row_and_report_hide_uncertified_bench_values(monkeypatch):
    """BENCH_DONE は certified の証拠ではない。screen 数値は WAL にだけ保持する。"""
    from campaign.layout import CampaignLayout

    layout = CampaignLayout(
        root=tempfile.mkdtemp(prefix="izanagi_s8ascreen_")
    ).ensure()
    W.wal.log(layout, "v-screen", W.STAGE_BENCH_DONE, W.ENV_TAG, {
        "median_tps": 12345,
        "cv": 0.01,
        "unstable": True,
        "leading_indicators": {
            "abort_rate": 0.12,
            "ipc": 1.23,
            "llc_miss_rate": 0.34,
        },
    })
    W.wal.log(layout, "v-screen", W.STAGE_ABORT, W.ENV_TAG, {
        "reason": pipeline.SCREEN_REJECTION_REASON,
        "screen": {"median_tps": 12345},
    })
    W.wal.log(layout, "v-certified", W.STAGE_BENCH_DONE, W.ENV_TAG, {
        "median_tps": 6789,
        "cv": 0.02,
        "unstable": False,
        "leading_indicators": {
            "abort_rate": 0.05,
            "ipc": 0.98,
            "llc_miss_rate": 0.21,
        },
    })
    # 空 payload も COMMIT の存在として扱う (truthiness で判定しない)。
    W.wal.log(layout, "v-certified", W.STAGE_COMMIT, W.ENV_TAG, {})

    entries = {
        "screened-out": {"variant_id": "v-screen", "category": "subset"},
        "certified": {"variant_id": "v-certified", "category": "subset"},
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
        if r.variant == "v-screen" and r.stage == W.STAGE_ABORT
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
    assert "screening 正常棄却" in text
    assert pipeline.SCREEN_REJECTION_REASON in text
    assert "12345" not in text.replace(",", "")
