# 段 1 brief — [T-1170] 自律試行 journal `run-start` の schema 版改版追随 (dev-wave、2026-09-18)

## 研究前進 (土台)
8c 自律試行の完全性検査 (`autonomous_trial_completeness`、report を書く関門) は、記録済み journal の
`run-start` の版を **producer の生きた定数** (`_producer_module().SCHEMA_VERSION`) と照合している。
producer が改版されるたびに、記録済み run の判定が黙って変わり、記録済み artifact の世代と現行 producer の
世代が区別できない (T-1170 / F332 副次的所見)。最小差分は consumer 側に「読める世代」を固定すること。
完了判定 = v4 の記録が通り、v3 (旧世代) と未知版が世代を名指す理由で fail-closed になり、変異が kill される。

## 確定済みユーザー裁定 (変更不可)
- D1898: 版を上げて解消する。版を上げる差分は「その版を出すが新機能を使わない構成」の正例を持つ。
  旧版 decoder は D1669 の条件 (実在成果物 + 読み手) が成立した場合だけ作る。
- 本 wave 引数: 記録済み artifact と現行 producer の世代を分け、consumer を追随させる。互換層は足さず、
  旧 record は旧版として読む。Codex author (D95) + 変異 matrix。規律 2 を緩めない。本題の改版追随だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- D2064 決定 3: 旧名成果物は書き換えず、再検証には生成時のコード版と契約を用いる。
- D1851: 版を上げないと新旧 event が同じ版で 2 通りになり consumer が区別できない。

## 段 1 で実測した事実 (依頼の前提を覆すもの含む)
- F1. producer `p3_autonomous_workload_trial.py:142` `SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"` は
  `run-start` event (5105-5137) と role payload (2924) の**両方**に使う 1 定数。
- F2. v3 設定 a506633ef (2026-08-06) → v4 4c6f03048 (2026-09-16、T-304 の role key 改名で bump、T-1170 は名指しなし)。
  この間に run-start へ 7 key が版据え置きで追加された (無条件: generation_driver / gating_spec_sha256 /
  honest_accounting_authority、trial_binding 条件付き: prereg_content_commit / prereg_effective_commit / slot_id /
  arm_execution)。**v4 以後、run-start の形は変わっていない** (HEAD と 4c6f03048 で key 集合一致)。
- F3. run-start の**版**を検査する consumer は `autonomous_trial_completeness._check_run_envelope` (2240-2241) だけ。
  trial_registry (5967-5993) と s8c_acceptance_receipt (1498-1506) は run-start の field を読むが版は見ない。
- F4. 依頼が挙げる 6 本のうち attempt_registry_core / s8b_attempt_profile / s8b_floor_attempt_launcher /
  s8b_attempt_registry は `run_start_receipt_sha256` (lifecycle の launch 受領証 digest) しか触らず、journal
  `run-start` の消費者ではない。6 本は `run-start|run_start` の grep hit をソートした先頭 6 件と一致 (起草時の grep 由来)。
- F5. repo 内の記録済み v3 run-start は `output/insights/2026-08-15_t1097-s8c-live-abc/verbatim/attempts.jsonl`
  (13 key 旧形) の 1 本。code / test からの読み手は 0 件。v3 + 新形 (20 key) の記録は repo 内に無い。
- F6. 完全性 test の `_start` fixture (test_autonomous_trial_completeness.py:476-495) は v4 + 無条件 3 key + binding 無し
  = D1898 の「新機能を使わない構成」の正例そのもので、既に consumer を通っている (明示 test は無い)。
- F7. 失敗文言 `does not match producer version` の pin は同 test の 2 node (2893-2925) だけ。両 file の sha256 は
  output/ と台帳に pin されていない。`s8c_preregistration_evidence_contract.v1.json:398` は field path / 到達性 pin。
- F8. role payload 側は `_ROLE_SCHEMA_VERSION` (completeness:427) と `s8c_generation_projection.ROLE_SCHEMA_VERSION` の
  独立二重定義で「consumer が読める世代」を持つ (D2064)。run-start 側だけが producer の生きた定数を見ている。

