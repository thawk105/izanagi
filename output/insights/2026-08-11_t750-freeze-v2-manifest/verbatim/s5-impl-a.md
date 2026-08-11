単位 A を専用 worktree `dev-wave-t750-impl-a` に実装しました。親 worktree、docs、所有外ファイル、実 `output/` は未変更で、commit も作成していません。

実装内容:

- [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-a/orchestrator/campaign/s8b_holdout_freeze.py:53)
  - pinned `BUDGET_APPROVAL_SHA256 = None` と固定 approval path。
  - strict floor/budget/approval 検証、`100` と `100.0` の canonical bytes 区別。
  - captured HEAD blob に基づく source と measurement closure の再導出。
  - v2 g1 builder/generator、SafeA dirfd writer。
  - `generate-v2-candidate` CLI。承認・root・世代番号指定面はありません。
- [s8b_v2_freeze_fixture.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-a/orchestrator/tests/s8b_v2_freeze_fixture.py:109)
  - tmp git repo 内だけで official-shaped floor result、budget、approval、closure を構築する synthetic fixture。
- [test_s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-a/orchestrator/tests/test_s8b_holdout_freeze.py:753)
  - 未批准、happy path、数値表現差、非 eligible floor、HEAD にない closure、揮発 hash、固定出力、symlink/既存 leaf、CLI surface のテストを追加。

保護対象の `build_document`、`generate`、`verify_document`、`verify`、`verify_cli_with_t080_receipt`、`TOP_LEVEL_KEYS`、`GENERATION_SCHEMA_FIELDS` は親原本と AST 完全一致です。

検査結果:

- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- synthetic fixture smoke:
  - build → SafeA writer 成功
  - `100` / `100.0` 不一致拒否
  - captured HEAD にない closure hit 拒否
- pytest は実装済み・未実走です。以下はすべて `tools/run_tests.py` が `qstat -Q` preflight rc=1、wrapper rc=16 で停止し、実行 node 数は 0 でした。
  - `test_s8b_holdout_freeze.py -k v2_candidate`（2回）
  - 同ファイル全体
  - `test_plain_runner_coverage.py`
  - `--collect-only`
- 事前指定した親 docs 由来の期待赤集合は空。テスト赤は観測されず、infra failure のみです。

静的な波及可能性:

- 現時点で新 API の所有外 caller はありません。
- `s8b_ratified_freeze.py` が v2 schema、transition、closure の後続 consumer です。
- 共有 fixture は `test_s8b_oracle_manifest.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_report.py` から import されています。既存 API は変更していません。
- generator source hash を観測する T-080／oracle driver 系テストと、単位 B の manifest／ratified consumer tests は親統合後の再走対象です。

## 総括

- v2 g1 candidate producer、pinned budget authority、SafeA writer、CLI を純増しました。
- v1 の保護本体と schema 定数は原本と同一です。
- 所有 3 ファイル以外、実成果物、docs、commit は変更していません。
- 残リスクは pytest 未実走と、単位 B 統合後の consumer 回帰確認です。