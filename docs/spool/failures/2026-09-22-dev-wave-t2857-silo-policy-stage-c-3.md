---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2857-silo-policy-stage-c
seq: 3
---

## 再発

### F139

- **再発: 2026-09-22** — silo-function-policy 軸の診断 driver (`orchestrator/campaign/silo_policy_coverage.py`) を計算ノードで走らせると、実走のたびに実機の前提の欠陥が 1 件ずつ出た。(1) 依存物を一度も build しないまま condition gate を掛け、masstree の `config.h` (build 時生成) が無く owner TU の前処理が失敗、(2) silo の `transaction.cc` が WORKLOADS 4 実行体へ compile されて `compile_commands.json` の行が 4 本あり、owner 行の 1 本前提で停止。いずれも既存 driver (`s3_lock_coverage.py`・`s3_mocc_lock_coverage.py`) は踏まない形で、机上レビュー 2 本も見落とした。4 巡目の fix で「全 case の外部との交点を既存 driver と CCBench に照合した表」を実装子に作らせてから、残る実行時の欠陥が出なくなった。記録 = `output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md` §4。

### F247

- **再発: 2026-09-22** — silo-function-policy 軸の上限出口の prefix unlock 変異を、事前登録どおり `maxwait` (lock 競合で 50 µs 待って retry) で走らせたところ、legacy workload では上限出口にほぼ届かず、変異ありでも certified になった (55 check 中この 1 件だけ偽)。同じ workload で `retry` (待機 0) の probe 走は上限 abort 125,445 回に到達していた。方策を `retry` に替え、同構成の probe 走で prefix を保持したままの上限到達 > 0 を判定に要求して閉じた ({{D:silo-policy-stage-c}} 項 4)。

### F112

- **再発: 2026-09-22** — 段 6 fix 6 巡目の fix 子が、同じ wave の fix 1 巡目で新設した test の期待 2 点 (build 数・両出口で同じ patch) を「既存テストの期待値」と読んで追随せずに残し、追随だけの fix 1 巡 (6b) を足した。prompt は「本 wave 以前からある entry・期待値を変えない」と書いていたが、同じ prompt の太字の「既存テストの期待値を変更しない」が優先された。
