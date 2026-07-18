# -*- coding: utf-8 -*-
"""strict v2 freeze fixture: per-pair floor table + budget 充填形 (C3-4)。

manifest / driver / report の 3 群テストが共有する。実 freeze document の
``holdouts[h].variant_binding.entries`` の key 集合 (= 構成集合) から stock 構成
(``stock_common``) を除いた集合を pair key として per-pair floor を組む。scalar (v1)
形は使わない。verifier 側 (s8b_oracle_manifest._validate_holdout_floor) の per-pair
exact 検査を満たす正例を単一源で生成し、各テストの fixture 分岐を防ぐ。
"""
from __future__ import annotations

from typing import Optional

# manifest verifier のハードコード stock 名と一致させる (両者とも freeze 記録値に
# stock_common が実在することを別途検査する)。
STOCK_CONFIGURATION = "stock_common"


def holdout_configuration_ids(document, holdout_id) -> set:
    """freeze の当該 holdout の構成集合 (variant_binding.entries の key 集合)。"""
    return set(document["holdouts"][holdout_id]["variant_binding"]["entries"])


def per_pair_floor(document, *, value: float = 0.01,
                   scale_ref: Optional[float] = 100.0) -> dict:
    """全 holdout・全 pair を同一有限正 ``value`` で満たした per-pair floor table。

    各 holdout 値 = exact 3 keys {pairs, scale_ref, scalar_alt}。pairs の key 集合 =
    構成集合 − stock。scalar_alt = max(pairs) (全 pair 非 null のとき)。
    """
    by_holdout = {}
    for holdout_id in document["holdouts"]:
        configs = holdout_configuration_ids(document, holdout_id)
        pairs = {cfg: value for cfg in sorted(configs - {STOCK_CONFIGURATION})}
        scalar_alt = max(pairs.values()) if pairs else None
        by_holdout[holdout_id] = {
            "pairs": pairs,
            "scale_ref": scale_ref,
            "scalar_alt": scalar_alt,
        }
    return {"by_holdout": by_holdout}


def budget(document, *, total_bench_s: float = 100.0,
           per_holdout_bench_s: float = 50.0) -> dict:
    """oracle 共有 budget (per_holdout は全 holdout 一律)。"""
    return {
        "total_bench_s": total_bench_s,
        "per_holdout_bench_s": {
            holdout_id: per_holdout_bench_s for holdout_id in document["holdouts"]
        },
        "oracle_shared": True,
    }


def fill(document, *, total_bench_s: float = 100.0,
         per_holdout_bench_s: float = 50.0, floor_value: float = 0.01,
         scale_ref: Optional[float] = 100.0) -> dict:
    """document に per-pair floor と budget を in-place 充填して返す。"""
    document["floor"] = per_pair_floor(
        document, value=floor_value, scale_ref=scale_ref,
    )
    document["budget"] = budget(
        document, total_bench_s=total_bench_s,
        per_holdout_bench_s=per_holdout_bench_s,
    )
    return document
