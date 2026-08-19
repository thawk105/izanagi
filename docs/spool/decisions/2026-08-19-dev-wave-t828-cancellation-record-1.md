---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t828-cancellation-record
seq: 1
---

## {{D:record-name-uniqueness-defense}}. exact-match schema 抽出器は record 名の短縮 anchor 一意性を、詳細な table_prefix 検索より前に検査する

**決定:** 設計 doc の一節から「marker + header + 行」を string search で抽出する contract
validator (`calibration_freeze_authority_contract.py` の `_extract_design_revocation_schema` /
`_extract_design_cancellation_schema` 等) は、詳細な table_prefix (marker 全文 + header) の
一意性検査だけでなく、その**手前**で record 名 (bold 短縮 anchor、例 `**上位取消 record C**`)
単体の section 内出現回数を、NFKC 正規化した文字列に対して検査し、ちょうど 1 件でなければ
拒否する。

**理由:**
- table_prefix 検索は「本物の marker の一部 (改行→空白、ASCII→全角等) を軽微に破壊しつつ、
  canonical な marker + header + 全行を別の場所へ挿入する」decoy に対して脆弱である。本物が
  table_prefix に一致しなくなり decoy だけが一致するため、relaxed な本物の内容を見過ごした
  まま受理してしまう ({{F:record-name-decoy-slips-past-table-prefix-check}})。
- record 名の一意性を先に検査すれば、decoy が record 名を含まない限り「それらしい」table
  decoy として機能せず、record 名を含めば本物と衝突して拒否できる。
- NFKC 正規化は全角/半角のような「畳み込み可能」な homoglyph だけを閉じる。それでも
  byte-exact 一致だけの検査より防御範囲が広く、実装コストも 1 関数呼び出しの追加に留まる。

**却下した選択肢:**
- table_prefix 検索の対象文字列を単純に拡張する — 「本物のどこかを破壊し decoy で補う」という
  攻撃の型そのものは閉じず、対症療法にしかならない。
- Cyrillic/Greek 等の視覚的 homoglyph まで含めた Unicode confusables (TR39 相当) の全体
  ホワイトリスト化 — CFAB-R4 gate を resolved にするという本 wave の scope に対して
  不釣り合いに大きい変更であり、DW-G03 の一般化ライセンス (同型欠陥の独立 2 件再現) の
  射程を超える。既知の残存限界として {{F:record-name-decoy-slips-past-table-prefix-check}}
  へ記録し、追加対応は再訪条件が生じたときに起票する。
