# 段 6 裁定 — レビュー A (過剰・削除 + P1) / B (稿との逐語照合 + 正しさ境界) の所見と fix1 の仕様 (2026-09-20 14:28 JST)

統合 commit `85b463655`。焦点走 focus-1 (計算ノード、14:15〜14:17): 161 passed / 1 failed (期待赤 = 未着地 T9)。レビューは 2 本とも NO-GO
(A: must-fix 1、B: must-fix 3)。逐語照合表 (B) は drawn_items 50 件・arrow label 7 件・caption 全文で、**値・判定・還流先・role 遮断・正しさ境界はすべて稿と一致**、
不一致は「提案日の『記録による』留保の脱落」だけ (B-M1)。

## 所見の裁定

| 所見 | 判定 | 採否 | fix1 での対応 |
|---|---|---|---|
| A-M1 規律 6 の自己申告 field が表示にも検査にも使われず、反転しても図が不変 | real | 採用 | 各 role cell の `discipline6` を typed object `{"form": <enum>, "instruction_like_detected": <bool>}` にする。`form` は role 固定 (planner → `uncertainty-prose`、coder → `structured-field`、critic → `trust-boundary-section`) を要求。marker は bool で形が変わる (false → 現行の盾形 `p`、true → 赤の `X`)。**drawn_items の role cell の text に `data boundary: none detected` / `data boundary: detected` を固定 template で含める** (provenance と test で反転が見える)。test: 1 cell を true に反転 → drawn_items と marker artist (独立表) が変わる。form 不一致は拒否 |
| B-M1 提案日が「記録による」留保を落としている | real | 採用 | 列見出しを typed で組み立て直す: `Round <n>` / `After round <n> (not a round)` + 2 行目 `proposal <date> (per round records) · evaluation <date> (job log)` (未評価列は `evaluation: none`)。caption に限定 6 の 1 文を足す (A-S1 と同じ文) |
| B-M2 `not-a-round` 固有制約 (kind・critic・date 整合) を負例が踏んでいない | real | 採用 | 負例を作り直す: (a) 未評価列の evaluation / evaluated / critic / date を相互整合させて kind だけ `round` に → `evaluation kind mismatch` (または専用文言) で拒否、(b) round 列で critic だけ null、(c) round 列で date_evaluation だけ null、(d) 巡 3 以外で has_diagnosis true。各 1 理由 |
| B-M3 M7 の fixture が layout 以外の拒否理由 (`_drawn_items` の文字列不一致) も作る | real | 採用 | `collision` fixture を「登録済み Text の座標移動」に変える (文字列不変、`_drawn_items` は緑、layout だけ赤)。T6 は同 fixture で publisher を通す |
| A-S1 限定 6 (起動・送付・生成日・順序は各巡の記録による、保存 prompt は送達証明でない) が caption に無い | real | 採用 | caption 固定文 7: `Role launch times, inline delivery, proposal dates, and the fine ordering of steps rest on each round's records; saved prompts and inputs are not proof of delivery.` |
| A-S2 B-6 非判定と遮断の範囲 (tool access に限る) | real | 採用 | role sublabel の `structural blockade` → `no tool access (structural blockade of tool use)`。caption 固定文 8: `This figure does not judge whether B-6 is met; the tool-less declaration concerns tool access only, and leak control is not complete.` |
| A-S3 / P1 提案値の二重表示 → (b) | real | 採用 | coder cell = instance + 固定文 `synthesizes one backoff literal` (値なし)。proposal cell = instance + `backoff literal <v>` + known / not known + evaluated / not + sublabel。`value` の語を使わない。sublabel の `outside the known set` 重複を除く (B-nit2) |
| A-S4 / B-S3 provenance の `arrows` が入力の写しで、描いた artist と caption の回数を束縛しない | real | 採用 | provenance `arrows` は `layout['arrows']` (描いた artist の id / kind / from / to / visible) から組み、保存前に JSON の arrows と完全一致を要求。caption の「twice / once」は JSON の kind 別件数から生成 (`once / twice / three times`、4 以上は拒否)。test は JSON から独立に期待を組み、artist の可視と件数を照合 |
| B-S1 / A-nit2 T5 の `tmp_path` 空検査は恒真 | real | 採用 | T5 から `tmp_path` assertion を外す。T6 を 3 種 (overlap / escape / arrow crossing、いずれも座標移動) で parametrize し publisher を通す |
| B-S2 coder の自己申告 field 名が図に無い | real | 採用 | 凡例 (生成器固定文) に `coder: structured field data_boundary_report.instruction_like_content_detected` を書く (固定文なので `=` 禁止に触れない。値は typed bool から `false in all recorded rounds` を組む) |
| B 表の「実装あり・負例不足」(schema 固定 / ISO 日付 / reference_ids 形式・重複・未使用 / roles 順序・path / lanes 順序 / columns 順序 / has_diagnosis 列 / certified flags / job 重複 / instance 重複 / arrow id 重複 / non-absent の to null / evaluated 片方向) | real (should) | 採用 | `test_t3_invalid_json_without_drawing` の parametrize に各 1 例を足す (描画なし、実 loader) |
| A-nit1 未使用の neutral marker 分岐 | real | 採用 | 削除 |
| A 削除候補「role と lane の label / sublabel 重複」 | real | 採用 | lanes の planner / coder / critic は `id` と `source_anchor` だけにし、表示は roles から導く (重複入力と一致検査を削除) |
| B-nit1 変異の母数表記 (10 群 12 変異) | real | 採用 (親の台帳) | 台帳に「10 群 12 変異」と書く |
| B M1 column-kind は後段が mask / M8 は関数内述語 | real | 採用 (親の変異登録) | M1 は `direction` の負例で評価、M8 は `_figure_number` 内の述語を恒真化 |
| 親の目視: 列見出し「Initial / Next / Final」 | real | 採用 | B-M1 の typed `number` で `Round 1/2/3` |
| 親の目視: `( R0 )` の括弧の空白 | real | 採用 | `check_display_text` の token 照合で両端の `()[].:` を剥いでから宣言 ID と照合。JSON は `(R0)` / `(T-2795)` に直す |
| 親の目視: a3 (absent、to null) が右端を上へ登る | real | 採用 | `to` が null の矢印は始点から右へ短い水平 stub (幅 0.02) を出して `×` で終える。label bank の行はそのまま |
| 親の目視: R6 marker が小さい | real | 採用 | markersize 4 → 7、cell の右上 (y+h−0.009) へ |
| 親の目視: 副題が説明不足 | real | 採用 | `Source: frozen results note <basename> (SHA-256 in provenance); figure created <date>` |
| 親の目視: round-1 evaluation の `bnode host` | real | 採用 | sublabel を `legacy verify condition` だけに |
| 親の目視: parent lane の sublabel 文言 | real | 採用 | `builds the planner and coder input JSON, sends the full JSON inline, runs preflight checks on the login node (per round records)` |
| 親の目視: lane の空白 (parent / proposal / evaluation) | real (should、任意) | 採用 | 各 lane の高さを内容に合わせて縮め (parent ≈ 0.11、proposal ≈ 0.06、evaluation ≈ 0.075、critic ≈ 0.07)、浮いた高さは矢印 label bank と凡例へ回す。layout check が緑である範囲で |

