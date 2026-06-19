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
from typing import Any, Dict

from .model import CampaignConfig, CampaignId


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
