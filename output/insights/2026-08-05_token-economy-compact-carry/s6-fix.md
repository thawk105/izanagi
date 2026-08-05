## 総括

F1〜F4: **closed**。受理集合維持、旧書式回帰、guard 注記、固定凡例を実装しました。  
F5〜F7: **closed**。rotation 2 件と ordinal-gap fixture を修正しました。  
残リスク: pytest 実走は禁止されているため、計算ノードでの親実測が必要です。

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | `carry_re` の終端 `$` のみ除去し、`fullmatch` は維持。複数行負例も保持 |
| F2 | closed | current `(2)` → archive `(3)` の旧書式未来参照テストを追加 |
| F3 | closed | 排他判定が将来の regex 改変用 guard である旨を注記 |
| F4 | closed | 指定凡例を byte-exact 生成。見出しに `[T-...]` token なし |
| F5 | closed | entry `(1)` に filler を追加。凡例の 115-byte 増を吸収するため entry `(2)` は短縮。limit 320・既存 assert は維持 |
| F6 | closed | gap canonical を commit してから fragment を生成 |
| F7 | closed | limit 400、entry `(2)` の filler、分割点を固定する byte 条件を追加 |

変更は [spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py) と [test_spool_fold.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py) のみです。docs、`tools/check_docs.py`、commit には触れていません。

既存 byte-exact golden は、producer の意図的変更である固定凡例と compact carry だけ追随しました。実 corpus の変換件数 `215`、UTF-8 byte equality、active/item 件数は緩めていません。production 閾値や既存 assertion、skip/xfail も変更していません。

静的検査結果:

- `py_compile`: 成功
- `pytest --collect-only`: 366 tests、追加した 2 node を収集
- 見出し consumer: `spool_fold`、`check_docs`、`dev_waves.checker` の 3/3 が指定 suffix を受理
- `git diff --check`: 成功
- pytest 本体: 未実行。緑は主張しません

所有外の波及候補は、`tools/dev_wave_land.py` の実 fold、`tools/check_docs.py` の動的 import/D70、`tools/dev_waves/checker.py` と daemon、`test_dev_wave_land.py` の rotation integration、固定 limit 320 の既存 rotation tests、real-corpus 共有 fixture です。親の計算ノード実測対象です。