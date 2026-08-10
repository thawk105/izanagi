# -*- coding: utf-8 -*-
"""critic digest の単体テスト (machine 非依存・mock WAL)。

pytest でも 素の `python orchestrator/tests/test_critic.py` でも走る。
"""
from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import env_contract, ident, pipeline, wal           # noqa: E402
from campaign.artifact_admission import (CampaignNotAdmitted,     # noqa: E402
                                         require_admitted_campaign)
from campaign.build_admission import (                            # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from campaign.layout import CampaignLayout                        # noqa: E402
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_BUILD_DONE, STAGE_BUILD_START,
                            STAGE_COMMIT, STAGE_VERIFY_DONE,
                            CampaignConfig, Genome)
from campaign.pin import CURRENT_PIN                              # noqa: E402
from campaign.source_digest import (                              # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from critic.digest import (STOCK_SRC_TOKEN, DiffQuarantineRejection,  # noqa: E402
                           IdentityProjection, LivenessRejection,
                           Rejection, VerifyAbortSignal,
                           build_digest, load_diff_rejections,
                           load_liveness_rejections, load_rejections,
                           load_screen_rejections, load_verify_abort_signals,
                           load_workload,
                           render_rejections as _render_rejections,
                           render_text)
from campaign_lock_test_support import build_v2_lock              # noqa: E402


_ADMISSION_CONTEXT = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
_ENV_CONTRACT = env_contract.GENERATIONS["linux-baremetal"][0].contract


def render_rejections(*args, **kwargs):
    """既存 renderer 期待値は明示 raw 診断として維持する。"""
    kwargs["identity_projection"] = IdentityProjection.RAW
    return _render_rejections(*args, **kwargs)


def _tmp_layout():
    parent = tempfile.mkdtemp(prefix="izanagi_critic_")
    atexit.register(shutil.rmtree, parent, ignore_errors=True)
    cfg = ident.bind_admission_policy(CampaignConfig(
        spec_slug="critic-fixture",
        search_tag="test",
        spec_content="critic post-policy fixture",
        ccbench_commit=CURRENT_PIN,
        search_config={"records": 1, "threads": 1},
        trial="test",
    ), _ADMISSION_CONTEXT.policy)
    cfg = ident.bind_environment_contract(cfg, _ENV_CONTRACT)
    layout = CampaignLayout(
        root=os.path.join(parent, str(ident.campaign_id(cfg)))
    ).ensure()
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    return layout


def _view(layout):
    return require_admitted_campaign(layout)


def _genome_value(canonical: str) -> Genome:
    protocol, body = canonical.split("|", 1)
    flags = {}
    if body:
        for field in body.split(","):
            name, value = field.split("=", 1)
            flags[name] = int(value)
    genome = Genome(protocol, flags)
    assert genome.canonical() == canonical
    return genome


def _start_attempt(
    lay: CampaignLayout, genome: str, *, src_token: str = STOCK_SRC_TOKEN,
) -> tuple[str, str, str, str]:
    """Write one canonical post-policy BUILD_START and return its binding."""
    genome_value = _genome_value(genome)
    dirty = src_token != STOCK_SRC_TOKEN
    admitted_src_token = (
        hashlib.sha256(f"fixture-src-token:{src_token}".encode("utf-8")).hexdigest()
        if dirty else STOCK_SRC_TOKEN
    )
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(lay.root),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode("utf-8")).hexdigest(),
        src_token=admitted_src_token,
        source_bytes_sha256=hashlib.sha256(
            f"fixture-source:{genome}:{src_token}".encode("utf-8")
        ).hexdigest(),
        tracked_clean=not dirty,
        tracked_diff_sha256=(
            hashlib.sha256(
                f"fixture-diff:{genome}:{src_token}".encode("utf-8")
            ).hexdigest()
            if dirty else EMPTY_TRACKED_DIFF_SHA256
        ),
        tracked_paths=(("include/fixture.hh",) if dirty else ()),
    )
    capability = None
    if dirty:
        capability = attest_generator_output(
            _ADMISSION_CONTEXT,
            evidence,
            generator_input_sha256=hashlib.sha256(
                f"fixture-input:{genome}:{src_token}".encode("utf-8")
            ).hexdigest(),
        )
    admission = derive_build_admission(
        _ADMISSION_CONTEXT, evidence, generator_receipt=capability,
    )
    receipt = admission.as_wal_receipt()
    variant = pipeline.variant_id(genome_value, admitted_src_token)
    attempt_id = "critic-fixture-attempt-%d" % sum(
        record.stage == STAGE_BUILD_START for record in wal.read_records(lay)
    )
    wal.log(lay, variant, STAGE_BUILD_START, _ENV_CONTRACT.env_tag, {
        "genome": genome,
        "src_token": admitted_src_token,
        "build_attempt_id": attempt_id,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    })
    return variant, attempt_id, receipt["receipt_sha256"], admitted_src_token


