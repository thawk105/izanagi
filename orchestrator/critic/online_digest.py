# -*- coding: utf-8 -*-
"""P2-5 誘導アームのリーク制御: 評価済み genome だけの online digest + 実行時 assert。

誘導 critic に渡す digest は「これまで評価した genome だけ」でなければならない (未評価の
fitness を見せると評価器の優位を評価器の定義で論証する出来レース、規律6/D14)。誘導専用の
layout (guided-WAL) は評価済みだけが育つので、`digest.build_digest` をそのまま当てれば未評価は
構造的に入らない。それに加え **『digest の genome 数 ≤ これまでの評価回数』を実行時 assert** で
機械保証する (WAL 分離だけに頼らない二重の関所)。`digest.load_p2_2_digests` (全 8 入り) は
誘導アームでは決して import しない。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign.layout import CampaignLayout          # noqa: E402
from critic import digest                           # noqa: E402


class LeakageError(AssertionError):
    """online digest が評価回数より多くの genome を含む = 未評価が漏れている。"""


def online_digest(layout: CampaignLayout, tag: str, workload: dict,
                  iterations: int) -> digest.WorkloadDigest:
    """評価済み (committed) genome だけの digest を作り、リーク不在を assert する。

    iterations = これまでに評価した回数。digest の genome 数がこれを超えたら、誘導専用 WAL に
    未評価 genome が混入している (= リーク) として LeakageError で止める。"""
    d = digest.build_digest(tag, workload, layout)
    n = len(d.genomes)
    if n > iterations:
        raise LeakageError(
            f"online digest が {n} genome を含むが評価は {iterations} 回 "
            "= 未評価 genome がリークしている (誘導専用 WAL の分離が壊れた)")
    return d


def online_digest_text(layout: CampaignLayout, tag: str, workload: dict,
                       iterations: int) -> str:
    """critic に渡す digest テキスト (評価済みのみ・リーク assert 済み)。"""
    return digest.render_text([online_digest(layout, tag, workload, iterations)])
