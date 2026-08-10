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
  再発にあたる。本 wave が同じ機械化を production 9 行で実装して反証した。
  検出は段 3 の敵対レビュー 2 本のうち 1 本が独立に一次資料へ当たったことによる。
  古くなった記述そのものは F173 の supersede 追記で明示する。

## supersede 追記

- F173 **supersede: 2026-08-11** — 恒久対応の「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」は誤り。実装面は `tools/check_docs.py` にあり byte 予算の対象外で、住所 (address edge) の構造 lint として実装済み ({{D:address-edge-structural-lint}})。ただし塞いだのは cleanup-branches command の F26 edge 1 件だけで、pin が bytes しか守らない構造そのものは変わらない。
