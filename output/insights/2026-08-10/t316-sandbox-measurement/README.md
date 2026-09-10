# [T-316] 計測段 — 計算ノード sandbox backend の実測

`worktree-dev-wave-t316-sandbox-measure` (2026-08-10) の成果物。
上流は `output/insights/2026-08-09_t316-semantic-gate/` の裁定パッケージ R3-1 / R3-2 と、
ユーザー裁定 R2-b (独立 oracle)。

- `package.md` — **判定材料の本体**。実装段への含意、成立/破れた/帰属不能の 3 分類、性能実測、
  未 discharge 項目、実装段が塞がれている理由。
- `mutation-spec.json` / `mutation-ledger-run1.json` — 変異事前登録 v1 と初回台帳
  (KILLED 3 / MISMATCH 4 / **SURVIVED 1**)。生存した M7 は検査側の穴で、erratum として残す。
- `mutation-spec-v2.json` / `mutation-ledger-v2.json` — 期待 node を実測へ訂正した v2 と
  その台帳 (**8/8 KILLED、SURVIVED 0、MISMATCH 0**)。変異の内容は v1 から変えていない。
- `mutation-ledger-v3-final.json` — `DW-M07` に従い、受入の赤を閉じた**最終 commit の tree**で
  同じ spec v2 を本走し直した台帳 (**8/8 KILLED、SURVIVED 0、MISMATCH 0**)。anchor 8 件が
  単一箇所であることを再検証してから走らせた。
- `verbatim/` — 段 1 brief、段 5 実装子、段 6 敵対レビュー 2 本、fix 4 巡、焦点再レビューの
  prompt と出力。

計測 receipt 本体は `output/env/pegasus/t316-sandbox-backend/<計測 ID>/receipt.json`。
計測 ID は `0:900383.nqsv` (bnode085、是正前) と `0:900427.nqsv` (bnode027、是正後)。

**一行で言うと**: 計算ノードで sandbox backend は動き、CCBench の build も走り、
実行時オーバーヘッドは測定上ゼロだったが、**build profile が `std::system` を封じ込めていない**
(2 ノードで独立再現)。この 1 点が候補 profile の NO-GO 要因であり、実装段の設計択一として返す。
