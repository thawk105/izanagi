指定の 3 ファイルのみ変更し、commit・`git add` は行っていません。`tools/audit_dangling_commits.py`、s8c テスト、`docs/` 配下は無変更です。

## 総括

- 入口の最終サイズ: **3,983 bytes**
- SHA-256: `757d46a3f7f7b4563d5731a931fde73cfd1bbd6364a6af1ee8a2c14279f39c35`
- 3 分岐の最終文言（逐語）:

  > `- python3 tools/audit_dangling_commits.py` rc0削除/1§5報告・救出判断/2実行不能・削除停止

  ※実ファイルではコマンド部分をバッククォートで囲んでいます。

- §2 の削除条件、§3 の F26/F51、§4 の事後検査、§5 の push 引き渡し義務は一切変更していません。
- SHA は `tools/check_docs.py`、テスト側期待値、whole-file fixture の独立 3 箇所へ反映済み。fixture と実ファイルの byte 一致も確認済みです。
- 実走結果:

  - `python3 tools/check_docs.py`: rc=0、違反 0 件
  - `python3 tools/check_codex_agents.py`: rc=0
  - `python3 -m py_compile tools/check_docs.py orchestrator/tests/test_check_docs.py`: 2 ファイル成功
  - `git diff --check`: 問題なし

- 未実走:

  - `orchestrator/tests/test_check_docs.py`: 未実走、件数未確認
  - `orchestrator/tests/test_audit_dangling_commits.py`: 未実走、`8 passed` 維持は未確認

  ホストが Pegasus ログインノード `pegasus02` で、AGENTS.md が単一 nodeid を含む pytest 直走を禁止しているためです。したがって本実装子からは closed と申告しません。