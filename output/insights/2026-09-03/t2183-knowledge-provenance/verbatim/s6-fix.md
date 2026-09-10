## 実装結果

FX1・FX2・FX3・FX5、および FX4 のコード／テスト部分を実装しました。commit・`git add` は行っておらず、作業ツリーには次の 4 ファイルだけが残っています。

- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:765)
- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:197)
- [test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:347)
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:1892)

refuted 所見の semantic validator と knowledge-aware legacy 欠落補正は実装していません。

## 対応表

| FX | 状態 | 根拠 |
|---|---|---|
| FX1 | closed | canonical/verified を別値で返す共通 validator [wal.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:817)、別 origin からの射影 [wal.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:986)、正例 [test_p3_s4_loop.py:1892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:1892) |
| FX2 | closed | 一致検査を維持 [wal.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:879)、単一理由負例 [test_p3_s4_loop.py:1910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:1910) |
| FX3 | closed | 同一 read の raw digest [wal.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:765)、artifact-ref 束縛 [layer3_report.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:197)、正負例 [test_layer3_report.py:1855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1855) |
| FX4 | partial | M3/M4 の独立 specimen [test_layer3_report.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:347)、独立検査 [test_layer3_report.py:1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1788)、M7 再照準 [test_layer3_report.py:1836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1836)。repo 外の read-only `mutation-prereg.md` は未更新 |
| FX5 | closed | baseline-valid を先に通す4負例 [test_layer3_report.py:1808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1808) |

regressed はありません。

## 受理・拒否の含意

- FX1 受理の含意: 無し。  
  FX1 拒否の含意: 無し。

- FX2 受理の含意: 無し。  
  FX2 拒否の含意: 製品入力としては無しだが、canonical と異なる自己整合済み verified source をテスト退行として新たに止めます。

- FX3 受理の含意: 無し。  
  FX3 拒否の含意: provenance 検証後から `artifact_refs` 読取前までに受領証 bytes が変わった knowledge-aware campaign が新たに止まります。

- FX4 受理の含意: 無し。  
  FX4 拒否の含意: 製品入力としては無しで、M3・M4・検証済み WAL 射影へ差し替える M7 を単一理由で止めるテスト構造になります。

- FX5 受理の含意: 無し。  
  FX5 拒否の含意: 製品入力の純増は無く、source/identity 未知 key、空配列、重複配列を受理する schema 退行が新たに止まります。

## 正例

各正例は実装済みですが、今回の変更後は pytest child が起動できなかったため未実走です。

- FX1: `test_validated_receipt_keeps_both_source_origins_distinct`
- FX2: `test_knowledge_material_report_reader_projects_verified_receipt_sources`
- FX3: `test_artifact_refs_accept_validated_knowledge_receipt_digest`
- FX4: `test_schema_accepts_independent_knowledge_provenance_specimen`
- FX5: `test_schema_accepts_independent_knowledge_provenance_specimen`

## 検査

実走した pytest nodeidはありません。焦点走と collect-only の両方を `tools/run_tests.py` 経由で試しましたが、`qstat -Q` の socket error により rc=16、`child_started=false` でした。親の既走結果は変更前 baseline なので、今回の緑には数えていません。

未実走範囲は、指定した12 selector・16 node、変更した2 test file全体、および下記 consumer 群です。

静的検査は成功しました。

- `git diff --check`
- 変更4 Python fileの AST parse
- `_checked_knowledge_provenance`、`validate_knowledge_provenance_bindings`、`_append_record` が対象 commit と AST 一致
- `layer3_schema.json` が対象 commit と一致
- `SCHEMA_VERSION=v3`、top-level required 16件が不変
- `content_utf8` の追加なし
- staged diffなし、禁止 pathの差分なし

## 波及可能性

production caller は `render`／`build_accepted_report` と `autonomous_trial_completeness._fresh_layer3_for_comparison` です。新しい拒否は knowledge-aware campaign に限定され、非 knowledge 経路は従来どおり receipt を読みません。

共有 fixture `_campaign`、`_knowledge_campaign`、`_knowledge_diff_reject_records` の既存定義・既定経路は変更していません。

未実走の所有外 consumer test は静的検索上、`test_autonomous_trial_completeness.py`、`test_ccbench_spawn_sites.py`、`test_layer3_admission_diagnosis.py`、`test_official_perf_closure.py`、`test_p3_autonomous_workload_trial.py`、`test_s8b_oracle_driver.py`、`test_s8c_acceptance_receipt_v2.py`、`test_t126_pegasus_tools.py`、`test_t126_qualification_artifacts.py`、`test_trial_registry.py` です。

## 判断に迷った点

[mutation-prereg.md](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/mutation-prereg.md:56) は workspace 外の read-only 射影で更新できませんでした。親側での M7 更新内容は「材料レポートの欄を、live receipt を読まず検証済み WAL projection から生成する変異。通常値は schema-valid で、受領証差替え負例だけが KILL する」です。

## 総括

4ファイルに FX1・FX2・FX3・FX5 と FX4 の実装／テスト部分を残しました。禁止対象・schema・WAL payload・受領証・既存期待値は不変で、commit／stage はしていません。pytest は infrastructure failure のため実装済み・未実走、FX4 は外部 prereg 更新だけ partial です。