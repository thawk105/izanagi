# -*- coding: utf-8 -*-
"""S8b campaign の公式実験時間と反復数を共有する単一 authority leaf。

2026-07-19 のユーザー裁定により、floor の
``s8b_floor_contract.validate_protocol`` と oracle の
``s8b_oracle_manifest._validate_run_contract`` は本 leaf を module-qualified で参照し、
同一値への一致を検査する。探索用の 3 秒・3 回目安は検証対象外であり、公式 artifact を
名乗れない。値を発明せず、ここには承認値だけを置く。

parser 分裂を構造的に排除するため、この module は stdlib 以外や他の campaign
module を import しない。
"""

APPROVED_EXTIME_S = 5
APPROVED_REPS = 5
