## 総括

(a) 修正箇所:

- [harness.py:629](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:629): child stdout 境界抽出、`| ` 除去、ANSI 除去。
- [harness.py:669](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:669): 説明なしの `FAILED <node>` にも対応。
- [harness.py:683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:683): pytest 集計行・件数抽出。
- [harness.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:709): 非ゼロ rc・node 0 件と集計不一致の健全性検査。
- [harness.py:788](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:788): `PARSE_FAILURE` 判定。
- [harness.py:822](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:822): 台帳への解析情報記録。
- [harness.py:924](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/.mutation-harness-t247/harness.py:924): stdout への集計・parse failure 理由表示。

(b) parser 自己検査:

- dispatch 前置＋ANSI: node 1件、`failed=1 / passed=2`、件数一致。
- 直接 pytest＋エラー説明なし: node 1件、件数一致。
- rc=1＋node 0件: `PARSE_FAILURE` 理由を検出。
- 集計2件＋node1件: 不一致を検出。
- 一時ファイルによる統合検査: `KILLED / PARSE_FAILURE / DIAGNOSTIC_ONLY` を正しく分離し、3走すべて復元成功。
- 静的 compile: 成功。

(c) 実ログから取得した node:

`orchestrator/tests/test_t126_qualification_contract.py::test_protocol_rejects_each_compensating_timing_cap_drift[900-1199-1]`

集計は `failed=1`、node 数との一致は `true` でした。

(d) 非回帰確認:

- 35 spec 全件で置換一意性と非空 diff をメモリ上で確認。
- 対象ファイルの前後 hash は全件不変。
- 復元処理と semantic/diagnostic 分離を一時ファイルで実行確認。
- 単一走行 guard は変更していません。
- tracked worktree/index は clean。docs・commit・既存ログ・台帳は変更していません。

(e) 未了事項:

Pegasus 実走は権限境界に従い未実施です。親による計算ノード上の `M-C1` 再走と全 harness 受入が残っています。