## 親の provisional 裁定 (攻撃対象)
- (P1) D1898 の「版を上げる」は 4c6f03048 (v4) で実体化済みとみなす。本 wave で v5 へは上げない —
  形の変更を伴わない bump は D1851 の趣旨 (版 ⇔ 形) に反し、09-16 以降の全記録を旧世代にする。
- (P2) 「世代を分ける」の実装位置は `_check_run_envelope` の run-start 版検査 (2240-2241)。producer の生きた定数との
  照合をやめ、consumer 所有の読める世代定数 (`_RUN_START_SCHEMA_VERSION = ".../v4"`、`_ROLE_SCHEMA_VERSION` と同型の
  独立二重定義、producer から import しない) と照合する。失敗理由は記録の版と consumer の読める世代を名指す
  (規律 3: 旧世代 v3 と未知版を区別できる構造化文言)。受理集合は v4 のみで**不変** (DW-O13 の受理形拡大に当たらない)。
- (P3) v3 decoder は作らない。F5 のとおり実在成果物はあるが読み手が無く D1669 条件不成立。「旧 record は旧版として読む」
  = 版で世代を分類して fail-closed、変換しない (互換層なし)。
- (P4) F4 の 4 本は変更なし。trial_registry / s8c_acceptance_receipt への版検査追加は仮想リスク向け gate で scope 外。
- (P5) producer 側は触らない。`SCHEMA_VERSION` が run-start と role payload の共有定数であることが T-1170 の根本原因だが、
  分離 (新 schema 名) は一般化に当たり本 wave 外。producer bytes 不変 = pin 閉包を動かさない。
- (P6) 同 function の report.schema_version 検査 (2238-2239) は本題外として触らない。
- (P7) consumer 定数と producer 定数の同期は「現行 producer の実走出力が consumer を通る」統合 test (既存) が担う。
  新規の同期 gate (import 比較など) は足さない。

## 不変条件
- 規律 2: 受理集合を広げない。v4 以外を受理する変更は不採用。
- 規律 3: 拒否理由は版と世代を名指す。規律 7: 記録済み artifact (t1097 verbatim 等) は書き換えない。
- producer bytes・凍結物・事前登録 (`s8c_preregistration_evidence_contract.v1.json`) を変えない。

## 成果物の形
- コード: `orchestrator/campaign/autonomous_trial_completeness.py` (定数 1 + 検査 2 行)。
- テスト: `orchestrator/tests/test_autonomous_trial_completeness.py` — 既存 2 node の期待文言更新、明示正例 (v4・binding 無し)、
  負例 (v3 旧形 = 旧世代、v99 = 未知)、consumer 定数 == producer 定数の同期は producer 実走 test の名指し。
- 変異 matrix (段 4 で事前登録): M1 版検査削除 → 負例が kill、M2 consumer 定数を v3 へ → producer 実走正例が kill、
  M3 旧世代/未知の分岐取り違え → 負例文言が kill、M0 等価 (docstring) → SURVIVED 期待。
- docs: worklog fragment (T-1170 閉じ、F4 の前提訂正を明記)、失敗台帳 F332 の副次的所見へ恒久対応を追記、
  decisions fragment は P1〜P3 が既裁定の適用なら不要 (段 4 で判定)。

## 変更面アンカー表
| file | 行 | 変更 |
|---|---|---|
| orchestrator/campaign/autonomous_trial_completeness.py | 427 付近 | `_RUN_START_SCHEMA_VERSION` 追加 |
| 同 | 2238-2241 | run-start 版検査を consumer 定数へ、理由を構造化 |
| orchestrator/tests/test_autonomous_trial_completeness.py | 54, 2893-2925 | 期待文言・正例/負例 |
| (無変更) p3_autonomous_workload_trial.py / trial_registry.py / s8c_acceptance_receipt.py / F4 の 4 本 | — | — |

## 並列分割
- 実装子 1 本 (author、code + test の両方、所有 = 上記 2 file)。レビュー 2 本 (レンズ A: 正しさ境界 / 受理集合・規律 2/3、
  レンズ B: 裁定適合 / D1898・D1669・D1851・D2064 と依頼文の逐語)。
- 受入・実測: login node で焦点走 (completeness + importer 16 file の test)、変異 harness、受入全走は dispatch。
