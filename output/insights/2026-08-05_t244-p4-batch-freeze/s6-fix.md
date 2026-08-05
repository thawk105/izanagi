# 実装結果

F1〜F8 を指定された 2 ファイルだけに反映しました。docs・registry・commit・stage 状態には触れていません。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| RA-1 | closed | 最大 floor を満たす batch 数区間の非空性を検査 |
| RA-2 | closed | 全 origin の runtime-head 寄与と共有 genesis を集約 |
| RA-3 | closed | cardinality の最大十進桁を batch ごとに予約 |
| RA-4 | closed | 公開 commit 経路の 2248/2249 境界を追加 |
| RA-5 | closed | 旧 event の raw 拒否・公開型不在・union 不在を固定 |
| RA-6 | partial | 再照準した assertion は追加済み。mutation anchor 検証・本走は親の担当 |
| RA-7 | closed | V14/V17/V19 を row proxy と読める名前へ改名 |
| RB-1 | closed | F1 と同じ partition 存在検査 |
| RB-2 | closed | 合法 3・不正 9 の全 12 outcome セルを共通 oracle 化 |
| RB-3 | closed | query 名乗りと V02 の event 数を訂正 |

regressed はありません。

## F1〜F8 の実装箇所

| Fix | file:line |
|---|---|
| F1 | [reflux_origin_ledger.py:1976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1976)、[test_reflux_origin_ledger.py:2653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2653) |
| F2 | [reflux_origin_ledger.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1537)、[test_reflux_origin_ledger.py:2671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2671) |
| F3 | [reflux_origin_ledger.py:1923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1923)、[test_reflux_origin_ledger.py:2693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2693) |
| F4 | [reflux_origin_ledger.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1088)、[test_reflux_origin_ledger.py:2718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2718) |
| F5 | [test_reflux_origin_ledger.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:658) |
| F6 | [test_reflux_origin_ledger.py:1695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1695)、[同:2383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2383)、[同:2537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2537) |
| F7 | [test_reflux_origin_ledger.py:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1610)、[同:2174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2174)、[同:2509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2509) |
| F8 | [test_reflux_origin_ledger.py:2383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2383) |

## 境界 literal

既存テストの期待 literal は変更していません。追加・内部計算が変化した境界は次のとおりです。

- F1: floor `2249`
  - 正例: `batch_min=1124`、`1124 + 1125`
  - 負例: `batch_min=2248`
- F2:
  - 2-origin max: `67,103,806`
  - 1 batch 超過: `67,109,233`
  - ceiling: `67,108,864`
- F3:
  - `qmax=73,748`: `67,107,988`
  - `qmax=73,749`: `67,108,897`
  - overflow 側の旧 affine 推定は `67,108,798`、新推定は `+99` bytes。33 batches × 3 桁予約が理由です。
  - 独立 exact: cardinality 10=`11,192`、100=`93,003`、1000=`911,104`
- F4: 公開経路で 2248 受理、2249 拒否。

golden は手書き JSON、`hashlib`、標準 JSON/base64 のみで再構築しています。

## Mutation 対応 nodeid

| Mutation | 赤になる nodeid / assertion |
|---|---|
| M-9′ | `test_v18_evidence_outcome_contract_and_fixed_member_tombstones` — partial opening |
| M-10′ | 同 V18 — matching commitment を持つ unknown outcome の codec/decode/reducer |
| M-14′ | `test_v14_i_q_k_sealed_evidence_row_proxy_floor_not_physical_query_and_aborted_seal` — sealed=0、tombstoned=4 の floor 拒否 |
| M-16′ | `test_v20_preseal_projection_hides_execution_counters_and_replicates` — committed/prepared 型・payload の replicate ordinal 不在 |
| M-18a | `test_v22_authority_floor_requires_an_existing_batch_partition` |
| M-18b | `test_v25_public_commit_enforces_2248_member_codec_cardinality` |
| M-18c | `test_v24_origin_ledger_total_decimal_cardinality_max_and_max_plus_one` |
| M-19 | V22 の到達不能 floor 負例 |
| M-20 | `test_v23_two_origin_shared_runtime_head_aggregate_max_and_max_plus_one` |
| M-21 | V24 の 10/100/1000 桁境界と max+1 |
| M-22 | `test_v02_exact_five_phase_five_event_transition_matrix_and_no_legacy_tombstone` |
| M-23 | V18 の `accepted-evidence-constraint` |
| M-24 | V18 の `rejected-no-evidence-constraint` |
| M-25 | V18 の `tombstoned-no-evidence-constraint` |

上記 mutation に恒真候補はありません。裁定済み residual 4 件（物理 query 一対一、seal 前の外部漏洩、referent 実在、provider source）は新設していません。

## 検査

成功:

- `python3 -m py_compile` — 対象 2 ファイル
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

pytest は `tools/run_tests.py` で V02/V14/V18/V20/V21/V22〜V25 と `test_plain_runner_coverage.py` を計算ノードへ dispatch しましたが、`qstat -Q preflight rc=1`、runner `rc=16` で失敗しました。テスト本体は実行されておらず、緑は主張しません。

## 所有外への波及

- `_check_budget_codec_feasibility()` の戻り値を tuple にしましたが、静的検索上の caller は対象実装内の 2 箐所だけです。
- 複数 origin authority は共有 head 上限により意図的に受理集合が狭まります。
- 旧 nodeid を参照する live mutation spec、共有 fixture、consumer test は検索上 0 件でした。外部 job artifact が旧 nodeid を保持している可能性はあります。
- 既存 staged の registry v1 削除/v2 追加には触れていません。
- V24/V25 は最大 2249 member を組むため、親は計算ノードで実測してください。

## 総括

所見集計は **closed 9 / partial 1 / regressed 0** です。partial は RA-6 の mutation 本走・最終 commit anchor 検証が親担当として残るためです。

残った赤は判定不能です。pytest dispatch が rc=16 で失敗し、実テスト結果がありません。親は統合後、上記 nodeid、plain-runner meta-test、再照準済み M-9′〜M-25、対象全走を計算ノードで確認してください。