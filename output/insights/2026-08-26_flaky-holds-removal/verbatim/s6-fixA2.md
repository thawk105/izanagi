## 総括

赤 1 は実装ではなく、新設 test の期待値誤りと判断して修正した。  
赤 2 は不足していた親 directory の再帰作成を追加した。  
実装本体と既存 test の期待値は変更していない。  
他 2 file の同型 control に静的な誤りは見つからなかった。  
焦点走は Pegasus preflight 失敗で開始されず、実装済み・未実走である。

## 赤 1 の原因と直し方 (実装が誤りか、期待値が誤りか)

期待値が誤りだった。

`output/variants` 以下に tracked descendant がないため、Git は ignored-only subtree の各祖先を除外可能な directory として畳む。このため `variants`、`variants/v1`、`variants/v1/bin` が返るのは正しい。

期待値をその集合へ合わせ、理由を 1 行コメントで固定した。非実在の literal 規則である `runs`、`cache/deep`、`global-cache`、`info-cache` の検査は変更していない。

## 赤 2 の直し方

`output/runs` が未作成でも `output/runs/nested` を作れるよう、`tracked.parent.mkdir(parents=True)` に変更した。

tracked file と祖先 directory が snapshot に現れ、同 prefix 内の untracked file が現れないという検査内容は変更していない。

## 他 2 file の同型検査の結果

- `test_real_repo_serialization.py`: `runs-visible` control は `tmp_path` 直下で、必要な親は存在するか `parents=True` で作成している。prefix は実 repository の `ROOT` から取得しており、M10 型の fixture repo 問題はない。
- `test_s8b_floor_campaign.py`: 同様に作成先は `tmp_path` 直下で、`runs-visible/nested` は `parents=True`。最適化版と独立 reference の両方を検査している。
- 親不在の `mkdir()`、tracked sentinel の置き忘れ、`tmp_path` と `output/` の取り違えは見つからなかった。

## 変更した file と行

- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_oracle_driver.py:700)
  - 701–704 行: wildcard subtree の正しい期待値と理由
  - 712 行: `mkdir(parents=True)`

今回の修正はこの 1 file、4 insertions / 2 deletions。`git add`、commit はしていない。`git diff --check` は通過した。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

**実装済み・未実走。**

次の焦点 2 nodeid を `tools/run_tests.py` 経由で指定したが、test process 開始前の `qstat -Q` preflight が失敗し、runner は `rc=16` を返した。

- `test_s8b_oracle_driver.py::test_git_ignored_output_prefixes_uses_rule_sources_before_paths_exist`
- `test_s8b_oracle_driver.py::test_git_ignored_output_prefixes_preserve_tracked_rule_descendant`

したがって、実走済み test は 0 件であり、緑は主張しない。

## 各項目の状態 (closed / unverified / not-done)

- 赤 1: **unverified** — 修正済み、未実走
- 赤 2: **unverified** — 修正済み、未実走
- 他 2 file の同型検査: **unverified** — 静的検査済み、未実走
- 焦点 2 nodeid: **unverified** — dispatch infrastructure failure
- 3 test file の file 全体走: **not-done**

## 所有外への波及可能性

repository 内検索では `output_snapshot_ignores.py` の consumer は指定された 3 test module だけだった。所有外 caller は見つからない。

共有 `conftest.py`、acceptance ledger、fix 子 B の所有 file、production code は変更していない。今回の変更は新設 contract test 内だけであり、受理集合への波及はない。

## 未完・未確認

- 修正した 2 nodeid の実走確認
- `test_s8b_oracle_driver.py` の file 全体走
- `test_real_repo_serialization.py` と `test_s8b_floor_campaign.py` の対象 control 実走
- runner は既定の dispatch receipt を `output/pegasus-dispatch/` に生成したが、編集・削除していない