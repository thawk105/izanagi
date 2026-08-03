# [T-338] RF 統計設計の裁定パッケージ — dev-wave 2026-08-03

`authority: none` / `default_effect: no-state-change` — 本 dir は凍結記録であり、可変状態の正本
(worklog 末尾) ではない。

**ユーザーが読むべきものは `package.md` である。** 他は一次資料。

## 構成

| ファイル | 中身 |
|---|---|
| `package.md` | **ユーザー裁定パッケージ (本 wave の成果物)。裁定項目 11 件** |
| `brief.md` | 段 1 親 brief (scope・不変条件・provisional 裁定 (P1)〜(P6)・前提実測) |
| `brief-addendum.md` | 段 1 追補 A〜D (段 2 実行中に親が独立実測した 4 件) |
| `s2-plan.md` | 段 2 read-only codex のプラン起草 |
| `s3-lensA.md` | 段 3 敵対レンズ A (統計的妥当性)。12 real / 4 refuted、NO-GO |
| `s3-lensB.md` | 段 3 敵対レンズ B (整合と実効性)。13 real / 5 refuted、NO-GO |
| `s4-adjudication.md` | 段 4 親裁定 (全所見の real/refuted、親の erratum 6 件) |

## 結論 (1 段落)

裁定 (121) は「RF 統計設計のうち paired session 差による floor の取り方を正例より先に裁定する」
だったが、**floor の意味は RF の推定量 (estimand) が決まらないと定まらない**ため、floor 単独の
先行裁定は実行できないことが判明した。段 3 の 2 レンズが独立に NO-GO を返し、5 点の外にある
estimand・最小識別幅・primary endpoint が受理条件を支配することを示した。パッケージは
5 点を **11 件の裁定項目**へ組み替えてユーザーへ返す。

## この wave が動かしていないもの

コード・テスト・gate・artifact・凍結 bytes・certified 選択・材料レポート・proof chain。
docs (本 dir + spool fragment) のみ。**変異 matrix と受入全走は射程外。**
Phase 2 `compare()` Gate1 の √2 保留も動かしていない (両レンズが「別件に保つ判断は正しい」で一致)。

## 実測環境

計測は行っていない (静的読解と既存 artifact の値の照合のみ)。
worktree = `dev-wave-t338-rf-statdesign` (branch `worktree-dev-wave-t338-rf-statdesign`)、
base main = `1a3604b`。子は codex `gpt-5.6-sol` / `reasoning=max` / `sandbox=read-only` を 3 本。
