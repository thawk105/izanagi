# 段 1 brief — [T-897] build gateway で trigger axis の semantic admission を必須化する

## 確定済みユーザー裁定

2026-08-12 第 6 束: **T-897 = (b)** — build gateway 側で trigger axis
(`BACKOFF_TRIGGER_GATING`) を検出して semantic admission を必須化する。敵対検証を受入条件とする。
一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-rulings7-batch.md:32`。
(a) 5 経路への個別結線と (c) 主張の縮小は不採用。

## scope

`orchestrator/campaign/build_admission.py` に **単一の semantic validator** を置き、
trigger 軸が materialize された source 木に対しては `trigger_gate_binding` の有無に関わらず
必ず発火させる。5 経路 (s8a trigger sweep / S-1 direct comparison / S8b oracle /
S8b floor / S-1 extime calibration) の call site は編集しない。

## 成果物影響 (DW-G05)

実装しないと、外周空白・tab・CRLF・別表記を保持した非正準 gate 述語を持つ source 木が
binding 省略経路から build → verify を経て、certified 判定・layer3 レポート・
session ledger・oracle/floor manifest の値へ到達しうる。

## 不変条件 (破ったら段 4 で不採用)

1. **fail-closed のみ。** 受理集合を広げる変更・警告化・env での無効化・CLI escape を作らない (規律 2)。
2. **admission receipt の key 集合と bytes を変えない。** `_ADMISSION_KEYS` / `receipt_sha256` は
   wal.py・buildcache の cache identity・critic/digest.py・p3_s4_loop.py・s8b_materialization.py・
   tools/mutation_fanout.py が独立に束縛している (実測)。新 field は凍結 bytes を壊す。
3. **既存の binding 経路の検査を弱めない。** `pipeline._require_materialized_trigger_predicate` の
   mask 一致検査は残す。新 validator はその下限であって代替ではない。
4. trigger 軸が materialize されていない木 (stock を含む) では **一切の挙動変化を起こさない**。

## 発火 gate の実在 (DW-G04 / DW-O13)

gate 入力 = `evidence.source_root` + `axis_trigger_gating.SOURCE_REL`
(`cc/silo/transaction.cc`) の `MARKER_ID` = `silo-backoff-trigger-gating` template marker。
stock 木では **0 件** (実測)。materialize 済み木の実在 path =
`patches/silo-backoff-trigger-gating-variant.patch` を quarantine 適用した木
(`p3_s4_loop.quarantine`、s8a trigger sweep が生成)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 軸検出は「marker の実在」で行う (cmake flag 値ではない)。`SourceEvidence` は
  genome flag を持たず `genome_sha256` だけを持つため、flag 値は gateway から読めない。
- **(P2)** validator は `derive_build_admission` と `require_build_admission` から呼び、
  `validate_build_admission_receipt` (永続 receipt の replay) からは呼ばない。replay 時点で
  source 木は既に無い/変わっている。
- **(P3)** 受理述語 = hole がちょうど 1 物理行で、
  `PREDICATE_HOLE_INDENT + emit_predicate(TriggerGateIR(mask))` の bytes と exact 一致する
  mask が 0..31 に存在すること。存在しなければ `BuildAdmissionError`。
- **(P4)** marker parse 不能・source file 読取不能は、**marker 実在が判定できた場合のみ** reject。
  file 不在は「軸を使っていない」として no-op (不変条件 4)。
- **(P5)** 実装は build_admission.py + 新規/既存テストのみ。5 call site と
  s8b_floor_campaign.py (t921 が所有) に触れない。

## 成果物の形

- `orchestrator/campaign/build_admission.py` の差分 (validator 1 本 + 2 箇所からの呼出し)。
- `orchestrator/tests/test_build_admission.py` の負例・正例 (正準 1 例、非正準 4 種以上)。
- 5 経路が binding なしでも検査に到達することを示す不変条件テスト。
- 変異 matrix (wave 前の実コードの形を含む)、受入全走 rc=0。

## 並列分割方針

実装単位は 1 本 (build_admission.py + そのテスト) — 所有が素集合に割れないため分割しない。
段 3 の敵対相談と段 6 のレビューは 2 レンズ並列。
