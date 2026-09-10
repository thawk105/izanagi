指定2ファイルのみ変更しました。commitは作成していません。

| Fix | 状態 | 内容 |
|---|---|---|
| compiler単独cache軸 | partial | genome、commit、trace、src token、admissionを固定し、`g++-12`と`g++-13`だけを変える正例を追加。実走未完了 |
| `cxx=cxx`統一 | partial | 対象9 nodeのconsumerをkeyword指定へ統一し、positional index表を削除。実走未完了 |
| qualified calleeとscope | partial | qualified name限定と、nested function/lambda/classを除外するwalker、decoy検査を追加。実走未完了 |
| `_any_cxx()` 4状態 | partial | 両helperについてg++-13 only、g++-12 only、g++ only、全候補不在を表駆動化。戻り値と探索順を検査。実走未完了 |

変更箇所は [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1526-t1527-site-compiler/orchestrator/tests/test_campaign.py:3036) と [test_skip_classification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1526-t1527-site-compiler/orchestrator/tests/test_skip_classification.py:83) です。

実走結果:

- 実走nodeid: 0件
- 対象16件相当の一括実行: rc=16
- `test_skip_classification.py`単独再試行: rc=16
- 両方とも`qstat -Q preflight rc=1`でdispatch infrastructure failure
- `child_started=false`のため、pass、skip、redはいずれも未観測です。未実走をgreenまたはclosedとは扱っていません
- 静的確認のみ、両ファイルのAST parse成功、`git diff --check`成功

所有外波及:

- `git status --short --untracked-files=all`で変更は指定2ファイルのみ
- production、README、docs、submodule、dev-wave job artifactは未変更
- ランナーがignored領域の`output/pegasus-dispatch/`へ失敗receiptを2件生成
- commitなし
- 差分内にU+0300からU+036Fなし

## 総括

4 fixの実装は完了していますが、Pegasus dispatch障害でテストは1件も開始されていないため、全項目をpartialと判定しました。期待赤0件は未確認です。