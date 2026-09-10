# 段 1 brief — [T-490] U-1/U-2 実装 wave (軽量)

## scope (ユーザー裁定済み、worklog (211))

- **U-1 = 択一 (b)**: `is_canonical_predicate` の strip 同値受理は維持したまま、
  **materialize 前に emitter の正準 bytes へ畳む**。同一 mask から複数の
  `src_token` / `variant_id` が生まれる余地を閉じる。
- **U-2 = 択一 (a)**: `prepare_cell` の `configuration` dispatch を
  **既知 6 構成の allowlist にして未知を fail-closed 拒否**する。
  裁定条件: `stock_common` と `p2_2_flag_opt` を必ず含める、S8b 側の全 caller を先に棚卸しする。
- scope 外: U-3 = [T-492] (freeze 生成・検証層の semantic membership)、
  U-4 = [T-493] (`sort_best.comparator` の閉じた権威集合)。**この wave で実装しない。**

正本 = `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7。

## 段 1 前提実測 (実行済み)

| # | 測ったこと | 結果 |
|---|---|---|
| P-A | `emit_predicate` 32 本の strip 恒等性 | **32/32 恒等** → 正準 bytes = strip 形 |
| P-B | 未 strip 出力の `CANONICAL_PREDICATES` 所属 | 32/32 所属 (digest 原文と membership 集合は一致) |
| P-C | 外周空白 7 種 (` `, `\t`, `\r\n`, `\x0b`, `\x0c`, NBSP, U+3000) | **すべて受理**、bytes は base と非同一 |
| P-D | 空白付き入力の sha256 | 正準 digest と**不一致** → identity 多重化は real |
| P-E | 実成果物の `configuration` 値 | **ちょうど 6 種**、裁定文の 6 構成と完全一致 |
| P-F | 凍結 cell の述語 bytes | `gate_predicate` 6 件は exact、**`sort_best.comparator` 3 件は外周空白付き** |
| P-G | 凍結 bytes の pin 閉包 (`DW-O09`) | `FROZEN_MANIFEST` が 23 artifact を sha256 で pin、`measurement_freeze.json` / `known_axes_freeze.json` を含む |

## 裁定時点で未見の新事実 (段 4 で再確認する)

**P-F**: `output/s1-freeze/measurement_freeze.json` の `sort_best` セル 3 件の `comparator` は
外周空白付きで、その空白は現行の materialized bytes と `src_token` に既に焼き込まれている。
裁定文の「現行 6 値は exact なので既存値は不変」は **`gate_predicate` については成立するが
`comparator` には成立しない**。よって畳み込みを述語一般へ広げると凍結物の identity が変わる。
裁定 U-1 の対象は `is_canonical_predicate` 面 (trigger 述語) であり comparator を含まないため、
裁定自体は覆らない。scope 境界として不変条件に格上げする。

## 不変条件 (違反したら停止)

1. **`sort_best` の `comparator` bytes に触れない。** 畳み込みは trigger 述語経路
   (`marker_id == TRIGGER_MARKER_ID` / gate 軸) に限定する。comparator は [T-493] の所有面。
2. **現行 6 構成の受理挙動を変えない。** allowlist は `backoff_fixed_best` / `ident_all` /
   `p2_2_flag_opt` / `sort_best` / `stock_common` / `system_gate` をすべて受理する。
   `stock_common` / `p2_2_flag_opt` は現行どおり flags-only の `PreparedCell` を yield する。
3. **凍結成果物の bytes を変えない。** `FROZEN_MANIFEST` の 23 件と既存 golden は不変のまま緑。
4. 受理集合の変更は U-2 の「未知 configuration の拒否」だけとする。それ以外の拡大・縮小をしない。
5. `is_canonical_predicate` の受理集合 (strip 同値) を狭めない (択一 (a) は不採用と裁定済み)。

## 成果物影響 (`DW-G05`)

- U-1 未実装: 外周空白付き述語が freeze / 直接 caller から入ると、同じ意味の mask に
  別 `src_token`・別 `variant_id` が付き、certified 選択と材料 proof chain に重複候補が入る。
- U-2 未実装: 別名 configuration (`"system-gate"` 等) が述語検査・patch 適用・quarantine を
  全て素通りし、構成ラベルと実 source が食い違ったまま試行台帳・材料レポートへ載る。

## provisional 裁定 (攻撃対象)

- **(P1)** 畳み込みの実装点は `p3_s4_loop.quarantine` の trigger 分岐 (共有 materialize 境界) とし、
  `prepare_cell` 側だけに置かない。理由: `prepare_cell` と P3 S4 loop の両方が同じ境界を通るため、
  片側だけでは identity 多重化が残る。
- **(P2)** 正準 bytes は `text.strip()` ではなく **emitter 由来の正準メンバへ解決**して得る
  (P-A より両者は現状一致するが、emitter が将来 strip 非恒等になっても壊れない)。
- **(P3)** allowlist は `prepare_cell` 内の分岐直前に置き、未知は既存の `DriverError` で拒否する。
  新しい例外型を作らない。
- **(P4)** テストは新規 fail-closed 正例・負例を追加し、既存の凍結 golden を一切変更しない。

## 成果物の形

- 実装: `orchestrator/campaign/` 配下の最小差分 (Codex `role=author` が書く)。
- テスト: U-1 の畳み込み証明 (空白付き入力 → 正準 bytes / 同一 `src_token`)、
  U-2 の 6 構成正例 + 未知拒否負例。
- 変異 matrix で両 gate の単一理由性を裏取り。

## 分割方針

U-1 と U-2 は同一ファイル (`s1_direct_comparison.py`) に触れる可能性があるため、
**単一 Codex 実装単位**とする (所有が素集合にならないため並列分割しない)。
