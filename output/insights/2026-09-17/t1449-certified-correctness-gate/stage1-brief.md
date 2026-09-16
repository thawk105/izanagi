# 段 1 brief — [T-1449] 成功・certified な受領証にだけ correctness_evidence 非空 + 三者比較を要求する条件付き最小 gate

worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1449-certified-correctness-gate`、base = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0`、2026-09-17 00:45 JST。

## 研究前進 (1 行)

T-139 RF study (positive control、論文の「pipeline が注入した正しさ欠陥を検出する」主張) の受領証は認証 (追補 A a10/a11 → J) の入力である。現行の受理述語は「性能 attempt が completed で検証 attempt が失敗/不在」の受領証を **correctness 側三者比較 0 回で受理する** (規律 2 の穴、D1272)。完了判定 = その受領証が `SemanticValidationError(reason_code="correctness")` で拒否され、検証 completed + 6 対の受領証は受理され続けること (unit3/unit5 実走 + 変異 matrix で負例 KILLED)。

## 確定済みユーザー裁定

- **D1272 (2026-08-29 /rulings 全件、相談で反転):** `correctness_evidence.minItems:0` は残したまま、成功・certified の受領証のときだけ非空かつ必要な三者比較ありを要求する条件付き最小 gate。失敗途中の受領証の空配列は維持。
- command 引数: 本題の gate 1 条件だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。Codex author (D95) + 変異事前登録。規律 2 を緩めない。

## scope (純増だけ)

1. `_semantic_validator.py` に gate 1 条件を追加 (実装面、Codex author)。
2. unit3 test: 正例 fixture `_full_receipt` を「検証 attempt completed + correctness_evidence 6 対 + liveness_run 6 件」へ直し、負例 (性能 completed + evidence 0 件 / 1 件 / 検証失敗) を **同じ変更単位**で置く。
3. docs: spool fragment (worklog / decisions は D1272 既裁定なので実装記録のみ)、insight README。

放置時の成果物影響 (DW-G05): 受理集合に「三者比較 0 回の性能受領証」が残り、T-139 認証へ未検証の性能値が入りうる。certified 選択・材料レポート・凍結 bytes は本 wave 時点では不変 (単位 6 未配線、D509 決定 7)。

## (P1) 親の provisional 裁定・攻撃対象 — gate 条件の定義

**(P1-a) 採用案:** 受領証に `reason_code == "completed"` かつ `cluster_slot_or_null` 非 null の性能 attempt が 1 件以上あるとき、**同じ受領証に `reason_code == "completed"` の検証 attempt (`cluster_slot_or_null == null`) が存在すること**を要求する。既存の検証 completed 分岐 (`_semantic_validator.py:1993-2015`) が 6 対 (arm × workload) の被覆を要求し、`_validate_correctness_builds` (1117-1150) が各 entry の三者比較 (D574 決定 3) を無条件に走らせるので、「非空かつ必要な三者比較あり」が帰着する。reason_code は `"correctness"`。
**(P1-b) 代案:** 検証 attempt の有無を見ず、性能 completed あり ⇒ `correctness_evidence` が (arm, workload) 6 対を過不足なく覆うことを直接要求する。検証 attempt が main_run 受領証に再掲されない設計なら (a) は正当な main_run を拒否するので (b) が要る。§0.1「検証割当ては study で 1 本、pilot と main_run が同一 bytes で記録」は割当てを言い、attempt の再掲は明文が無い → 段 2/3 で追補 A・record-items-v2 §4.13/§5 の逐語から確定させる。
**(P1-c) 「成功・certified」の読み:** 受領証に `certified` field は無い。性能 completed attempt の存在を「成功」と読む。`declared_use_class` は §8 で受理入力に使用禁止なので条件に使わない。

## 不変条件

