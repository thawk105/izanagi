# 変異事前登録の erratum (T-2135、2026-09-02)

`DW-M02` / `DW-M08` に従い、初回の登録内容を消さず訂正として残す。

## E1: M4 の期待 pair 集合が誤っていた

- **初回登録 (段 4 裁定 §4、2026-09-02 00:28 JST):**
  「M4 = `_cicada_promotion_requires_inline_opt` を逆向き (`OPT ⟹ PROMOTION`) にする。
  KILLED。pair 集合が `{(0,0),(1,1)}` 側へ変わり赤」
- **誤りの内容:** 逆向き制約 `not OPT or PROMOTION` が許す組は `{(0,0),(0,1),(1,1)}` の 3 組であり、
  `{(0,0),(1,1)}` の 2 組ではない。
- **発見者:** 段 6 レビュー A (nit として報告)。
- **親の独立検算 (2026-09-02 01:00 JST):**
  ```
  python3 -c "def rev(o,p): return (not o) or p; ..."
  → 残る組 = [(0,0), (0,1), (1,1)]、有効数 = 24
  ```
- **期待 node への影響:** 有効数が 24 のまま変わらないため、
  `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes` は**落ちない**。
  期待赤 node は `test_cicada_space_requires_inline_opt_for_promotion` の **1 件のみ**である。
- **訂正済み:** 段 4 裁定 §4 の M4 行を訂正した。本走の期待 node 完全集合は訂正後を使う。
- **成果物影響:** なし。訂正前の記述で本走すると期待 node が過大になり、
  MISMATCH と誤判定して変異検査そのものが信用できなくなった。本走前に訂正できた。
