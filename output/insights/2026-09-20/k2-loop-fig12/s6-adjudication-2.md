# 段 6 裁定 (2 巡目) — 焦点再レビューの所見と fix2 の仕様 (2026-09-20 14:53 JST)

fix1 統合 commit `7debd680c`、local main 取込み merge `0802c0df3` (docs のみ)。焦点再レビュー (`codex/s6-focus.md`): closed 20 / partial 3 / regressed 0、
NO-GO (must-fix 2、should 4、nit 0)。変異 11 群 14 変異はすべて位置一箇所・kill nodeid 実在・mask なし (静的)。

## 所見の裁定

| 所見 | 判定 | 採否 | fix2 での対応 |
|---|---|---|---|
| F-M1 caption の `Measurement reflux paths are drawn three times` が「還流 3 回」と読める。`when counted by distinct source evaluation` は稿の定義の読み替え | real | 採用 | caption を次の固定文に差し替える (回数語の可変生成をやめる): `Measurement reflux occurred twice between the recorded rounds (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round), and diagnosis reflux occurred once (the second critic into the third-round inputs as the typed key k2_critic_diagnosis with fields attribution, recommend, avoid, uncertainty, data_boundary, source_sha256, identical for planner and coder). Three measurement arrows are drawn because the second evaluation feeds both the unevaluated proposal and the third-round proposal; three dotted arrows mark absent paths.` 生成器はこの凍結図の矢印集合を定数 `EXPECTED_ARROWS` (id / kind / from / to の 7 組) として持ち、JSON の arrows と完全一致を要求する (F-S3 / F-S4 も閉じる)。test は稿から手で確定した独立の 7 組の表を持ち、JSON・provenance の両方と照合する |
| F-M2 typed bool true を受理するのに caption は「検出なし」を断定、凡例の coder field の集約が全 role の any になっている | real | 採用 | caption の規律 6 文を bool に束縛: 全 false なら `... no instruction-like strings; none is reported in the recorded rounds.`、1 つでも true なら `...; at least one recorded output reports detection.`。凡例は coder の 4 出力だけで `data_boundary_report.instruction_like_content_detected: false in all four coder outputs` (true があれば `true in at least one coder output`) を組み、全 role の集約は別の句 (`no role reported detection` / `at least one role reported detection`)。反転 test は planner 単独 true でも caption / 凡例が変わることを検査 |
| F-S1 `data boundary: none detected` の主語が不明瞭 | real | 採用 | cell の固定 template を `instruction-like content: none detected (self-report)` / `instruction-like content: detected (self-report)` に |
| F-S2 `known / not known` の基準が run-card の既知集合と分からない | real | 採用 | `in the run-card known set` / `outside the run-card known set` に。lane-proposal の sublabel も `known-value` → `run-card known-value` に |
| F-S3 T7 の期待が JSON に追従 (経路の転記誤りを検出しない) | real | 採用 | F-M1 の独立表 (test 側の定数、稿 §0.1 / §2.2 / §2.3 から) で閉じる |
| F-S4 caption の経路列挙が固定なのに回数だけ可変 | real | 採用 | F-M1 で回数語も固定 + `EXPECTED_ARROWS` 束縛 |

refuted: なし。scope 外: なし。3 巡目の fix は行わない (DW-O16 の上限)。fix2 後は親が変異 (probe 済みの anchor を再検証) と受入で裏取りし、残る所見は親が裁定して閉じる。

## fix2 の所有と契約

所有 path は同じ 3 file (+ `probe-k2fig12/`)。unit worktree を wave HEAD `0802c0df3` (fix1 + main 取込み) へ切り替え、branch `dev-wave-k2fig12-unit-fix2`。
実装子契約 (DW-S05-A/B/C) を全文継承。変異登録 (11 群 14 変異) の anchor 文字列は保つ (`_enum` / `_keys` / `check_display_text` の先頭行 /
`_intersection` / `_contains` / `_segment_intersects_box` / `caption_source=dict(path=SOURCE,sha256=by_path[SOURCE])` / `tools_none mismatch` の行 /
`_publish_outputs` の `check_figure_layout(fig, layout)` 呼出し / `_figure_number` の `_require(match is not None, ...)` / `_anchor` の `== 1` /
`_drawn_items` の `_require(actual == _display_items(...))` / `discipline6 form mismatch` の行 / marker の `'X' if ... else 'p'` 式)。
変えるなら報告に旧→新を書く。
