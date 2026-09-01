# -*- coding: utf-8 -*-
"""P3 段6前提タスク (i): sort comparator 空間の機械列挙 sweep (偵察、D44)。

段 6 本走の前に sort comparator 空間の性能地形を機械列挙で偵察し、coder 到達点
(段 5 iteration 1 = stock 同値順序) の空間内位置を記述する。設計は 3 レンズ敵対
レビュー (2026-07-10、事前登録整合/機構安全/統計) の must/should 全反映済み。

**位置づけ = 偵察 (preliminary)。事前登録 (phase3-main-experiment.md) が定義する
どの実験構成 (sweep-matched / sweep-ceiling / ベースライン 3) でもない**:
  - 失敗条件 (c) の判定は出さない — 16 対 1 は「同一試行予算」要件に反し、
    本空間は coder iteration 1 出力を見た後の設計 (grid pre-commitment 未充足)、
    かつ random-variation アーム欠落 (非 SWO ハング (D42) を機械検査なしで踏むため
    列挙のみに scope 縮小。Tier0+SWO 検査つき生成器は段 6 タスク (c))。
  - **firewall: 段 6 の正式 grid / (c) 判定は本結果を材料流用せずゼロから再導出する。**
  - 出力は記述統計 + 限定つき観察のみ (「軸の生死」を断定しない)。floor 0.030 は
    stock silo 実測の暫定流用の参考線であり、high-abort 点 (退化点 + abort 率が
    stock 対比 2 倍超) には適用しない (事前登録「floor の流用禁止」)。
  - 本 sweep は fairness 偏向 (D41 型15) を検出しない。
  - write-heavy の S2 verify は S2_FLAGS 固定 (rr50) のため被覆は off-workload。

列挙空間 = 構文契約 (hole が参照できる全メンバ storage_/key_/rcdptr_ × asc/desc ×
辞書式順列 prefix) + 退化点 nosort。先頭キーが全順序 (key_ は (storage,key) 一意 +
YCSB 単一 storage、rcdptr_ はポインタ一意) なら後続キー到達不能のため打ち切り。
型 14 (非 SWO comparator) について、列挙候補は構成的に SWO を満たすよう生成する
(SWO-by-construction: キー比較の辞書式合成は SWO を保存し、恒 false も valid な SWO)。
転写ミス由来の非 SWO への機械 backstop は diff 検疫、permutation 保存 assert、
本モジュールテストの Python 有限モデル SWO 総当たり検査 (test_s6_sort_sweep.py)。
独立 SWO oracle (sort_swo_oracle) は versioned な有限 corpus 上の反例発見器であって
全入力に対する strict weak ordering の証明ではなく、coder 自律ループが合成する comparator
を対象とする経路で、s6 sweep からは呼ばれない。D42 実測では write_set_.size()>=16 の
非 SWO comparator はハングしうる。

auditor 段は持たない: auditor は LLM 生成物の reward hack の番人 (D38/D43) であり、
本候補は信頼中核が構成原則から機械生成する (全文が本ソースから決定論的に導出され、
provenance を campaign identity と reports/ に焼く)。AuditorVerdict の自己生成
(self-attest) はしない — 「自己申告 pass」の前例を作らないため段そのものを省く。

実行 (計測機で直列、実行前に single-tenant を確認):
  python3 campaign/s6_sort_sweep.py balanced                    # 本走 16 点
  python3 campaign/s6_sort_sweep.py write-heavy                 # 本走 16 点
  python3 campaign/s6_sort_sweep.py balanced --report     # 集計のみ (計測なし)
  python3 campaign/s6_sort_sweep.py balanced --remeasure --names stock,sk_aa,k_asc
      # cross-run 裏取り (別 campaign = 別 trial に分離、argmax winner+stock+sk_aa)
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (campaign_lock as campaign_lock_codec, env_contract, ident,  # noqa: E402
               pin, pipeline, screening_driver, source_digest, wal)
from . import p3_s4_loop as L                              # noqa: E402
from . import p3_s4_loop_sort as S                         # noqa: E402
from .artifact_admission import (                          # noqa: E402
    ArtifactAdmissionError,
    CampaignReadPurpose,
    CertifiedCampaignView,
    require_admitted_campaign,
    require_certified_campaign_view,
    require_persisted_certified_commit,
)
from .build_admission import (BuildAdmissionError,         # noqa: E402
                                      BuildRunContext, GeneratorId,
                                      attest_generator_output,
                                      build_run_context)
from .layout import campaign_layout                       # noqa: E402
from .loop import run_campaign                            # noqa: E402
from .model import (STAGE_ABORT, STAGE_BENCH_DONE,        # noqa: E402
                            STAGE_COMMIT, CampaignConfig, Genome)
from .p2_2 import (EXTIME, RECORDS, REPS, THREADS,        # noqa: E402
                           _assert_single_tenant)
from .pipeline import (SEARCH_CONFIG_VERIFY_KEY,          # noqa: E402
                               VERIFY_LEGACY_PLUS_S2, PerfConfig, variant_id)


PIN = pin.CURRENT_PIN                 # 511c953 (sort 軸系 driver と同一 pin)
ENV_TAG = "linux-baremetal"
CLK = 1800
NUMA = ["numactl", "--interleave=all"]

SPACE_VERSION = "mech-enum-v1"
TRIAL_MAIN = "p3-s6-sort-sweep"

# floor: stock silo (B0-L-W0, t48/1M/extime3) 実測の暫定流用 (D19)。参考線のみ —
# high-abort 点には適用しない (事前登録「floor の流用禁止」、レビュー must-fix)。
FLOOR_CV = 0.030
HIGH_ABORT_FACTOR = 2.0   # stock 対比この倍率超の abort 率は floor 未較正 = 判定不能

# 計測 workload (backoff_sweep と同じ座標系。read-heavy は sort 感度が無いので回さない)
WORKLOADS = {
    "balanced": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
    "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
}


# ==== 列挙空間 (構文契約からの機械的導出。ラベルをコメントで付けない —
#      src_token は preprocess 後ハッシュでコメントが消えるため) =================

def _one(member: str, asc: bool) -> str:
    return f"a.{member} < b.{member}" if asc else f"b.{member} < a.{member}"


def _mk(body_lines: List[str]) -> str:
    """p3_s4_loop_sort.main の fixture_impl と同一フレーム (実機 E2E 実証済み形式)。"""
    body = "\n".join("         " + ln for ln in body_lines)
    return ("  sort(write_set_.begin(), write_set_.end(),\n"
            "       [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b)"
            " -> bool {\n" + body + "\n"
            "       });")


def _single(member: str, asc: bool) -> str:
    return _mk([f"return {_one(member, asc)};"])


def _two(member2: str, asc1: bool, asc2: bool) -> str:
    return _mk([f"return a.storage_ != b.storage_ ? {_one('storage_', asc1)}",
                f"                                : {_one(member2, asc2)};"])


# nosort は無名引数 (通常形は -Werror=unused-parameter でビルド不能 — 機構レンズ
# must-fix、GCC13 実測)。恒 false は valid な SWO (全要素同値)。
_NOSORT_IMPL = ("  sort(write_set_.begin(), write_set_.end(),\n"
                "       [](const WriteElement<Tuple>&, const WriteElement<Tuple>&)"
                " -> bool {\n"
                "         return false;\n"
                "       });")

# (name, category, implementation)。category:
#   full-order = 全 trx が同一全順序で施錠 (性能地形の主対象)
#   degenerate = 順序不定 (s_*: YCSB 単一 storage で恒 tie / nosort: 全同値)。
#                abort 増・unstable が予想される観測点。レンジ集計から分離する。
CANDIDATES: List[Tuple[str, str, str]] = [
    ("s_asc", "degenerate", _single("storage_", True)),
    ("s_desc", "degenerate", _single("storage_", False)),
    ("k_asc", "full-order", _single("key_", True)),
    ("k_desc", "full-order", _single("key_", False)),
    ("p_asc", "full-order", _single("rcdptr_", True)),
    ("p_desc", "full-order", _single("rcdptr_", False)),
    ("sk_aa", "full-order", _two("key_", True, True)),
    ("sk_ad", "full-order", _two("key_", True, False)),
    ("sk_da", "full-order", _two("key_", False, True)),
    ("sk_dd", "full-order", _two("key_", False, False)),
    ("sp_aa", "full-order", _two("rcdptr_", True, True)),
    ("sp_ad", "full-order", _two("rcdptr_", True, False)),
    ("sp_da", "full-order", _two("rcdptr_", False, True)),
    ("sp_dd", "full-order", _two("rcdptr_", False, False)),
    ("nosort", "degenerate", _NOSORT_IMPL),
]

STOCK_NAME = "stock"      # SORT_VARIANT=0 (#else 枝 = 素の operator< sort)。
CODER_EQUIV = "sk_aa"     # coder iteration 1 の到達順序と同値な点 (第 3 段到達不能)。

# provenance の自蔵性 (stock は hole 挿入でないため実効 comparator を注記で残す)
STOCK_IMPL_NOTE = ("SORT_VARIANT=0 の #else 枝 (テンプレ骨格そのまま) = "
                   "sort(write_set_.begin(), write_set_.end()) — WriteElement::operator< "
                   "による (storage_, key_) 昇順 2 段辞書式 (silo_op_element.hh)")


def candidate_names() -> List[str]:
    return [STOCK_NAME] + [n for n, _c, _i in CANDIDATES]


# ==== campaign 構成 ===========================================================

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def config_for(tag: str, trial: str = TRIAL_MAIN) -> CampaignConfig:
    """workload を search_config に焼く (ycsb + workload タグ) — balanced/write-heavy の
    identity をハッシュで分離し variant_id クロス汚染を構造的に防ぐ (機構レンズ
    should-fix、backoff_sweep.config_for と同型)。"""
    workload = WORKLOADS[tag]
    cfg = CampaignConfig(
        spec_slug=f"p3-s6-sort-sweep-{tag}", search_tag="sweep",
        spec_content=(
            "P3 段6前提 (i): sort comparator 空間の機械列挙 sweep (偵察、D44)。"
            "preliminary = 事前登録外カテゴリ、断定 verdict なし、(c) 判定は出さない。"
            f"空間 = {SPACE_VERSION}: keys{{storage_,key_,rcdptr_}} x dir{{asc,desc}} x "
            f"lexicographic-prefix + nosort、全点 SWO-by-construction。workload={tag}。"),
        ccbench_commit=PIN,
        search_config={"scale": "silo", "axis": S.MARKER_ID,
                       "generator": SPACE_VERSION,
                       "space": "keys{S,K,P}xdir{a,d}xprefix+nosort",
                       "workload": tag, "ycsb": workload,
                       "records": RECORDS, "threads": THREADS,
                       SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_S2},
        trial=trial)
    context = build_run_context(generator_id=GeneratorId.S6_SORT_SWEEP)
    cfg = ident.bind_admission_policy(cfg, context.policy)
    return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))


def perf_for(tag: str) -> PerfConfig:
    """p2_2 確定動作点 (D15: t48/1M/extime3/reps5)。配線規模 (t4/100k) では contention が
    弱く施錠順序の影響が観測できない懸念が支配的 (読解 2026-07-10)。"""
    return PerfConfig(records=RECORDS, threads=THREADS, workload=WORKLOADS[tag],
                      extime=EXTIME, reps=REPS)


def _genome(sort_variant: int) -> Genome:
    return Genome("silo", {**S._BASE, "SORT_VARIANT": sort_variant})


def _capability_resolver(name: str, context: BuildRunContext, implementation: str | None):
    """Return source-bound capability evidence for one deterministic candidate."""
    if name == STOCK_NAME:
        return lambda _source: None
    input_sha = hashlib.sha256((implementation or "").encode("utf-8")).hexdigest()
    return lambda source: attest_generator_output(
        context, source, generator_input_sha256=input_sha,
    )


# ==== 駆動 ====================================================================

def run_sweep(tag: str, names: Optional[List[str]] = None, trial: str = TRIAL_MAIN,
              isolate: bool = True, log=print, *,
              screening_enabled: bool = False,
              calibration_dir: str = "") -> Dict[str, Dict]:
    """候補ごとに applied(骨格) → quarantine(write) → run_campaign を直列に回す。

    1 候補 = 1 run_campaign 呼び出し (同一 campaign dir に WAL 追記、variant_id は
    src_token で分岐)。中断再開は WAL replay (評価済み variant はスキップ)。失敗は
    variant 単位で abort 隔離され campaign は継続する (pipeline 既存)。
    返り値 = name → {variant_id, category, src_token, outcome}。"""
    from .patchharness import applied, assert_pinned_clean, checkout

    _assert_single_tenant()
    root = _repo_root()
    fixed_sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(fixed_sub, PIN)

    sel_names = names if names is not None else candidate_names()
    unknown = [n for n in sel_names if n not in candidate_names()]
    if unknown:
        raise ValueError(f"未知の候補名: {unknown} (選択肢: {candidate_names()})")

    build_context = build_run_context(generator_id=GeneratorId.S6_SORT_SWEEP)
    cfg = ident.bind_admission_policy(config_for(tag, trial), build_context.policy)
    perf = perf_for(tag)
    layout = campaign_layout(str(ident.campaign_id(cfg)))
    if not screening_enabled:
        layout.ensure()
    patch = os.path.join(root, S.TEMPLATE_PATCH)

    wt_cm = checkout(PIN, base_dir=fixed_sub) if isolate else \
        contextlib.nullcontext(fixed_sub)
    cache_root = os.path.join(fixed_sub, "build-variants") if isolate else ""

    prov: Dict[str, Dict] = {}
    if not screening_enabled:
        log(f"\n=== s6 sort sweep  workload={tag}  trial={trial}  "
            f"{len(sel_names)} 点 (campaign {layout.root}) ===")
    try:
        with wt_cm as sub:
            active_screening = None
            if screening_enabled:
                baseline_ref = _candidate_ref(STOCK_NAME, cfg, sub, patch)
                baseline_entry = {}

                def measure_baseline(screen_cfg, screen_layout):
                    baseline_entry.update(_eval_one(
                        STOCK_NAME, screen_cfg, perf, screen_layout, sub, patch,
                        cache_root, build_context=build_context,
                        log=log, force=True))

                prepared = screening_driver.prepare_screening_campaign(
                    cfg, WORKLOADS[tag], baseline_ref, measure_baseline,
                    protocol=_genome(0).protocol,
                    authorization_contract=env_contract.authorize(ENV_TAG),
                    env_tag=ENV_TAG, clocks_per_us=CLK, numactl=NUMA,
                    calibration_dir=calibration_dir, build_context=build_context)
                cfg, layout, active_screening = (
                    prepared.cfg, prepared.layout, prepared.screening)
                n_points = len(set(sel_names) | {STOCK_NAME})
                log(f"\n=== s6 sort sweep  workload={tag}  trial={trial}  "
                    f"{n_points} 点 (screening opt-in, campaign {layout.root}) ===")
                prov[STOCK_NAME] = baseline_entry
            # provenance/quarantine reject より前に identity 照合済みの active attempt を閉じる。
            ident.ensure_resumable_attempts(
                cfg, layout, admission_policy=build_context.policy,
            )
            if screening_enabled:
                _write_provenance(layout, tag, trial, prov)
            for name in sel_names:
                if screening_enabled and name == STOCK_NAME:
                    continue
                try:
                    entry = _eval_one(name, cfg, perf, layout, sub, patch, cache_root,
                                      build_context=build_context, log=log,
                                      screening=active_screening)
                except (wal.WalAppendError, wal.WalFramingError):
                    # 壊れた同一 WAL に driver-error/reject を重ねず sweep 全体を止める。
                    raise
                except BuildAdmissionError:
                    # admission の誤配線を候補固有の transient driver error に丸めない。
                    raise
                except Exception as e:
                    # run_campaign の外側 (applied/quarantine/resolve) の例外も候補単位で
                    # 隔離する — 1 点の transient 失敗で全走を落とし成果ゼロにしない
                    # (実装後レビュー should-fix。run_campaign 内は自前の per-variant 隔離)。
                    log(f"  ✗ {name}: driver 層エラーで隔離 — {type(e).__name__}: {e}")
                    entry = {"variant_id": None, "category": None, "src_token": None,
                             "outcome": "driver-error", "error": str(e)}
                prov[name] = entry
                _write_provenance(layout, tag, trial, prov)   # 逐次書き (中断でも復元可能)
    finally:
        if prov:
            _write_provenance(layout, tag, trial, prov)
    return prov


def _candidate_ref(name: str, cfg: CampaignConfig, sub: str, patch: str) -> str:
    """candidate の確定variant id。screening identityを実測前に焼くために使う。"""
    from .patchharness import applied
    if name == STOCK_NAME:
        impl, genome = None, _genome(0)
    else:
        _cat, impl = next((c, i) for n, c, i in CANDIDATES if n == name)
        genome = _genome(1)
    with applied(patch, PIN, sub):
        if impl is not None:
            res, _b, _e, _wd = L.quarantine(
                sub, impl, marker_id=S.MARKER_ID, source_rel=S.SOURCE_REL, write=True)
            if not res.passed:
                raise ValueError(f"baseline candidate {name} がdiff検疫を通らない")
        src_tok = source_digest.resolve(genome, cfg.ccbench_commit, sub)
    return variant_id(genome, src_tok)


def _eval_one(name: str, cfg: CampaignConfig, perf: PerfConfig, layout, sub: str,
              patch: str, cache_root: str, log=print, *, screening=None,
              force: bool = False, build_context: BuildRunContext) -> Dict:
    from .patchharness import applied
    if name == STOCK_NAME:
        cat, impl = "stock", None
        genome = _genome(0)
    else:
        cat, impl = next((c, i) for n, c, i in CANDIDATES if n == name)
        genome = _genome(1)

    with applied(patch, PIN, sub):
        if impl is not None:
            res, _b, _e, _wd = L.quarantine(sub, impl, marker_id=S.MARKER_ID,
                                            source_rel=S.SOURCE_REL, write=True)
            if not res.passed:
                v = L.record_diff_reject(layout, genome, impl, res, env_tag=ENV_TAG)
                log(f"  ✗ {name}: diff 検疫 reject ({res.digest.get('subtype')}) — "
                    f"機械生成候補が検疫を通らないのは driver のバグ (要修正)")
                return {"variant_id": v, "category": cat, "src_token": None,
                        "outcome": "quarantine-reject"}
        src_tok = source_digest.resolve(genome, cfg.ccbench_commit, sub)
        vid = variant_id(genome, src_tok)
        capability_resolver = _capability_resolver(name, build_context, impl)
        log(f"  --- {name} ({cat}) variant={vid} src={src_tok[:12]} ---")
        if screening is None and not force:
            summary = run_campaign(cfg, [genome], perf, ENV_TAG, CLK, numactl=NUMA,
                                   log=log, ccbench_dir=sub, cache_root=cache_root,
                                   authorization_contract=env_contract.authorize(ENV_TAG),
                                   build_context=build_context,
                                   declared_use_class="official",
                                   capability_resolver=capability_resolver)
            r = summary.results[0] if summary.results else None
        else:
            r = screening_driver.evaluate_candidate(
                cfg, layout, genome, perf, ENV_TAG, CLK, screening=screening,
                authorization_contract=env_contract.authorize(ENV_TAG),
                build_context=build_context,
                capability_resolver=capability_resolver,
                numactl=NUMA, src_token=src_tok, force=force, log=log,
                ccbench_dir=sub, cache_root=cache_root)
    if r is not None:
        if r.certified and not r.aborted:
            outcome = "certified"
        else:
            terminal = wal.replay(layout, admission_policy=build_context.policy).get(vid)
            reason = (terminal.last_terminal.payload.get("reason")
                      if terminal and terminal.last_terminal else None)
            outcome = ("screen-rejected"
                       if reason == pipeline.SCREEN_REJECTION_REASON else "aborted")
    else:
        # WAL replay で skip (中断再開時)。terminal は commit も abort も含むため WAL を
        # 引いて区別する — 一律 "replayed" にすると前 run の abort 点が完了サマリ/exit
        # code から消える (実装後レビュー should-fix)。
        outcome = _replay_outcome(layout, vid, build_context)
    return {"variant_id": vid, "category": cat, "src_token": src_tok,
            "outcome": outcome}


def _replay_snapshot(layout, build_context: BuildRunContext):
    try:
        lock_bytes = Path(layout.lock_file).read_bytes()
        decoded_lock = campaign_lock_codec.decode_campaign_lock_bytes(lock_bytes)
    except (OSError, campaign_lock_codec.CampaignLockCodecError) as exc:
        raise ArtifactAdmissionError(
            "replay campaign lock cannot be read or decoded"
        ) from exc
    campaign_lock_sha256 = hashlib.sha256(lock_bytes).hexdigest()
    records = wal.read_records(layout)
    try:
        lock_sha256_after_records = hashlib.sha256(
            Path(layout.lock_file).read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise ArtifactAdmissionError(
            "replay campaign lock cannot be re-read after WAL"
        ) from exc
    if lock_sha256_after_records != campaign_lock_sha256:
        raise ArtifactAdmissionError(
            "replay campaign lock changed while reading WAL"
        )
    wal.validate_commit_contract_bindings(records, campaign_lock=decoded_lock)
    wal.validate_trigger_bindings(records, campaign_lock=decoded_lock)
    wal._validate_attempt_topology(
        records,
        admission_policy=build_context.policy,
        campaign_lock=decoded_lock,
    )
    return records, wal.replay_admitted_records(records), campaign_lock_sha256


def _replay_outcome(layout, vid: str, build_context: BuildRunContext) -> str:
    records, states, campaign_lock_sha256 = _replay_snapshot(
        layout, build_context,
    )
    state = states.get(vid)
    if state is not None and state.committed:
        commit_record = next(
            record for record in reversed(records)
            if record.variant == vid and record.stage == STAGE_COMMIT
        )
        require_persisted_certified_commit(
            records, commit_record,
            campaign_lock_sha256=campaign_lock_sha256,
        )
        return "replayed-certified"
    if state is not None and state.aborted:
        return "replayed-aborted"
    return "replayed-unknown"


def _write_provenance(layout, tag: str, trial: str, prov: Dict[str, Dict]) -> str:
    """name → variant_id / implementation 全文の対応を reports/ に凍結する。
    variant_id は src_token 由来で候補名を含まないため、この対応が無いと WAL から
    地形を復元できない (proof-chain 成果物 (runs/ 等) には書かない — guard_write)。
    既存 entries とは merge する (部分 --names 実行で全点の対応を truncate しない —
    実装後レビュー nit)。"""
    impls = {n: i for n, _c, i in CANDIDATES}
    impls[STOCK_NAME] = STOCK_IMPL_NOTE
    path = os.path.join(layout.root, "reports", "s6_sort_sweep_provenance.json")
    existing: Dict[str, Dict] = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f).get("entries", {})
        except (json.JSONDecodeError, OSError):
            existing = {}
    entries = {**existing,
               **{n: {**e, "implementation": impls.get(n)} for n, e in prov.items()}}
    doc = {"space_version": SPACE_VERSION, "workload": tag, "trial": trial,
           "pin": PIN, "floor_cv_provisional": FLOOR_CV,
           "coder_equiv": CODER_EQUIV, "entries": entries}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return path


# ==== 集計 (記述統計のみ — 断定 verdict を出さない) ============================

def _rows_from_certified_view(
        view: CertifiedCampaignView,
        prov_entries: Dict[str, Dict],
) -> List[Dict]:
    view = require_certified_campaign_view(view)
    by_variant: Dict[str, Dict[str, Dict]] = {}
    for record in view.records:
        by_variant.setdefault(record.variant, {})[record.stage] = record.payload
    rows = []
    for name, e in prov_entries.items():
        vid = e.get("variant_id")
        if not vid:
            continue
        recs = by_variant.get(vid, {})
        commit = recs.get(STAGE_COMMIT)
        certified = commit is not None
        # BENCH_DONE は screening 経路では uncertified のまま存在し得る。性能値は
        # COMMIT の存在で gate し、探索・正式レポートへ漏らさない。
        bench = (recs.get(STAGE_BENCH_DONE) or {}) if certified else {}
        abort = recs.get(STAGE_ABORT)
        li = bench.get("leading_indicators") or {}
        rows.append({
            "name": name, "category": e.get("category"), "variant_id": vid,
            "certified": certified,
            "aborted": not certified and abort is not None,
            "abort_reason": (abort or {}).get("reason"),
            "median_tps": bench.get("median_tps"), "cv": bench.get("cv"),
            "unstable": bool(bench.get("unstable")),
            "abort_rate": li.get("abort_rate"), "ipc": li.get("ipc"),
            "llc_miss_rate": li.get("llc_miss_rate"),
        })
    return rows


def _load_certified_rows(
        layout, prov_entries: Dict[str, Dict],
) -> tuple[CertifiedCampaignView, List[Dict]]:
    view = require_certified_campaign_view(require_admitted_campaign(
        layout, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    return view, _rows_from_certified_view(view, prov_entries)


def _load_rows(layout, prov_entries: Dict[str, Dict]) -> List[Dict]:
    return _load_certified_rows(layout, prov_entries)[1]


def report(tag: str, trial: str = TRIAL_MAIN, log=print) -> Optional[str]:
    """WAL 直読みの記述統計レポート。unstable 点はレンジ集計から除外し (pipeline が
    per-variant に焼いた unstable フラグを読む — digest.load_workload 経路は unstable が
    届かない既知限界があるため使わない)、退化点は valid full-order と分離して別掲する
    (統計レンズ must-fix)。"""
    context = build_run_context(generator_id=GeneratorId.S6_SORT_SWEEP)
    cfg = ident.bind_admission_policy(config_for(tag, trial), context.policy)
    layout = campaign_layout(str(ident.campaign_id(cfg)))
    ppath = os.path.join(layout.root, "reports", "s6_sort_sweep_provenance.json")
    if not os.path.exists(ppath):
        log(f"provenance がまだ無い: {ppath} (先に本走を回す)")
        return None
    with open(ppath, encoding="utf-8") as f:
        prov = json.load(f)
    view, rows = _load_certified_rows(layout, prov["entries"])

    ok = [r for r in rows if r["certified"] and r["median_tps"] is not None]
    stock = next((r for r in ok if r["name"] == STOCK_NAME), None)
    stable = [r for r in ok if not r["unstable"]]
    full = [r for r in stable if r["category"] == "full-order"]
    degen = [r for r in stable if r["category"] == "degenerate"]
    screen_rejected = [
        r for r in rows
        if not r["certified"]
        and r["abort_reason"] == pipeline.SCREEN_REJECTION_REASON
    ]
    other_aborted = [
        r for r in rows
        if r["aborted"]
        and r["abort_reason"] != pipeline.SCREEN_REJECTION_REASON
    ]

    lines: List[str] = []
    w = lines.append
    w(f"# s6 sort sweep 偵察レポート — workload={tag} trial={trial}")
    w("")
    w(f"- **受理目的**: `{view.read_purpose.value}`")
    w("- **campaign_verifier_epoch**: "
      f"`{view.campaign_verifier_epoch.campaign_verifier_epoch}`")
    w(f"- **epoch identity scope**: {view.campaign_verifier_epoch.identity_scope}")
    w(f"- **epoch excluded scope**: {view.campaign_verifier_epoch.excluded_scope}")
    w("")
    w("**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。")
    w("**限定 (必読):** (1) 失敗条件 (c) の判定は出さない (16対1 の非対称比較・空間は "
      "coder iter1 後の設計で grid pre-commitment 未充足・random-variation アーム欠落)。"
      "(2) floor 0.030 は stock silo 実測の暫定流用の参考線 — high-abort 点 (退化点 + "
      f"abort 率 stock 比 {HIGH_ABORT_FACTOR} 倍超) は floor 未較正 = 判定不能。"
      "(3) 本 sweep は fairness 偏向 (D41 型15) を検出しない。"
      "(4) write-heavy の S2 verify は rr50 固定 (off-workload 被覆)。"
      "(5) 段 6 の正式 grid / (c) 判定は本結果を材料流用しない (firewall)。")
    w("**集計母集団:** 数値テーブルとレンジ・min・best は certified 生存点限定。"
      "screening 正常棄却は未認証のため reason だけを別掲し、性能数値を描画しない。")
    w("")
    w("| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |")
    w("|---|---|---:|---:|---:|---|---|---|")
    for r in sorted(ok, key=lambda x: -(x["median_tps"] or 0)):
        note = []
        if r["name"] == CODER_EQUIV:
            note.append("coder iter1 同値順序")
        if r["name"] == STOCK_NAME:
            note.append("対照 (operator<)")
        elif _floor_uncalibrated(r, stock):
            note.append("high-abort/未較正: floor 判定不能")
        w(f"| {r['name']} | {r['category']} | "
          f"{_fmt(r['median_tps'])} | {_fmt_pct(r['cv'])} | {_fmt_pct(r['abort_rate'])} | "
          f"{'⚠' if r['unstable'] else ''} | {'✓' if r['certified'] else '✗'} | "
          f"{'; '.join(note)} |")
    w("")

    if screen_rejected:
        w("### screening 正常棄却 (未認証のため性能数値なし)")
        w("")
        w("| 点 | 分類 | reason |")
        w("|---|---|---|")
        for r in sorted(screen_rejected, key=lambda x: x["name"]):
            w(f"| {r['name']} | {r['category']} | {r['abort_reason']} |")
        w("")
    if other_aborted:
        w("### その他の非認証 ABORT (性能数値なし)")
        w("")
        w("| 点 | 分類 | reason |")
        w("|---|---|---|")
        for r in sorted(other_aborted, key=lambda x: x["name"]):
            w(f"| {r['name']} | {r['category']} | {r['abort_reason']} |")
        w("")

    if full:
        best, worst = max(full, key=_tps), min(full, key=_tps)
        w(f"**valid 全順序点 (certified 生存点限定、stable, n={len(full)}):** "
          f"max={best['name']} {_fmt(_tps(best))} tps / min={worst['name']} "
          f"{_fmt(_tps(worst))} tps / レンジ {_rel(best, worst)} "
          f"(選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)")
        if stock:
            w(f"**best vs stock:** {best['name']} {_rel(best, stock)} "
              f"(参考線: 暫定 floor ±{FLOOR_CV:.1%}。未再測 = 位置関係は暫定、"
              f"断定は cross-run 再測後)")
    if degen:
        w(f"**退化点 (別掲、レンジ集計外):** " + ", ".join(
            f"{r['name']} {_fmt(_tps(r))} tps" for r in degen))
    excl = [r for r in ok if r["unstable"]]
    if excl:
        w(f"**unstable 除外点:** " + ", ".join(r["name"] for r in excl))
    ck = next((r for r in rows if r["name"] == CODER_EQUIV), None)
    if ck is not None and any(r["name"] == CODER_EQUIV for r in full):
        rank = 1 + sum(1 for r in full if _tps(r) > _tps(ck))
        w(f"**coder 到達点の位置 (記述のみ):** {CODER_EQUIV} (coder iter1 と同値順序) は "
          f"valid 全順序 {len(full)} 点中 {rank} 位。coder は iteration 1 (n=1) 中間時点の"
          f"提案であり最終到達ではない。coder 実測値 (配線規模 t4/100k) とは規模が"
          f"異なるため直接比較しない (代理 = 本 sweep の {CODER_EQUIV} 点)。")
    elif ck is not None:
        w(f"**coder 到達点の位置:** {CODER_EQUIV} は "
          f"{'abort' if ck['aborted'] else ('unstable' if ck['unstable'] else '未計測')} "
          f"のため空間内位置づけは保留 (偽の順位を出さない。WAL: {ck['abort_reason']})。")

    text = "\n".join(lines)
    rpath = os.path.join(layout.root, "reports", f"s6_sort_sweep_report_{trial}.md")
    os.makedirs(os.path.dirname(rpath), exist_ok=True)
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    log(text)
    log(f"\nレポート: {rpath}")
    return rpath


def _tps(r: Dict) -> float:
    return r["median_tps"] or 0.0


def _floor_uncalibrated(r: Dict, stock: Optional[Dict]) -> bool:
    """floor (暫定 0.030) を適用してはいけない点か。退化点は stock の有無と無関係に
    無条件で True (設計 §4)。非退化点は abort 率が stock 比 HIGH_ABORT_FACTOR 倍超で
    True、比較材料 (stock または abort_rate) が欠けたら fails-closed で True
    (実装後レビュー should-fix: fails-open だった分岐の反転)。"""
    if r["category"] == "degenerate":
        return True
    ab = r.get("abort_rate")
    sab = stock.get("abort_rate") if stock else None
    if ab is None or sab in (None, 0):
        return True
    return ab > HIGH_ABORT_FACTOR * sab


def _rel(a: Dict, b: Dict) -> str:
    ta, tb = _tps(a), _tps(b)
    return f"{(ta - tb) / tb:+.2%}" if tb else "n/a"


def _fmt(x) -> str:
    return f"{x:,.0f}" if isinstance(x, (int, float)) else "—"


def _fmt_pct(x) -> str:
    return f"{x * 100:.2f}" if isinstance(x, (int, float)) else "—"


# ==== CLI =====================================================================

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="P3 段6前提 (i): sort comparator 機械列挙 sweep (偵察)")
    ap.add_argument("workload", choices=sorted(WORKLOADS.keys()))
    ap.add_argument("--names", help="カンマ区切りの候補名 (省略 = 全 16 点)")
    ap.add_argument("--remeasure", action="store_true",
                    help="cross-run 裏取り (trial を分けた別 campaign)。--names 必須")
    ap.add_argument("--report", action="store_true", help="集計のみ (計測なし)")
    ap.add_argument("--trial", default=None, help="trial 上書き (通常は使わない)")
    ap.add_argument("--no-isolate-worktree", action="store_true",
                    help="worktree 隔離を無効化 (デバッグ用。既定 ON)")
    ap.add_argument("--list", action="store_true", help="候補と implementation を表示")
    ap.add_argument("--screening", action="store_true",
                    help="bench-first screeningをopt-in (既定off)")
    ap.add_argument("--calibration-dir", default="",
                    help="between_run_noise_*.jsonの置き場")
    a = ap.parse_args(argv if argv is not None else sys.argv[1:])

    if a.list:
        for n, c, i in CANDIDATES:
            print(f"--- {n} ({c}) ---\n{i}")
        return 0

    trial = a.trial or (f"{TRIAL_MAIN}-remeasure1" if a.remeasure else TRIAL_MAIN)
    if a.remeasure and not a.names:
        print("--remeasure には --names (argmax winner,stock,sk_aa 等) が必須")
        return 2
    names = [n.strip() for n in a.names.split(",")] if a.names else None

    if a.report:
        if a.screening:
            print("--report と --screening の同時指定は不可 (screening run直後のWALを参照すること)")
            return 2
        return 0 if report(a.workload, trial=trial) else 1

    prov = run_sweep(a.workload, names=names, trial=trial,
                     isolate=not a.no_isolate_worktree,
                     screening_enabled=a.screening,
                     calibration_dir=a.calibration_dir)
    bad = {n: e for n, e in prov.items()
           if e["outcome"] not in ("certified", "replayed-certified", "screen-rejected")}
    print(f"\n=== s6 sort sweep 完了: {len(prov) - len(bad)}/{len(prov)} 点 OK ===")
    if bad:
        for n, e in bad.items():
            print(f"  ✗ {n}: {e['outcome']}")
    if not a.screening:
        report(a.workload, trial=trial)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