def _attempt_event(
    lay: CampaignLayout, attempt: tuple[str, str, str, str], stage: str,
    payload: dict,
) -> None:
    variant, attempt_id, receipt_sha, _src_token = attempt
    wal.log(lay, variant, stage, _ENV_CONTRACT.env_tag, {
        **payload,
        **({"contract_sha256": _ENV_CONTRACT.contract_sha256}
           if stage == STAGE_COMMIT else {}),
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt_sha,
    })


@pytest.mark.parametrize("loader", [
    load_workload,
    load_rejections,
    load_liveness_rejections,
    load_screen_rejections,
    load_diff_rejections,
    load_verify_abort_signals,
])
def test_every_raw_loader_requires_validated_view(loader) -> None:
    layout = _tmp_layout()
    with pytest.raises(TypeError, match="require_admitted_campaign"):
        loader(layout)


def test_real_legacy_s4_critic_entry_is_rejected() -> None:
    campaign = (
        Path(__file__).resolve().parents[2]
        / "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387"
    )
    with pytest.raises(CampaignNotAdmitted, match="legacy-unclassified"):
        require_admitted_campaign(campaign)


def _write(lay, genome, committed=True, **li):
    attempt = _start_attempt(lay, genome)
    _attempt_event(lay, attempt, STAGE_BUILD_DONE, {})
    _attempt_event(lay, attempt, STAGE_BENCH_DONE, {"leading_indicators": li})
    if committed:                                  # digest は committed のみ拾う
        _attempt_event(
            lay, attempt, STAGE_COMMIT,
            {"fitness_tps": li.get("throughput_tps")},
        )


_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def test_load_sorts_by_throughput_and_marginal_back_off():
    lay = _tmp_layout()
    # BACK_OFF 0→1: throughput 半減・latency 倍・abort 不変 (= backoff は latency コスト)
    _write(lay, _G.format(b=0, l=1, t=0, w=0),
           throughput_tps=8_000_000, abort_rate=0.05, latency_ns=1000,
           llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0),
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("balanced", {"ycsb_rratio": "50"}, lay)
    assert len(d.genomes) == 2
    assert d.fastest.flags["BACK_OFF"] == 0           # throughput 降順
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"] == {"0": 8_000_000, "1": 4_000_000}
    assert abs(bo.rel_throughput - (-0.5)) < 1e-9     # 0→1 で -50%
    assert bo.means["abort_rate"]["0"] == bo.means["abort_rate"]["1"]  # abort 不変
    assert bo.means["latency_ns"] == {"0": 1000, "1": 2000}            # latency 倍


def test_no_wait_axis_is_categorical_LT():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0),         # L = 即abort
           throughput_tps=2_700_000, abort_rate=0.40, latency_ns=500,
           llc_miss_rate=0.3, ipc=1.0)
    _write(lay, _G.format(b=0, l=0, t=1, w=0),         # T = retry
           throughput_tps=1_900_000, abort_rate=0.50, latency_ns=700,
           llc_miss_rate=0.3, ipc=0.9)
    d = build_digest("balanced", {}, lay)
    nw = next(e for e in d.axes if e.axis == "no_wait")
    assert set(nw.levels) == {"L", "T"}                # NWL=1→L / NWT=1→T に畳む
    assert nw.means["throughput_tps"]["L"] == 2_700_000
    assert nw.means["throughput_tps"]["T"] == 1_900_000
    assert nw.means["latency_ns"]["L"] == 500 and nw.means["latency_ns"]["T"] == 700


