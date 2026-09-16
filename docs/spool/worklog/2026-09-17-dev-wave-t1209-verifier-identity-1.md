---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t1209-verifier-identity
seq: 1
title: [T-1209] T126 qualification の code identity へ verifier の dsg / model / parse を含めた — 裁定済み (2026-08-17 第 5 回 #20) の identity 純増を Codex author + 変異事前登録で実装し、旧 37-key 形は現行 verify で不受理になる事実を歴史記録と分けて記録した (コード + docs、branch worktree-dev-wave-t1209-verifier-identity、変異 matrix = baseline PASSED・負例 6/6 KILLED 期待 node 完全一致・等価 1 SURVIVED)
---

## 本文

- 依頼は command 引数のとおり (裁定済みの identity 集合追加。着手直前の local main から fresh worktree、起動時に編集面の重複検査、
  Codex author + 変異事前登録、本題の identity 集合だけ、gate・検査・台帳・一般化の追加は scope 外)。一次資料は
  `output/insights/2026-09-17/t1209-verifier-identity/README.md`、逐語は同 `verbatim/`、運転 script・log・spec は
  job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1209-verifier-identity/`。
- 裁定の出所を `rulings-inbox/2026-08-17-rulings-full5-36rulings.md` #20 と entry 622 で照合した。設計判断は
  {{D:t126-code-identity-verifier-dsg-model-parse}}。
- **編集面の重複検査は branch tip (0 件) と 139 worktree の作業ツリー (blob hash 比較、scanned 136 / unreadable 2 = 撤去済み dir の残登録)
  の 2 段で行い、未 commit 差分は着地済み T-548 の Codex 子木 (稼働 process 0) だけで contract.py には無かった。**
- 段 3 の 2 レンズは実装 must-fix 0。**親 brief の一般化 6 件を real として訂正した**: 「壊れる既存成果物なし / live 未実施」は
  「tracked JSON に `code_identity` key 0 件、phase3 の見送り台帳は scope 外と記すのみ、repo 外は未確認」へ、
  「series identity が反応しない」は「3 file の個別 code hash と disk/blob 照合の対象外」へ、「path pin は loader 閉包のみ」は
  T126 自己包含 / 現行閉包 (campaign_lock.py:107) / 歴史 exact62 (:204) の区別へ。A1 (旧 37-key 形は現行 verify で
  `required set mismatch` → driver rc=2 / collector invalid) は D の決定 3 として記録した。
- 裁定パッケージ候補 A7 (`verifier/__init__.py` / `report.py` / `commit_receipt.py` を T126 でも直接束縛するか) は scope 外として
  実装せず、次の一手へ新規登録した。
- 実装 commit `c09211d17` (Codex author、2 file +10 行、逐語どおり)。焦点走 (4 file、計算ノード): 変更前 457 passed / 変更後 461 passed
  (新規 1 + parametrized 3)。**未 commit の contract.py で焦点走が緑だったことを、この 4 file に HEAD blob 比較の drift gate が無い
  実測として変異 matrix の probe 省略の根拠にした。**
- 段 6 レビュー 2 本: A 所見 0、B must-fix 0 / nit 1 (焦点走外の consumer test 7 箇所は受入全走で覆う)。fix 子なし。
- **変異 matrix の 1 回目は harness が起動前に中止した (走行 0)。** 期待 node に登録した
  `test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/pars.py]` は変異下でしか生まれず、
  harness は baseline の pytest collection で実在検査する。N5 を「`parse.py` → tracked 兄弟 `report.py` へ置換」に再照準
  (期待 = 新 test のみ、既存 test は緑のまま) し、初回 spec と attempt json は erratum として job dir と insight に残した。
- 変異 matrix (spec v2、4 file、dispatch): baseline PASSED、N1〜N6 すべて KILLED で期待 node と観測 node が完全一致、等価 E1 SURVIVED。
  N1〜N4 / N6 は新 test だけが赤 = 新規検出力。
- **最終受入 1 走目 (tip `09b79657e`、main `1042a1bc9`、3 shard) は 1 failed / 24389 passed / 67 skipped で rc=70 (受領証なし)。**
  赤は `test_dev_waves_integration.py::test_malformed_child_output_is_output_invalid[oversize]` が `LOG_LIMIT` を期待して
  `SPAWN_FAILED` (子 process の起動失敗) を得た形。本 wave の差分 (contract.py の定数と T126 test) から到達しない file であり、
  entry 462-465 / 557 に同 node・同 assertion のフレーク記録がある。DW-O18 に従い単独再走 (同 file `-k test_malformed_child_output_is_output_invalid`、
  login node bounded local) は 7 passed / 17.0 秒 rc=0 で非再現 → 非帰属のフレークと判定し、この判定を含む tip で受入を再走した
  (結果は land の受領証が持つ)。`flaky_test_holds.py` への登録は再赤時のみ (main に既存 F が無いので登録せず、再赤なら裁定送り)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra`、plan/consult `medium`)。計算ノード job: 焦点走 2、
  変異 9 走 (collection 1 + baseline 1 + 変異 7)、最終受入 1。

## 次の一手差分

### 完了

- [T-1209] verifier の dsg / model / parse を T126 code identity へ含めた (commit `c09211d17`)。旧成果物は据え置き、以後の取得から新 identity。
  remaining: none
  base: b8e4132612ce45d39c738a1c6a3d3d01524dfbfba0afae2ea73aa33cbbad8378

### 新規

- {{T:t126-identity-verifier-init-report-receipt}} **P2・ユーザー裁定待ち**: T126 code identity に `orchestrator/verifier/__init__.py` /
  `report.py` / `commit_receipt.py` も直接束縛するか。pipeline.py の `from ..verifier import` (dispatch 面)、core.py の
  `result_to_dict` / `_domain_digest`、qualification/artifacts.py の `validate_live_receipt` が依存し、T126 の個別 code hash と
  disk/blob 照合の対象外に残る (superproject commit/tree と D473 の loader 閉包では束縛済み)。択 (a) 3 file を足す (D473 と対称) /
  (b) 足さない (commit/tree 束縛で足りる)。
