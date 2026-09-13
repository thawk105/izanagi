## 総括

binding と policy hash を修正しました。
実 policy の `load_policy(V3_SIZED_STUDY_ID)` は成功しました。
焦点テストは dispatch 障害で起動できず、**実装済み・未実走**です。
テストの期待値と、指定外の policy 値は変更していません。

## 所見への対応表

| 所見 | 状態・根拠 |
|---|---|
| pilot_result binding の key 集合 | **partial**：`path` / `sha256` のみに修正し、loader 成功。焦点テスト未実走のため closed とはしません。 |

## 変更した file と要点

- `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`：余分な 4 key を削除。
- `orchestrator/campaign/paper_story_a1_paired.py`：`V3_SIZED_POLICY_SHA256` を更新。

テストファイルは変更なし。凍結 README・証明書の hash は不変です。

## 実走した検査

```bash
PYTHONDONTWRITEBYTECODE=1 IZANAGI_TASK_RUNS_ROOT=/tmp/a1-sizing-fix-task-runs python3 tools/run_tests.py orchestrator/tests/test_paper_story_a1_paired.py -n 4 -p no:cacheprovider --basetemp=/tmp/a1-sizing-fix-pytest
```

対象 nodeid 範囲：同ファイル全体。
結果：runner **rc=16**、pytest 未起動。実走 nodeid なし、passed **0** / failed **0**。

別途、loader 呼出し、hash 一致、AST 構文解析、`git diff --check` は成功しました。

## 赤と、その帰属

`qstat -Q preflight rc=1` による実行基盤障害です。残存するテストの赤の件数・内訳は未取得です。自動生成された dispatch 証跡は `/tmp/a1-sizing-fix-dispatch-1912bcc73009cfd5525843ea979f2b66` へ退避しました。

## 実測した hash

policy bytes と `V3_SIZED_POLICY_SHA256` は一致しています。

```text
4a1ff56962538fdeb8ecbde3349a597a633186d8e33f1f4651e960a8edd720be
```

## 親へ返す項目

焦点テスト全体を再実走し、D1452 の 5 負例、underflow、十進精度の拒否を確認してください。commit・branch 操作・push は行っていません。