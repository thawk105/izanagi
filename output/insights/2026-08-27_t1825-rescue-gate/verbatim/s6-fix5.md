# 段 6 fix (3 巡目) 報告

## 1. この fixture が実際に落ちていた issue code (調べた結果、推測でなく)

実 payload は次の内容でした。

```text
code: git-command-error
message: for-each-ref failed: fatal: missing object c354f885b56264014c061c6a578b9c3b1d1187b2 for refs/heads/topic
```

`removed-reflog-object-missing` へ到達する前に、現在の `refs/heads/topic` 自体が missing object を指していたため、`for-each-ref` が失敗していました。

## 2. 実装が悪かったのか fixture が悪かったのか、その判断根拠

fixture が悪いと判断しました。

`missing_oid` と `live_oid` は、同じ tree、parent、時刻、空 message で連続生成されていました。そのため両者が同一 OID となり、`live_oid` へ更新したはずの `topic` が、削除対象の `missing_oid` を引き続き指していました。

修正後は missing object が候補 reflog にだけ残り、実装済みの [tools/check_branch_rescue.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/tools/check_branch_rescue.py:1044) が意図どおり `removed-reflog-object-missing` を出しました。実装変更は不要でした。

## 3. 直した内容 (file:line)

- [orchestrator/tests/test_check_branch_rescue.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:1118)
  - `live_oid` を固有 message `live` を持つ commit として生成。
  - `live_oid != missing_oid` を明示的に検査。
- [orchestrator/tests/test_check_branch_rescue.py:1179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/orchestrator/tests/test_check_branch_rescue.py:1179)
  - issue code 一覧を先に抽出。
  - `rc == 2` と固有 code の assert に診断メッセージを追加。

`tools/check_branch_rescue.py` は今回変更していません。

## 4. この負例が「missing を黙って落とす」変異でだけ落ちることの確認

修正後の通常経路を同じ test 関数で直接診断した結果です。

```text
M25_FIXED_PASS
M25_FIXED_RC 2
M25_FIXED_ISSUE_CODES ['removed-reflog-object-missing', 'removed-reflog-object-missing', 'removed-reflog-object-missing', 'removed-reflog-object-missing']
```

code の重複は start/end snapshot と reflog 内の出現によるものです。他種の issue はありません。

次に、snapshot から `removed-reflog-object-missing` だけを除去し、completeness を再計算する silent-drop 変異を注入しました。

```text
M25_MUTATION_KILLED AssertionError([])
M25_MUTATION_RC 0
M25_MUTATION_ISSUE_CODES []
```

この一変異だけで rc は 2 から 0 になり、負例は `rc == 2` で失敗しました。別の rc=2 事由は残っていません。

## 5. 実走結果 (そのまま貼る)

```text
$ python3 tools/run_tests.py orchestrator/tests/test_check_branch_rescue.py
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1825-rescue-gate/output/pegasus-dispatch/fc732c274c61e93791916d1d5e139d59/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

command の rc は 16 です。test child は起動していないため、pytest green とは報告しません。runner が生成した対象外 artifact は除去しました。

## 6. 壊していないことの確認

- 変更した期待値はありません。
- 今回の変更は指定範囲内の test fixture と診断 assert だけです。
- `tools/check_branch_rescue.py` および他 test 関数は今回変更していません。
- `git diff --check`: rc=0
- Python AST parse: `ast-parse: ok`
- U+0300 から U+036F の scan: `combining-scan: ok`
- runner artifact: 除去済み
- index: unchanged
- `git add`、commit は実行していません。
- full pytest が起動しなかったため、closed 済み所見の動的 regression 確認は未実施です。

## 総括

赤の原因は実装ではなく、`missing_oid == live_oid` となる fixture の OID 衝突でした。live commit を確実に別 OID とし、意図した missing reflog 経路だけで rc=2 になるよう修正しました。silent-drop 変異では rc=0、issues 空となり、負例がその欠陥を殺すことをコードで確認済みです。公式 runner は Pegasus の queue preflight 障害で実走できませんでした。