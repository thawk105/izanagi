---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2686-recovery-codex
seq: 1
---

## 再発

### F43

- **再発: 2026-09-18** — T-2686回収authorはCLI0でも必須総括見出しを落としてf43_fragment/launcher1になった。実装残差を保全し、DW-O01どおり独立review2本で実コードを監査した。未受理を成功報告へ書き換えず、後続promptでliteral見出しを明示した。

### F992

- **再発: 2026-09-18** — T-2686のwalk観測wrapperがオプション名 --name-only だけで対象を選び、git diffを履歴logへ混入させた。test_check_branch_landed.pyの7 selectorをlogとオプションの積へ限定し、期待0/1とassertを維持して373件の焦点走を通した。さらに一回限りの対測定driverではtruncatedという状態語だけで実行失敗と読み、仕様上の非決定的patch-id merge省略を誤拒否した。producerのexactな経路と実raw4正例/timeout等の負例で区別し、元の不完全表示とrun1のrc1を保持した。成果物は output/insights/2026-09-18/t2686-exact-state-union-walk/。
