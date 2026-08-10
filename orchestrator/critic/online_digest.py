# -*- coding: utf-8 -*-
"""P2-5 誘導アームのリーク制御: 評価済み genome だけの online digest。

誘導 critic に渡す digest は「これまで評価した genome だけ」でなければならない (未評価の
fitness を見せると評価器の優位を評価器の定義で論証する出来レース、規律6/D14)。

**中立性の真の担保は 2 つの構造的分離である**:
1. 誘導専用 layout (guided-WAL) は評価済みだけが育つので、`digest.build_digest` をそのまま
   当てれば未評価は構造的に入らない (WAL 分離)。
2. `digest.load_p2_2_digests` (全 8 入り) を誘導アーム (critic-experiment) では決して import
   しない (import レベルの物理分離)。

下の実行時 assert は **独立な第二防壁ではない**: digest の genome 数も `iterations` も同一の
誘導 WAL の STAGE_COMMIT から導出されるため、同一 layout 経路では構造的に `n <= iterations` が
成り立ち恒真化する (audit 2026-06-30 / D26 で確認)。残しているのは `iterations` 誤計算・layout
取り違えという**配線ミス**への sanity check としてであり、中立性そのものを担保するのは上記 1/2。
真に独立な照合 (評価回数を WAL 外の独立カウンタから取る) は、Phase 3 で誘導ループを実コード化する
際に検討する (それまでは P2-5 が replay = 新規計測ゼロで完了済みゆえ実害なし)。
"""
from __future__ import annotations

from orchestrator.campaign.layout import CampaignLayout

from . import digest


class LeakageError(AssertionError):
    """online digest が評価回数より多くの genome を含む = 未評価が漏れている。"""


def online_digest(layout: CampaignLayout, tag: str, workload: dict,
                  iterations: int) -> digest.WorkloadDigest:
    """評価済み (committed) genome だけの digest を作る (配線 sanity 込み)。

    iterations = これまでに評価した回数。digest の genome 数がこれを超えたら配線ミス (layout
    取り違え / iterations 誤計算) として LeakageError で止める。同一誘導 layout 経路では構造的に
    恒真ゆえ中立性の独立保証にはならない (module docstring 参照) — 真の担保は WAL 分離である。"""
    d = digest.build_digest(tag, workload, layout)
    n = len(d.genomes)
    if n > iterations:
        raise LeakageError(
            f"online digest が {n} genome を含むが評価は {iterations} 回 "
            "= 配線ミス (layout 取り違え / iterations 誤計算 / WAL 分離破れ)")
    return d


def online_digest_text(layout: CampaignLayout, tag: str, workload: dict,
                       iterations: int) -> str:
    """critic に渡す digest テキスト (評価済みのみ・リーク assert 済み)。"""
    return digest.render_text([online_digest(layout, tag, workload, iterations)])
