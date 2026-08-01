# 段 6 変異台帳 (R5 closure)

- anchor commit: `ab09eb618803e730a2873c5265dac5caca0e6096`
- 実行環境: Pegasus gen_S 計算ノード `bnode021`、`/usr/bin/python3.10`、`pytest -n 16`
- 対象 suite: `orchestrator/tests/test_pegasus_test_dispatch.py` (81 node)
- harness 規律: 単一 anchor 検査 (置換対象がちょうど 1 箇所)、注入実在検査 (mutated != source)、
  復元は内容比較 (`read_text() == 元ソース`)、赤 node 名を毎回記録 (`DW-M03`〜`DW-M08`)
- BASELINE: rc=1 / 3 failed / 78 passed。3 赤は継承済みの U2 自己不整合であり本 wave の scope 外

## 本走 (9 変異)

| ID | 単一変異 | 結果 | 新たに赤くなった node |
|---|---|---|---|
| R1 | witness ゼロの resume を fail-closed にしない | **KILLED** | `test_resume_refuses_a_submit_receipt_no_hash_bound_evidence_witnesses` |
| R2 | `qsub.stdout` witness の照合を外す | **KILLED** | `..._job_id_absent_from_qsub_stdout` / `..._raw_prefix_absent_from_qsub_stdout` |
| R3 | accounting footer の `Group Name` 照合を外す | **KILLED** | `test_monitor_rejects_accounting_group_other_than_policy_account` / `test_resume_rejects_published_final_sealed_with_a_foreign_group` |
| R4 | final 再検証の group 束縛を `queue` へ差替 | **KILLED** | `test_real_filesystem_final_receipt_rechecks_accounting_group_on_resume` |
| R5 | monitor の group 束縛を `queue` へ差替 | **KILLED** (診断 pin) | 10 node (positive control 群 + 既存 resume 系) |
| R6 | lookup candidate の group 照合を外す | **KILLED** | `test_resume_rejects_lookup_wal_candidate_from_another_group` |
| R7a | `submit-identified` WAL witness の照合を外す | **KILLED** | `..._forged_receipt_when_qsub_stdout_cannot_be_parsed` / `..._absent_from_submit_identified_wal` |
| R7b | matched lookup candidate witness の照合を外す | **SURVIVED** | — |
| R8a | monitor 入口の snapshot policy 束縛を外す | **KILLED** | `test_monitor_refuses_a_caller_policy_whose_group_left_the_snapshot` |

- 集計: **killed 8 / survived 1 / abort 0**、復元失敗 0 (走行後 `git status` clean)
- R5 は裁定 2 のとおり **冗長 gate の診断 pin** であり、closure の証拠には数えない (`DW-M08`)
- R6 の入力は製品が書けない WAL 行 (段 6 レビュー B の RB-5) なので、成果物影響は書けない。
  fail-fast と対称性回復の pin として数える

## R7b 生存の裏取り (`DW-M02`)

他層 mask と等価変異を疑い、両層同時変異まで実行した。

| 変異 | 内容 | 結果 |
|---|---|---|
| L1 単独 | R7b と同一 (`if lookup_identity != ... :` → `if False:`) | SURVIVED |
| L2 単独 | resume の `matched_results` 選択 filter から `candidates[0]["job_id_normalized"] == normalized` を外す | SURVIVED |
| L1+L2 | 両層同時 | **SURVIVED** |

両層同時でも生存したため、**他層 mask ではなく真の被覆欠落**と確定した。matched lookup
candidate の identity が receipt と食い違う入力を作る test が 1 件も存在しない。

到達可能な唯一の不一致形は raw 表記のみである。選択 filter が
`candidates[0]["job_id_normalized"] == normalized` を、`_policy_bound_lookup_candidate` が
`candidate["job_id_normalized"] == normalize_job_id(raw)` をそれぞれ要求するため、candidate の
raw は必ず receipt の normalized へ正規化される。`normalize_job_id` が `0:` 接頭辞を落とすので、
`0:123.nqsv` と `123.nqsv` の差だけが R7b の照合を実際に発火させうる。

→ 実効 gate へ再照準し、fix 第 2 巡でこの形の expected-red を 1 件追加した。
**初回の SURVIVED 結果は消さず、本節を erratum として残す。**
