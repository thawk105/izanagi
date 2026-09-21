---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-r29-items4-9-diagnosis
seq: 2
---

## 再発

### F561

- **再発: 2026-09-21** — 第 29 回 /rulings の索引 項 9 (焦点走から漏れる exact 目録 test の扱い、D2206 項 9 = [T-2843]) は、同じ test file
  (`orchestrator/tests/test_ccbench_spawn_sites.py`) を DW-O26 の inventory 群へ足す既裁定・未実装の [T-2820] (D2194 項 8、同日の第 27 回で裁定) を引かずに、新しい択として提示された。
  しかも項 9 の 1 例目 (T-2737) は D2194 項 8 の理由欄が挙げる entry 1695 そのもので、既裁定の根拠例を別の択として出していた。索引 (`rulings-all-20260921c/final-index.md`) に
  T-2820・D2194・1695 の hit は 0。照合が項目の識別子 (未採番) と見出しの話題語だけで、既裁定が立つ側 (対象 test file 名、根拠 entry 番号) で引いていなかった点が本 F と同型である。
  実害は小さい (ユーザーの裁定は「範囲を限定した調査」で、診断 wave が段 1 で既裁定を見つけ「新しい択は不要」と再提示した、insight `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md` §5)。
  独立 2 例目で、恒久対応の再訪条件 (独立 3 例) には未達。
