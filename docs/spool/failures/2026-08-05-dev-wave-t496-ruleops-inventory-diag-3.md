---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t496-ruleops-inventory-diag
seq: 3
---

## 新規

### {{F:first-run-classification-site-undefined}}. 新規スクリプトの初回分類走行の置き場が未定義で、必ずログインノードに落ちる [手順漏れ]

- 事象: 本 wave の S2 probe をログインノードで実行した。runbook §7.0 の手順で測った
  cgroup charged memory のピークは 567 MiB、certified peak = 観測 + 128 MiB = 695 MiB で、
  規範値 512 MiB を超えていた。事後的には計算ノードへ dispatch すべき量だった。
- 根本原因: §7.0 は実行場所を「その 1 回の実行の cgroup charged memory のピーク」で決めると
  定めるが、**その値は一度走らせないと得られない**。未計測の新規スクリプトをどこで
  1 走目に掛けるかの規定がないため、分類のための走行が必ずログインノードに落ちる。
  `tools/pegasus/dispatch_compute.py` の `TASKS` は `tests` と `provenance` の 2 つに閉じており、
  任意 command を計算ノードへ送る経路も無い。
- 恒久対応: 未着手。runbook §7.0 へ「未計測の新規スクリプトの初回走行は、
  上限を明示した計算ノード経路で行う」規定を足すか、`dispatch_compute` に汎用 task を足すかは
  {{D:ruleops-failclosed-threshold-unchanged}} とは独立の裁定であり、
  {{T:first-run-classification-site}} として起票した。
- 再発検知: 本 wave のように certified peak を記録すれば事後に判定できる。事前検知は
  上記の規定が入るまで不可能である (計測しないと分類できないという構造がそのまま残る)。
