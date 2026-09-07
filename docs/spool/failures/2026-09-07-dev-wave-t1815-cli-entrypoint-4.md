---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t1815-cli-entrypoint
seq: 4
---

## supersede 追記

- F631 **supersede: 2026-09-07** — 恒久対応が独立入口として名指しした `-m` 形式は、判定器では同じ二重実体化を起こす (`runpy` が対象コードを `__main__` の namespace で実行するため)。gate report の `-m` が正しい内訳を返すのは、そこで core が通常の canonical import になるからであって `-m` 形式が安全だからではない。CLI を実プロセスとして起動する再発検知は `orchestrator/tests/test_s8c_cli_entrypoints.py` として実装済みで、判定器と gate report をファイルパスと `-m` の両形で起動し、同じ commit の library 判定と突き合わせる。
