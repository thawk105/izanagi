# 段 6 fix (M24 検出力の穴) 報告

## 1. 足した走行 (非空閉包 / 空閉包、それぞれの起動引数)

[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:570) 内だけに追加した。

- 非空閉包:
  `_run_tool(repo, "--branch", "nonempty-topic", "--landed-checker", str(checker))`
  - main の子 commit を候補 tip にして `commit_count > 0` を確認。
- 空閉包:
  `_run_tool(repo, "--branch", "missing-topic", "--landed-checker", str(checker))`
  - `candidate-ref-missing` により `_closure()` の early return を通過。
  - rc=2、`commit_count == 0` を確認。

両 payload で次を検査し、失敗メッセージへ検出値を含めた。

- `branch_delete_authorized`
- `deletion_authorized`

## 2. M24 の変異を入れると落ちることの確認方法と結果

repo 外の一時コピーへ変異を適用し、対象関数を直接呼ぶ限定 harness で確認した。repo 本体の `tools/check_branch_rescue.py` は変更していない。

非空 return 側の M24:

```text
M24_MUTANT_KILLED: non-empty closure contains branch_delete_authorized values: [False]
```

空 early return 側の同等変異:

```text
M24_MUTANT_KILLED: empty closure contains branch_delete_authorized values: [False]
```

変異なしの対象関数:

```text
TARGET_FUNCTION_BASELINE_PASSED
```

一時コピーは確認後に削除した。

## 3. 既存 assert を壊していないことの確認

- 差分は 45 行追加、削除 0 行。
- `object_retention_provided` の既存 assert は維持。
- 不正 retention claim の既存 assert も維持。
- 他の test 関数は未変更。
- `git diff --check` は rc=0。
- `git status --short` は対象テスト一ファイルだけ。
- `git add`、`git commit` は未実施。

## 4. 実走結果 (そのまま貼る)

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/2d10e14d25c7c266b1182be4dcd75db8/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

終了コードは 16。qstat preflight で停止し、テスト子プロセスは起動していない。force を外した runner も同じ理由で rc=16 だったため、対象ファイル全体の正式な pytest 実走はできておらず、緑とは報告しない。生成された receipt は削除済み。

## 総括

指定された一関数だけへ、非空 return と空 early return の両経路を覆う M24 検査を追加した。両変異が新しい assert で殺されることは限定 harness で確認済み。正式な runner 実走のみ Pegasus dispatch infrastructure failure のため未完了。