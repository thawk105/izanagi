# [T-316] 実装段 — coder hole の有限 lexical 効果 gate と auditor deny-only 化

`worktree-dev-wave-t316-semantic-gate-impl` (2026-08-11) の成果物。
上流は `output/insights/2026-08-09_t316-semantic-gate/` の裁定パッケージ (R1〜R5)、
`output/insights/2026-08-10_t316-sandbox-measurement/` の計測段判定材料、
およびユーザー裁定 **案 2** (worklog 403、2026-08-11 /rulings)。

- `package.md` — **本体**。実装した範囲、意図的に主張しない範囲、未閉鎖の層、
  ユーザーへ返す裁定 R-1〜R-5。
- `mutation-spec-v1.json` / `mutation-ledger-run1.json` — 変異事前登録 v1 と初回台帳
  (baseline 緑、**SURVIVED 0 / PARSE_ERROR 0**、KILLED 2 / MISMATCH 10)。全変異が赤を出した一方、
  親が静的推定した期待 node が seam・critic・非反射投影への波及を取りこぼしていた。erratum として残す。
- `mutation-spec-v3.json` / `mutation-ledger-v3.json` — 期待 node を実測へ訂正し、M8 を単一理由へ
  再照準した最終 spec と台帳 (**12/12 KILLED、SURVIVED 0、MISMATCH 0**)。
- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装子 2 本、
  段 6 敵対レビュー 2 本・fix 2 巡・焦点再レビューの出力。

**一行で言うと**: 段 1 で実測した 4 種の注入 (`std::system` / `execl` / `std::ofstream` /
`while(true){}`) を hole の単一 seam で拒否できるようにしたが、これは**裁定 案 2 が指定した
build 段防壁ではない** — 案 2 の二択 (source の DSL/IR 化 / build 出力 copy-out の厳格化) の
どちらでもない第 3 の形であり、段 3 の 2 レンズが独立にそう判定した。したがって
**測定済み 4 種に対する受理集合の縮小 (defense-in-depth)** としてのみ主張し、
build 防壁本体の択一は R-1 として裁定へ返す。
