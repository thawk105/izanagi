---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t434-cap-lift-receipt
seq: 1
title: [T-434] cap-lift receipt と consumer 結線の設計 v2 を起草した — 全 24 所見 real で blocked design memo + 設計択一 10 件を裁定パッケージで返す (docs のみ、branch worktree-dev-wave-t434-cap-lift-receipt)
---

## 本文

- **依頼はユーザー command 引数 `/dev-wave [T-434]` (背景 job)。** 裁定 = (175) の
  「設計 wave が cap-lift receipt と consumer 結線の案を起草して返す」。起草のみで、
  段 4 で「実装しない」を裁定し遷移は `4→7→8→9`。**実装差分ゼロのため変異 matrix と
  受入全走は対象外** (射程明記)。軽量版だが設計択一が割れるため省略せず、
  段 2 = codex 起草 1 本、段 3 = codex 敵対 2 本 (いずれも gpt-5.6-sol / max / read-only)。
- **段 3 の 24 所見は refuted 0 件・全件 real。** 親 brief の provisional 前提も 3 件中 3 件が
  無傷で残らなかった — (Q1)「receipt は機械 gate ではない」は撤回 (人間が発効する機械 admission
  gate の policy input と修正)、(Q2)「受理集合を広げない」は基準集合の明記へ書き分け
  (現状 cap=1 比では拡大、裸の定数引上げ比では縮小)、(Q3) T-433 独立は部分撤回
  (起草は独立可、v1 schema 凍結は T-433/V1 裁定依存)。
- 主要な訂正 3 件: (a) 初稿は 8c 事前登録の正本を `docs/phase3-main-experiment.md` と取り違えて
  おり、正本は `docs/phase3-8c-preregistration.md` (69–72 行が多世代化の 3 条件を既記。
  main-experiment + S-1 freeze は no-touch へ)。(b) receipt cap と対象 revision の
  `MAX_APPROVED_GENERATIONS` 定数の一致検査は申請側の自己一致であり証拠から除外 (実効 cap は
  receipt からだけ導出、literal 1 は no-receipt fallback として恒久維持)。(c) 実装 wave は
  D96 に加えて **D114 決定 (1) の「解除はこの定数 1 個と境界テストの同時変更だけ」の逐語を
  明示 supersede** しない限り効力を持たない (D150 決定 (2-b) と同型の遷移契約)。
- 成果物 = `output/insights/2026-08-04_t434-cap-lift-receipt/` (design-v2.md が確定版 +
  裁定パッケージ。設計択一 10 件、推奨付き)。DW-G04 により blocked design memo とし、
  再開条件 (択一裁定・T-433/V1/T-435・P 群の実 artifact) を列挙した。実装 wave は起票しない。
- 運用メモ: 段 3 の並列 codex 起動で 2 本目の `.done`/log が相対 path 書き込みにより
  worktree 直下へ迷子になった (回収済み、tree clean 確認済み)。DW-O01 の wrapper redirect を
  絶対 path で書く改善候補として段 8 で routing した。

## 次の一手差分

### 更新

- [T-434] **P1・起草済み (2026-08-04) → ユーザー裁定待ち (V3)**: 設計 wave が cap-lift receipt
  (小 receipt + witness 分離、exact-pin、receipt からだけの実効 cap 導出、発効 commit topology)
  と consumer 結線 6 面 (事前登録の正本は `docs/phase3-8c-preregistration.md` に訂正) の
  設計 v2 を起草し、**設計択一 10 件を裁定パッケージで返した** =
  `output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md`。blocked design memo であり、
  再開条件 (択一裁定、[T-433]/V1/[T-435]、P 群の実 artifact) が揃うまで実装 wave を起票しない。
  実装時は D96 + D114 決定 (1) 逐語の明示 supersede が必須
  base: cd1ab4ca7de399bf8e22b77ccbb497c4a8823475e27f60c5674d46b7108a44e7