refuted: なし。scope 外 real 所見: なし。

## fix1 の所有と契約

所有 path は段 5 と同じ 3 file (+ `probe-k2fig12/` scratch)。unit worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/k2fig12-unit` を統合 commit `85b463655` へ切り替え、
branch `dev-wave-k2fig12-unit-fix1`。実装子契約 (DW-S05-A/B/C) を全文継承。**同 wave の新 test file は編集対象** (tracked の既存 test は不変)。

## 変異事前登録の更新 (DW-M01、10 群 12 変異)

| # | 位置 (関数) | 変異 | kill する test |
|---|---|---|---|
| M1 | `_enum` | membership 恒真 | `test_t3_invalid_enum_is_rejected[direction]` (column-kind は後段 mask のため評価外) |
| M2 | `_keys` | `set(value) == set(expected)` → `set(expected) <= set(value)` (未知 key を許す向き) | `test_t3_unknown_key_is_rejected[top]` |
| M3 | `check_display_text` | 早期 return | `test_t4_free_text_rejects_quantities[38%]` |
| M4a | `_intersection` | 常に 0 | `test_t5_overlap_is_a_layout_error` |
| M4b | `_contains` | 常に True | `test_t5_escape_is_a_layout_error` |
| M4c | `_segment_intersects_box` | 常に False | `test_t5_arrow_crossing_text_is_a_layout_error` |
| M5 | `build_provenance` | caption_source sha256 を別の 64-hex 定数へ | `test_t7_caption_source_hash_is_independent` |
| M6 | `load_flow` の tools 比較 | 常に一致扱い | `test_t2_tools_none_mismatch_is_rejected[0]` |
| M7 | `_publish_outputs` | `check_figure_layout` 呼出し削除 | `test_t6_publish_runs_layout_check[overlap]` (座標移動 fixture、単一理由) |
| M8 | `_figure_number` | 内部述語を常に受理 | `test_t8_cli_rejects_invalid_prefix` |
| M9 | `_anchor` | `== 1` → `>= 1` | `test_t3_non_unique_anchor_is_rejected` |
| M10 | `_drawn_items` | 照合削除 | `test_t7_drawn_items_match_flow` |
| M11 (新) | `load_flow` の discipline6 form 照合 / marker 形の分岐 | form 不一致を許す、または bool を無視して常に `p` | `test_t3_invalid_json_without_drawing[discipline6-form]` / `test_t7_discipline6_flip_changes_marker_and_items` (2 変異、群 M11) |

実装後に位置を実行番号へ確定して probe → final で走らせる。
