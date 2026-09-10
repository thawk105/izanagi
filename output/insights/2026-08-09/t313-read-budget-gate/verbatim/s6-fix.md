実装は完了しました。編集は指定された2ファイルだけで、docs・stage・commit・stash・branch操作は行っていません。pytest は実行基盤障害により未実走です。

## 根本原因の分類

| 原因 | 影響 node 数 | 修正箇所 | 状態 |
|---|---:|---|---|
| synthetic 条件 dispatch header が実契約と不一致。逐語 pin もなくデータ行化 | 187 | [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:487)、[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3340)、[test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:510) | partial：実装済み・pytest未実走 |
| `_grow_test_section()` が次の H2 の行頭へ payload を挿入し、H2を前行へ連結 | 4 | [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2351) | partial：実装済み・pytest未実走 |

完全な親ログを再分類した結果、191件は上記の187+4件です。

- cleanup SHA、model finding、warning、共有 edge、provenance family の赤はヘッダ finding の連鎖でした。
- 独立した4件は層予算3 nodeと `test_dev_wave_l2_accepts_dw_o20_plus_154_bytes` で、すべて growth helper の同一不具合でした。
- `PROVENANCE_REFERENCE_LIMITS` および provenance production 経路は変更していません。
- 既存テストの期待値、skip、xfail、受理・拒否方向は変更していません。

条件表 header は `| # | 発火条件 | 読む節 |` のexact 1件かつ先頭表行に限定しました。不一致行はデータとして解析せず、専用のheader構造 findingだけを出します。専用回帰テストとF42 meta-test登録も追加しています。

受理集合はheaderについてのみ狭まりました。重複、空白差、別表記、先頭表行でない配置を新たに拒否します。growth helper修正はfixture構成のみで、productionの受理集合を動かしません。

実走済み:

- `python3 -B tools/check_docs.py` — rc=0、違反なし
- `python3 tools/check_codex_agents.py` — rc=0
- `git diff --check` — rc=0
- 両編集ファイルのAST parse — rc=0

未実走:

- `orchestrator/tests/test_check_docs.py` 全node
- 新規header専用nodeとF42 meta-test
- 層予算3 node、共有edge、DW-O20正例、provenance consumer群

runnerは強制dispatch 2回、通常判定1回のすべてで、テスト開始前に `qstat -Q preflight rc=1`、rc=16となりました。pytestの緑は主張しません。

波及可能性は、productionでは `_dispatch_tables()` → `_check_command_docs_guard()` → `main()` とCI、テストでは `_build_min_repo()` を使う全synthetic consumer、growth helperを使う層予算3 nodeとDW-O20正例です。親所有のdocs差分には触れていません。

## 総括

- 全191赤を、header fixture連鎖187件とgrowth helper 4件へ分類。
- 条件headerをexact pinし、不一致を専用findingへ分離。
- synthetic headerを実repoと同一表記へ修正。
- H2を破壊しない位置へgrowth payloadを挿入。
- provenance familyの受理集合は不変。
- standalone checker・agent検査・AST・差分衛生は緑。
- pytest全体はrunner rc=16のため実装済み・未実走。