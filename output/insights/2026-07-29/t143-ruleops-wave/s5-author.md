T-143 RuleOps 段5 author 実装を完了しました。コード・テスト6ファイルだけを変更し、commit は作成していません。

## 変更

- [tools/ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1) 新規
  - read-only Git CLI、`inventory` / `inspect --draft` / `check`
  - HEAD tree inventory、canonical JSON出力、strict ledger schema
  - Git env scrub、timeout、replace/graft/shallow拒否
  - blob drift、symlink/gitlink、候補循環、未裁定hitのfail-closed検査
  - mutation receiptはadvisory packageとしてのみ検査
- [tools/run_tests.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:506)
  - acceptance runだけproduction ledgerをpreflight
  - targeted runは従来どおり非発火
  - 子rc/reasonを表示しrunner rc=15で停止
- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/check_docs.py:48)
  - `docs/ruleops.md`をliving docと行番号参照検査へ登録
- [orchestrator/tests/test_ruleops.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:1) 新規
  - M1〜M12、synthetic Git repo、real checkout CLI dry-run
- [orchestrator/tests/test_run_tests_preflight.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_run_tests_preflight.py:295)
  - 発火・非発火・失敗伝播・main結線
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_check_docs.py:2122)
  - 独立literal pinと消失・行番号参照positive control

現行受理は、acceptance形がdeletion/submodule preflightを通り、targeted形はそれらを回避する契約でした。変更後もその分類を維持し、acceptance形だけにRuleOps構造検査を追加しました。`check`成功出力は `structurally_valid=true`、`candidate_count=N`、`human_approved=false` の3キーだけです。

## 実走結果

- `orchestrator/tests/test_ruleops.py`: **34 passed in 11.39s**
- `orchestrator/tests/test_run_tests_preflight.py`: **83 passed in 0.32s**
- `orchestrator/tests/test_check_docs.py`: **124 passed / 1 expected failure**
  - `test_real_repo_clean`
  - 親所有の `docs/ruleops.md` 未landのみ
- `test_plain_runner_coverage.py`: **2 passed / 1 expected failure**
  - `test_every_test_file_is_self_runnable_or_allowlisted`
  - 親所有READMEのpytest-only allowlist未landのみ
- `python3 tools/check_codex_agents.py`: 緑
- `python3 tools/check_docs.py`: 上記 `docs/ruleops.md` 不在1件だけ

予期せぬ赤はありません。子の実走は親の全受入走を代替しません。

## 波及・未解決事項

- 親が `docs/ruleops-candidates.json` をlandするまで、実production acceptance preflightはrc=15になります。
- 親による `docs/ruleops.md` と `orchestrator/tests/README.md` のland後、期待赤2件は解消予定です。
- 共有fixtureの所有外変更はありません。runnerの既存mainテストだけ、新preflight mockを追加しました。
- 開始時から存在した親所有の `?? output/insights/2026-07-29_t143-ruleops-wave/` は終了時も存在します。authorからは書き込んでいません。
- `git diff --check`および新規2ファイルのno-index whitespace検査は緑です。
- hookはCodex未配線として手動契約を遵守し、発火したとは主張しません。
- commit禁止のためcommit後provenance検査は未実施です。

## 総括

RuleOps v1のread-only inventory・人間レビュー用候補package検査・acceptance preflightを実装しました。M1〜M12は実位置の単一理由境界へ照準済みで、残る赤は事前指定された親docs/allowlist未landの2件だけです。