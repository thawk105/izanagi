---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t316-semantic-gate
seq: 1
title: 意味 gate の設計択一 ([T-316]) を裁定パッケージで返した — 実装はしていない (docs のみ、実装差分なし、branch worktree-dev-wave-t316-semantic-gate)
---

## 本文

- **依頼 = [T-316] の意味 gate 設計択一を実測付き裁定パッケージで返す。** `tools=[]` + JSON schema が
  止められない 2 脅威: α (hole 内 1 行 C++ 注入)・β (auditor が実 diff の digest を echo して
  `verdict="pass"` を返す fail-open)。3 案 (i) 全軸 AST/DSL・(ii) build/run sandbox・(iii) 両方 を比較。
  **実装差分ゼロ**で終端し `4→7→8→9` を通った (`DW-S04` の「実装しない」)。変異 matrix は免除。
  裁定パッケージと逐語は `output/insights/2026-08-09_t316-semantic-gate/`。
- **前提の訂正 1 件。** [T-316] は D127 で一度 land 済みだが、意味 gate 本体 (a)/(b)/(c) は D127
  決定(1) が明示的に「別 wave へ分離」しており、現状の `build_admission.py` の opt-in gate は
  D127 決定(4) 自身が「検出器でも意味 gate でもない」と自認している。**本 wave がその分離された別 wave。**
- **段 3 の敵対 2 レンズはいずれも NO-GO** (sol / luna)。ただし「設計の方向」への NO-GO ではなく
  「この前提のまま実装 wave を起票するな」への NO-GO。**方向 (非対称 iii) は生存**し、両レンズの所見は
  すべて real (自己 refuted 分を除く)。親は 4 件の load-bearing 主張を実ファイルで裏取りした。
- **両レンズが独立に突いた最深の所見 (real・要ユーザー裁定):** 意味 gate は **sort の reward hack を
  塞がない**。raw sort comparator は sandbox 内でも候補が制御する trace/stdout に偏った abort/性能値を
  書け、pipeline がそれを `certified=true` + `fitness_tps` にする。現行の非 SWO/fairness 防壁は auditor
  静的目視依存で、β がそれを fail-open にする。sort では (i) 却下 [合成毀損] と (ii) [host 封じ込めのみ] の
  どちらも規律2 本体を塞がない。これは規律2 と規律5/D39 が衝突する非同値な設計択一なので、
  親は決めず (R2-a typed IR / R2-b 独立 oracle [推奨] / R2-c 台帳明示) をユーザーへ返す。
- **親裁定 = 非対称 (iii)。** 全軸 sandbox を host-security boundary (子 process だけを包む)、
  backoff/trigger を限定 DSL (trigger は既存 `reflux_ir.py` 再利用)、sort は raw 合成維持、auditor は
  mandatory deny-only veto (`pass` は capability 発行なし、`diff_digest` は attribution 専用)。
  全軸一律 DSL は却下 (sort の合成実証を別実験に変える)。
- **refuted 3 件を確定。** (i) D127 決定(5) の class-cross cache hole は後続 **D136** が閉じた
  (legacy key が admission receipt SHA を含むことを実確認)。(ii) 「login で測れたので計算ノードでも」は
  brief/plan が明示的に未計測とし計測 ID を実装条件にしているので未犯。(iii) 「有限 DSL は必ず
  allowlist で合成を失う」は plan 自身が反証済み。
- **実装 wave は起票しない (`DW-G04`)。** 前提 = 計算ノード backend 実測 ID + 実発火する正負制御 +
  D75 準拠の field mapping + sandbox execution receipt & WAL topology。順序は
  [T-664] 予算捻出 → [T-184] stage matrix → 計算ノード計測 → 実装。
- **エージェント工数: 親 1、read-only codex 子 3** (段 2 プラン sol 1、段 3 敵対 sol/luna 2、
  いずれも `-s read-only`、effort=max)。実装子・fix 子・変異はゼロ (実装しない裁定のため)。
- **受入全走を記録する** (下記)。実 repo を読むテストは docs-only wave でも `DW-S04` により免除しない。

## 次の一手差分

### 更新

- [T-316] **P1・裁定パッケージを返した ((本エントリ)) → ユーザー裁定待ち**: 3 案の実測比較を
  `output/insights/2026-08-09_t316-semantic-gate/package.md` の R1〜R5 として返した。親裁定 =
  非対称 (iii)。要ユーザー裁定 = R2 の sort reward-hack 分岐 (typed IR / 独立 oracle / 台帳明示)。
  実装の前提 = 計算ノード backend 実測・正負制御・field mapping・sandbox receipt、順序は
  [T-664] → [T-184] → 計測 → 実装。実装方向まで裁定済みではないため実装 wave は起票しない。
  base: a3743acadf738f47e444c3db901f67663a4bad40d26daa7e6bc4c3588e2d4832
