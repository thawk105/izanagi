---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1363-c06-budget-consumer
seq: 1
title: 8c 条件 C06 の予算 consumer と評価器を新設する (コード、branch worktree-dev-wave-t1363-c06-budget-consumer)
---

## 本文

- 2026-08-18 のユーザー裁定「EVIDENCE_UNDEFINED 7 件の証拠契約を定義する (裁定不要・実装のみ)」に
  従い、§6-6 が要求する累積ベンチ実時間予算の実 consumer を新設した。
- **引数の前提が 1 件 stale だった。** 「t822 wave が世代 7 を占有中」とあったが、
  `condition-freeze.v1.g7.json` は同日 17:50 に main へ着地済みだった。ただし C03 / C07 / C08 を
  扱う稼働 wave が 3 本あり、そちらと凍結世代が衝突するため、scope 除外 (契約反転・凍結 record・
  `DECIDER_VERSION` bump をしない) は理由を差し替えたうえで維持した。
- **「評価器を実装・登録する」という指示は、単独では実行不能だった。** 契約 JSON の
  `machine_checkable` と `_MACHINE_EVALUATORS` は双射で機械 pin されており
  (`test_machine_checkable_contract_and_evaluator_registry_are_bijective` ほか 1 本)、片方だけ動かせない。
  段 4 で {{D:staged-evaluator-registry}} を裁定した。
- **親が実測して覆した前提。** `load_ratified_freeze(ROOT)` は現 HEAD で
  `[no-active] live active pointer が無い (v2 未発効)` を送出する。契約が要求する
  `run_trial -> load_ratified_freeze -> reserve_all_cells` は今日の repo では 1 度も成功しない。
  したがって本 wave の配線は必ず fail-closed で倒れる。「配線して動作を確認した」とは記録しない。
- **§5 の欄名を原典で確認し、単一総予算では不足と判定した。** 欄は「累積ベンチ実時間の総上限と
  arm ごと・holdout ごとの上限」であり、3 層すべてを持つ `BudgetLimits` にした。
- **8b の `schedule_sha256` は流用しなかった。** 名前は `s8b_oracle_manifest.py:273` ほかに実在するが
  別族であり、流用は D75 が禁じる同名識別子の二義化に当たる。C05 の schedule
  (`output/s8c-preregistration/schedule.v1.json` / `orchestrator/campaign/s8c_schedule.py`) は
  どちらも未実装のため、取得できなければ bench 前に fail-closed とした。
- **段 3 敵対相談は blocker 9 件・must-fix 12 件、refuted ゼロ。** 段 6 敵対レビューは blocker 0 件で、
  3 層上限が数値 witness で各分岐へ到達すること・`symmetric_indeterminate` が片 arm 起動を拒否すること・
  段階 registry が production dispatch から閉じていること・評価器に充足経路が無いことを確認した。
- **両レビューが独立に同じ最重要欠陥を指摘した (= real)。** 壁時計終了時に `settle` が飛び、
  予約が `held` のまま残る経路。`_settle_budget_cell` は空世代を許容する設計なのに、
  `_finish_trial` が `break` してから精算するため到達しなかった。fix 第 3 巡で共通 finalizer へ集約した。
- **fix は 3 巡 (上限) を使い切った。** 第 1 巡は `ast.Call` に `.id` を読む型の取り違え (4 赤 → 2 赤)、
  第 2 巡は正例 fixture の ledger 欄不足 (2 赤 → 全緑)。実装子は pytest を実走できないため、
  AST を扱う実装で型の取り違えが素通りした。
- **第 3 巡 (W1 / W2 / W3) は破棄した。** 実装子は 3 件とも `closed` と申告したが、親の実測では
  1 failed + 1 error (542 passed) で、**fix 前に緑だった状態からの回帰**だった。内訳は
  (a) 候補 commit 合成を worktree 全体の `git add -A` に変えたため 20 秒でタイムアウト
  (setup error)、(b) 第 2 巡で閉じた正例 `test_c06_staged_fixture_is_not_a_contract_promotion` が
  `UNSATISFIED` へ逆戻り。(a) は段 6 レビュー B の所見 6 が「時間制限時には受入結果自体が
  得られなくなる」と事前に予測していた形であり、「開発するほどテストが遅くなる構造を作らない」
  規律にも触れる。`DW-O16` の 3 巡上限に従い fix を重ねず、検証済みで緑の実装を着地させ、
  W1 / W2 / W3 は real のまま {{T:c06-settlement-and-runtime-tests}} へ送った。
- **子の完了申告は実測ではない。** 第 3 巡は「W1 / W2 / W3 すべて closed」「regressed 0 件」と
  報告したが、実測は回帰だった。申告を検査の代わりにしない。
- **wave slug の `t1363` は実在する無関係な [T-1363] と衝突していた。** commit message からは外した
  (branch 名は稼働中のため変えていない)。本 wave に対応する T は台帳に存在しなかった。

## 次の一手差分

### 新規

- {{T:c06-machine-checkable-promotion}} **P2・新規**:
  C06 を機械検査対象へ昇格させる。残る作業は契約 JSON の `machine_checkable` 反転 1 bit、
  `_MACHINE_EVALUATORS` への 1 行、`DECIDER_VERSION` bump、その版を持つ次世代 record の 4 点で、
  **4 点は同一変更単位でしか動かせない**。兄弟 wave (C03 / C07 / C08) と凍結世代が衝突するため、
  それらの land 後に単独 wave で行う。
- {{T:c06-settlement-and-runtime-tests}} **P2・新規**:
  段 6 敵対レビュー 2 本が独立に real と判定した 3 件。本 wave の fix 第 3 巡が試みたが回帰を入れた
  ため破棄した。(W1) 壁時計終了時に `settle` が飛び予約が `held` のまま残る
  (`_finish_trial` が `break` してから精算する構造)。**成果物影響:** v2 発効後に
  `settlement.cells` と実測秒が欠落し、certified 選択・層3 材料・試行台帳の予算参照が成立しない。
  現状は `load_ratified_freeze` が `no-active` で倒れるため発火しない。
  (W2) 予算不足の早期 return が `run_root` / `report.json` / `attempts.jsonl` を作らない。
  (W3) 新設テストが AST 検査と合成 fixture に留まり実効経路を実行していない。
  **W3 の実装では候補 commit 合成に worktree 全体走査を持ち込まないこと** — 第 3 巡はこれで
  20 秒タイムアウトを起こした。
- {{T:c06-consumer-followups}} **P3・新規**:
  段 6 敵対レビューが real と判定しつつ本 wave の scope 外とした 6 件。
  (a) malformed consumer 用の専用 reason code、(b) schedule cell と `TrialBinding` の対応検証
  (C05 未実装のため現状発火しない)、(c) O_EXCL stale lock の診断と人間向け復旧手順
  (fail-closed 方針は維持)、(d) 実 repository candidate commit 合成 fixture の共通化、
  (e) 到達解析の余裕 (modules / depth / states / bytes) を受入成果物へ記録、
  (f) 兄弟 wave 統合後の I1 と全受入の再確認。
