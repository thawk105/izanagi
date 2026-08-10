## 実装した変更

- [tools/spool_fold.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:57)
  - literal `F<n>`、R2 の署名、暦日を検査する regex を追加。
- [tools/spool_fold.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:228)
  - `_FailureSupersede` を追加。
- [tools/spool_fold.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:687)
  - `supersede 追記` の節順、空節、raw 物理行 shape、暦日、`再発` 誤用を検査。
- [tools/spool_fold.py:1598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1598)
  - 本文 placeholder 解決後の supersede payload を抽出。
- [tools/spool_fold.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1663)
  - fold が `- ` を付与し、target 不存在・canonical 重複・exact 行重複・fold 内重複を拒否。
- [tools/spool_fold.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1720)
  - 描画前後の F-ID 列を検査する `failure-topology` postcondition を追加。
- [tools/spool_fold.py:1988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1988)
  - `再発 → supersede → 新規 F 追加` の適用順を配線。
- [orchestrator/tests/test_spool_fold.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:171)
  - failures fragment helper を純増。
- [orchestrator/tests/test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093)
  - R1〜R7、全 issue code、決定性、replay、実 canonical 3 境界、CLI dry-run、M1〜M10 を固定するテストを追加。
- [orchestrator/tests/test_check_docs.py:1696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_check_docs.py:1696)
  - supersede validate issue が check_docs finding になる consumer test を追加。
- [orchestrator/tests/test_dev_wave_land.py:2240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_dev_wave_land.py:2240)
  - 既存 helper で実 spool fold を構成できたため、lock 内 supersede fold テストを追加。

## 現行の受理・拒否挙動と、本変更による差分

変更前は `新規`、`再発`、`新規 → 再発` のみ受理し、`再発` payload は任意文字列でした。そのため supersede は書けても再発として誤記録され、専用節は拒否されていました。

変更後は次を追加します。

- `新規 → 再発 → supersede 追記` の任意部分列を受理し、supersede 単独も受理。
- item は `- F<n> **supersede: YYYY-MM-DD** — <非空本文>` の1物理行だけを受理。
- canonical では fold が list marker を付け、F エントリ末尾へ挿入。
- literal target、exact 行重複、暦日、F topology を検査。
- 既存 `新規`／`再発`／worklog／decisions の受理・描画は維持。既存受理集合を縮小する例外は、裁定どおり `再発` の可視行が `- **supersede:` で始まる場合だけです。

## 走らせた検査

緑を確認できた検査:

- `python3 -m py_compile`、変更4ファイル: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`: rc=0

pytest はすべて「実装済み・未実走」です。`tools/run_tests.py` 経由で以下を試行しましたが、いずれも pytest 起動前に rc=16 でした。

- `orchestrator/tests/test_spool_fold.py` の supersede/topology/CLI 新設範囲
- `orchestrator/tests/test_check_docs.py::test_dev_wave_new_gate_case_registration_is_complete`
- 新設 consumer・land・主要 mutation nodeid 7 本

停止理由は `qstat -Q preflight rc=1`。直接確認では `NQSconnect: [API EACCTAUTH] Unknown user-id` でした。pytest 実行件数は 0 で、緑は主張しません。

## 変異 M1〜M10 に対する対応表

すべてテスト実装済み・未実走です。

| 変異 | kill nodeid |
|---|---|
| M1 | `test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact` |
| M2 | `test_failure_supersede_real_f196_f197_boundary_is_byte_exact` |
| M3 | `test_failure_supersede_real_final_entry_eof_is_byte_exact` |
| M4 | `test_failure_recurrence_precedes_supersede_for_same_target_byte_exact` |
| M5 | `test_failure_supersede_substring_of_existing_line_is_accepted` |
| M6 | `test_failure_supersede_body_shape_and_calendar_date_are_rejected` |
| M7 | `test_failure_topology_rejects_forged_heading_from_recurrence` |
| M8 | `test_failure_recurrence_supersede_misuse_is_rejected_but_prose_mention_is_accepted` |
| M9 | `test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact`、`test_failure_list_marker_neutralizes_heading_if_shape_gate_regresses` |
| M10 | `test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact` |

## 波及可能性

- `tools/check_docs.py` の spool guardは、新しい validate issue を `spool <code>` finding として返します。
- `tools/dev_wave_land.py` の lock 内 `plan_fold`／`apply_fold` は、supersede 挿入・fragment GC・fold commit の対象になります。
- `tools/spool_fold.py --dry-run` は semantic issue を rc=1 JSON として返し、書き込みません。
- `FOLDED.md` の receipt schema、transaction state、allocation schemaは変更していません。
- 共有 fixture `_repo`、`_fragment`、`_copy_real_canonical_family` の既存定義・期待値は変更せず、専用 helperのみ追加しました。
- 所有外 production callerは `tools/check_docs.py` と `tools/dev_wave_land.py`。両 consumer testを追加済みです。

## docs 未更新に起因する予想赤

予想 finding 集合は空集合です。実際に `python3 tools/check_docs.py` は rc=0 でした。

README と `docs/failures.md` の意味上の記述不足は checker が検査する契約ではないため、docs 未更新だけでは赤になりません。親による正本更新は引き続き必要です。

## 要裁定 / 未実装

- 要裁定となる既存 nodeid・期待値変更はありません。
- pytest、変異実走、受入全走は dispatch 基盤の rc=16 により未実走です。
- docs 3ファイルと F196 fragment は親の担当として未編集です。
- A4 の rollback 欠陥は裁定どおり scope 外です。
- commit は作成していません。

## 総括

指定された4ファイルだけを変更し、R1〜R7、全 issue code、consumer／CLI／land 経路、M1〜M10 のテストを実装しました。静的検査と必須 check_docs は rc=0ですが、pytest は基盤障害により未実走のため、完了状態は「実装済み・未実走」です。