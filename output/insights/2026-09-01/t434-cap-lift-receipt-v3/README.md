# 2026-09-01 [T-434] cap-lift 受領証と consumer 結線 — 実装不可の確定と裁定パッケージ

wave: `dev-wave-t434-cap-lift-receipt` (branch `worktree-dev-wave-t434-cap-lift-receipt`)
基準: main `265aa16e3` (着手時 `08a17b3b3` から ff 取り込み)
実装面の差分: **ゼロ**。機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変。

## 何を確定したか

D841 (択 (a)) に従って受領証と consumer 結線を単一変更単位で実装しようとしたが、
**本 wave では実装しないと裁定した**。独立に成立する 3 本の理由と、実装時に必要な閉包・
設計の穴・再利用方針を確定し、3 択の裁定パッケージをユーザーへ返す。

D841 とは矛盾しない。D841 が定めたのは実装するときの不可分性であって実装時期ではない。

## 読む順

| file | 中身 |
|---|---|
| `design-v3.md` | **正本**。失効した前提、実装不可の 3 根拠、consumer 閉包、設計の穴 5 件、再利用方針、裁定パッケージ |
| `s4-adjudication.md` | 段 4 裁定 (所見の real / refuted、scope から外したもの) |
| `s1-brief.md` | 段 1 brief (親の provisional 裁定 P1〜P4 を含む。P3・P4 は段 3 で反証された) |
| `parent-measurements.md` | 親の実測メモ。**M3 / M4 / M6 に誤りがあり、冒頭に訂正を付した** |
| `s2-plan.md` | 段 2 プラン起草 (codex, read-only, xhigh) の逐語 |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 正しさ境界と受理集合 (must-fix 7 件) の逐語 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 整合と実効性 (must-fix 7 件) の逐語 |

## 先行する設計

`output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md` (2026-08-04)。
骨格は維持するが、前提のうち 4 件が失効している。差分は `design-v3.md` §1。