def test_marginal_averages_over_other_flags():
    """限界効果は他フラグで周辺化する: WAL=0/1 各 2 genome の平均で軸効果を出す。"""
    lay = _tmp_layout()
    # BACK_OFF=0 を 2 genome (WAL 0/1)、BACK_OFF=1 を 2 genome (WAL 0/1)
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=0, l=1, t=0, w=1), throughput_tps=7_000_000,
           abort_rate=0.05, latency_ns=1100, llc_miss_rate=0.2, ipc=1.4)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), throughput_tps=4_000_000,
           abort_rate=0.05, latency_ns=2000, llc_miss_rate=0.2, ipc=1.0)
    _write(lay, _G.format(b=1, l=1, t=0, w=1), throughput_tps=3_000_000,
           abort_rate=0.05, latency_ns=2100, llc_miss_rate=0.2, ipc=0.9)
    d = build_digest("x", {}, lay)
    bo = next(e for e in d.axes if e.axis == "BACK_OFF")
    assert bo.means["throughput_tps"]["0"] == 7_500_000     # (8M+7M)/2
    assert bo.means["throughput_tps"]["1"] == 3_500_000     # (4M+3M)/2
    wal_eff = next(e for e in d.axes if e.axis == "WAL")
    assert wal_eff.means["throughput_tps"]["0"] == 6_000_000  # (8M+4M)/2
    assert wal_eff.means["throughput_tps"]["1"] == 5_000_000  # (7M+3M)/2


def test_uncommitted_genome_excluded():
    """A (atomicity): bench_done はあるが COMMIT 前にクラッシュした genome は digest から除外。"""
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    _write(lay, _G.format(b=1, l=1, t=0, w=0), committed=False,  # half-evaluated
           throughput_tps=4_000_000, abort_rate=0.05, latency_ns=2000,
           llc_miss_rate=0.2, ipc=1.5)
    d = build_digest("x", {}, lay)
    assert len(d.genomes) == 1                   # 非 committed は不採用
    assert d.genomes[0].flags["BACK_OFF"] == 0


def test_render_text_has_axes_and_indicators():
    lay = _tmp_layout()
    _write(lay, _G.format(b=0, l=1, t=0, w=0), throughput_tps=8_000_000,
           abort_rate=0.05, latency_ns=1000, llc_miss_rate=0.2, ipc=1.5)
    txt = render_text([build_digest("read-heavy", {"ycsb_rratio": "95"}, lay)])
    assert "read-heavy" in txt
    assert "BACK_OFF" in txt and "no_wait" in txt and "WAL" in txt
    assert "throughput_tps" in txt and "abort_rate" in txt
    assert "限界効果" in txt