- 凍結 schema `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json` (manifest pin d541ccd5…) の bytes 不変。`minItems:0` 維持。
- 凍結 §7.1(1) (record-items-v2.md、pin 61ba2f8b…) の「検証割当てが失敗した stage は 0〜5 件を正当な受領証として受理」は **性能 completed が無い受領証**について維持される。追補 A a01/a04/a05 により検証割当ては性能 binary の唯一の生成元で、失敗なら `design_not_feasible` 終端 → 「性能 completed かつ検証非 completed」は正規手順で生じない。gate はこの偽造経路だけを閉じる。
- 凍結 conformance vector (index-v2.json、approval payload pin) の 46 本の期待 reason は不変。vector は unit3 の **test 名** (`test_semantic_validator_accepts_complete_performance_receipt`) を参照するので test 名は変えない。`negative-7.1-08-*` 2 本は attempts[0] を失敗へ倒すので新 gate は発火せず既存 `reason` が先に立つ (段 6 で実走)。
- 規律 2/3: gate は緩めない。拒否は構造化 reason で返す。
- 変更 file の sha256 pin 0 件 (実測)、path pin は所要台帳 (`acceptance_duration_ledger.json`、新 test は未登録既定値) と vector の test 名参照のみ。

## 実アンカー表

| 面 | file:line | 内容 |
|---|---|---|
| gate 挿入点 | `orchestrator/submission_gate/_semantic_validator.py:1953-2049` | `_validate_reason_branches`。`performance_slots` (1962) が completed 性能 attempt を集める。loop 後に gate を置く |
| 既存 6 対規則 | 同 `:1993-2015` | 検証 completed ⇒ evidence 6 / live 6 / 被覆 |
| 三者比較 | 同 `:1117-1150` | `_validate_correctness_builds` (entry ごと無条件) |
| 呼出順 | 同 `:2596-2605` | builds → raw evidence → reason_branches |
| 正例 fixture | `orchestrator/tests/test_t338_submission_gate_unit3.py:332-645` | `_full_receipt`。attempts 542-575 (性能 completed / 検証 infra failure)、evidence 581-600 (1 件)、liveness 641 (空) |
| fixture 木 | 同 `:181-330` | `tree_files` に correctness 出力 1 本 (`correctness/stock-w1.json`) と binary 3 本 |
| 既存 6 対 test | 同 `:685-695` | `test_completed_verification_requires_six_pairs` |
| unit5 relabel | `orchestrator/tests/test_t338_submission_gate_unit5.py:385-395, 560-600` | `_full_receipt` を再利用し vector の mutation を当てる |
| 凍結 index | `orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v2.json` | 46 vector、bytes 不変 |

## 成果物の形

- コード: gate 1 条件 + 拒否 message。テスト: 正例 1 (fixture 更新)、負例 ≥2 (evidence 0 件・検証失敗のまま性能 completed; evidence 6 件だが検証 attempt 非 completed は (P1) の裁定に従う)。
- 変異事前登録 (段 4): gate 条件の反転・削除・恒真化・reason_code 変更を負例、comment 変更を等価対照 M0。
- 記録: spool fragment (worklog 1 本、decisions は実装形の判断があれば 1 本)、`output/insights/2026-09-17/t1449-certified-correctness-gate/README.md`。

## 模擬 / 実の差

fixture は合成 git repo (tmp_path) 上の合成受領証。実 T-139 受領証は未発行 (単位 6 未配線・T-139 未実走)。gate 入力 (attempts[].reason_code / cluster_slot_or_null / correctness_evidence[]) は schema 必須 field で、値域は enum で閉じている (DW-O13: 到達可能)。

## 受入・実測環境

login node で unit3/unit5 焦点走 (自走 harness `python3 -c "import pytest; pytest.main([...])"`、PYTHONPATH=.)、変異 matrix は container worktree、受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` で計算ノード (所在 = worklog 1579 の形)。

## 並列分割方針

段 2 plan 1 本 (read-only)。段 3 敵対 2 レンズ: A = 正しさ境界 (gate 定義が §7.1(1)/追補 A と矛盾しないか、(P1-a) vs (P1-b)、恒真化)、B = 凍結束縛 (vector 46 本の期待値、fixture 変更が他 test を壊さないか、pin 閉包)。段 5 author 1 本 (validator + unit3 test を同一 diff)。段 6 review 2 本 + fix 1 本。
