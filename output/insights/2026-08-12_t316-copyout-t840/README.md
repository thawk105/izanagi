# [T-316] R-1 (b)+(c) 実装段 と [T-840] の分割

`worktree-dev-wave-t316-copyout-t840` (2026-08-12) の成果物。
上流はユーザー裁定 `rulings-inbox/2026-08-12-coarse-provenance-45rulings.md` 34–35 行、
裁定パッケージ `output/insights/2026-08-09_t316-semantic-gate/` (R3-6)、
実装段 `output/insights/2026-08-11_t316-semantic-gate-impl/` (R-1 / R-2)。

- `package.md` — **本体**。実装した範囲、意図的に主張しない範囲、残余、
  [T-840] を分割した理由、ユーザーへ返す裁定 Q1〜Q5、検査の信頼性。
- `mutation-spec-probe3.json` / `mutation-ledger-probe3.json` — fix 後の probe。
  期待 node の完全集合を実測で再導出した (静的推定では必ずずれるため)。
- `mutation-spec-run.json` / `mutation-ledger-run.json` — 本走の spec と台帳
  (**KILLED 8 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0、9 件すべて期待と一致**、
  baseline `PASSED`)。SURVIVED 1 件は事前に `SURVIVED` 期待で登録した M2 (冗長 gate)。
- `probe_env.json` — 段 1 の環境実測 (POSIX capability、`/proc/self/fd`、
  実在 cache tree 1,674 entry の種別内訳と binary の mode / nlink / 動的依存)。
- `verbatim/` — 段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装子 2 本、
  段 6 敵対レビュー 2 本・fix 3 巡 (2A / 2B / 3)・焦点再レビューの出力。

**一行で言うと**: build 出力の copy-out を「許可した binary 1 本の inode 束縛」へ厳格化し、
coder issuer の集合を機械的に閉じた。しかし **[T-840] が求めた「非認証成果物としての機械隔離」は、
同じ裁定が後回しにした [T-841] の receipt 束縛なしには成立しない** — 下流の `artifact_admission` が
構造的に妥当な campaign を一律 `admitted` で返すためである。この新事実を添えて再裁定へ返す。

**この wave で最も価値があった手続き**は、敵対レビューに「指摘を書くな、実際に試して結果を示せ」と
要求したことと、変異検査を回したことである。前者は AST 閉包の 4 つの回避経路を実データで暴き、
後者は静的レビュー 5 本が原理的に見つけられない 2 件 (並列走行でのみ出るフレークによる帰属汚染、
等価変異の読み違え) を摘出した。