def test_load_rejections_surfaces_structured_anomaly():
    """S4 (規律3 配線): load_rejections が verify-red の構造化 anomaly を次手入力として拾い、
    verify を持たない abort (build-error 等) は除外する。`load_workload` (緑) と対をなす。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    builderr = _G.format(b=0, l=1, t=0, w=0)
    # verify-red の variant (pipeline が書く形 = abort payload に verify 構造)
    red_attempt = _start_attempt(lay, red, src_token="codediff1")
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": {"verdict": "non-serializable", "anomaly_count": 1,
                   "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                                  "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                             "reasons": [{"type": "rw", "key": "aa"}]}]}],
                   "integrity": {"clean": True}},
    })
    # verify を持たない abort (build-error) は規律3 の次手入力ではない → 除外
    builderr_attempt = _start_attempt(lay, builderr)
    _attempt_event(lay, builderr_attempt, STAGE_ABORT, {"reason": "build-error"})

    rej = load_rejections(_view(lay))
    assert len(rej) == 1                          # build-error は除外
    assert rej[0].genome == red
    assert rej[0].flags["BACK_OFF"] == 1          # genome flags まで復元
    assert rej[0].verdict == "non-serializable"
    assert rej[0].anomalies[0]["phenomenon"] == "G2"
    assert rej[0].anomalies[0]["edges"][0]["reasons"][0]["key"] == "aa"
    assert rej[0].integrity == {"clean": True}
    # コード軸の識別 (D23): 同 canonical 別コードの RED variant が alias しないよう
    # WAL キーと src_token も次手入力に載る
    assert rej[0].variant == red_attempt[0]
    assert rej[0].src_token == red_attempt[3]


def test_load_liveness_rejections_surfaces_reason_and_extra():
    """S4 consumer (規律3): liveness-red (verify 前に死んだ) が構造化されて次手入力に
    届き、infra 系 (build-error/eval-exception 等) は詳細でなく正規化 reason の件数に
    集約される (詳細は返さないが沈黙もさせない)。verify-red は混ざらない。"""
    lay = _tmp_layout()
    to = _G.format(b=1, l=1, t=0, w=0)
    to_attempt = _start_attempt(lay, to, src_token="codediff9")
    _attempt_event(lay, to_attempt, STAGE_ABORT, {
        "reason": "trace-timeout", "timeout_s": 120.0,
    })
    te = _G.format(b=0, l=1, t=0, w=0)
    te_attempt = _start_attempt(lay, te)
    _attempt_event(lay, te_attempt, STAGE_ABORT, {
        "reason": "trace-empty", "commits": 0, "aborts": 4321,
    })
    b1 = _G.format(b=0, l=0, t=1, w=0)
    b1_attempt = _start_attempt(lay, b1)
    _attempt_event(lay, b1_attempt, STAGE_ABORT, {"reason": "build-error"})
    b2 = _G.format(b=1, l=0, t=1, w=0)
    b2_attempt = _start_attempt(lay, b2)
    _attempt_event(lay, b2_attempt, STAGE_ABORT,
                   {"reason": "eval-exception: TypeError: boom"})
    vr = _G.format(b=1, l=1, t=0, w=1)
    vr_attempt = _start_attempt(lay, vr)
    _attempt_event(lay, vr_attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": {"verdict": "non-serializable"},
    })

    lrs, other = load_liveness_rejections(_view(lay))
    assert {l.reason for l in lrs} == {"trace-timeout", "trace-empty"}
    lto = next(l for l in lrs if l.reason == "trace-timeout")
    assert lto.extra.get("timeout_s") == 120.0
    assert lto.variant == to_attempt[0] and lto.src_token == to_attempt[3]
    assert lto.flags["BACK_OFF"] == 1
    lte = next(l for l in lrs if l.reason == "trace-empty")
    assert lte.extra.get("commits") == 0 and lte.extra.get("aborts") == 4321
    assert other == {"build-error": 1, "eval-exception": 1}


def test_screen_rejection_loader_is_disjoint_and_render_hides_uncertified_metrics():
    """screen reject は専用 loader だけが拾い、未認証性能値は render へ渡さない。

    否定 assert の恒真化を防ぐため、同じ WAL の payload["screen"] に 12345 が
    実在することを正対照で先に固定する。
    """
    lay = _tmp_layout()
    genome = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, genome, src_token="codediff-screen")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": pipeline.SCREEN_REJECTION_REASON,
        "screen": {
            "median_tps": 12345, "cv": 0.01, "baseline_tps": 20000,
            "baseline_ref": "stock-v1", "floor": 0.10, "k": 1.5,
            "margin": -0.38275,
        },
    })

    records = list(wal.read_records(lay))
    abort = next(r for r in records if r.stage == STAGE_ABORT)
    assert abort.payload["screen"]["median_tps"] == 12345  # 正対照

    assert load_rejections(_view(lay)) == []
    liveness, other = load_liveness_rejections(_view(lay))
    assert liveness == [] and other == {}
    screened = load_screen_rejections(_view(lay))
    assert len(screened) == 1
    assert vars(screened[0]) == {
        "genome": genome,
        "flags": {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
                  "NO_WAIT_OF_TICTOC": 0, "WAL": 0},
        "variant": attempt[0],
        "src_token": attempt[3],
        "reason": pipeline.SCREEN_REJECTION_REASON,
    }

    out = render_rejections([], [], {}, None, screen_rejections=screened)
    assert "screening 正常棄却 (未認証のため性能数値なし)" in out
    assert "件数: 1" in out and f"genome={genome}" in out
    assert "codediff-screen" not in out
    assert pipeline.SCREEN_REJECTION_REASON not in out
    assert "全 variant 緑" not in out
    for hidden in ("12345", "median_tps", "baseline_tps", "cv"):
        assert hidden not in out


def test_rejection_types_keep_forward_workload_tag():
    """D36 決定 4 (段 5 配線予定) への前方寛容: abort payload に workload タグが来たら
    verify-red / liveness-red の両型が生値で保持する (形の確定は D36 実装時)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    red_attempt = _start_attempt(lay, red)
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable", "workload": {"tag": "s2"},
        "verify": {"verdict": "non-serializable", "anomalies": [],
                   "integrity": {}},
    })
    lv = _G.format(b=0, l=1, t=0, w=0)
    lv_attempt = _start_attempt(lay, lv)
    _attempt_event(lay, lv_attempt, STAGE_ABORT, {
        "reason": "trace-timeout", "workload": {"tag": "s2"},
    })
    rej = load_rejections(_view(lay))
    lrs, _ = load_liveness_rejections(_view(lay))
    assert rej[0].workload == {"tag": "s2"}
    assert lrs[0].workload == {"tag": "s2"}
    assert "workload" not in lrs[0].extra      # 別フィールドに分離 (extra と二重化しない)


