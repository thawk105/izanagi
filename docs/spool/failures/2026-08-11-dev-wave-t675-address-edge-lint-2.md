---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t675-address-edge-lint
seq: 2
---

## 再発

### F1

- **再発: 2026-08-11** — F173 の恒久対応が「機械化は `docs/dev-wave/**` の byte 予算に阻まれて
  おり、段 8 の改善候補として残す」と書いていたが、**この機械化の実装面は
  `tools/check_docs.py` (Python) にあり `TextLimit` の byte 予算の対象外**である。阻害要因を
  実在確認なしに断定した誤記で、2026-07-28 の追記が顕在化させた「機構の実在状態を転写する」型の
  再発にあたる。本 wave が同じ機械化を production 9 行で実装して反証した。追記のみの台帳のため
  F173 本文の bytes は訂正できない。**正しい判断は {{D:address-edge-structural-lint}} が正本**である。
  検出は段 3 の敵対レンズ 2 本のうち 1 本 (独立に一次資料へ当たった) による。
