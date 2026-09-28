---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: worktree-dev-wave-vhash-cicada-version-measure
seq: 2
---

## 再発

### F139

- **再発: 2026-09-29** — [T-2875] の Cicada 診断 driver (`orchestrator/campaign/vhash_cicada_vlife.py`) を計算ノードで走らせると、実機の前提の欠陥が 1 回に 1 件ずつ出た。(1) smoke1 (33792.nqsv): Cicada の `transaction.cc` も WORKLOADS 4 実行体へ compile されるので `compile_commands.json` の行が 4 本あり、1 本前提の行選択で停止 (2026-09-22 の再発 (2) と同じ形)。(2) smoke2 (33926.nqsv): condition gate の meaning 検査は owner TU (`transaction.cc`) の前処理だけで分岐の目印を数えるので、別 TU (`util.cc`・`ycsb_cicada.cc`) に置いた計器分岐と `#if SINGLE_EXEC` (既定 0) の内側の分岐を観測できず、宣言 44 に対し観測 38 で拒否。login の在庫 test (宣言件数と patch の `#if` 件数の一致) は緑のままだった。机上の plan・相談・レビュー 4 本はどちらも挙げなかった。2026-09-22 の再発で効いた「全 case の外部との交点を既存 driver と CCBench に照合した表を実装子に作らせる」を段 5 の prompt に入れていなかった。分岐を owner TU と、それが include する header だけに集めて smoke3 以降は通った。記録 = `output/insights/2026-09-29/vhash-cicada-version-measure/README.md` §5・§9、裁定 = 同 `verbatim/s6-fix3-ruling.md`・`s6-fix4-ruling.md`。
