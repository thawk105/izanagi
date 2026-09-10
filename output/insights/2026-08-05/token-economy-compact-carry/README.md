# 次の一手 carry 行の compact 化 (dev-wave token-economy、2026-08-05)

ユーザー依頼「トークンの使用量を品質を落とさずに節約する」に対する 1 wave 分の逐語凍結。

## 何をしたか

fold が生成する持ち越し行を `- [T-NNN] 変わらず ((N) 参照)` (38 bytes) から
`- [T-NNN] (N)` (16 bytes) へ縮めた。全クラス 2/3 セッションが起動時に読む箇所である。

## 実測 (ログインノードの読み取りのみ、追加計測ゼロ)

- `docs/worklog.md` 98,391 bytes のうち exact carry 行が **1,671 行 / 63,498 bytes (64%)**。
- 末尾エントリ 15,168 bytes のうち **237 行 / 9,006 bytes (59%)**。
- archive 累計の exact carry は **21,964 行 / 830,541 bytes**。
- carry 短縮 5,214 bytes − 見出し凡例 +115 bytes = **正味 5,099 bytes/エントリ**
  (末尾エントリの 33%)。
- 繰り越し 245 件のうち **129 件が 50 エントリ以上連続で無変化**、最長 109 連続、今回更新は 8 件。

## ordinal を残した理由 (親 brief の反証)

親は「`((N) 参照)` の N は常に直前エントリで構成上導出可能」と書いたが、段 3 レンズ A が
**exact carry 23,635 行中 1,316 行が `参照先 != エントリ番号 - 1`** を指すことを実測して反証した。
`_global_ordinal_entries` は欠番・単調性を固定しない。よって ID 単独行案 (P1) は却下し、
ordinal を行内に残す (P1′) を採った。

## ファイル

- `brief.md` 段 1、`s2-plan.md` 段 2、`s3-lensA/B.md` 段 3 敵対 2 レンズ
- `s4-ruling.md` 段 4 裁定 (変異事前登録を含む)
- `s5-impl.md` 段 5、`s6-revA/B.md` 段 6 敵対レビュー、`s6-fix.md` / `s6-fix2.md` fix、
  `s6-refocus.md` 焦点再レビュー (GO)
- `mutation-spec.json` / `mutation-ledger.json` 初回 9 変異、
  `mutation-spec-m07b.json` / `mutation-ledger-m07b.json` M07 再照準

## 変異 matrix の読み方 (erratum を含む)

- **SURVIVED は実効変異で 0 件。**
- M06 / M08 / M09 は期待 node と完全一致で KILLED。
- M01〜M05 と M07b は **MISMATCH だが「期待した node はすべて赤」で、加えて更に多くの node も赤**。
  親の期待 node 列挙不足であり、検出力は登録より強い方向である (F87 の再発)。
- **初回 M07 は SURVIVED だったが等価変異だった** — `int(...)` だけを try/except で包んだため、
  正規表現で検証済みの数字列に対して例外が起きず fail-open を注入していない。
  実効 gate (再帰呼び出し) へ再照準した M07b で、期待した 2 node が両方とも赤になった。
  初回結果は `mutation-ledger.json` に保存してある (DW-M02)。
