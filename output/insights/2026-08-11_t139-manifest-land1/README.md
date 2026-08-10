# [T-139] 第 2 波 — land 1 の承認候補と逐語 (2026-08-11)

branch `worktree-dev-wave-t139-manifest-land1` (local main から分岐)。
可変状態の正本は `docs/worklog.md` 末尾である。本ディレクトリは凍結記録であり、後から書き換えない。

## 結論

**land 1 (文書承認 fold) は実行していない。** 裁定 R1 (a) を実行しようとしたところ、
**R1 の裁定時点で未見だった事実が承認対象そのものを承認不能にしていた** (`package.md` §S1)。
`DW-S04` に従い、親は不採用にせず、承認候補を承認可能水準へ直して新事実付きで裁定へ返した。

## 置いたもの

| ファイル | 内容 |
|---|---|
| `record-items-v2.md` | 受領証の要件文書 (自己完結版)。**承認候補** |
| `erratum-core-s7-stresscheck-v2.md` | 凍結 core への第 2 erratum (2 operation)。**承認候補** |
| `receipt-schema-v1.json` | 上記と exact 1:1 の機械可読 schema (JSON Schema draft-07)。**承認候補** |
| `package.md` | ユーザー裁定 7 問 (S1〜S7) と報告 3 件 |
| `verbatim/` | 段 1 brief、段 2 プラン、段 3 敵対レンズ 2 本、段 4 裁定、段 5 実装子報告、段 6 レビュー |

## 直した欠陥 (段 2 プランと段 3 レンズ 2 本が挙げ、親が一次資料で裁定した)

| # | 欠陥 | 直し方 |
|---|---|---|
| 1 | 凍結 core の較正義務が 221 行と **333 行**の 2 箇所にあり、1 operation では二重状態になる | erratum を 2 operation へ。合成 = `e0b0caea…8e0c` |
| 2 | 草案が承認後に自分の承認状態について偽を述べる | `approval_status` を削除し、承認状態を台帳の管轄に戻した |
| 3 | `pre_performance_infra_failure` が `a04` より広く、裁定外の受理拡大だった | `a04` 準拠へ縮小 (性能 raw / `a03` 不成立証拠があれば pre へ写せない) |
| 4 | nested exact key 閉包が未完で内部矛盾があった | 全 object を閉じ、`binary_rehash` 9 要素・`malformed_reason` 非 null 必須・`exclusivity.method` enum 閉包へ |
| 5 | `a13` の検査が現 tip の重複だけだった | append-only 全履歴検査 + 保証境界の逐語固定 (R3 (a)) |
| 6 | 受領証 schema が無く dialect も未確定だった | draft-07 で発行 (実環境の `jsonschema` は 3.2.0、repo の先例も draft-07) |
| 7 | pilot が消費する 8 slot が未凍結で結果依存に選べた | `pilot_cluster_slots = [1..8]` を要件として固定 |
| 8 | `schedule_sha256` の対象 bytes が未定義で再導出できなかった | canonical bytes (TSV・157 行・並び順) を逐語定義 |

## 本ディレクトリが主張しないこと

- **承認された、とは主張しない。** 3 文書はいずれも承認候補であり、承認は canonical 台帳と
  approval manifest だけが定める。
- **pilot を投入した、とは主張しない。** T-139 の投入 API は 1 つも実装されておらず、
  D264 の非 export 検査が機械固定している。本 wave はそれを緩めていない。
- **land 2 (manifest + producer + pilot) の層は 1 つも実装していない。**
