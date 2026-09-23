## 直したこと

[対象試験](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/tests/test_campaign.py:7516) の `first` を `U` から `I` に変更しました。`existence` case で `read-unborn-genesis` が 1 件発生し、malformed と framing は 0、commit witness は期待値と一致することを assertion で確認します。存在違反の件数を除けば integrity が clean になることも確認します。

## 変更行数

試験のみ **+9 / −1 行**。production と他の試験は変更していません。

## 実走結果

指定の直接実行は **PASS**。同じ試験内の certified 正例、v2 対照、witness 3 case も通過しました。`git diff --check` も通過しました。

## 総括

`existence` case は存在違反だけで indeterminate になります。
正常な挿入版の読みは certified のままです。
v2 対照と witness 3 case の期待値は維持しています。