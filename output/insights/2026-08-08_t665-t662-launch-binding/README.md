# [T-665] + [T-662] 起動値の機械束縛 — 設計択一を裁定へ返した (2026-08-08)

wave = `dev-wave-t665-t662-launch-binding` / branch = `worktree-dev-wave-t665-t662-launch-binding` /
起点 main = `3ae4856c`。親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave は **実装差分ゼロの設計 wave** である。land したのは裁定パッケージと逐語だけで、
**起動値を機械照合する層は 1 行も実装していない。**

- したがって「[T-662] / [T-665] が解決した」と書いてはならない。解決したのは
  **択一の整理と、その前提事実の実測**だけである。
- 三案 (launcher 集約 / 事後検査 / 宣言 + 照合) はいずれも **docs 予算 16 bytes に収まらず**、
  **[T-664] の予算捻出が前提条件**である。
- **stage matrix の所有は [T-184]**、**起動前の model×effort 検査は F56(c) / [T-183]・[T-184]**、
  **served model の attest は [T-189]** にある。本 wave はどれも実装していない。

## 成果物

- `package.md` — 裁定パッケージ (R1〜R5 + 不変条件 7 件 + 負例 5 件)。**ユーザーが読む正本。**
- `verbatim/s1-brief.md` — 段 1 brief (provisional 裁定 P1〜P6 を含む)
- `verbatim/s1-measurements.md` — 段 1 実測 A〜J
- `verbatim/s2-plan.md` — 段 2 codex プラン (sol / max / read-only、rc=0、29,250 bytes)
- `verbatim/s3-lensA.md` — 段 3 レンズ A (sol / max、NO-GO / must-fix 7)
- `verbatim/s3-lensB.md` — 段 3 レンズ B (luna / max、NO-GO / must-fix 8)
- `verbatim/s4-adjudication.md` — 段 4 親裁定 (real/refuted、P1〜P6 の最終処置)

## 証拠の状態 (これを隠して引用してはならない)

- **実測はすべて本 wave で取った** (rollout 実読、既存ツール実走、`git blame`、byte 集計)。
  ただし **codex 子は 1 本も実装をしておらず、pytest / checker / launcher の実走もしていない**。
  段 2・段 3 の子は read-only sandbox で静的読解のみである (`DW-O05`)。
- 実装規模の概算 (600〜1,600 LOC) と docs 純増の概算 (350〜1,200 bytes) は**静的見積り**であり、
  実測ではない。段 3 レンズ A は「同じ保証範囲を比較していない」として、
  scope 閉包後の再見積りを must-fix にした。
- **取りこぼし率 46% / 過剰包含 5.4 倍は [T-181] 1 wave 固有の値**である。
  一般化できるのは「primary cwd selector は sibling worktree の全 session を落とす」
  「時刻単独には wave identity がない」という構造的主張までで、率そのものは wave 形状に依存する。
- 段 3 レンズ A は外部 URL (`learn.chatgpt.com`) を根拠に session 中の model 変更を主張したが、
  **親は検証していない**。パッケージの根拠に含めていない。

## 親が裏取りして refuted にした所見 1 件

段 3 レンズ B は「既存決定 D60 が『現用 Codex 相談は launcher を経由しない』と決めている」として
移行境界の明示を must-fix にした。**D60 の「この launcher」は `orchestrator/codex_roles/` の
role runtime launcher** (pinned Codex + bwrap を要求する休眠サブシステム) を指しており、
争点の `tools/codex_worker_launch.py` ではない。**D60 は launcher 集約案の障害にならない。**

## 親自身の実測の訂正 1 件

段 1 で親は「`turn_context` は 1 session あたり 1 件」と書いたが、段 3 レンズ A の指摘を受けて
再測した結果、**109 session 中 14 件 (12.8%) が 2 件持ち**だった (ただし 14 件とも model / effort は
不変)。検査は「最初の 1 件」ではなく**全 `turn_context`** を対象にしなければならない。
