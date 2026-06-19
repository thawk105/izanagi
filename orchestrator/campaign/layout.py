# -*- coding: utf-8 -*-
"""出力レイアウト — campaign 軸 + env 軸の二分 (D13 / orchestrator-design.md)。

```
output/
  env/<env-tag>/{calibration,noise-floor}   ← 環境スコープ (campaign 横断・入力非依存)
  campaigns/<campaign-id>/
    campaign.lock    同一性の正準 pre-image (改竄不能な identity 源)
    spec/            凍結した入力 spec (レポート自己完結)
    runs/            この campaign の WAL (env-tag 必須)
    variants/        variant ソース/patch + ビルドキャッシュキー
    reports/         D12 材料レポートの射影先
    insights/        campaign 固有 insight / whiteboard
  insights/          グローバル知見 (CCBench 還元等, D6)
  whiteboard/        campaign 横断の教訓 (任意)
```

paths を一箇所に集約し、WAL/ビルドキャッシュ/lock がここだけを参照する。
**WAL を開く前に campaign-id が確定している前提** (orchestrator-design.md Phase1 反映 1)。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def repo_output_root() -> str:
    """リポジトリ直下の output/ (orchestrator/campaign/layout.py からの相対)。"""
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    return os.path.join(repo, "output")


@dataclass(frozen=True)
class CampaignLayout:
    """1 campaign のディレクトリ群。`ensure()` で作る。"""
    root: str                   # output/campaigns/<id>/

    @property
    def lock_file(self) -> str:
        return os.path.join(self.root, "campaign.lock")

    @property
    def spec_dir(self) -> str:
        return os.path.join(self.root, "spec")

    @property
    def runs_dir(self) -> str:
        return os.path.join(self.root, "runs")

    @property
    def wal_file(self) -> str:
        return os.path.join(self.runs_dir, "wal.jsonl")

    @property
    def variants_dir(self) -> str:
        return os.path.join(self.root, "variants")

    @property
    def reports_dir(self) -> str:
        return os.path.join(self.root, "reports")

    @property
    def insights_dir(self) -> str:
        return os.path.join(self.root, "insights")

    def ensure(self) -> "CampaignLayout":
        for d in (self.root, self.spec_dir, self.runs_dir, self.variants_dir,
                  self.reports_dir, self.insights_dir):
            os.makedirs(d, exist_ok=True)
        return self


def campaign_layout(campaign_id: str, output_root: str = "") -> CampaignLayout:
    root = output_root or repo_output_root()
    return CampaignLayout(root=os.path.join(root, "campaigns", str(campaign_id)))


def env_scope_dir(env_tag: str, output_root: str = "") -> str:
    """環境スコープ (calibration/noise-floor の置き場、campaign 非依存)。"""
    root = output_root or repo_output_root()
    return os.path.join(root, "env", env_tag)
