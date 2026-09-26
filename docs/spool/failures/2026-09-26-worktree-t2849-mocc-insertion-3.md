---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-t2849-mocc-insertion
seq: 3
---

## 新規

### {{F:pin-advance-scope-misread-as-driver-pin}}. 「pin 前進は済み」を driver の campaign pin まで含むと読み、比較 harness の MOCC を旧 pin で走らせかけた [手順漏れ]

- 事象: [T-2849] 単位 8 の依頼・設計 (設計 insight §9.1)・段 1 brief は、gitlink・`pin.CURRENT_PIN`・`CCBENCH_FULL_SHA` の更新をもって「MOCC の差し込みの前提の pin 前進は済み」とした。read-only の Codex 子 5 本 (段 2 plan 1・段 3 相談 2・段 6 レビュー 2) と焦点走 2 回がこれを指摘しないまま通った後、計算ノードの生死確認で job body が driver 起動前に「CCBench P3 S4 campaign pin mismatch」で止めて初めて、評価入口の campaign pin (`p3_s4_loop.PIN`、D1936 項 1 で 511c9538) が別にあると分かった。511c9538 の mocc には X/P 計装が無い。止めたのは既存の job body の照合で、計算の損失は 16 秒 (2 job)。
- 根本原因: pin 前進の決定 (D2150 項 1) は範囲を ①④⑦ に限り、driver の campaign pin を「③ 各新系列の着手時」に委ねていたが、設計・brief は「pin 前進」を 1 つの事象として扱い、差し込む driver の campaign pin を棚卸ししなかった。
- 恒久対応: {{D:mocc-slot-campaign-pin-c}} (MOCC の slot の campaign pin を C の literal にし、`campaign_pin_for_protocol` の試験と変異 M11・M12 で固定)。検出は job body の fail-closed な campaign pin 照合 (`tools/pegasus/p3_s4_loop_pegasus.sh` の `refuse "CCBench P3 S4 campaign pin mismatch"`)。
- 再発検知: pin 前進後に新しい系列・driver を始めるとき、その driver が参照する campaign pin 定数 (`PIN` など) を grep で列挙し、D2150 項 1 の ①④⑦ の外にあるものを brief に書く。
