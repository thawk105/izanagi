# -*- coding: utf-8 -*-
"""Izanagi critic の支援ロジック (Phase 2)。

critic は LLM 推論エージェント (`.claude/agents/critic.md`) = 評価結果を読んで
設計選択に帰属させ、次に試す genome の方向を出す (agent-architecture §critic)。
このパッケージはその**機械準備**: WAL の leading indicators を genome 別表 +
フラグ軸ごとの限界効果に構造化し、critic が推論できる digest にする
(verifier の parse/dsg が DSG を作るのと同じ「生データ→構造」の役割)。

書き込みはしない (critic の規律: 読み取り + 解析のみ)。
"""
from .digest import GenomeLI, WorkloadDigest, build_digest, render_text  # noqa: F401