def _red_verify_payload(total_cycles=1, txns=100):
    """pipeline が書く形 (result_to_dict) の verify payload (cycle 型)。"""
    return {"verdict": "non-serializable", "anomaly_count": 1,
            "total_cycles": total_cycles,
            "stats": {"txns": txns, "reads": 300, "writes": 100,
                      "keys": 50, "edges": 120},
            "anomalies": [{"phenomenon": "G2", "cycle": [1, 2],
                           "edges": [{"from": 1, "to": 2, "types": ["rw"],
                                      "reasons": [{"type": "rw", "key": "aa",
                                                   "u_ver": [1, 1],
                                                   "v_ver": [1, 2]}]}]}],
            "integrity": {"clean": True, "notes": []}}


def test_render_rejections_cycle_shape_shows_total_cycles():
    """cycle 型 (non-serializable): witness と全数 (total_cycles) を併記し切り詰めを
    明示する — witness 数を全数と誤読させない (S2 で total 4,053 / witness 20 の前例)。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, red, src_token="cd1")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "non-serializable",
        "verify": _red_verify_payload(total_cycles=57),
    })
    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "cycle 全数 57 / witness 1 件" in out
    assert "抜粋" in out                                # 切り詰めの明示
    assert "T1 → T2" in out and "rw key=aa" in out      # どの依存を断つかが読める


def test_render_rejections_liveness_hints_and_other_counts():
    """liveness 型: reason 別の帰属枠ヒント (枯渇/不全/計器破れ) が付き、infra 系は
    件数 1 行サマリに集約される。"""
    lrs = [
        LivenessRejection(genome=_G.format(b=1, l=1, t=0, w=0),
                          flags={"BACK_OFF": 1}, reason="trace-timeout",
                          extra={"timeout_s": 120.0}, variant="v1"),
        LivenessRejection(genome=_G.format(b=0, l=1, t=0, w=0),
                          flags={"BACK_OFF": 0}, reason="trace-empty",
                          extra={"commits": 0, "aborts": 4321}, variant="v2"),
        LivenessRejection(genome=_G.format(b=0, l=0, t=1, w=0),
                          flags={}, reason="trace-parse-error", variant="v3"),
    ]
    out = render_rejections([], lrs, {"build-error": 2, "eval-exception": 1}, None)
    assert "[liveness:trace-timeout]" in out and "timeout_s=120.0" in out
    assert "commit 枯渇" in out                      # trace-empty の読み方
    assert "計器" in out                             # parse-error = 計器破れ
    assert "build-error×2" in out and "eval-exception×1" in out


def test_render_rejections_carries_no_perf_tokens():
    """規律2: rejection 節に性能語彙 (fitness/throughput/tps/latency) が一切出ない —
    「赤に fitness を付けない」を散文でなく否定 assert で固定。"""
    lay = _tmp_layout()
    red = _G.format(b=1, l=1, t=0, w=0)
    red_attempt = _start_attempt(lay, red, src_token="cd1")
    _attempt_event(lay, red_attempt, STAGE_ABORT, {
        "reason": "non-serializable", "verify": _red_verify_payload(),
    })
    lrs = [LivenessRejection(genome=red, flags={}, reason="trace-timeout",
                             extra={"timeout_s": 120.0}, variant="v1")]
    stock = _G.format(b=0, l=1, t=0, w=0)
    stock_attempt = _start_attempt(lay, stock)
    _attempt_event(lay, stock_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
    })
    out = render_rejections(load_rejections(_view(lay)), lrs, {"build-error": 1},
                            load_verify_abort_signals(_view(lay)))
    low = out.lower()
    for tok in ("fitness", "throughput", "tps", "latency"):
        assert tok not in low, f"rejection 節に性能語彙 {tok} が混入"


def _indeterminate_verify_payload(txns=100, missing=0, notes=None, clean=None):
    """pipeline が書く形の verify payload (integrity 型 = indeterminate)。"""
    if clean is None:
        clean = (missing == 0)
    return {"verdict": "indeterminate", "anomaly_count": 0, "total_cycles": 0,
            "stats": {"txns": txns, "reads": 0, "writes": 0, "keys": 0, "edges": 0},
            "anomalies": [],
            "integrity": {"clean": clean, "orphan_reads": 0, "version_dups": 0,
                          "dup_txids": 0, "genesis_commits": 0,
                          "missing_txids": missing, "write_version_mismatch": 0,
                          "malformed_keys": 0, "notes": notes or []}}


def test_integrity_class_rejection_closes_loop():
    """段 2 の positive control 本丸 (J8-B): integrity-class (indeterminate) の赤が
    WAL → load_rejections → render で **cycle 型と区別して**描画される — clean G2
    (broken-silo) だけで規律3 閉ループを certify しない (phase3.md 残存リスク節)。"""
    lay = _tmp_layout()
    v = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, v, src_token="cdI")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate",
        "verify": _indeterminate_verify_payload(
            txns=97, missing=3,
            notes=["missing txids sample: [7, 8, 9]"],
        ),
    })
    rej = load_rejections(_view(lay))
    assert len(rej) == 1 and rej[0].verdict == "indeterminate"
    assert rej[0].integrity["missing_txids"] == 3
    out = render_rejections(rej, [], {}, None)
    assert "missing_txids" in out                    # どのカウンタが非ゼロか
    assert "missing txids sample" in out             # notes (欠番の見本) が届く
    assert "cycle 全数" not in out                   # cycle 型の描画をしない (区別)


def test_write_intent_rejection_is_mechanism_gap_not_cycle():
    """I 行由来の indeterminate は X と同じ機構欠落型に分類し、次手を write-set
    membership / API 意図の復元へ向ける。cycle witness を捏造しない。"""
    lay = _tmp_layout()
    v = _G.format(b=1, l=0, t=1, w=0)
    payload = _indeterminate_verify_payload(
        txns=1, notes=[
            "1 write-intent coverage violation(s) "
            "[write-set-entry-without-intent×1]"
        ])
    payload["integrity"].update({
        "lock_coverage_violations": 0,
        "permutation_violations": 0,
        "write_intent_violations": 1,
    })
    attempt = _start_attempt(lay, v, src_token="cdWI")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate", "verify": payload,
    })

    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "機構欠落型 (write intent coverage)" in out
    assert "write-set membership / API 意図の復元" in out
    assert "cycle 帰属を捏造しない" in out
    assert "write-set-entry-without-intent×1" in out
    assert "cycle 全数" not in out
    assert "lock acquisition / retention" not in out


def test_empty_dsg_rejection_renders_explicitly():
    """J8-B 形状 (ii): integrity 全クリーンでも txns=0 (空 DSG) の indeterminate は
    「trace が空」を明示する — 7 カウンタ全ゼロの空パネルとして沈黙しない
    (実 run では trace-empty が手前で先取るが、verifier 単体経路では到達する形)。"""
    lay = _tmp_layout()
    v = _G.format(b=0, l=1, t=0, w=0)
    attempt = _start_attempt(lay, v, src_token="cdE")
    _attempt_event(lay, attempt, STAGE_ABORT, {
        "reason": "indeterminate",
        "verify": _indeterminate_verify_payload(txns=0, clean=True),
    })
    out = render_rejections(load_rejections(_view(lay)), [], {}, None)
    assert "trace が空 (txns=0)" in out
    assert "緑ではない" in out                       # クリーンでも certify しない旨


def test_verify_abort_signal_stock_contrast():
    """J1 シグナル: verify run の abort 率を stock 対照比つきで表示 (閾値判定なし)。"""
    lay = _tmp_layout()
    stock = _G.format(b=0, l=1, t=0, w=0)
    stock_attempt = _start_attempt(lay, stock)
    _attempt_event(lay, stock_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
    })
    var = _G.format(b=1, l=1, t=0, w=0)
    var_attempt = _start_attempt(lay, var, src_token="cd2")
    _attempt_event(lay, var_attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 600, "aborts": 400,
    })
    out = render_rejections([], [], {}, load_verify_abort_signals(_view(lay)))
    assert "rate=10.00%" in out                       # stock 100/1000
    assert "rate=40.00%" in out and "stock 比 4.0×" in out


def test_verify_abort_signal_no_stock_and_legacy_are_explicit():
    """規律3 (沈黙禁止): stock 対照不在・旧形式 WAL (aborts 記録なし)・未発火の
    3 形は明示表示 (欠落を無言で流さない)。"""
    lay = _tmp_layout()
    var = _G.format(b=1, l=1, t=0, w=0)
    attempt = _start_attempt(lay, var, src_token="cd3")
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 500,
    })                                                     # aborts 無し = 旧形式
    out = render_rejections([], [], {}, load_verify_abort_signals(_view(lay)))
    assert "stock 対照なし" in out
    assert "aborts 記録なし (旧形式 WAL)" in out
    out2 = render_rejections([], [], {}, [])
    assert "未発火" in out2


def test_verify_abort_signal_prefers_first_pass_when_s2_writes_second_record():
    """D36 決定4 (S2 有効時): variant ごとに legacy→S2 の順で STAGE_VERIFY_DONE が
    複数回書かれうる (敵対レビュー 2026-07-09 CONFIRMED — 修正前は最後勝ちで legacy の
    commits/aborts が消え、stock 対照とスケールが食い違う比較になっていた)。
    campaign 内の全 genome (stock 含む) は同じ passes 順序で評価されるため、
    legacy パス (常に最初) を先勝ちで採用しスケールを揃える。"""
    lay = _tmp_layout()
    stock = _G.format(b=0, l=1, t=0, w=0)
    attempt = _start_attempt(lay, stock)
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 900, "aborts": 100,
        "workload": {"tag": "legacy"},
    })
    _attempt_event(lay, attempt, STAGE_VERIFY_DONE, {
        "verdict": "serializable", "commits": 1_500_000, "aborts": 500_000,
        "workload": {"tag": "s2"},
    })
    out = load_verify_abort_signals(_view(lay))
    assert len(out) == 1
    assert out[0].commits == 900 and out[0].aborts == 100  # S2 (2 件目) でなく legacy を採用


def test_stock_token_matches_source_digest():
    """STOCK_SRC_TOKEN のローカル定数が source_digest.STOCK から drift しない。"""
    from campaign import source_digest
    assert STOCK_SRC_TOKEN == source_digest.STOCK


class _OneChannelProjection(IdentityProjection):
    """1 test node で 1 identity channel だけを発火させる sentinel。"""

    def __init__(self, channel: str, raw: str, projected: str):
        self.channel = channel
        self.raw = raw
        self.projected = projected

    def _project(self, channel: str, value):
        if value is None or value == "":
            return value
        assert channel == self.channel
        assert value == self.raw
        return self.projected

    def project_variant(self, value):
        return self._project("variant", value)

    def project_src_token(self, variant, value):
        return self._project("src_token", value)

    def project_build_attempt_id(self, variant, value):
        return self._project("build_attempt_id", value)

    def project_build_admission_receipt_sha256(self, variant, value):
        return self._project("build_admission_receipt_sha256", value)


def _assert_one_projection_channel(out: str, raw: str, projected: str) -> None:
    assert projected in out
    assert raw not in out


def test_projection_m2_verify_red_variant_channel():
    raw, projected = "M2-raw-verify-variant", "M2-projected-verify-variant"
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", variant=raw)],
        [], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m3_verify_red_src_token_channel():
    raw, projected = "M3-raw-verify-src", "M3-projected-verify-src"
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", src_token=raw)],
        [], identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m4_liveness_variant_channel():
    raw, projected = "M4-raw-live-variant", "M4-projected-live-variant"
    out = _render_rejections(
        [], [LivenessRejection(genome="g", flags={}, reason="trace-empty", variant=raw)],
        identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m5_liveness_src_token_channel():
    raw, projected = "M5-raw-live-src", "M5-projected-live-src"
    out = _render_rejections(
        [], [LivenessRejection(genome="g", flags={}, reason="trace-empty", src_token=raw)],
        identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m6_liveness_build_attempt_channel():
    raw, projected = "M6-raw-attempt", "M6-projected-attempt"
    out = _render_rejections(
        [], [LivenessRejection(
            genome="g", flags={}, reason="trace-empty",
            extra={"build_attempt_id": raw},
        )],
        identity_projection=_OneChannelProjection("build_attempt_id", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m7_liveness_build_admission_channel():
    raw, projected = "M7-raw-admission", "M7-projected-admission"
    out = _render_rejections(
        [], [LivenessRejection(
            genome="g", flags={}, reason="trace-empty",
            extra={"build_admission_receipt_sha256": raw},
        )],
        identity_projection=_OneChannelProjection(
            "build_admission_receipt_sha256", raw, projected,
        ),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m8_diff_quarantine_variant_channel():
    raw, projected = "M8-raw-diff-variant", "M8-projected-diff-variant"
    out = _render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", variant=raw,
        )], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m9_diff_quarantine_src_token_channel():
    raw, projected = "M9-raw-diff-src", "M9-projected-diff-src"
    out = _render_rejections(
        [], [], diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", src_token=raw,
        )], identity_projection=_OneChannelProjection("src_token", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projection_m10_verify_abort_variant_channel():
    raw, projected = "M10-raw-abort-variant", "M10-projected-abort-variant"
    out = _render_rejections(
        [], [], abort_signals=[VerifyAbortSignal(
            variant=raw, genome="g", commits=1, aborts=1, is_stock=False,
        )], identity_projection=_OneChannelProjection("variant", raw, projected),
    )
    _assert_one_projection_channel(out, raw, projected)


def test_projected_candidate_label_is_never_rendered_as_variant_field():
    raw = "raw-candidate"
    projected = "candidate-0001"
    projection = _OneChannelProjection("variant", raw, projected)
    out = _render_rejections(
        [Rejection(genome="g", flags={}, verdict="indeterminate", variant=raw)],
        [LivenessRejection(
            genome="g", flags={}, reason="trace-empty", variant=raw,
        )],
        diff_rejections=[DiffQuarantineRejection(
            genome="g", flags={}, subtype="fixture", reason="fixture", variant=raw,
        )],
        abort_signals=[VerifyAbortSignal(
            variant=raw, genome="g", commits=1, aborts=1, is_stock=False,
        )],
        identity_projection=projection,
    )
    assert out.count(f"candidate_label={projected}") == 4
    assert f"variant={projected}" not in out


def test_synthetic_rejection_heading_has_closed_origin_not_workload_provenance():
    out = _render_rejections(
        [Rejection(
            genome="g", flags={}, verdict="indeterminate",
            origin_kind="synthetic-fixture",
        )],
        [],
        identity_projection=IdentityProjection.RAW,
    )
    assert "origin_kind=synthetic-fixture" in out
    assert "workload:" not in out
    with pytest.raises(ValueError, match="origin_kind"):
        _render_rejections(
            [Rejection(
                genome="g", flags={}, verdict="indeterminate",
                origin_kind="unknown",
            )],
            [],
            identity_projection=IdentityProjection.RAW,
        )


def test_critic_digest_direct_cli_uses_canonical_projection_type():
    layout = _tmp_layout()
    attempt = _start_attempt(layout, _G.format(b=1, l=1, t=0, w=0))
    _attempt_event(
        layout, attempt, STAGE_ABORT, {"reason": "direct-cli-fixture"},
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(_ORCH) / "critic" / "digest.py"),
            "--campaign-dir",
            layout.root,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "# rejections" in completed.stdout
    assert "Traceback" not in completed.stderr


def test_render_rejections_requires_identity_projection():
    with pytest.raises(TypeError, match="identity_projection"):
        _render_rejections([], [])
    with pytest.raises(TypeError, match="IdentityProjection"):
        _render_rejections([], [], identity_projection=None)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}"); failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
