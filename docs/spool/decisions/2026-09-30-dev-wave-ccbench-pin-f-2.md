---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-ccbench-pin-f
seq: 2
---

## {{D:ccbench-pin-f-advance}}. CCBench の pin を C から F へ進め、F で厳密適用が外れる壊し patch 4 本は作り直さず、C に独立束縛の系列と生成器対照の本走は C のまま残す

**決定 (親の実施判断。ユーザーの再裁定ではない):** D2277 項 1・D2293・D2322 項 6 に従い、gitlink `external/ccbench`・`s8b_approved.CCBENCH_FULL_SHA`・`pin.CURRENT_PIN` を同一 commit で C `68106660686232781bca3be792a750d3e19d7a8a` から F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` (7 桁 `25898d0`) へ進めた。手順と追随の範囲は D2150 / D2184 と直近の同型前進 (D2227 項 1) と同じで、現行 pin を独立 literal で主張する test・実 checkout を照合する test と probe・admission policy epoch に束縛された golden だけを F へ追随し、C epoch の値は歴史 golden として保持した。次の 3 点を併せて決めた。

1. **F で `git apply` (fuzz なし) が外れる patch 4 本 (`broken-mocc-early-unlock`・`broken-mocc-hot-update-unlock`・`broken-silo-corrupt-write-payload`・`broken-silo-published-version-mismatch`) は、この前進では作り直さない。** 4 本とも壊し (positive control) で、MOCC の 2 本の consumer は e9e477ca に独立束縛の driver と test、Silo の 2 本は condition gate の静的登録と一回限りの変異走だけで、現行 pin に自動で当てる経路が無い (段 6 レビュー 2 本も同じ結論)。作り直すなら、F の上で壊れ方が発火することを実走で示すまでを 1 単位とする。
2. **C に独立束縛の literal は据え置く。** MOCC の関数方策の campaign pin (`p3_s4_loop.campaign_pin_for_protocol("mocc")` と MOCC の較正の注記)、VHash の Cicada 系列の `PIN` (`vhash_cicada_hot_block`・`vhash_cicada_vlife`)、MOCC 候補の proof の `C`、test の fake `ccbench_head`。いずれも C で測った・登録した系列を束縛しており、現行 pin との一致を主張しない。
3. **生成器対照の本走 (D2305 項 1、pin C 固定) は影響を受けない。** 本走の submit checkout 16 本は固定 commit の detached worktree で submodule の格納域も worktree ごとに別であり、main の gitlink 変更は届かない。ただし Silo の方策 driver は `pin.CURRENT_PIN` を読むので、新しい main から submit checkout を作り直すと pin は F になる。本走は固定 checkout のまま完走させる。

**理由:**
- 前提は実測で確かめた: GitHub (HTTPS) の fresh clone で F を取得でき (C は祖先、C..F は 4 commit・4 file で CMake に触れない)、F の check-runs は build・format-check とも success。
- 4 本の壊し patch は、現行 pin の成果物 (certified 選択・レポート・台帳) の値・受理集合・参照を変えない。作り直しを前進に抱き合わせると、壊れ方の発火の実走まで前進の land が延び、F の上に積む修理 (Silo・MOCC)・正しさ関門の記録の前提を遅らせる。
- 規律 7: C で測った系列と登録を、現行コードとの差だけを理由に張り替えない。

**却下した選択肢:**
- 4 本を今 F に合わせて文脈だけ書き換える — 壊れ方が F で発火するかを確かめないまま「壊し」と名乗る patch を増やすことになる。
- MOCC 方策・VHash の C 束縛を `pin.CURRENT_PIN` へ寄せる — 登録済み系列の pin が黙って F に変わる。
