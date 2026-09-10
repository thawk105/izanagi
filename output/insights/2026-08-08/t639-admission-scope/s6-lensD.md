[所見 1] must-fix / 場所: [docs/pegasus-runbook.md:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/docs/pegasus-runbook.md:424)、[hooks/README.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/README.md:78) / 何が起きるか: runbook は「未登録をすべて拒否」とした直後に「非 Pegasus の未登録は素通り」と述べており矛盾する。さらに hooks README は「各 entry point 自身が一次強制」とするが、[claude_session_ledger.py:1061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/claude_session_ledger.py:1061) には site gate がなく、実際には Claude Bash hook だけが強制面である。`tools/README.md` の runbook 委譲自体は妥当だが、委譲先が矛盾しているため規範を確定できない / 検出方法: `_pegasus_admission_entry()` は非 Pegasus 未登録を `None` へ落とし、既存正例も全 site allow を要求する一方、ledger 内には `site_policy` 使用箇所がないことを静的に追跡 / 提案: 「登録済み deny class と Pegasus 配下の未登録を拒否し、非 Pegasus 未登録は許可」と一文で書き直す。hooks README では ledger が hook-only であることと、cwd 相対・変数・未解析 launcher・IDE・cron・subprocess 内部を含む射程外を同期する。  
成果物影響: 誤った fail-closed 保証を前提に未登録の重量 tool がログインノードで実行されると、OOM により検査・provenance・台帳 producer が終了し、受入証拠や台帳参照が欠落する。

[所見 2] nit / 場所: [hooks/guard_bash.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:594)、[hooks/guard_bash.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/hooks/guard_bash.py:1181) / 何が起きるか: canonical registry に登録済みの ledgerも、loader 障害時には fallback から `_PEGASUS_UNREGISTERED` となり「未登録 admission 実行体」と表示される。実際の原因は登録欠落ではなく registry 読込障害であり、一般の未登録非 Pegasus path も拒否されるかのように読める / 検出方法: fallback 分岐から sentinel、診断生成まで追跡し、`_PEGASUS_ADMISSION_DIAGNOSTIC` が拒否理由に使われていないことを確認 / 提案: fallback 専用 sentinel、または「admission registry 障害時の fallback 拒否」という別文言にする。

[所見 3] nit / 場所: [orchestrator/tests/test_hooks.py:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:1557)、[orchestrator/tests/test_hooks.py:1605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:1605) / 何が起きるか: 逐語維持された `outside-path` は、現在では「subtree 外だから」ではなく、fixture が `local-ok` だから拒否される。恒真ではないが、独立した path-schema 検査という既存コメント上の意味は失い、新設した非 Pegasus `local-ok` 拒否テストと同じ条件を検出する / 検出方法: `_SYNTHETIC_VALID_ENTRY` の class と [loader の class guard](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/tools/pegasus_admission_registry.py:105) を照合 / 提案: 指定された case は変更せず、変異台帳では M2 の追加 detector と明記し、subtree 外 path 自体の拒否証拠として数えない。

静的確認では、削除されたテスト行は許可済みの inventory 絞り込みと stale `24` 名・文言だけだった。指定5本は逐語維持され、lookup、wrapper、nested sentinel、sanctioned 導出はいずれも恒真化していない。provenance・pytest の受理経路と現行 `_SANCTIONED_PATHS` に追加の退行は見つからなかった。plan v2 の1〜4は実装され、5は所見1のため部分完了である。

既知の赤の原因は次のとおりで、所見数には含めない。

- 内部例外テストはループ2回目でも `_install_login_site_policy()` を呼び、[非冪等な `mkdir`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_hooks.py:1809) が既存 directory に衝突する。
- check_docs テストの [短い `first_row`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t639-admission-scope/orchestrator/tests/test_check_docs.py:1082) は投影表と unknown 表の双方に現れるため、`count()` は 2 になる。完全な投影行を anchor にすべきである。

## 総括

テストは実行しておらず、緑は主張しない。

- 最重要は、runbook と hooks README が実装より強い fail-closed 範囲を主張している点。
- 既知の fixture 衝突により、内部例外時の module 綴りはまだ実証されていない。
- 既知の曖昧 anchor により、非 Pegasus entry の projection-only テストは最終 clean assertionへ到達しない。