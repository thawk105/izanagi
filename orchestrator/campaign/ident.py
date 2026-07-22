# -*- coding: utf-8 -*-
"""campaign 同一性 — 内容ハッシュによる安定・無衝突・決定論的な id (D13)。

`<spec-slug>-<search-tag>-<cfg-hash8>`。ハッシュは spec の**名前でなく内容**を覆う
(編集して名前据え置きでも別 campaign になる = honest-by-construction, §3.4)。
**env も date も同一性に含めない** (env は WAL の読み出しフィルタ、date はクラッシュ後
再開で別ディレクトリを生むので禁止、D13)。

`campaign.lock` = 正準 pre-image。再開時はハッシュ一致に加えて lock と現在 config を
照合し、万一ハッシュ一致で中身相違なら**黙ってマージせずエラー** (改竄/衝突の関所)。
"""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from .layout import CampaignLayout
from .model import CampaignConfig, CampaignId
from . import wal

if TYPE_CHECKING:
    from .pipeline import ScreeningConfig


def screening_search_config(
        screening: Optional["ScreeningConfig"]) -> Dict[str, Dict[str, str]]:
    """screening 方針だけを campaign-id 用 search_config entry に正準化する。

    基準の再アンカーで campaign-id を割らないため、実測値と測定時刻・基準 abort 率は
    含めない。None はキー自体を返さず、歴史的 campaign-id を完全に温存する。
    """
    if screening is None:
        return {}
    return screening_policy_search_config(
        screening.baseline_ref, screening.floor, screening.k,
        screening.high_abort_factor)


def screening_policy_search_config(
        baseline_ref: str, floor: float, k: float,
        high_abort_factor: float) -> Dict[str, Dict[str, str]]:
    """実測値をまだ持たない driver が campaign identity を先に焼くための正本。"""
    return {"screening": {
        "baseline_ref": baseline_ref,
        "floor": repr(floor),
        "k": repr(k),
        "high_abort_factor": repr(high_abort_factor),
    }}


def verify_screening_preimage(
        screening: "ScreeningConfig", stored_preimage: Optional[str]) -> None:
    """runtime screening と campaign.lock に焼き込まれた方針を機械照合する。

    lock 欠落・JSON 破損・screening key 欠落・値の相違はすべて ValueError。既存 campaign
    へ runtime 引数だけで screening を混在させる迂回を、評価開始前に拒否する。
    """
    if stored_preimage is None:
        raise ValueError("screening 有効評価には campaign.lock の方針焼き込みが必要")
    try:
        stored = json.loads(stored_preimage)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("campaign.lock が正準 JSON でなく screening 方針を検証できない") from exc
    if not isinstance(stored, dict):
        raise ValueError("campaign.lock の正準JSONがobjectでなくscreening方針を検証できない")
    search_config = stored.get("search_config")
    actual = search_config.get("screening") if isinstance(search_config, dict) else None
    expected = screening_search_config(screening)["screening"]
    if actual != expected:
        raise ValueError(
            "runtime ScreeningConfig と campaign.lock の screening 方針が不一致: "
            f"stored={actual!r}, expected={expected!r}")


def canonical_preimage(cfg: CampaignConfig) -> str:
    """ハッシュ対象の正準シリアライズ。決定論的 (キー順固定・区切り固定)。

    覆うもの: spec の内容 + ccbench-commit + 探索軸 (search_tag) + 探索 config
    (ablation/Tier/scale) + trial。**slug は覆わない** (人間ラベルで spec_content が
    真の同一性源、要件: 名前でなく内容)。**env/date/実測値は覆わない** (派生値)。
    """
    obj: Dict[str, Any] = {
        "spec_content": cfg.spec_content,
        "ccbench_commit": cfg.ccbench_commit,
        "search_tag": cfg.search_tag,
        "search_config": {k: cfg.search_config[k] for k in sorted(cfg.search_config)},
        "trial": cfg.trial,
    }
    # sort_keys + 固定 separators で、同じ内容は必ず同じバイト列に。
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def cfg_hash(cfg: CampaignConfig) -> str:
    """正準 pre-image の SHA-256 先頭 8 hex。"""
    pre = canonical_preimage(cfg).encode("utf-8")
    return hashlib.sha256(pre).hexdigest()[:8]


def campaign_id(cfg: CampaignConfig) -> CampaignId:
    """(spec, config) から campaign-id を純粋に導く (状態を保存しない)。"""
    return CampaignId(slug=cfg.spec_slug, search_tag=cfg.search_tag,
                      cfg_hash8=cfg_hash(cfg))


class IdentityMismatch(Exception):
    """ハッシュ一致だが格納済み lock と現在 config の中身が相違 (衝突/改竄)。"""

    def __init__(self, message: str, *, reason: str = "lock-mismatch"):
        super().__init__(message)
        self.reason = reason


def verify_against_lock(cfg: CampaignConfig, stored_preimage: str) -> None:
    """再開時の関所: 現在 config の正準 pre-image が格納済み lock と一致するか。

    一致しなければ IdentityMismatch (黙ってマージしない、D13)。8 hex 衝突や、
    ハッシュに含めていない軸の相違を捕まえる最終防壁。
    """
    cur = canonical_preimage(cfg)
    if cur != stored_preimage:
        raise IdentityMismatch(
            "campaign.lock と現在 config の正準 pre-image が不一致。"
            "ハッシュ衝突か config ドリフト。黙ってマージせず停止する。\n"
            f"  stored : {stored_preimage}\n  current: {cur}")


def ensure_resumable_wal(
        cfg: CampaignConfig, layout: CampaignLayout,
) -> wal.WalTailRepairResult:
    """identity を確定してからに限り WAL の無終端 tail を物理修復する。

    lock の無い既存 WAL は、どの config の記録か照合できないため修復も追記も
    しない。初回 campaign (lock 無し・WAL byte 無し) だけは原子的に lock を
    作成し、その後に機構層の repair を呼ぶ。
    """
    ensure_campaign_identity(cfg, layout)
    return wal.repair_truncated_tail(layout)


def ensure_campaign_identity(
        cfg: CampaignConfig, layout: CampaignLayout,
) -> bool:
    """repair を行わず campaign.lock を原子的に確立・照合する。

    戻り値はこの呼び出しが lock を新規獲得したときだけ True。lock 無しで WAL
    byte がある場合は identity 不明のため拒否する。既存 lock との競合敗者は
    lock を再読して同一 config なら False を返す。
    """
    stored = wal.read_lock(layout)
    if stored is not None:
        verify_against_lock(cfg, stored)
        return False

    # lock 作成前に WAL の lstat/open/fstat を行う。EIO 等は fail-closed に伝播する。
    if wal.wal_bytes_present(layout):
        raise IdentityMismatch(
            "campaign.lock が無い既存 WAL は identity を照合できないため "
            "resume/repair を拒否する。WAL bytes は変更していない。",
            reason="missing-lock-with-wal-bytes",
        )

    preimage = canonical_preimage(cfg)
    if wal.acquire_lock_atomic(layout, preimage):
        return True

    # 並行 winner が作った lock だけを正本として読み、敗者は何も書かない。
    stored = wal.read_lock(layout)
    if stored is None:
        raise IdentityMismatch(
            "campaign.lock の原子的獲得に失敗し、既存 lock も読めない。",
            reason="lock-create-failed",
        )
    verify_against_lock(cfg, stored)
    return False
