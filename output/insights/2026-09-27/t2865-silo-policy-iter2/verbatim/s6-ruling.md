# 段 6 裁定 — [T-2865] silo-function-policy 軸 2 iteration 目以降 (2026-09-27)

対象: 実装 commit `361e094f7` (Codex author) と runbook docs `0ff7645c4`。入力: 焦点走 1 回目 (31814.nqsv)、レビュー A (`s6-review-A.md`、GO、nit 2)、レビュー B (`s6-review-B.md`、NO-GO、should-fix 2・nit 2)。fix 前の統合 snapshot は job dir の `snapshot-before-fix-1.patch`。

| 所見 | 出所 | 判定 | 採否 |
|---|---|---|---|
| 計器 patch `instr-silo-function-policy-probe.patch` が新骨格に当たらない (`test_silo_policy_coverage.py` の 3 件が `git apply` rc=1) | 焦点走 1 | real (本 wave 帰属、consumer 取り残し。plan は注意していたが実装子が確認を漏らし、レビュー 2 本も拾わなかった) | fix-1 (Codex): hunk 行番号と `begin()` hunk の文脈行 1 行だけを更新、+/- 行本文は不変。変異 patch 11 本は無変更で当たる |
| `test_p3_b4_wiring_probe.py` が作業木の未 commit docs を拾う | 焦点走 1 | real だが非実装 (未 commit の runbook が原因) | docs を commit して解消 (焦点走 2 で緑) |
| 新 checkout の HEAD に seed 修正を含める確認が runbook に無い | B should-fix | real | 親が docs で修正 (§3) |
| critic 入力の抜き出し元が曖昧 | B should-fix | real | 親が docs で修正 (§1(g): 当該 pair の iteration 番号の履歴行、同じ stdout の stock 2 値) |
| 余分な H2 が節を切る | A nit | real | 親が docs で修正 (§1(g) に「他の H2 を持たない」) |
| walltime 起点の文が既出 / 実績 iteration 数の 1 行が無い | B nit | 一部 real | 「止まった系列は続けられない」は新情報なので残し、実績 iteration 数は実走後に足す |
| test の文字列検査が compile と重なる / 呼出しの完全一致が等価な書き換えで偽赤 | A・B nit | refuted (不採用) | 検出力に影響せず、脆さは許容。test を変えない |

変異: probe (clone main=`361e094f7`) で M1〜M3 が新焦点 test 1 node だけを赤にし、失敗 assert はそれぞれ別 (different thid / continued sequence / begin must seed) で単一理由を確認。final は fix 後の最終 commit `3205dd93e` の独立 clone で走らせる。fix-1 は patch の位置合わせだけで受理集合を変えないため、追加の変異は登録しない (焦点走 1 の赤→焦点走 2 の緑が検出の実証)。
