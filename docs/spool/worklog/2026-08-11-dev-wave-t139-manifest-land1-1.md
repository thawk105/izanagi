---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-manifest-land1
seq: 1
title: 承認候補 3 点を承認可能水準へ直し、R1 裁定時に未見だった 7 事実を裁定へ返した ([T-139] 第 2 波) — land 1 は実行せず、core の較正義務が 2 箇所ある事実で草案 erratum が承認不能と判明 (docs のみ、branch worktree-dev-wave-t139-manifest-land1)
---

## 本文

- **R1 (a) の land 1 (文書承認 fold) を実行しようとして停止した。** 承認対象の内容が、
  R1 の裁定時点で未見だった事実で承認不能になっていた。`DW-S04` に従い親は不採用にせず、
  承認候補を直したうえで新事実付きの再裁定へ返した。裁定 7 問 = 同 branch の
  `output/insights/2026-08-11_t139-manifest-land1/package.md` §S1〜§S7。
- **最も重い新事実は「凍結 core が較正義務を 2 箇所に持つ」。** `較正` を含む行は
  221 行 (§7) と **333 行 (§14 の `a12` 行、LF 込み `a7852ad9…9952`)** のちょうど 2 件で、
  第 1 波が起草した 1 operation の erratum では置換後 core が「§7 = stress check、
  §14 = 較正」の二重状態になる。したがって草案 erratum (`9eb96f88…885c`) と
  合成 digest `dfb821a5…678c` は**承認可能でない**。2 operation 版の合成は
  `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c` (適用順不変、
  置換後 core に `較正` 0 件)。
- **草案には裁定外の受理拡大があった。** `pre_performance_infra_failure` を marker 不在だけで
  成立させており、追補 A `a04` が「開始後の失敗・置換しない」と定める attempt (性能 raw を持つ /
  `a03` 不成立) を予備置換可能にしていた。v2 で `a04` 準拠へ縮小した。
- **受領証 schema の dialect は実測で決まった。** この環境の `jsonschema` は 3.2.0 で
  `Draft202012Validator` を持たず、repo の既存受領証 schema も draft-07 + `definitions` 形式である。
  段 2 が置いた「2020-12 前提」は環境実測で否定された。
- **段 2・段 3 はいずれも NO-GO。** 段 3 のレンズ 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`) は
  blocker 11 件 / 8 件を返し、親は refuted 2 件 (再発行版の暗黙参照という一般論、
  「1 wave に必ず収まらない」の証明)、残りを real と裁定した。親の (P2)・(P3)・(P6) は撤回した。
- **`a13` の予約と R1 の同一 land が因果循環する** (予約は pilot の前、受領証は pilot の後に
  canonical main へ入る必要があるが land は 1 度だけ ff/fold する)。親の推奨は
  予約 entry を land 1 の fold へ同梱する案で、これも裁定へ返した。
- **pilot は投入していない。** 投入 API は 1 つも実装されておらず D264 の非 export が機械固定している。
  land 2 の層 (manifest / resolver / writer / 台帳 / submit / driver / collector / consumer) は
  1 つも実装していない。見積りは production 7,600 行 + test 7,820 行、PBS 9〜11 割当て。
- 変異 matrix は免除した (diff に実行可能コード・テスト・gate が 1 行も無く、kill を観測する面が無い)。
  代わりに敵対レビュー 2 本を凍結対象の文書と schema へ当て、要件文書と schema の key 集合の
  exact 1:1 を親が機械照合した。

## 次の一手差分

### 更新

- [T-139] **P1・第 2 波は承認候補を直して裁定へ返した (2026-08-11) → land 1 は S1〜S5 の裁定後に
  実行可**: 承認候補 3 点 (`record-items-v2.md` / `erratum-core-s7-stresscheck-v2.md` /
  `receipt-schema-v1.json`) を branch `worktree-dev-wave-t139-manifest-land1` に置いた
  (local main から分岐、実装面 0 byte)。残作業は「S1〜S5 の裁定 → main 取り込み → 受入全走 →
  land 1」だけ。**S2 は core の逐語を 2 箇所変える承認**、**S4 は pilot slot を 1〜8 に固定する
  closure**、**S5 は `a13` 予約の因果循環の解** (予約 entry を land 1 へ同梱する案が推奨)、
  **S6 は land 2 を 1 land のまま複数 session に跨げるか**。land 2 の必須要件 7 件 (台帳→manifest の
  第 1 矢印、`PATH` 差し替え、symlink/TOCTOU、correctness anomaly の還流、変異帰属、`a05` の
  build 再利用、`b03`) は同 `package.md` §S7 に名指しで記録した。第 1 波 branch
  `worktree-dev-wave-t139-manifest-w2` (tip は第 1 波 tip + main 取り込み) は land 2 用に残置する
  base: a59df3904ae743296d5baa6eb48e8dc63e6fdf6b968582bafa7a4816da1bc9ba
