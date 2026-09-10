修正済み・commitなしです。編集は [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py) のみです。

## 総括

1. O25除去2箇所で末尾改行を保持。O26は正しいH2として認識され、fixture実測は期待1件・実測1件。

2. `condition_all_operations_deleted` を `len(_OPERATION_CONDITION_KEYS) + 1` に修正。fixture実測は21件。

3. titleless reorder fixtureも同じ改行欠落を修正。O26 H2と順序違反findingを確認。`_assert_violation` は共通契約への影響が大きいため未変更。

pytestはrunner経由で全体走行を試みましたが、`qstat -Q` preflight rc=1／`qlogin` socket拒否により未実走です。`python3 tools/check_docs.py` は親復元中のO26欠落による想定どおりrc=1、`git diff --check` は成功。**実装済み・未実走であり、closedとは申告しません。**