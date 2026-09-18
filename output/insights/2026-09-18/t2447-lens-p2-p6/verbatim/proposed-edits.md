# 候補文言と byte 差 (親の実測、main d2ebef7a4)

層予算の現在値 (tools/check_docs.py の定数と同じ計算): L1 = 10,622 / 10,625 (残 3)、L1.5 = 9,696 / 9,696 (残 0)。
L1.5 = workers.md 全節 + preamble、mutation.md M02〜M06/M08、operations.md O01/O02/O05。
L1 = core.md 全 U 節 + preamble、mutation.md preamble + M01、operations.md preamble + O23。

## E1. workers.md DW-S03 (P2) — delta +109 (L1.5)
旧 (1 行):
正しさ境界と整合・実効性を分け、親 brief 自身も検査対象だと明記する。
新:
正しさ境界・整合と過剰・削除（追加が実測欠陥か研究前進に対応するか、削除・局所修正で
済まないか）に分け、親 brief 自身も検査対象だと明記する。

## E2. workers.md DW-S06-A (P2 + 原資) — delta +27 (L1.5)
旧 (2 行):
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
所見ゼロの扱いは `DW-M02`。
新:
1 本は `DW-S03` の過剰・削除レンズに固定する。
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
(pin 行「実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。」は不変)

## E3. workers.md DW-S06-C (原資) — delta −61 (L1.5)
旧:
成立した条件の operations と `DW-G05` を適用し、成果物影響を書けない所見を must-fix にしない。
新:
成立した条件の operations と `DW-G05` を適用する。
担い手: DW-G05 (段 6 U、同一読点)「示せない must-fix は nit/backlog とし、追加 review を起動しない。」

## E4. workers.md DW-S06-B (原資) — delta −99 (L1.5)
旧 (2 行):
実装子契約の継承では権限、reasoning/sandbox、テスト弱体化禁止、受理集合、期待赤、波及報告、段 4 の
規模上限を省略せず、超過は所見が閉じても差し戻す。
新:
実装子契約の継承では段 4 の規模上限も省略せず、超過は所見が閉じても差し戻す。
担い手: 入口 (L0)「段 6 で fix を codex へ再投する子は、段 5 の実装子契約 `DW-S05-A`、`DW-S05-B`、`DW-S05-C` を全文継承する」+ 段 6 U の DW-S05-A (reasoning/sandbox)、DW-S05-B (権限、期待赤)、DW-S05-C (テスト弱体化禁止、受理集合、期待赤、波及報告)。「段 4 の規模上限」は docs/dev-wave でここにしか無い。

L1.5 合計: +109 +27 −61 −99 = −24 → 9,672 / 9,696。

## E5. core.md DW-S04 (P6) — delta +109 (L1)
旧 (1 行):
scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージでユーザーへ返す。
新:
scope 外の real 所見は実装せず、研究前進か実測欠陥の根拠がある所見だけ設計択一・推奨案付きの
裁定パッケージでユーザーへ返し、無い所見は起票せず insight に記録する。

## E6. core.md DW-S09 (原資) — delta −43 (L1)
旧:
再試行・停止は `DW-O23` に従い、正式な停止時だけ main HEAD と既存 branch を報告する。
新:
正式な停止時だけ main HEAD と既存 branch を報告する。
担い手: 入口 終端 (L0)「段9は `DW-O23` に従い、競合時は再試行する。」+ 段 9 U の DW-O23 本文 (再試行・停止の手順)。

## E7. operations.md preamble (原資) — delta −70 (L1)
旧 (2 行):
発火条件の正本は入口の条件dispatch、成立時の実行手順だけは本書。
該当節を操作直前に読み、停止条件を迂回しない。
新 (1 行):
発火条件の正本は入口の条件dispatch、成立時の実行手順だけは本書。
担い手: 入口 読み込み契約 (L0)「wave 開始時、段 1〜9 の各段と条件成立操作の直前に条件を再評価して表の節を読み」+ 凍結境界「規定の停止条件、検査赤、権限・scope・参照不整合を迂回しない。」

L1 合計: +109 −43 −70 = −4 → 10,618 / 10,625。

## 触らない pin (tools/check_docs.py 実測)
- DW-S03: `reasoning=medium` が可視本文にちょうど 1 回 (E1 は触れない)。
- DW-S06-A / DW-S06-C: 上記の pin 行がちょうど 1 行 (E2 / E3 は別行)。
- core.md: 「実装面があれば段 5 の Codex 実装子と fix 子は」「親は直接編集しない」(DW-C00、触らない)。
- DW-S09: 「`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路」(E6 は別行)。
- 構造 pin: 入口 D2 巻き戻し・D4 fix 継承の regex、`CODEX_AUTHORING_STRUCTURE` (入口)。
