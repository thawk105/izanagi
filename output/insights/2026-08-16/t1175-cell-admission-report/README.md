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
| `mutation-spec-final.json` | 走 2 の spec | 10 変異 (negative 8 / both-layers 1 / positive 1)、期待 node は実測完全集合 |
| `mutation-result-probe.json` | 走 1 (probe) | baseline PASSED、KILLED 5 / MISMATCH 5 / SURVIVED 0 / TIMEOUT 0 |
| `mutation-result-final.json` | 走 2 | baseline PASSED、**KILLED 10 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0** |
| `mutation-spec-v2.json` | 走 3 (最終 commit の権威走) の spec | P1 のアンカーが fix4 で消えたため差し替え |
| `mutation-result-v2.json` | 走 3 (権威走) | baseline PASSED、**negative/both-layers 9 件すべて KILLED、SURVIVED 0 / TIMEOUT 0**。P1 は MISMATCH (下記 erratum) |

**走 3 が権威走である。** 走 2 の後に受入全走が帰属赤 1 件を出し (下記)、その fix で
`assert_campaign_layer3_chain` から 4 行を削除したため、P1 のアンカーが消えて
`anchor count=0` で harness が起動前に停止した。`DW-M07` に従い最終 commit で再登録・再走した。

### erratum — 走 3 の P1 は過剰決定である

差し替えた P1 (新設した failure 最終配置 gate の発火条件を `if failure_indices or True:` にする
過剰拒否変異) は **106 node** を落とした。登録した期待 node は暫定 1 件だったため MISMATCH である。
これは検出力の不足ではなく `DW-M03` が言う**過剰決定 fixture** であり、
**単独変異の証拠からは外す**。したがって本 wave の変異検出力の主張は
**「negative 8 + both-layers 1 = 9 件すべて KILLED」**までとし、10/10 とは名乗らない。

正例そのものの検出力は別に実証されている。走 1 (probe) で、chain の positive 判定へ
到達不能条件を足す変異が **正例テストを含む 13 node** を落とした。
また走 3 の P1 の失敗 node 集合にも
`test_three_workload_build_positive_admission_passes_real_layer3_chain` が含まれている。

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
| fix 第 3 巡後 | 同上 | 320 passed |
| main 合成監査後 | 同上 | 322 passed (main 側の新規テスト 2 件が加わった) |
| **受入全走 1 回目** | 全走 | **帰属赤 1 件** — `test_layer3_report.py::test_completeness_rejects_certifying_historical_admission` |
| fix 第 4 巡後 / 最終 commit | 上記 2 file + `test_layer3_report.py` | 383 passed |

## 受入で出た帰属赤 (本 wave の過剰拒否)

`[campaign-chain] cells[0] admission decision is invalid`。
本 wave が chain へ追加した positive 述語は `classification == "admitted-new-schema"` を要求するが、
これは **cell 単位** の completeness 検査の要求であって chain の受理集合ではない。
chain は `verified-post-admission-schema` の admitted も従来受理しており、当該テストの
第 1 呼び出しはその成功を明示的に期待している。

**焦点範囲では検出できなかった。** 本 wave の正例が `admitted-new-schema` の fixture しか
使っていなかったためである。受入全走で初めて出た。
fix は chain から当該 4 行を削除して受理集合を wave 前へ戻し、
`verified-post-admission-schema` / `admitted` の cell が chain を通る正例を追加した。
免除条件・`admitted` 完全一致・cell 単位検査はいずれも不変。

段 5 実装子と 3 巡の fix 子はいずれも pytest を実走できず (`qstat -Q` preflight rc=1 /
runner rc=16)、全員「実装済み・未実走」と正しく申告した。緑の偽申告はない。
