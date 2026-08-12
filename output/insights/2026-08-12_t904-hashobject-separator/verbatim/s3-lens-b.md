静的検証のみです。必読資料は読了し、pytest は実走していません。`git status` は clean です。

`git grep -n "hash-object"` の production hit は `tools/codex_reasoning_ab.py:1330` と `tools/spool_fold.py:3208` の2箇所だけです。後者は `--stdin` で path 引数を取らず、見落としはありません。

## 所見

1. **MAJOR — production 到達性と受理集合の説明が誤っている**

   根拠は [`codex_reasoning_ab.py:54`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:54)、[`codex_reasoning_ab.py:675`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:675)、[`codex_reasoning_ab.py:1448`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1448)です。production の `untracked` は常に `output/.../<name>` で、name が `-answer` でも argv token は `output/.../-answer` になります。実際の root `-answer` は [`codex_reasoning_ab.py:1483`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1483) の allowlist 不一致で拒否されます。

   提案テストは [`s2-plan.md:53`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:53) で private helper に `("-answer",)` を直接渡しており、production の status／allowlist 経路を通りません。`--` 修正自体は裁定どおり維持すべきですが、brief の「将来 artifact 名で到達する」という説明か、テストの到達範囲を修正すべきです。

   **成果物影響:** 放置すると certified 選択・レポート・台帳の現行受理集合は変わらず、private helper の緑だけで production acceptance の拡大を証明したことになります。

2. **MAJOR — report／replay consumer の列挙漏れ**

   [`s2-plan.md:94`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:94) は CLI を `main:5394,5399,5430` までしか列挙していません。実際には [`codex_reasoning_ab.py:5446`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:5446) の `aggregate` と [`codex_reasoning_ab.py:5451`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:5451) の `verify` が [`codex_reasoning_ab.py:4889`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:4889) → [`codex_reasoning_ab.py:4723`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:4723) を通ります。対応するテストも [`test_codex_reasoning_ab.py:2459`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:2459) にあります。

   **成果物影響:** 新テストが通っても aggregate／verify の replay で `valid`、`RC_AGGREGATE`、failure reference が変わる回帰を受入で見逃し、レポート・台帳の受理結果が未検証になります。

3. **MAJOR — mutation の正式な帰属登録が未記載**

   [`s2-plan.md:128`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:128) は `--` 削除変異の実行だけを述べ、期待 node、anchor、mutation ID、単一理由性を登録していません。`DW-M01` は [`mutation.md:5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/docs/dev-wave/mutation.md:5) で事前登録を要求しています。

   ただし、提案骨格の private-helper 直呼びでは帰属自体は成立します。`path.is_file()` は [`codex_reasoning_ab.py:1328`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1328) で通り、status／filesystem allowlist はその前に実行されず、`--` 削除時の失敗点は [`codex_reasoning_ab.py:1330`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1330) に絞れます。

   **成果物影響:** 事前登録を欠いたままなら mutation ledger の `KILLED` が期待 node と単一理由で裏付けられず、certified 成果物の受入証拠が不完全になります。

4. **MINOR — fixture が必要以上に重く、無関係な赤の面積が広い**

   提案は [`s2-plan.md:37`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:37) の `_synthetic_nested_submodule_snapshot` を使います。この helper は child／snapshot の複数 `git init`、local `submodule add` clone（[`test_codex_reasoning_ab.py:1325`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1325)）、detach checkout を行い、さらに `_seal` と closure scan を複数 repo に対して実行します。既存の [`test_codex_reasoning_ab.py:1376`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1376) が同じ clean closure を既に検査しています。

   **成果物影響:** certified 値は変わりませんが、受入全走の時間・共有資源競合・submodule 初期化由来の偽赤が増え、時間切れ時にはレポート／台帳が未生成になります。root-only の最小 repo fixture が適切です。

## 総括

- 最大の危険は、production では到達しない `-answer` を private helper 直呼びで検査し、受理拡大を証明したと誤認することです。
- `aggregate`／`verify` の replay consumer と mutation の正式登録が段 2 計画から漏れています。
- nested submodule fixture は検出力に不要なコストと環境依存性を持ちます。