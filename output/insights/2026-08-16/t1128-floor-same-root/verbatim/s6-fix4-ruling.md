# 段 6 fix 契約 (第 4 巡・F2 の完成) — [T-1128]

親裁定。2026-08-16 01:35 JST。

## 0. `DW-O16` の 3 巡上限との関係 (明示)

`DW-O16` は「NO-GO が続く場合は fix を**重ねず** 3 巡を上限」とする。本巡はこれに抵触しないと裁定する。

- 本巡が直すのは**新しい所見への追加対応ではなく、第 1 巡 fix 契約 F2 の未完了部分**である。
  F2 は「`build_v2` が completion を publish する前に、masstree の HEAD・`config.h` sha256・
  archive sha256 を再取得して入力 receipt と比較する」と書いたが、
  **どの root から再取得するかを書かなかった**。実装は期待 base から取っており、
  build が実際に使った root からは取っていない。これは親の指示の欠落であり、
  第 2 巡の G1 と同じ型 (親の裁定文の不備) である。
- 焦点再レビューの対応表でも A-2 は `closed` ではなく **`partial`** である。
  未完了の項目を完成させることは、閉じた所見を蒸し返すことではない。
- 成果物影響が重い: **oracle が検証していない依存で作られた binary に
  certified の admission receipt が出る。** 放置して land できない。

本巡でも閉じなければ、`DW-O16` に従い 5 巡目へ進まず、変異で裏取りして裁定で閉じる。

## 1. 所見の裁定 (焦点再レビュー)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| Z-1 | fresh で拒否した wrong-root completion が次回 cache hit で admission される | **real / must-fix** | 採用 (F2 の完成として) |
| Z-2 | M1 の期待 node の一部が後段 gate に過剰決定されている | **real / nit** | 採用 (変異台帳の注記として。コードは変えない) |
| Z-3 | generator 内の SOURCE_DIR 個数・BASE_DIR 個数の検査は外部入力から発火不能 | **real / nit** | 採用 (記録で保証範囲を過大表示しない。コードは変えない) |

焦点再レビューが `closed` と判定した A-3・B-2・B-3・B-4 はそのまま閉じる。
A-1 の `regressed` 判定は Z-1 と同一原因であり、Z-1 の fix で閉じる。

## 2. fix 契約 (K1)

- **K1。** `build_v2` の completion publish 前の検査を、**build が実際に使った masstree source root**
  を権威にする形へ完成させる。
  1. build 後に CMakeCache 等から**実効 masstree source root** を取得する
     (`s8b_floor_campaign` の postflight が使っているのと同じ観測源)。
  2. 実効 root が期待する `<canonical base>/masstree-src` と**一致しなければ publish しない**。
  3. HEAD・`config.h` sha256・archive sha256 の再取得を、**期待 base ではなく実効 root から**行い、
     入力 receipt と比較する。不一致なら publish しない。
  - **負例**: 実効 root が期待 base の外を指す build は completion を 1 件も残さず、
    同じ key の次回呼出しが `cached=False` になる (前回の wrong-root entry を hit しない)。
  - **正例**: 実効 root が期待 base と一致し内容も一致する build は従来どおり publish される。
  - **正例 2**: 内容が同一の別 base からの cache hit は引き続き通る (第 2 巡 G1 と第 1 巡 F1 の維持)。
- campaign 側の postflight (`s8b_floor_campaign`) は**そのまま残す** (二重防壁)。
  cache hit 時に absolute root の再一致を要求しない片方向規則も維持する。

## 3. 変更しない事項

- 第 1 巡 F1・F5・F6、第 2 巡 G1・G2、第 3 巡 H1・H2 には触るな。
- 編集面 7 ファイルを増やすな。
- **既存 (本 wave より前から tracked の) テストの期待値を変更するな。**
- production を fail-open にして辻褄を合わせるな。
- Z-2 / Z-3 はコードを変えない。記録側で扱う。

## 4. 記録での扱い (親の義務。子は関与しない)

- Z-2: 変異台帳に「M1 の期待 node のうち
  `test_floor_postflight_gate_rejects_effective_root_and_content_drift` の wrong-root
  parameter は後段の source-missing gate に過剰決定されており、単一理由の kill 証拠に数えない」
  と注記する (`DW-M03`)。
- Z-3: 「generator 内の SOURCE_DIR 個数・BASE_DIR 個数の検査は構成不変条件であり、
  外部入力から発火する実効 gate ではない」と記録する。実効 gate は campaign の postflight 側である。
