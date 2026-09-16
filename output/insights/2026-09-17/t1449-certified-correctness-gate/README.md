# [T-1449] 受領証 validator に D1272 の条件付き最小 gate を入れる — 性能 completed かつ検証割当ての失敗が未記録なら correctness_evidence の 6 対を要求する (2026-09-17)

## 一言で

T-139 受領証の semantic validator (`orchestrator/submission_gate/_semantic_validator.py`、`_validate_reason_branches`) に
gate を 1 条件だけ足した。**既存の raw 検査を通過した completed 性能 attempt があり、検証割当て (`cluster_slot_or_null == null`)
の非 completed な attempt が 1 件も無い受領証は、`correctness_evidence` が (stock, mode1, modeX) × (W1, W2) の 6 対を各 1 件・
計 6 件で覆わない限り `SemanticValidationError(reason_code="correctness")` で拒否する。** 凍結事前登録 §7.1(1) の失敗記録
(検証 attempt が失敗を申告した stage、0〜5 件) と、completed 性能 attempt の無い受領証は従来どおり受理する。
凍結 schema (`receipt-schema-v1.json`、`correctness_evidence.minItems:0`) と凍結 conformance vector 46 本は bytes 不変。

## 経緯

1. T-1449 は entry 766 (2026-08-20、T-1441 監査の副次的所見 1) が起票: `minItems:0` により correctness 側三者比較
   (D574 決定 (3): schema argv macro / `compile_commands` / raw `CMakeCache.txt`) が 1 度も走らない受領証が成立しうる。
2. 2026-08-29 の /rulings 全件で D1272 が裁定: 「成功・certified の受領証のときだけ非空かつ必要な三者比較ありを要求する
   条件付き最小 gate。失敗途中の受領証の空配列は維持」。親の初版「記録だけ」は相談が「規律 2 を満たさない」と反転させた。
3. 本 wave (command 引数で起動)。段 1 で現物同定: 検証器は「検証 attempt completed ⇒ 6 対」を既に持ち (V:1994-2017)、
   穴は「性能 completed かつ検証 attempt の帰結が記録されない受領証」。既存正例 fixture `_full_receipt` は
   性能 completed + 検証 `pre_performance_infra_failure` + correctness 1 件で受理されている。
4. 段 2 plan (Codex) は P1-b「性能 completed ⇒ 無条件に 6 対」を採った。段 3 レンズ A (sol) が **P1-b は §7.1(1) の
   失敗記録を過剰拒否する** と指摘 (real)。親が検算: 検証 attempt の失敗は正規運用上 `pre_performance_infra_failure` に写り
   a10 で study は `design_not_feasible` 終端、その stage 受領証は §7.1(1) が 0〜5 件で受理すると凍結している。
   → 段 4 で gate v2 (上記) に確定 ({{D:certified-gate-raw-success-definition}})。
5. 段 5 Codex author が validator +24 行 / unit3 test +157 行を同一 diff で実装。`_full_receipt` は不変 (失敗記録の正例 +
   凍結 vector の基底)。段 6 敵対レビュー 2 本は must-fix 0。

## 変更 (commit `abce1ff51`)

- `_validate_reason_branches` の attempts loop 後: `verification_failure_recorded` (検証 attempt で `reason_code != "completed"`)、
  `if performance_slots and not verification_failure_recorded:` → 6 件かつ (arm, workload) 集合一致を要求。
- unit3: `tree_files` に correctness 出力 5 本 + liveness raw 6 本、helper `_certified_receipt` (検証 completed + 6 対 + liveness 6)、
  `_without_verification_attempt`、`_completed_performance_reason_payload` (36 run 双射の最小 payload)。
- 新 test 11 node: 正例 `test_certified_receipt_accepts_six_pairs` (top-level)、`test_failed_performance_accepts_partial_correctness[0,5]`、
  `test_recorded_verification_failure_accepts_empty_correctness`; 負例
  `test_completed_performance_requires_correctness_top_level[0,1]`、`..._reason_branches[0,1,5]`、
  `test_completed_performance_rejects_duplicate_correctness_pair` (6 件 5 対)、`test_completed_performance_rejects_seven_correctness_entries`。

## 受理集合の差

| 入力 (他の既存検査は満たす) | 変更前 | 変更後 |
|---|---|---|
| 性能 completed + 検証 attempt 無し + correctness が 6 対の完全被覆を欠く (0〜5 件、6 件中の重複対) | 受理 | `correctness` で拒否 |
| 性能 completed + 検証 `pre_performance_infra_failure` + 0〜5 件 (§7.1(1) の失敗記録) | 受理 | 受理 |
| 性能 completed + 検証 completed + 6 対 | 受理 | 受理 |
| completed 性能 attempt 無し + 0〜5 件 | 受理 | 受理 |

「成功・certified」の raw 定義 = 「completed 性能 attempt があり、検証割当ての失敗が受領証に記録されていない」。
`declared_use_class` と `reason_code` の申告だけを正の根拠にしない (§8)。

## 検証

