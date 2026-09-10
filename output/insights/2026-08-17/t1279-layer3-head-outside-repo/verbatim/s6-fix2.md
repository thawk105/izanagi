## 総括

- 指定された前提 assert のみ修正した。
- production コードと docs は触っていない。
- 既存テスト本体の期待値は変更していない。
- skip、warning、期待値の緩和は追加していない。
- commit は作成していない。
- 実装済み・未実走である。

### 変更した箇所

[test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_layer3_report.py:218) の helper を `_assert_external_campaign_without_git_head` に改名し、呼び手3箇所も追随させた。

helper は次の2点を直接検査する。

1. campaign が source repo の外側にある。
2. `layer3_report._git_head(campaign)` が `Layer3ReportError` を送出する。

### 前提 assert の新旧の差

旧実装は filesystem root まで遡り、各祖先の `.git` が存在せず symlink でもないことを要求していた。このため、有効な Git repository ではない空の `/tmp/.git` でも失敗した。

新実装は祖先 marker の loop を削除し、テストが必要とする「campaign から Git HEAD を取得できない」という性質を `_git_head` の例外で直接検査する。祖先に本物の Git repository があれば `_git_head` が成功し、前提 assert が赤になる。

### 弱めていないことの根拠

source repo 外であることを確かめる既存の `assert not resolved.is_relative_to(source_repo)` は維持した。例外検査は skip や warning ではなく `pytest.raises(Layer3ReportError)` である。

対象3 node にある lock pin の完全一致、certifying 入口の送出、v1 の送出に関する本体 assert は変更していない。production コードにも今回の編集を加えていない。

### 未実走であることの明記

指示どおり pytest は実行していない。実装済み・未実走であり、緑とは報告しない。

静的確認として、対象ファイルの `git diff --check` と Python 構文解析は成功した。旧 helper 名と `git_marker` loop が残っていないことも確認済みである。