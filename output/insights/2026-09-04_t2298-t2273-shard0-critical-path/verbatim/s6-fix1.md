## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| MF-1 | partial（実装済み・未実走） | read scope で競合 SH 成功・競合 EX 失敗、write scope で競合 SH 失敗を検査。共通 scope の mode 転送と両 wrapper の literal mode・yield nesting も AST で固定。 |
| MF-2 | partial（実装済み・未実走） | production `seed()` の atomic helper call-edge と直接書込み禁止を AST で固定。replace 元の temp 実体、命名、同一親、`source != target`、temp fd の fsync を検査。 |
| regressed | なし | AST parse、隔離自己検証、保護対象ハッシュで退行なし。 |

pytest が起動しなかったため、契約に従い `closed` とはしていません。

## 変更一覧

変更ファイルは [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py) の検査部分だけです。

- [実 fixture mode 実測検査 :1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1496)
- [mode 転送・wrapper yield AST 検査 :1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1537)
- 新規 node: [production seed call-edge AST 検査 :1625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1625)
- [atomic metadata 実体検査 :1741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1741)

保護対象は変更前後の関数 byte-slice を SHA-256 で比較しました。

- 実装本体 5 関数: `e11d9a329776431676fd69d83bc06313035f14454cd8f706d6adeae914378011`
- 17 consumer: `20e76fecfc24909a20f4a2e2248a846ffdae408fab605ddaaafb675921566bdd`

両値とも変更前後で一致しています。`git diff --check`、結合文字検査、全ファイル AST parse も通過しました。

## 変異 h / g2 と殺す検査

- h: `test_certified_evidence_fixture_scope_holds_both_modes_through_yield`
  - `"write"` 定数化では read scope 中の競合 SH が失敗するため、mode 識別という単一理由で赤になります。
  - `test_certified_evidence_fixture_scope_yield_is_inside_lock_ast` も `access_mode` の RHS が `Name("access_mode")` でなくなるため独立に殺します。
- g2: 新規 `test_certified_evidence_seed_publishes_metadata_only_through_atomic_helper_ast`
  - helper call が消え、metadata への `write_bytes` 直接書込みが現れるため赤になります。
  - helper 自体を直接検査する atomic node は影響されないため、production call-edge という単一理由です。

一時コピー上の静的変異 probe は `h=killed, g2=killed` でした。作業ツリーの実装は変異していません。

## 実走

`tools/run_tests.py` 経由で変更対象 4 node を実行しようとしましたが、Pegasus dispatch の `qstat -Q` preflight が `rc=1`、子プロセス未起動で全体が `rc=16` となりました。[dispatch receipt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/output/pegasus-dispatch/f1acc9c9701c498ffba4b3bd791bb419/receipt.json)

したがって pytest は未実走です。補助確認として、2 本の AST node と atomic helper nodeを隔離実行し、3/3 通過しました。

## 総括

MF-1、MF-2 とも検査実装は完了しました。実装本体と 17 consumer は不変です。Pegasus 側で pytest が起動できなかったため、最終状態は両件とも partial（実装済み・未実走）です。