---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t8b-reopen-inspection
seq: 1
title: 8b 再開の検分で 7 月実装分の生死を実測した — 腐りなし・未実装 3 段に加え Pegasus に固定要求の compiler が無い blocker を新たに検出し裁定 4 件を返す (docs のみ、branch worktree-dev-wave-t8b-reopen-inspection)
---

## 本文

- **起票根拠 = スコープ B 部分再開のユーザー裁定 (2026-08-10、Q1 = (a))。** 一次控えは
  `dev-wave-jobs/rulings-inbox/2026-08-10-scope-b-reopen.md`。本 wave は検分と手順書だけを担い、
  本番コードを一切編集していない (実装面ゼロ、Codex 子ゼロの docs-only)。
- **並走ガード (Q3) の充足:** キュー投入は s8b テストの dispatch 2 本だけで、ノード同居なし。
  T-139 の pilot / 本走 job は wave 中を通じて走行していなかった (投入前に `qstat` で確認)。
- **検分の結論 = 7 月実装分に腐りはない。** pin・封印・受領証はすべて現行 main と整合し、
  gate は設計どおりの拒否を返した。実測値は `docs/phase3-8b-restart-runbook.md` §1 の表が正本。
  再開を塞いでいるのは腐りではなく未実装の段である。
- **新事実 (今まで表に出ていなかった blocker)。** 床値 driver は CCBench のビルドで
  `gcc-13` / `g++-13` を固定要求し、`buildcache` は PATH 不在なら fail-closed で倒れる。
  Pegasus にはログイン・計算ノードのどちらにも `g++-13` が無い (runbook §7 に既記録)。
  Pegasus 用の較正証明と floor job script の依存ビルド段は `command -v gcc` で system の
  既定 compiler を解決する設計であり、driver 側の固定要求とかみ合っていない。
  **official guard が build より手前で rc=2 を返していたため、実機 job 873225 はビルドへ到達せず
  この不整合が露見しなかった。** env contract には toolchain を束縛する field が無く、
  「どの compiler で床値を測ったか」は現状どの契約にも紐付かない。
- **偽の赤を 1 件特定した。** `s8b_holdout_freeze.py verify` 単体 CLI は恒常的に赤を返す
  (`design_source` / `generator` の worktree drift)。T-080 移行でこれらは受領証へ移し替え済みで、
  live の oracle gate は移行基準 commit の blob を見るため緑である。単体 CLI だけが旧経路のまま。
  生死判定は oracle gate-check の 1 本で行うと手順書へ固定した。
- **裁定は 4 件返す** (下記「新規」の 4 項)。裁定帯域は Q3 (iii) により A 系 (T-139 本走線) の後ろ。

## 次の一手差分

### 新規

- {{T:s8b-floor-toolchain-binding}} **P1・ユーザー裁定待ち (B 系、A 系の後)**: 床値 driver が
  固定要求する `g++-13` が Pegasus に無い。択 (a) env contract へ toolchain を束縛する field を
  足し Pegasus 世代は system compiler を実体・版数つきで焼き込む / (b) Pegasus に `gcc-13` を
  用意できるか先に調べる / (c) driver の固定要求を env 依存の解決へ変える。いずれも計測条件を
  変えるため、既存 `linux-baremetal` 値との混用可否も同時に決める。
  **これを決めるまで床値実測を投入しても必ずビルド段で倒れる。**
  材料 = `docs/phase3-8b-restart-runbook.md` §1.2
- {{T:s8b-restart-order-vs-generation}} **P1・ユーザー裁定待ち (B 系)**: 8b 床値実測を pegasus
  第 1 世代のうちに走らせるか、[T-657] の世代交代を先に通してから protocol と封印を作り直すか。
  registry には未発効の第 2 世代が既にあり、交代が先に発効すると現行 floor protocol が current と
  食い違って実測が塞がる (式 1)。floor を作り直すと selector の予測封印と食い違う (式 3)。
  材料 = 同手順書 §4
- {{T:s8b-legacy-verify-cli-supersede}} **P2・ユーザー裁定待ち (B 系)**: `s8b_holdout_freeze.py
  verify` 単体 CLI が T-080 受領証を参照せず恒常的に赤を返す。択 (a) CLI を受領証参照へ寄せる /
  (b) supersede を明記して手順から外す / (c) 現状維持。材料 = 同手順書 §1.1
- {{T:s8b-v2-producer-and-manifest-wiring}} **P2・ユーザー裁定待ち (B 系)**: freeze v2 の
  producer が存在せず (`generation_number` を書く経路が repo に無い)、oracle manifest の
  `build_manifest` にも production caller / CLI が無い (テストからのみ)。この 2 つを 1 wave に
  まとめるか分けるか。path 規約 `holdout_freeze.v2.g{N}.json` は既定済み。材料 = 同手順書 §3
