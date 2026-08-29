---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t1905-b10-shape-prereg-v2
seq: 1
---

## 再発

### F182

- **再発: 2026-08-29** — [T-1905] wave で親が事前登録 §5 の機械可読 spec を v4 へ書き直す際、
  末尾の `external_floor_reference_widths` を原文を読まずに再構成し、登録済みの
  `terminology` と `reference_width_pct` (write-heavy 1.9、balanced 3.0、read-heavy 0.62) を
  落として top-level に `power_guarantee` を新設していた。F182 と同型 (対象の現本文を読まず
  自 wave の関心事だけで再構成し、内容を狭める変更が機械検出されない) であり、producer は
  worklog fragment でなく事前登録 spec、consumer は fold でなく driver の parser である。
  段 5 実装子は誤った文書に忠実に追随したため、driver と test も同時に狭まっていた。
  **新版だけを検証する検査 (JSON 妥当性・block 15 点・残差 12 cell・上限判定) は全項目緑で通過した。**
  捕捉したのは新旧 spec の構造比較 (旧版を `git show HEAD~1:<path>` で取り出し、
  key の追加・削除・値の変化を再帰列挙する使い捨て script) だけである。
  恒久対応として、機械可読 spec を書き直す wave では新版の自己検証に加えて
  **旧版との構造 diff を意図した変更 (この wave では schema 版・grid・族・残差表・新設 field) の
  閉集合と突き合わせる**手順を段 7 の記録前に置く。実体は
  `output/insights/2026-08-29_t1905-b10-prereg-v2/README.md` の「親の誤りと訂正」節と、
  同 wave の commit `c0a2689da` (訂正) である。
  再発検知は、意図した変更の閉集合を裁定に書いてから diff と突き合わせること。
