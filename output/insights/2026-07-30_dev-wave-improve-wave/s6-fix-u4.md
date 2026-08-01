変更は所有2ファイルだけです。

- [guard_bash.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u4/hooks/guard_bash.py:196)
  - `env -S`、`--split-string=...`、分離形を再tokenize。
  - 不正quote、payload欠落、GNU固有escape、過深ネストをheavy候補としてloginでfail-closed。
  - 既存protected-path解析は従来経路を維持。
- [test_hooks.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u4/orchestrator/tests/test_hooks.py:324)
  - login拒否、compute/OTHER許可、runner・submitter・qsub・configure許可を追加。
  - wrapper・compound・shell-cの正負ケースと、不正payloadを実`decide()`・site observer経由で検査。

所見は実装上closed、実走確認はpartialです。Python 3.10 AST解析、isolated import、`git diff --check`は成功しました。

未実走:

- pytest、build、qsub、live PBS
- `check_codex_agents.py`、`check_docs.py`
- compute nodeでのtargeted/full検査

残riskは、GNU `env -S`文法全体を完全再現するものではない点です。shlexと意味が異なる既知escapeはloginで安全側へ拒否しますが、変数・alias・encoded commandなど元来の保証外surfaceは残ります。commit・push・他owner file編集は行っていません。

## 総括

F6のdirect-heavy bypassはcurrent bytesで閉鎖しました。greenは主張せず、compute nodeでの実走と統合後re-reviewが残っています。