- baseline (変更前、unit3 + unit5 + t139_submission_path、計算ノード): 122 passed / 36.3 秒。
- patch 適用後の焦点走 (計算ノード dispatch 2328.nqsv): **133 passed / 34.5 秒、rc=0**。
- 変異 matrix (container worktree、commit abce1ff51、dispatch): container worktree `.codex/worktrees/t1449-mutcontainer` (commit abce1ff51)、`tools/run_tests.py` 3 file 133 node を dispatch で 11 走。
  **baseline PASSED (63.0 秒)、等価対照 M0 (comment のみ) SURVIVED、負例 M1〜M9 は 9/9 KILLED、期待 node 完全一致 10/10、MISMATCH 0、TIMEOUT 0**
  (`mutation-final-ledger.json`、spec sha256 `1fc080dfd863ab74563800b6c24991732821b134342f39ecfed5347ddd5586bc`)。期待 node は probe 走
  (`mutation-probe-ledger.json`、全件 SURVIVED 期待で観測) の完全集合を写した。M1 (gate 削除) の赤は新負例 7 node だけ = 既存 test は
  本 gate を要求していなかった反実仮想。M3 / M9 (carve-out の削除 / 反転) は `_full_receipt` を通す既存正例 (unit3 の完全正例・study test、
  unit5 の `semantic_positive`・publish authority・destination 経路) と phase 負例 5 本の期待 reason を覆す = §7.1(1) の失敗記録を通す
  carve-out が凍結契約に要る証拠。M5 (件数だけ) = T4 のみ、M6 (被覆だけ) = T5 のみ。所要: probe 31 分、本走 39 分 (dispatch 往復込み)。
- 受入全走: 記録 commit 後の tip で `tools/dev_wave_wait.py acceptance` により投入する (README 記録時点では未実施)。結果は land の受領証 (job dir `acceptance-final-*`) が持つ。

## 実効性の層 (レビュー A12 / B11)

- 直接検証 = `_validate_reason_branches` 単体と top-level `_validate_receipt_semantics`。
- 呼出経由の影響 = private writer `_publish_receipt` (`_writer.py:73`) と `_validate_study_receipts_inner` (単票検証を呼ぶ)。
- 未配線 = 単位 6 の公開 API と認証 (a10/a11) への統合。**検証失敗を記録した受領証が下流で certified 採用されないことは
  認証実装の責務であり、本 gate は保証しない。**

## 裁定パッケージ候補 (scope 外、実装せず)

1. 「成功・certified」の 3 択 (attempt 成功 / stage 成功 / certified 採用) と、失敗例外記録 (allocation 未成立・post failure を含む)
   の認証上の扱い — 単位 6 以降の認証実装が確定するときに再裁定。
2. evidence-without-attempt の参照整合 (検証割当てを指す evidence があるのにその attempt が無い受領証は v2 で 6 対なら受理)。
3. correctness compile の TU / arm 束縛 (D574 決定 (3) の「当該 TU」は correctness 側で照合していない)。
4. 検証 attempt の両 stage 再掲の契約 (§0.1 は割当ての同一 bytes を言い、attempt の再掲は明文が無い)。

## 記録の訂正 (段 3 / 6 が親の brief・裁定を正した点)

- 「失敗なら `design_not_feasible`」は広すぎる: a10 は開始前 infra failure = `design_not_feasible`、correctness anomaly = 候補終端 reject。
- 「検証 attempt は post_performance_failure の raw 経路を持てない」は現 validator の保証でなく正規運用上の想定 (V:2040 は slot を条件にしない)。
- `negative-6.6-correctness-raw` は名前と違い `schedule_seed` を変える vector。raw anomaly 検出の根拠は unit3 1011 / 1037。
- `test_mocc_trace_job_contract.py:3856` の `correctness_evidence` は同名 enum で consumer でない。
- 凍結 vector が拘束するのは unit3 の test 名の実在 (U5:352) と recipe の実行結果 (U5:267)。`_full_receipt` 不変で両方不変。

## 逐語 copy の可逆最小正規化 (DW-S07)

`verbatim/` の 4 本は Codex 出力の markdown 行末空白 (改行 2 個の代替 `  `) が末尾空白検査に抵触するため、**各行末の空白列 (`[ \t]+`) を除去**した (可視文字不変)。原文は job dir `artifacts/dev-wave-t1449-certified-correctness-gate/` (`s3-a-1.md` / `s3-b-1.md` / `s6-a-1.md` / `s6-b-1.md`) に保全し、復元は原文の copy (下記 sha256 で照合) で行う。

| file | 原文 bytes | 原文 sha256 | 正規化後 bytes | 正規化後 sha256 | 除去 |
|---|---:|---|---:|---|---|
| `s3-lensA.md` | 15693 | `31f1bfd980c92dfbce3f1cbdb19679f35a2dea905a00527b4ccf0002b322f28b` | 15557 | `3c1797438c9c83dedb72367a39b4dab1434e50a2643812d3e61121d2063f43bd` | 68 行 / 136 bytes |
| `s3-lensB.md` | 14600 | `b913083ba8c3cf4a4245516f2c31110270982168ad9f5012a2048fc1d3e459fa` | 14464 | `f8ae3ed21f31fd3e2d0385eb65a140c8602e8386db9b7760cacf5965256fa9f0` | 68 行 / 136 bytes |
| `s6-reviewA.md` | 9894 | `00fa92f374a6e42bf7c2c290bfa037e9606383395bc4d345dbc5a4d0b3ed9a78` | 9782 | `05de8b1d9db683c48bb9661127369d4812370ed4f00f8109942d18dc538b3c35` | 56 行 / 112 bytes |
| `s6-reviewB.md` | 9286 | `4a700689ae0dfb345c7052e47d54295d5b7ce22316a06d292e5df67d694ee504` | 9190 | `a546a984d0d1818458ea87b53d4d65bf0a051c6f111a435e1437c386bb413f79` | 48 行 / 96 bytes |

`s2-plan.md` / `s5-author.md` は行末空白なし (bytes 不変)。

## 一次資料

- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1449-certified-correctness-gate/` (brief、逐語、plan、レンズ A/B、裁定、
  author 報告、diff、レビュー A/B、焦点走 log、変異 spec / result、受入 log)。
- 変異 spec sha256: probe `ddb98f0c2de9d9163865f7c80b93f47a30534cc5253b402baab3ca96fb29bc56`、本走 `1fc080dfd863ab74563800b6c24991732821b134342f39ecfed5347ddd5586bc`。
