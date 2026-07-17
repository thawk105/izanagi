# -*- coding: utf-8 -*-
"""Izanagi orchestrator (campaign engine) — データモデル。

orchestrator を **DB のトランザクション実行エンジンの原理**で設計する
(orchestrator-design.md)。ここに置くのはその語彙の中間表現:
- `Genome` — variant の遺伝子 = 最適化フラグの割り当て (ビルドキャッシュキーの素)
- `CampaignConfig` / `CampaignId` — campaign 同一性 (内容ハッシュ、D13)
- `WalRecord` — 評価ログ (WAL) の 1 レコード。env-tag 必須
- `EvalState` — WAL リプレイで復元する variant ごとの評価状態 (A: atomicity)

設計対応 (orchestrator-design.md):
  Genome/評価 = トランザクション / WalRecord = WAL / EvalState = リカバリの復元単位
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# 評価パイプラインの段 (orchestrator-design.md A/D)。commit が唯一のコミットポイント。
STAGE_BUILD_START = "build_start"
STAGE_BUILD_DONE = "build_done"
STAGE_VERIFY_DONE = "verify_done"
STAGE_BENCH_DONE = "bench_done"
STAGE_COMMIT = "commit"
STAGE_ABORT = "abort"        # 段で失格 (verifier red 等)。commit と同じく終端だが不採用
STAGES = (STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE,
          STAGE_BENCH_DONE, STAGE_COMMIT, STAGE_ABORT)


@dataclass(frozen=True)
class Genome:
    """variant 一つ = (protocol, 最適化フラグ割り当て)。

    フラグはビルド時 `-D` define (CCBench は最適化を cmake CACHE で受ける、anatomy §3)。
    `canonical()` が決定論的な正準文字列 = ビルドキャッシュキー兼 provenance。
    """
    protocol: str
    flags: Dict[str, int]

    def __post_init__(self):
        if "TRACE" in self.flags:
            # trace 有無は buildcache.build() の trace 引数が唯一の決定点 (規律1)。
            # flags 経由の TRACE は CMake の -DCCBENCH_TRACE 後勝ちで実体に効かず、
            # variant_id/cache_key だけが分裂して同一バイナリを重複評価する (identity 汚染)。
            raise ValueError("genome.flags に 'TRACE' は入れられない (予約名)")

    def canonical(self) -> str:
        """フラグを名前順に並べた正準表現。同じ割り当ては必ず同じ文字列。"""
        body = ",".join(f"{k}={self.flags[k]}" for k in sorted(self.flags))
        return f"{self.protocol}|{body}"

    def cmake_defines(self) -> List[str]:
        """cmake に渡す `-DCCBENCH_<FLAG>=<v>` のリスト。"""
        return [f"-DCCBENCH_{k}={self.flags[k]}" for k in sorted(self.flags)]


@dataclass(frozen=True)
class CampaignConfig:
    """campaign 同一性を決める入力 (D13)。**env は含めない**・**date は含めない**。

    ハッシュ対象 = spec の**内容** + ccbench-commit + 探索 config (ablation / Tier 集合 /
    scale protocol) + trial。spec を編集して名前据え置きでも内容が変われば別 campaign に
    なる (honest-by-construction, §3.4 改竄識別)。
    """
    spec_slug: str              # 可読プレフィクス (例 readheavy-locont)
    search_tag: str             # ablation 軸 (例 fullsearch / llmguided)
    spec_content: str           # 入力 spec の**中身** (名前でなく)
    ccbench_commit: str         # 素材コーパスの版
    search_config: Dict[str, str] = field(default_factory=dict)  # ablation/Tier/scale
    trial: Optional[str] = None  # 入力同一でも別 campaign を切るとき (seed study 等)


@dataclass(frozen=True)
class CampaignId:
    """`<spec-slug>-<search-tag>-<cfg-hash8>` (git の name@digest 型)。"""
    slug: str
    search_tag: str
    cfg_hash8: str

    def __str__(self) -> str:
        return f"{self.slug}-{self.search_tag}-{self.cfg_hash8}"


@dataclass
class WalRecord:
    """WAL の 1 行 (campaigns/<id>/runs/ への逐次追記)。

    env-tag は**必須フィールド** (orchestrator-design.md 環境タグ節)。性能比較は
    linux タグの record しか読まない。1 campaign が Mac (ダミー fitness) と Linux
    (実 fitness) の record を併存させ、射影時に env でフィルタする。
    """
    variant: str                # Genome.canonical() のハッシュ (variant の id)
    stage: str                  # STAGES のいずれか
    env_tag: str                # linux-baremetal / mac-devcontainer (必須)
    ts: float                   # 追記時刻 (provenance。同一性キーではない)
    payload: Dict = field(default_factory=dict)  # 段ごとの内容 (binary hash / verdict / tps 等)


# transient な環境故障ゆえ terminal abort でも次 run で再評価してよい abort reason
# (identity-error = g++/git の一時失敗、*-probe-error = 競合検知 pgrep の一時失敗)。
# variant 固有の欠陥 (verifier-red / build-error) や実競合検知 (competing-tenant) は含めない
# — それらは terminal のまま。retryable 判定の正本 (loop / screening_driver が参照, D25/B-3)。
RETRYABLE_ABORT_REASONS = frozenset({
    "identity-error", "bench-probe-error", "verify-probe-error"})


@dataclass
class EvalState:
    """1 variant の評価状態 (WAL リプレイで復元)。

    A (atomicity): commit レコードがある variant だけ「採用済み」。なければ
    リカバリ時に破棄 (rollback)。half-evaluated を population に混ぜない。
    """
    variant: str
    stages_seen: List[str] = field(default_factory=list)
    committed: bool = False
    aborted: bool = False
    env_tag: Optional[str] = None
    last: Optional[WalRecord] = None
    # 最後の terminal (commit/abort) レコード。retryable 判定はこれを基準にする —
    # last (最終レコード全般) 基準だと「abort → 修復後の再評価が in-flight クラッシュ
    # (BUILD_START が最後)」で判定から漏れ、permanent skip が復活する (D25 の破れ)。
    last_terminal: Optional[WalRecord] = None

    @property
    def terminal(self) -> bool:
        """終端 (commit=採用 / abort=不採用) に達したか。"""
        return self.committed or self.aborted

    @property
    def resumable(self) -> bool:
        """未終端 = リカバリで破棄して再評価すべき (in-flight でクラッシュした)。"""
        return not self.terminal

    @property
    def retryable_abort(self) -> bool:
        """terminal abort だが transient な環境故障ゆえ次 run で再評価すべきか (D25/B-3)。

        commit 済みは対象外。判定は last_terminal (最後の commit/abort) の reason で行う —
        last (最終レコード全般) 基準だと abort→修復後の再評価が in-flight クラッシュ
        (BUILD_START が最後) で判定漏れし permanent skip が復活する (D25 の破れ)。"""
        return (self.aborted and not self.committed
                and self.last_terminal is not None
                and self.last_terminal.payload.get("reason")
                in RETRYABLE_ABORT_REASONS)
