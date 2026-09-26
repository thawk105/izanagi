## 所見

1. **must-fix — 計測の collection 一致条件は、今回の差分と両立しない。** 新規 test は [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1128) で B にだけ増える。一方、[集計器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:367) は全走の collection 一致を要求し、[同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:428) でも対を無効にする。**影響:** 正常な A/B 系列でも land 判定に到達できない。**最小是正:** 段 4 の事前登録を訂正し、追加した当該 node だけを差分として明示した比較にする。各走内部の全件照合は維持する。

2. **should — probe に前回からの不要な集計残骸がある。** [集計器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:6) の `Decimal`、同ファイル 20 行の `ESTIMATE_NOTE`、92・154 行の `all_rows` は使われない。**影響:** 台帳用集計が残ったように見え、レビュー対象を増やす。**最小是正:** これらを削除する。台帳 hash・予測負荷・shard 移動・旧 L 候補の判定は除去済み。

3. **nit — 新規 test の mtime 照合は一部重複する。** [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1187) で各 destination と写しの mtime を照合すれば M4 を kill できる。続く direct との照合は同じ経路を再検査する。**影響:** 小さいが不要な assert と stat が増える。**最小是正:** direct との mtime 照合だけ削る。

## 総括

**修正後 GO。** 実装の digest は段 4 裁定が指定した source root 別の写しに必要で、仮想リスク向けの追加 gate とは判断しない。新規 test の集合・bytes・呼出し回数・mtime、および実 builder の呼出し観測は M1〜M5 の kill に必要なので残す。新規 test は小さい一時 Git repo を使い、実 repo の走査を増やさない。既存 test の追加 assert も実 builder の呼出し回数を増やさない。最大の未解決点は計測条件と新規 test の矛盾であり、実測前に裁定の訂正が要る。