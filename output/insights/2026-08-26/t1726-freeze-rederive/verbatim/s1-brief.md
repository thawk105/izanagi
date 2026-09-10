# 段 1 brief — dev-wave-t1726-freeze-rederive

## scope
- [T-1726] `orchestrator/campaign/s8c_acceptance_receipt.py` を「受け取った値の自己整合検査」から
  「ratified legacy freeze から条件を再導出して照合する verifier」へ昇格する。
- [T-1727] serialized binding の v4 世代交代を、本 wave で**裁定だけ**行う。
- 実装面は `orchestrator/campaign/s8c_acceptance_receipt.py` とその test に限る。
  `orchestrator/campaign/trial_registry.py` は**触らない** (t822 / t1484 が稼働中、実測済み)。

## 確定済みユーザー裁定 (覆さない)
- T-1726 = 昇格する。T-1727 = 単独で決めず本 wave で同時に決める。
- 正しさゲートを緩める方向の変更は一切採らない (絶対規律 2)。
- 昇格後に positive control (誤値 receipt が実際に赤になる負の対照) を置く。

## 成果物影響 (DW-G05)
実装しない場合、`layer3_report.py:618` は `require_current_verified_receipt` の緑だけで
H1/H2 各セルを受理するため、ratified freeze と異なる条件で走った試行が
論文 B-3 (8c 正式系列) の certified 選択・selected/tie・レポート数値をそのまま決めうる。

## 実アンカー (実測済み)
| 位置 | 事実 |
|---|---|
| `s8c_acceptance_receipt.py:_verify_v2_trial_arm_execution` | receipt ↔ report ↔ run-start の三者一致だけを見る。freeze 由来の値と比べない |
| `s8c_acceptance_receipt.py:_arm_binding_digest` | digest の原像は (holdout, arm, content_digest) のみ。content_digest は report 側 descriptor の sha256 |
| `trial_registry.py:_expected_registered_arm_execution_record` (5320) | 受入経路では `s8c_arm_inputs.resolve_arm_input` で既に独立再導出済み |
| `s8c_arm_inputs.resolve_arm_input` (434) | (arm, holdout, repository_root, commit) → content/binding digest。on/swapped は in-source `HOLDOUTS`、off は commit 指定 blob |
| `p3_autonomous_workload_trial._formal_profile_source_record` (851) | legacy freeze `output/s8b-freeze/holdout_freeze.json` (`V1_FREEZE_SHA256` pin) ↔ `HOLDOUTS` ↔ descriptor の束縛の既存実装 |
| `trial_registry.launch_admission_record` (4098) | serialized binding は条件のうち `ycsb_rratio` 1 本だけを載せる |
| `layer3_report.py:618` | 標準 verifier の戻り値をそのまま信じる唯一の下流 |

## 既存被覆と純増検出力 (性質で検索した結果)
「receipt 記載値を freeze 由来の再導出値と照合する」検査は
`trial_registry.assert_trial_registry_acceptance` 経路にだけ存在する。
標準 verifier (`require_current_verified_receipt`) 単独経路と layer3_report 経路には無い。
**純増 = 標準 verifier 単独で、自己整合した誤値 receipt を赤にする検出力。**

## 不変条件
- 受理集合は狭くする方向にしか変えない。既存の緑を通す正例を必ず 1 つ添える。
- `s8c_acceptance_receipt` は `trial_registry` / `layer3_report` へ依存しない (module docstring の契約)。
- receipt / report / run-start の保存 bytes・exact key 集合・canonical preimage を変えない
  (変えると `test_reflux_originless_compatibility._PRE_WAVE_ORIGINLESS_BASELINE` と
  `test_trial_registry.py` を巻き込む。後者は t822 が稼働中)。

## 親の provisional 裁定 (攻撃対象)
- **(P1)** 昇格は `_verify_v2_trial_arm_execution` へ、(holdout, arm, measurement_head) から
  再導出した expected content_digest / arm_binding_digest との exact 一致検査を足すことで行う。
  権威の連鎖は legacy freeze bytes → `HOLDOUTS` → `s8c_arm_inputs`。
- **(P2)** T-1727 の v4 は本 wave では**上げない**。旧 artifact は legacy として読み続ける。
  根拠: 再導出は measurement_head があれば成立し、v4 の純増は provenance 記録に留まる。
  一方 v4 は receipt bytes を変え、稼働中 wave の編集面 (`trial_registry.py` / `test_trial_registry.py`)
  を巻き込む。
- **(P3)** v1 receipt は `arm_execution` を持たないため再導出できず、C02 reason を落とせない
  現行の扱いを変えない。昇格対象は v2 / v3 のみ。
- **(P4=既知の穴)** `resolve_arm_input` の on/swapped は **現在の source** の `HOLDOUTS` を読み、
  measurement_head 時点の freeze を読まない。歴史的再導出としては不完全であり、
  ここが v4 (freeze SHA の serialized binding 搭載) の本来の動機。段 3 で攻撃させる。

## 成果物の形
- `s8c_acceptance_receipt.py` の gate 追加 (署名 = 禁止の向きを 2 文で書く)。
- positive control test: 自己整合した誤値 descriptor の receipt が指定 gate 名で赤になる。
- 正例 test: 現行の正しい receipt が緑のまま通る。
- 段 7 で T-1727 の裁定を decisions fragment へ記録する。

## 並列分割方針
- 段 2 plan 1 本 / 段 3 敵対相談 2 レンズ (sol=昇格の抜け道、luna=受理集合と legacy の巻き添え)。
- 段 5 実装子 1 本 (単一ファイル + test のため分割しない)。段 6 review 2 本 + fix。
