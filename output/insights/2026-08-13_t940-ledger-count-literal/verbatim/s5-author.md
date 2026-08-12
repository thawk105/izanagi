## 総括

段 4 裁定 D1〜D5 を指定どおり実装しました。実装済み・未実走です。commit は作成していません。

変更ファイル: [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1328)

- 1328:
  `def test_known_violation_ledger_is_exactly_thirty_eight_literal_entries():`
  → `def test_known_violation_ledger_matches_literal_entries():`
- 旧 1448:
  `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38`
  を代替なしで削除。
- 旧 1450／現 1449:
  `assert len({row[0] for row in expected}) == 38`
  → `assert len({row[0] for row in expected}) == len(expected)`
- 旧 1914／現 1913:
  `assert len(registry) == 38`
  → `assert len(registry) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)`

`git diff --stat`:

```text
 orchestrator/tests/test_check_ai_provenance.py | 7 +++----
 1 file changed, 3 insertions(+), 4 deletions(-)
```

`tools/check_ai_provenance.py` と `docs/` の diff/stat はともに空で、変更数は 0 です。`git diff --check` も成功しました。

静的検査:

- `python3 -m py_compile ...`: rc=0
- `python3 -m ast ...`: rc=0
- AST 点検: 新 node 1 件、旧 node 0 件、ローカル定数 12 個、`expected` 38 literal 要素、starred 要素 0 件。

D5 は `git diff --unified=0` で変更が指定 4 箇所だけであることを確認し、AST の source segment でも以下を逐語確認しました。

- `assert observed == expected`
- `observed` の `for spec in provenance.KNOWN_PROVENANCE_VIOLATIONS`
- 12 個のローカル定数と 38 行の `expected`
- 両 finding-kind assert
- `assert tuple(registry.values()) == provenance.KNOWN_PROVENANCE_VIOLATIONS`

受理・拒否挙動:

- 変更前: production と literal 表へ承認済み entry を同時追加しても、2 個の `== 38` が拒否。
- 変更後: 承認済み entry の件数変更は、production と literal 表の内容が完全一致すれば件数 literal では拒否しない。
- 未承認追加、削除、順序変更、commit/kind/ruling/note/value の変更は、引き続き `observed == expected` が拒否。
- `expected` 内の重複 SHA は動的な一意性 assert が拒否。
- registry と production 台帳の件数・値 tuple 一致要求も維持。

したがって、指示された「承認済み entry の件数変化」以外へ受理集合を広げていません。

波及点検:

- production caller は `_known_violation_registry()` と `_audit_history()`。いずれも未変更。
- 改名したテストには引数・decorator・共有 fixture がなく、fixture 波及なし。
- 同ファイルの registry、malformed finding、real-commit 関連 consumer test は共有 production API を使いますが、旧 node 名を参照していません。
- Python 上の台帳 consumer は対象テストファイルと production checker の 2 ファイルだけでした。

改名の自己点検:

- 編集前の `git grep -l` で旧 node 名の tracked 参照は対象テストファイルだけ。
- 編集後は旧名 0 件、新名は対象ファイル 1 件だけで、衝突なし。
- `tools/check_docs.py` に node 一覧・名称 pin なし。
- `orchestrator/tests/test_hooks.py` に当該 node の skip/deselect/hold pin なし。
- `pytest.ini` は `testpaths` と `norecursedirs` のみで、`addopts`、skip、deselect、node 一覧なし。
- 現行 Python/config を対象とした ledger node 名検索でも対象ファイルだけでした。docs/output の歴史成果物は編集していません。

pytest は指示どおり未実行です。実走した nodeid はなく、通過結果は申告しません。