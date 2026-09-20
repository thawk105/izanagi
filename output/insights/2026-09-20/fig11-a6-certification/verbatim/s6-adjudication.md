# 段 6 裁定 — レビュー A (過剰・削除) / B (正しさ境界・整合) の所見 (2026-09-20 14:2x JST)

レビュー 2 本とも NO-GO (must-fix 各 1 件)。生成器の共有化・fig11 の値・A-2 着地互換・fail-closed 経路・fixture 実寸には作り直しを要する欠陥なし (両レビュー一致)。

| id | 種別 | 裁定 | 対応 |
|---|---|---|---|
| A-1 / B-4 | must-fix / should | **real・採用** — m1 の既存 m11 は pin 表不在で手前拒否 (単一理由でない)、m6 は producer 側の未知 study 拒否層が背後にある | 変異の再照準 (spec)。m1 の検出 node は `test_a6_pin_drift_is_rejected` を主にし probe の実測集合で確定。m6 は 2 本へ: m6a = legacy が A-6 study を受理する変異 (kill = `test_a6_legacy_profile_is_rejected`、legacy 経路に他層なし)、m6b = current-full の受理集合から A-6 を落とす変異 (`accepted_studies = (STUDY,)`、kill = A-6 正例 test 群)。current-full の未知 study 拒否は「生成器が先、producer が背後」の冗長 gate と台帳に明記し単独変異の証拠から外す (DW-M03)。実装は変えない |
| A-2 | should | **real・採用 (文言)** — 「A-2 provenance 射影を 1 byte も変えない」の範囲 | 着地済み fig5/6/7 の bytes・caption・artist 射影は不変、**再生成する A-2 current-full provenance には top-level `study` が加わる**、と worklog / plotting README に書き分ける。コード変更なし |
| A-3 / B-3 | should | **real・一部採用** — `validate_repo_closure` は provenance の自己整合と hash だけを見る | (1) fig11 着地 test に、provenance の `study` / `outer_status` / `effects` / `cells[].median_tps` が tracked certification.json の値と一致すること、`external_inputs` の path 集合が raw-manifest の `files` と完全一致することの直接照合を足す (fig10 の着地 test が provenance と稿の値を照合するのと同型。新 gate ではなく着地 test の束縛)。(2) README「再現できるのは…」「proof chain」の射程を実装どおりに限定して書く。`validate_repo_closure` 本体は変えない |
| A-4 / B-5 | nit | **real・採用 (docs)** | README fig11 節: 「study が pin 表の exact 2 件」→ `STUDY_PROFILES` の 2 study と `CANONICAL_SHA256` の 3 leaf を書き分ける。「内部識別子は出さない」→ 図中ラベルは `no backoff` / `fixed 2 us` / workload 名 (read-heavy、rr95) と書く。「作図規約への適合」の重複を削り短くする |
| B-1 | must-fix | **real・採用** — abort 率は「5 rep のうち throughput が median に最も近い rep の 1 点」(稿 §2.3・限定 6) で、"one aggregate abort-rate point" は集約値と読める | A-6 caption を「one abort-rate observation per cell, taken from the repetition whose throughput is closest to the median (the runner's representative-repetition rule)」へ。README の「何を示す図か」も同じ規則で書く。A-2 caption (fig6 凍結) は触らない |
| B-2 | should | **real・採用** — 稿 §0「文を分けたまま使う」、限定 4 (iii)(v) の欠落 | A-6 caption の正しさ部分を 3 文に分ける: 「Correctness comes from separate trace-enabled runs: all 2 cells were certified.」「This is not a performance certification.」「The performance reject does not withdraw that correctness evidence.」続けて限定を 1 文で: L01 / D1257 / artifact hash 単独は compile-out の証明でない / src_token 一致は翻訳単位全体の意味一致を保証しない (稿 §4 (i)〜(v))。固定文の test と m5 の anchor を追随 |
| B (対応表) | should | **採用 (小)** | 「campaign claim recorded at <時刻>」と時刻の出所を明示。限定 2 (他の read 比率・機体・pin・protocol へ外挿しない) を 1 節追加 |
| A (削除候補) | — | `check_figure_layout` の `len(plot_axes) != 2 * ncols` は冗長だが害なし → 残す (受理集合不変、削除しても変わらない = nit)。`'four'/'two'` は両枝到達で削除対象外 | 変更なし |

scope 外のまま (実装しない): producer 迂回・fixture 一般化、`validate_repo_closure` の意味検査拡張、新 gate・台帳。

## fix の分割

一枚岩 (生成器の A-6 caption + test の固定文・着地 test) → 同じ unit worktree に fix branch を切り、Codex fix 子 1 本。docs (README の文言・caption 正文・SHA 行、plotting README) と fig11 の再生成は親。

## 変異事前登録の改訂 (DW-M01、fix 前)

| id | category | 位置 | 期待 |
|---|---|---|---|
| m0-equivalent-docstring | positive | 生成器 docstring | SURVIVED |
| m1-a6-pin-drift-accepted | negative | `_load_tracked_authority` certification SHA 検査の恒真化 | KILLED: `test_a6_pin_drift_is_rejected` (+ probe で観測した同層 node) |
| m2-closure-count-fixed-12 | negative | current-full `expected_count` を 12 固定 | KILLED: A-6 6-file 正例・過不足 test |
| m3-drop-a6-caption-source | negative | `build_provenance` の caption_source 追加を無効化 | KILLED: A-6 caption_source test (+ CLI 3 成果物 test) |
| m4-layout-accept-any-axes | negative | `check_figure_layout` の axes 数検査を恒真化 | KILLED: wrong-axes-count test |
| m5-drop-a6-caption-literal | negative | A-6 caption の「This is not a performance certification.」文を削除 | KILLED: A-6 caption literal test (+ 着地 fig11 test = caption 不一致) |
| m6a-legacy-accepts-a6-study | negative | `accepted_studies` を profile 不問で `STUDY_PROFILES` に | KILLED: `test_a6_legacy_profile_is_rejected` |
| m6b-current-full-drops-a6 | negative | `accepted_studies` を profile 不問で `(STUDY,)` に | KILLED: A-6 正例 test 群 (fixture load / 6-file / caption / layout / CLI / 実データ / 着地) |
| m7-distinct-check-removed | negative | request / created_utc 一意検査を除去 | KILLED: `test_current_rejects_duplicate_workload_requests[request_id]` / `[created_utc]` |
| m8-landed-skip-on-missing | negative (test) | fig11 着地 test を全欠落で skip | KILLED: `test_landed_fig11_rejects_all_missing_outputs` |
| m9-a2-caption-drift | negative | A-2 current-full caption に 1 語追加 | KILLED: `test_a2_current_full_caption_is_unchanged_for_landed_fig6` |

期待 node の完全集合は probe (全件 SURVIVED 登録) の観測で確定し、final で照合する。
