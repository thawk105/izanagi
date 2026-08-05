### R1-F1 — 終端 lock 再照合

[artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:614) の歴史枝と post-policy 枝の両方で、終端時に lock/WAL hash を再照合するよう復元しました。再読 bytes は拒否判定だけに使い、parse・分類・receipt は最初の `lock_raw` に固定しています。

固定するテストは `test_lock_read_snapshot_is_rechecked_against_terminal_path[historical]` と `[post-policy]`。各枝の再照合を削除すると `ArtifactAdmissionError` が出ず赤になります。

### R1-F2 — M8 境界テスト

[test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:419) で `Path.read_bytes` 注入を採用しました。tmp campaign の A を読んだ直後、path を末尾改行付き B に置換してから A を返します。

正実装は hash A と終端 B の不一致で拒否します。M8 は初回 hash を live path B から取るため、終端 B と一致して誤受理し、同テストが `DID NOT RAISE` で赤になります。

### R1-F3 / R2-4 — corpus census

[test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:300) に census を追加しました。ledger の `created_from_commit` にある全 `campaign.lock` 集合と、overlay 3件＋旧 trigger 6件＋正例21件の和集合を完全一致で比較します。

現在の snapshot は静的確認で30件です。将来の追加・列挙漏れでは `test_trusted_snapshot_campaign_corpus_is_fully_enumerated` が赤になります。

### 静的な波及範囲

所有外 caller は `critic/digest.py`、`campaign/replay.py`、`layer3_report.py`、`p3_s4_loop.py`、`s8a_trigger_sweep.py`、`s6_sort_sweep.py`、`p3_s4_red.py`、`p3_s4_loop_sort.py`、`autonomous_trial_completeness.py`。

共有 corpus/fixture と consumer test は `output/campaigns`、overlay ledger、`test_critic.py`、`test_bench_first_real_wal.py`、`test_p3_s4_loop*.py`、`test_layer3_report.py`。no-touch 対象、output、docs は変更していません。既存の親所有 decision fragment も未接触です。

## 総括

修正: 両終端の lock 再照合、A→B 注入テスト2ケース、30件 census を追加。commit は作成していません。

検査: `git diff --check` と対象3ファイルの `py_compile` は成功。`pegasus02` のため pytest／meta-test は未実行で、緑は主張しません。

残る risk: post-policy membership 穴、WAL ABA、provenance 二義化はscope外。validator SHA driftと外部 run-root の未探索限界は親の記録対象です。