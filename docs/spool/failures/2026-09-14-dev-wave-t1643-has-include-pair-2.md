---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1643-has-include-pair
seq: 2
---

## supersede 追記

- F660 **supersede: 2026-09-14** — 本 F の射程は「新しい Pegasus 実行体を要する実測」であり、計算ノードでの実測一般ではない。既登録の `tools/pegasus/dispatch_compute.py --task generic` (main 側 `admission_registry.json` で `class=local-ok`、D895) は任意 argv を計算ノードの job 内で実行するので、probe が `tools/pegasus/` 配下の新規実行体でなければ本 F に当たらず、同じ wave で compute 実測を行える ([T-1643] で rc=0 を実測、request `997000.nqsv`、bnode009)。段 1 で本 F を読んだ親は compute 実測を不可能と判断しかけ、段 3 の敵対相談がこの経路を見つけた。ただし `generic` の job は `env_mode=clean` で cwd を repo root に固定するため、そこでの観測は本番 admission の呼出しと探索環境まで対応づけたものにはならない。
- F212 **supersede: 2026-09-14** — 恒久対応の `--show-diff` 付き dry-run は `status` の機械判定には使えない。before/after hash 行と unified diff が JSON より先に出るため、出力全体が JSON として parse できない ([T-1643] で実測)。再発検知の「dry-run の `status` が `planned` 以外なら受入を投入しない」を機械で確かめるには `--show-diff` なしの走行で JSON を取り、land 前の挿入 bytes 目視には `--show-diff` 付きを併用する (`--dry-run` は書き込まないので 2 回走らせても副作用はない)。
