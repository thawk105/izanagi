# [T-2773] 段 6 裁定 — レビュー A / B の所見 (2026-09-19 23:36 JST)

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 / B1 | 両 must-fix | `test_mocc_template_checks_are_input_derived` に全 30 check の「成立入力 → 1 箇所破壊で当該 key が False」対照が無い。M8 (DQ subtype 比較の削除) と tools の Bash 混入 (projections 欠落で別理由 False) を検出できない | **real**。放置時: check の弱化 (subtype 無視・tools 比較削除) が test を通り、誤った拒否 subtype を記録した JSON でも `all_pass` が true になりうる | **採用 → fix F1** |
| A3 | nit | R1 の X 恒偽化対照が `(false && A) \|\| B` で全体の恒偽化になっていない。各対照が固定の理由 (added_body / operation_contexts / line_restorations) で落ちることを個別に要求していない | real (nit) | **採用 → fix F2** (同じ test file、小) |
| A2 | nit | OFF の `.text` 2 行差 (`ERR` の `__LINE__`) は R4 の限定 identity と矛盾せず must-fix ではない。統合報告に限定を明記 | real (記録) | 採用 → insight「主張しないこと」に書く (R-A2) |
| A5 | nit | author 報告と統合版の時点差 (adapter は親の別 commit で補完、liveness-run-1 は失敗 log)。虚偽ではない | real (記録) | 採用 → insight に時系列を書く |
| B2 | must-fix | liveness-run-1 の rc=2 (「旧計装が template 適用後に当たる」) と author 報告 (rc=1) の矛盾 | **refuted (欠陥ではない)**: attempt 1 は親 script が GNU `patch --dry-run` (fuzz 2、offset 許容) を使ったため hunk 1 が fuzz 1 で当たった。driver・author は `git apply --check` (厳密)。attempt 2 (`liveness-run-2.log`、B には渡っていなかった) で `git apply --check` へ直し rc≠0 を確認、R11 の全 build を完走 (rc=0)。実装差分に帰属しない (DW-O06 の精神) | 不採用 (記録のみ)。DW-O12 で「attempt 1 = script 側の fuzz、attempt 2 = 正」を worklog へ |
| B4 | nit | 親が `liveness-run.sh` を書いたのは R20 / D95 決定 2 の所有逸脱 | real (逸脱の記録)。理由 = author sandbox が job dir へ書けない (Errno 30 と同型)。script は repo に入れず計測操作に限る。修正資材が要れば Codex author | 採用 → DW-O12 記録 + 段 8 候補 (job dir 資材の所有を裁定で親へ置く) |
| B3 / B5 / B6 / A4 | nit / refuted | pin 3 箇所・登録簿閉包・鍵・束縛に欠落なし。焦点走は受入全走ではない | refuted / 記録 | 記録のみ |

fix 単位 = 1 (test file 1 本、所有 = `orchestrator/tests/test_mocc_template_proof.py` のみ)。一枚岩の理由: 2 所見とも同一 test file 内の対照追加で、production code は変えない。fix は wave worktree 内 (dispatch なし、compute 済み) で Codex fix 子が行う。fix 後: 焦点再レビュー 1 本 (DW-S06-C) は変異 matrix と焦点走で裏取りして省く (wave 1 と同じ)、または実測次第で投じる。
