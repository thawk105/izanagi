---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t1449-certified-correctness-gate
seq: 1
title: [T-1449] 受領証 validator に D1272 の条件付き最小 gate を入れた — 性能 completed かつ検証割当ての失敗が未記録なら correctness_evidence の 6 対を要求する (コード + docs、branch worktree-dev-wave-t1449-certified-correctness-gate、変異 matrix = baseline PASSED・負例 9/9 KILLED 期待 node 完全一致・等価 1 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼 (command 引数): 「成功・certified な受領証のときだけ correctness_evidence を非空かつ必要な三者比較ありに要求する
  条件付き最小 gate を入れる (D1272)。失敗途中の受領証の空配列 (minItems:0) は維持。対象 schema と verifier を段 1 で現物同定し、
  正例・負例を同じ変更単位で置く。Codex author + 変異事前登録。本題の gate 1 条件だけ。規律 2 を緩めない」。
- 一次資料は `output/insights/2026-09-17/t1449-certified-correctness-gate/README.md`。brief・逐語・plan・レンズ・裁定・author 報告・
  diff・レビュー・log・変異 spec / result は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1449-certified-correctness-gate/` に保全。
- **段 1 の現物同定:** 受領証 schema は凍結 blob (`receipt-schema-v1.json`、manifest pin) で触らない。検証器
  `_semantic_validator.py` の `_validate_reason_branches` は「検証 attempt completed ⇒ 6 対」を既に持ち、穴は「性能 completed かつ
  検証 attempt の帰結が未記録」の受領証。既存正例 `_full_receipt` は性能 completed + 検証 `pre_performance_infra_failure` +
  correctness 1 件で受理されている。編集面の重複検査: branch tip 0 件、登録 worktree 141 本の作業ツリー走査で 0 件。
- **段 2 plan の P1-b (性能 completed ⇒ 無条件に 6 対) は段 3 レンズ A が過剰拒否と指摘し不採用。** 検証割当ての失敗は正規運用上
  `pre_performance_infra_failure` に写り、追補 A a10 で study は `design_not_feasible` 終端。その stage 受領証は凍結事前登録 §7.1(1)
  が 0〜5 件で受理する。gate は「性能 completed かつ検証割当ての失敗が未記録」の受領証にだけ 6 対を要求する形に確定
  ({{D:certified-gate-raw-success-definition}})。
- 段 3 の親 brief への訂正: 「失敗なら `design_not_feasible`」は a10 の区別 (開始前 infra failure / correctness anomaly) より広い;
  凍結 vector が拘束するのは unit3 の test 名の実在と recipe の実行結果; `negative-6.6-correctness-raw` は `schedule_seed` を変える
  vector; `test_mocc_trace_job_contract.py:3856` は同名 enum で consumer でない。
- **実装 (commit `abce1ff51`、Codex author):** validator +24 行、unit3 +157 行。`_full_receipt` は不変 (§7.1(1) の失敗記録の
  正例 + 凍結 vector 46 本の基底)。helper `_certified_receipt` (検証 completed + 6 対 + liveness 6)、`_without_verification_attempt`、
  `_completed_performance_reason_payload`。新 test 11 node (正例 4、負例 7、top-level と `_validate_reason_branches` 単体の両方)。
  既存 test の期待値は不変。
- 段 6 敵対レビュー 2 本は must-fix 0。real 所見は記録の精度 (M3/M9 が殺す既存 node の完全列挙は probe で、M6/M7 の old は行全体、
  裁定 §2 の「6 対未満」は「完全被覆を欠く」)。
- 焦点走 (unit3 + unit5 + t139_submission_path、計算ノード dispatch): 変更前 122 passed / 36.3 秒、変更後 **133 passed / 34.5 秒**。
  1 回目の変更後走は login node の bounded local が OOM 上限 (≈2 GB) で退き dispatch へ切り替わった (変更に帰属しない)。
- **変異 matrix (container worktree、commit abce1ff51、dispatch、3 file 133 node):** baseline PASSED (63.0 秒)、M0 (comment のみ) SURVIVED、M1〜M9 KILLED、期待 node 完全一致 10/10、MISMATCH 0
  (spec sha256 1fc080df…、期待 node は probe 走の観測完全集合)。M1 (gate 削除) の赤は新負例 7 node だけ = 既存 test は本 gate を
  要求していなかった反実仮想。M3 / M9 (carve-out の削除 / 反転) は `_full_receipt` を通す既存正例 (unit3 + unit5、study test) と phase
  負例 5 本の期待 reason を覆す = §7.1(1) の失敗記録を通す carve-out が凍結契約に要る証拠。M5 = T4 のみ、M6 = T5 のみ。
  所要 probe 31 分 + 本走 39 分。
- 受入全走: 記録 commit 後の tip で単独に投げ、結果は land の受領証が持つ (worklog 記録時点では未実施)。
- 実効性の層: 直接検証 = 単体 + top-level。呼出経由 = private writer と study 検証。未配線 = 単位 6 の公開 API と認証。
  **検証失敗を記録した受領証が下流で certified 採用されないことは認証実装の責務であり、本 gate は保証しない。**
- 工数: codex 子 6 本 (plan 1 [1 本は prompt 誤りで親が 3 分で停止し再投入]、consult 2、author 1、review 2、全段 `gpt-6-astra` /
  `medium`)。計算ノード job: 焦点走 2、変異 probe + 本走、受入。

## 次の一手差分

### 完了

- [T-1449] D1272 の条件付き最小 gate を `_validate_reason_branches` に入れ、正例・負例を同じ変更単位で置いた
  (commit abce1ff51、{{D:certified-gate-raw-success-definition}})。
  remaining: none
  base: aaec5f0f1fc3325a255690436484b6a8f8c26750f22f91564aa00868dbaf7b78

### 新規

- {{T:certified-gate-scope-out-followups}} **P3・ユーザー裁定待ち**: D1272 gate ({{D:certified-gate-raw-success-definition}}) の
  scope 外として段 4 / 段 6 が返した 4 件。(1) 「成功・certified」の 3 択 (attempt 成功 / stage 成功 / certified 採用) と、失敗例外記録
  (allocation 未成立・post failure を含む) の認証上の扱い — 単位 6 以降の認証実装が確定するときに再裁定。(2) 検証割当てを指す
  correctness_evidence があるのにその attempt が無い受領証の参照整合 (現 gate は 6 対なら受理)。(3) correctness compile の
  TU / arm 束縛 (D574 決定 (3) の「当該 TU」は correctness 側で照合していない)。(4) 検証 attempt の両 stage 再掲の契約
  (§0.1 は割当ての同一 bytes を言い attempt の再掲は明文が無い)。いずれも防御的堅牢化の側なので既定は見送り、実害または
  認証実装の着手で再訪。
