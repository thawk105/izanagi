# -*- coding: utf-8 -*-
"""承認済み固定値の集約・再輸出 (C4-3/C4-4)。

protocol builder (``s8b_floor_campaign.build_protocol_document``) と
``validate_protocol`` は数値の正本 ``s8b_experiment_numbers`` を参照し、承認凍結値の
二重リテラルを残さない。値は **発明しない** — 既に承認済みの pin と、実測した trust
root だけを集約する。

- 公式実験数値 (extime_s=5 / reps=5) の正本は ``s8b_experiment_numbers``
  (ユーザー裁定 2026-07-19)。ここは import 束縛だけを再輸出する。
- ``APPROVED_MASTER_SEED`` は worklog 2026-07-18 (11) のユーザー委任により、親が
  メッセージ受領時刻で確定した事前登録値。以後選び直さない。
- ``APPROVED_ENV_TAG`` は同じ worklog 2026-07-18 (11) のユーザー裁定 (Pegasus、
  slug ``pegasus``)。環境契約への登録は 2026-07-19 に完了済み。
- ``APPROVED_STOCK_CONFIGURATION`` は 2026-07-18 の F1 パッケージ承認で確定した
  stock 構成 (``output/insights/2026-07-16_s8b-floor-protocol-package.md``) で、v1
  holdout freeze の variant binding key に実在する値。
- ``APPROVED_WIRED_MIN_REL_FLOOR`` は同じ F1 パッケージ承認の 3.0% 値
  (``output/insights/2026-07-16_s8b-floor-protocol-package.md`` の F1)。canonical
  protocol bytes の型を固定するため float literal で保持する。
- その他の標本設計 pin (n_sessions=8 / retry_slots=2 / 閾値 3 種 / 除外理由表) は §9
  承認状態 (2026-07-18) の凍結値。閾値は decimal 文字列で凍結し stats が Fraction 厳密
  算術で解釈する (α-9)。除外理由表の正本は ``s8b_floor_stats`` (ここは固定順を再輸出する
  だけで独立の literal を持たない)。
- v1 trust root (freeze path + bytes sha256) は ``s8b_ratified_freeze`` の ``V1_*`` を
  単一源として再輸出する (C2-5/C4-4)。重複リテラルを置かないため、値はここに焼き直さず
  import 束縛のみとする (drift の余地を構造的に消す)。
- ccbench full commit sha は ``external/ccbench`` の gitlink 実測値 (40 hex)。
  ``pin.CURRENT_PIN`` ("6810666") はこの prefix であり、prefix 一致・gitlink 一致の検査は
  ``test_s8b_approved`` が実 repo に対して固定する (定数の追認を許さない)。

このモジュールは stdlib と葉 module のみに依存する葉であり、``s8b_floor_campaign`` を
import しない (循環回避)。
"""
from __future__ import annotations

from . import s8b_experiment_numbers as _experiment_numbers
from . import s8b_floor_stats
from .s8b_ratified_freeze import V1_FREEZE_PATH, V1_FREEZE_SHA256

# --- 公式実験数値 pin (単一源 = s8b_experiment_numbers、裁定 2026-07-19) --- #
APPROVED_EXTIME_S = _experiment_numbers.APPROVED_EXTIME_S
APPROVED_REPS = _experiment_numbers.APPROVED_REPS

# --- protocol 自由値 pin (ユーザー裁定 / F1 パッケージ承認 2026-07-18) --- #
APPROVED_MASTER_SEED = "2026-07-18T17:16:12+09:00"
APPROVED_ENV_TAG = "pegasus"
APPROVED_STOCK_CONFIGURATION = "stock_common"
APPROVED_WIRED_MIN_REL_FLOOR = 0.03

# --- その他の標本設計 pin (§9 承認状態 2026-07-18) --- #
APPROVED_N_SESSIONS = 8
APPROVED_RETRY_SLOTS = 2
APPROVED_SESSION_CV_MAX = "0.10"
APPROVED_CELL_CV_MAX = "0.15"
APPROVED_SCALE_ADEQUACY = "0.10"
# 閉じた除外理由表 (固定順、正本 = s8b_floor_stats)。immutable な tuple で保持する。
APPROVED_REASONS = tuple(s8b_floor_stats.ALLOWED_EXCLUDED_REASONS)

# --- v1 trust root (単一源 = s8b_ratified_freeze、C2-5/C4-4) --- #
# 重複リテラルを持たず import 束縛のみ。値の照合は builder が実 v1 bytes に対して行う。
APPROVED_FREEZE_PATH = V1_FREEZE_PATH
APPROVED_FREEZE_SHA256 = V1_FREEZE_SHA256

# --- ccbench full commit sha (external/ccbench gitlink 実測、40 hex) --- #
# 2026-09-20 [T-2304] D2150 項 1: 511c9538 → e9e477ca (mocc trace v2 など 4 commit)。
# 2026-09-23 [T-2858] D2227 項 1: e9e477ca → 68106660 (mocc X/P 計装 1 commit)。
# pin.CURRENT_PIN ("6810666") はこの prefix。gitlink 一致・prefix 一致の検査は test_s8b_approved。
CCBENCH_FULL_SHA = "68106660686232781bca3be792a750d3e19d7a8a"
