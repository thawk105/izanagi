# 段 1 brief — [T-532] name↔mask 束縛一致検査

## scope

凍結文書 `output/s1-freeze/known_axes_freeze.json` の trigger 系 record について、
`name` が指す要因部分集合 (mask) と `gate_predicate` 本文が符号化する mask の**一致**を
機械検査する。対象は 3 workload × {`system_gate`, `ident_all`} の 6 record。
検査点は (a) 生成層 `s1_known_axes_freeze._trigger_entries`、(b) 本番到達点
`s1_known_axes_freeze._validate_schema` の 2 箇所。scope 外: holdout / measurement / ratified の
各 freeze、変異合成側 (`p3_s4_loop*`)、`selection_rules` の権威記述。

## 確定済みユーザー裁定 (worklog 235)

> name が指す mask と述語本文の mask の一致検査 (emitter 由来の期待 mask との照合) を、
> land 済み membership 検査の追補として軽量 wave で入れる。誤 certification への到達経路を閉じる。

## 段 1 前提実測 (実施済み)

- **(A)** 現行凍結 6 record は name→reasons→`s8a_trigger_sweep.predicate_for` の期待述語と 6/6 一致。
  新検査は現行凍結物を赤にしない。
- **(B)** DW-O09 pin 閉包: 凍結 source に `axis_trigger_gating.py` / `s8a_trigger_sweep.py` が入る。
  `/generator/sha256` = `1d4d45a3…` (t080 `METADATA_SPECS` 定数と同値)。live HEAD 実 sha は
  generator=`a7505a96…`、s8a=`8911dd24…` で**既にドリフト済み**、T-080 移行 receipt の repin 投影が吸収。
  generator へ 1 行入れて freeze 系 8 test file を実走し **238 passed / 1 skipped、赤ゼロ** (即時復元済み)。
  T-492 当時の赤 1 本は同 wave の是正で解消されている。
- **(C)** 本番到達点は `t080_freeze_migration._verify_known_schema` → `_validate_schema`。
  T-492 の「検査点は schema 側」は現在も有効。`verify_document` (legacy) は receipt active 時に呼ばれない。
- **(D)** `trigger_gate_binding` は `wal` / `pipeline` / `loop` から import される。`s8a_trigger_sweep` は
  `pipeline` を import するため、binding→s8a の import は循環する。

## 既存被覆と純増検出力 (性質で検索)

同じ性質 (name と述語本文の対応) を束縛する既存箇所は **1 つだけ**:
`s1_verify_extime_calibration.validated_target` が read-heavy の `system_gate` 1 record を
`_constructed_target()` (reasons を `("readvali-locked",)` にハードコード) と全一致比較する。
ただし (i) read-heavy 以外を覆わない、(ii) `ident_all` を覆わない、(iii) 呼ぶのは extime 較正 tool だけで
本番 gate 経路ではない、(iv) `verify_document` (legacy) 経由。
`assert_s1b_pairing` は name を s1b_pairing 表に、述語を「gate≠ident」にしか束縛せず、
`g_rl` に `g_rt` の正準述語を入れた入れ替えは通る。`_require_canonical_trigger_predicate` は集合帰属のみ。

**純増検出力** = 残り 5 record (balanced/write-heavy の system_gate、3 workload の ident_all) の束縛 +
本番 schema 層への到達 + 生成層での拒否。

## 不変条件

1. 凍結成果物 `known_axes_freeze.json` の bytes を変えない (再発行しない)。世代移行は [T-531]/[T-478] の面。
2. 凍結 source として sha256 が記録されている `s8a_trigger_sweep.py` / `axis_trigger_gating.py` を編集しない。
3. 受理集合は**縮小のみ**。現行 6 record は通り続ける ((A) で実測済み)。過剰拒否の正例を変異へ登録する。
4. `trigger_gate_binding` から `s8a_trigger_sweep` を import しない ((D))。
5. 既存テストの期待値を反転・緩和・skip・削除しない。

## 成果物の形

- `trigger_gate_binding`: 正準述語 → mask の公開導出 (既存 `_CANONICAL_PREDICATE_INDEX` の自然な拡張)。
- `s1_known_axes_freeze`: name → 期待 mask の導出と一致検査を `_trigger_entries` と `_validate_schema` の
  両方から呼ぶ。導出は `s8a_trigger_sweep.subset_name` / `predicate_for` を emitter として使う。
- テスト: 現行 6 record が通る正例 1 本 + name/述語を入れ替えた coordinated tamper を
  生成層・schema 層の双方で拒否する負例。

## DW-G05 成果物影響

入れない場合、`/entries/<workload>/system_gate/name` が実際の gate 意味と食い違ったまま受理され、
certified 選択の構成名・材料レポートの gate 記述・試行台帳の name 欄が実際の述語と非整合になる。
`g_rl` と記録された行が実際は `g_rt` の gate を測った値になりうるため、
誤 certification (別 gate の性能を別名で認定する) へ到達する。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 期待値照合は mask→name の**正引き** (`subset_name(reasons(mask))` と記録 name の比較) で足り、
  `g_rl` → mask の逆パーサは不要。
- **(P2)** `ident_all` は mask 31 の別名として特別扱いしてよく、`stock` / 他 4 種 entry は
  `gate_predicate` を持たないので対象外。
- **(P3)** 検査点は生成層 + schema 層の 2 箇所で本番到達に十分 ((C) の実測に依拠)。
- **(P4)** 実装は `trigger_gate_binding.py` + `s1_known_axes_freeze.py` の 2 ファイルに閉じ、
  凍結 source 群を触らずに済む。

## 分割方針・環境

編集ファイルが素集合にならないため**単一実装単位**。受理集合が変わる wave なので軽量版にせず、
段 2・3 と段 6 の敵対レビュー 2 本を実施する。
受入・実測は Pegasus 計算ノード (`tools/run_tests.py` の dispatch)。ログインノードは pytest を拒否する。
