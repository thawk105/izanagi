---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-t1356-sort-closed-region-wiring
seq: 1
title: '[T-1356] sort closed-region 残余を auditor の gallery/checklist/入力へ結線した (コード+テスト+docs+記録、branch worktree-t1356-sort-closed-region-wiring、変異matrix = baseline PASSED・4/4 KILLED (単一原因)・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 2026-08-18 /rulings 全件第8回裁定 (`docs/archive/worklog-phase3-0819-671.md:551-554`)
  「sort の closed-region 残余を auditor の入力と checklist へ結線する」の実装。段2 codex plan・
  段3 敵対相談2レンズ (lane sol/luna) が独立に「型番号は5個 (17-21) に分割、1個集約は不採用」
  「auditor 入力側 (`docs/phase3-s5-sort-runbook.md`) の未結線」を real 所見として発見・採用した。
- **段6 レンズB が must-fix を検出: 実装時の型17-21記述が D48/D511 の「境界条件を書かない」に
  違反していた。** 親の段5 prompt 自体が「なぜ verifier が見逃すか具体的機序を file:line 付きで
  書け」と指示したことが D511 と緊張関係にあり、機械 gate が検査しない具体的識別子・
  検出/未検出のループ形・corpus 発火条件を開示する結果になった (T-396 が一度是正した同型の
  誤りの再演)。fix で coder-v4-autonomous-sort.md の「機械執行の範囲」表と同じ抽象度へ後退させ、
  機序説明は auditor 自身の `verifier_blind_spot` (発見時の事後報告) へ委ねる設計に直した。
  焦点再レビューで全所見 closed・GO を確認。
- fix commit の trailer で scope 値に大文字 (`s6-revA`/`s6-revB`) を使い `docs/ai-provenance.md`
  の IDENT 正規表現 (小文字のみ) 違反となり、全史 provenance 監査が新規違反2件で rc=1 になった。
  `AI-Agent-Correction` 前方訂正機構 (`docs/provenance/correction.md`) は特定 historical commit
  1件に固定・消費済みで使えなかったため、`git reset --soft HEAD~1` (非破壊、ファイル内容は
  完全温存) で trailer だけを訂正し再commit した (`--amend` は使わない既定規律のため代替)。
  再監査で新規違反なしを確認。
- **変異 matrix で `tools/mutation_harness.py` の構造的限界を2種類実測した。** (1) role-spec pin
  drift 系の変異は `test_codex_agents.py` の module import 時即時評価により個別 test node でなく
  pytest collection ERROR (ファイル全体1件) になり、harness の canonical node 抽出器が
  fail-closed abort する ([T-1411] が踏んだ別種の harness 非互換と同系統)。(2) 複数ファイル合計
  166 test の `--collect-only` 出力が dispatch capture のバイト上限で切り詰められ、期待 node が
  誤って「実在しない」と判定された。前者は Edit→`run_tests.py`実走→`git checkout --`復元の
  手動検証 (2件、単一原因のエラー文言を確認)、後者は `file::test_name` の直接指定への retarget
  (2件、標準harnessでKILLED確定) で解消した。詳細は {{F:mutation-harness-collection-error}}、
  {{F:mutation-harness-collection-truncation}}。恒久対応は memory
  `mutation-harness-collection-error-needs-manual-verify` /
  `mutation-harness-collection-output-byte-cap`。
- 設計判断は {{D:auditor-violation-type-vocabulary-expansion}}。
- **エージェント工数**: codex 子 6本 (plan 1 [researcher]・consult 2 [reviewer, lane sol/luna]・
  author 1・review 2 [reviewer]・fix 1 [author])。全 job で `model=gpt-5.6-luna` 実測
  (`--lane` は consult 専用でモデル選択とは別軸、DW-O01「全段luna」を実測確認)。
  plan/consult は明示 `--reasoning max`、author/review/fix は docs-authority 由来の自動導出
  (T-1362 相当の拘束が main へ着地済みと本wave中に実測、`--reasoning` 明示指定は rc=2)。
- 正本 = `output/insights/2026-08-20_t1356-sort-closed-region-wiring/README.md`。

## 次の一手差分

### 完了

- [T-1356] sort の closed-region 残余5項目 (新しい型/関数の追加・非決定ビルトイン・
  副作用のある呼び出し・ループ・例外送出) を auditor の gallery (型17-21)・checklist (項目14)・
  入力 (runbook 明記) へ結線した。CC variant 側の raw 受理集合 (DENY_TABLE・sort_swo_oracle
  判定ロジック) と coder-v4-autonomous-sort.md の禁止5bulletは1byteも変更していない。
  変異matrix 4/4 KILLED (単一原因) で pin 閉包の実効性を実証した。受入全走は本記録commit後に
  land の前提として投入する (結果は受入 lease/land の受領証が正本、DW-S01 の「記録を後から
  足すと land が rc=23」規律に従い worklog への追記はしない)。
  remaining: none
  base: ad071fae2c6159a0cbe0b3e97ff6f662b65d29129478b071cd14e643a12d8ae3
