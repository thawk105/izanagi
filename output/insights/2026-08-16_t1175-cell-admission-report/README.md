# [T-1175] cell admission 失敗時の診断可能な成果物 — 逐語と変異台帳

wave: `worktree-dev-wave-t1175-cell-admission-report` / 2026-08-16 / base local main `8b060d64`

## 何を閉じたか

`orchestrator/campaign/p3_autonomous_workload_trial.py` の
`_finalize_build_cell_admission` が契約上の `AutonomousTrialError` を送出したとき、
`run_root/report.json` が 1 バイトも書かれなかった経路。
設計判断の正本は decisions の該当 D、経緯の正本は worklog の該当エントリ。

**閉じていない面:** `_write_json_atomic` 自身の I/O 失敗、journal 永続化の失敗、
`KeyError` 等の予期しない例外は従来どおり report を残さない。

## 親が読んだ一次資料 (repo 外、参照のみ)

- `/work/1/SFC/tanab/izanagi-exploration/t1112/exploration/autonomous-trials/live-abc-g1-20260816a/attempts.jsonl`
  — 5 event、`run-finish` 不在、`report.json` 不在。seq4 が `role=coder status=invalid`
  (`JSON object を読めない: coder response: Expecting ',' delimiter: line 1 column 695`)。
- 同 `.../live-abc-g1-20260816b/attempts.jsonl`
  — 7 event、seq7 が `supervisor-error type=KeyError message="'build_start'"`、
  `run-finish` 不在、`report.json` 不在。

## 逐語 (`verbatim/`)

| file | 段 | lane | 結論 |
|---|---|---|---|
| `s3-lensA.md` | 3 敵対相談 | sol | NO-GO。failure decision の自己申告で Layer 3 免除を引き出せる |
| `s3-lensB.md` | 3 敵対相談 | luna | NO-GO。関門は 4 つでなく、workload coverage が第 5 の関門 |
| `s6-lensA.md` | 6 敵対レビュー | sol | NO-GO。must-fix 4 件 (非最終 failure / accounting 未束縛 / fallback の穴 / 裁定との食い違い) |
| `s6-lensB.md` | 6 敵対レビュー | sol | NO-GO。走 a・走 b は writer に到達するが正例が無い |
| `s6-focus.md` | 6 焦点再レビュー | sol | NO-GO。R1/R2/R4 closed、R3 partial (`count in {0,1}` の穴) |

## 変異台帳

| file | 走 | 内容 |
|---|---|---|
| `mutation-spec-final.json` | 権威走の spec | 10 変異 (negative 8 / both-layers 1 / positive 1)、期待 node は実測完全集合 |
| `mutation-result-probe.json` | 走 1 (probe) | baseline PASSED、KILLED 5 / MISMATCH 5 / SURVIVED 0 / TIMEOUT 0 |
| `mutation-result-final.json` | 走 2 (権威走) | baseline PASSED、**KILLED 10 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0** |

走 1 の MISMATCH 5 件はすべて期待 node 集合の不足であり、検出力の欠如ではない。
実測 node を完全集合として再登録して走 2 を権威走とした (`DW-M08` の probe + 再登録経路)。

**正例 P1 が正例として機能することの実証:** chain の positive 判定へ到達不能条件を足す変異は、
正常 3 workload build の正例テストを含む **13 node** を落とした (走 1 の実測)。
恒真な正例ではない。

**遮蔽により再照準した変異が 2 件ある。** M4 は共通 gate に遮蔽されるため M9 (共通 gate 直撃) へ
統合し、M6 (status) は artifact gate に遮蔽されるため producer・verifier・artifact gate の
3 箇所同時変異 (`both-layers`) へ再照準した。焦点再レビューが両方を独立に指摘した。

## 親の実測 (すべて計算ノードの dispatch。login node の bounded local は輻輳で使用不能)

| 時点 | 対象 | 結果 |
|---|---|---|
| base (実装前) | `test_p3_autonomous_workload_trial.py` + `test_autonomous_trial_completeness.py` | 296 passed |
| 段 5 実装後 | 同上 | 311 passed |
| fix 第 1 巡後 | 同上 | 1 failed / 318 passed (赤は追加した正例のみ) |
| fix 第 2 巡後 | 同上 | 320 passed |
| fix 第 3 巡後 / 最終 commit | 同上 | 320 passed |

段 5 実装子と 3 巡の fix 子はいずれも pytest を実走できず (`qstat -Q` preflight rc=1 /
runner rc=16)、全員「実装済み・未実走」と正しく申告した。緑の偽申告はない。
