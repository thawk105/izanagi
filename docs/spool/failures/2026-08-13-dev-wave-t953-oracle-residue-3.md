---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t953-oracle-residue
seq: 3
---

## 新規

### {{F:brief-search-truncated}}. 段 1 brief の「存在しない」実測を head で切った検索から書いた [誤前提]

- 事象: 親が段 1 brief に「finding の `observations` を生成する箇所は 0 件」と書いた。実際は
  producer に 3 箇所ある。この誤った前提の上に消費側 schema の設計を組み立てていた。
- 根本原因: 完全性を要する検索を `grep -rn observations ... | head -20` で切っており、
  campaign 側の hit が truncate されて表示に出ていなかった。**「無い」ことの実測は全件を見ないと
  成立しない**が、親は truncate された出力を根拠にした。
- 検出経路: 段 3 の敵対レンズ 2 本が独立に同じ誤りを指摘した (レンズ A と B が別の攻撃面から
  到達)。親はその後に自分で測り直して是正し、schema を実 producer の emit 形から作り直した。
  実害には至っていない (near miss)。
- 恒久対応: memory `complete-search-not-truncated-for-absence` (「無い」の実測は全件検索でだけ
  成立し、`head` 等で切った出力を根拠にしない)。**`DW-S01` への統合は予算で入らなかった** —
  本文を 1 文足すと `docs/dev-wave/**` の L1 unique footprint が 10,731 bytes となり
  予算 10,625 bytes を超えて `check_docs.py` が赤になる (実測)。予算引き上げは自己改善の範囲外
  なので入口・reference は変更せず、機構は memory に置いた。
- 再発検知: 段 3 の敵対レンズが「親自身の実測値とその一般化」を攻撃対象に含める既存契約
  (`DW-S03`) が検出経路として実際に働いた。この経路を弱めない。
