## 総括

閉包を 21 module / 30 site へ補完し、共有 `_resolve_duplicate()` を admission helper へ結線しました。  
legacy 実 WAL は拒否、正規 receipt 付き合成 WAL は受理する回帰を対で追加しました。  
例外種別は証拠不足のみ `ArtifactAdmissionError` へ是正しました。  
duration ledger は実測不能のため未変更で、B-03 のみ partial です。commit は作成していません。

## 1. _resolve_duplicate の結線 (file:line、拒否時に success を書かない根拠)

[p3_s4_loop.py:1034](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_s4_loop.py:1034) で次の snapshot 契約を実装しました。

1. lock bytes を取得して SHA-256 を導出
2. WAL records を一度読み取り
3. lock を再取得して SHA 一致を要求
4. 同じ records 内の COMMIT record を helper へ渡す

[p3_s4_loop.py:1111](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_s4_loop.py:1111) の helper が成功した場合だけ `commit_admitted=True` となり、success 射影は [同:1120](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_s4_loop.py:1120) 以下へ限定されています。拒否時は [同:1135](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_s4_loop.py:1135) から `project_whiteboard(..., "fail")` へ進み、caller が [同:1645](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/p3_s4_loop.py:1645) で保存する checkpoint にも fail が残ります。

回帰は [test_p3_s4_loop.py:5292](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_p3_s4_loop.py:5292) に追加しました。

`test_resolve_duplicate_rejects_uncertified_commit_without_success_checkpoint[invalid-receipt]`

lock 変更競合も [同:5330](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_p3_s4_loop.py:5330) で fail 側へ固定しています。

## 2. bench_first_real_wal の期待値変更と、対で追加した正例

拒否側:

`orchestrator/tests/test_bench_first_real_wal.py::test_real_wal_backoff_repro_bench_tps_requires_certified_commit_receipt`

[実 WAL の legacy COMMIT を `ArtifactAdmissionError` として拒否](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_bench_first_real_wal.py:440)します。

正例側:

`orchestrator/tests/test_bench_first_real_wal.py::test_synthetic_wal_backoff_repro_bench_tps_accepts_certified_commit_receipt`

[同一 attempt の正常 verify と正規 receipt を持つ合成 WAL](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_bench_first_real_wal.py:452)では `_bench_tps()` が `8470959.0` を返します。実 artifact は変更していません。

## 3. duration ledger の追随手順と、親に必要な実測

partial です。[台帳の旧 critic node](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/acceptance_duration_ledger.json:4911)は未変更です。

契約上、次が必要です。

1. `tools/run_tests.py` 経由で現行 acceptance collection を実走し、全 shard の JUnit を生成
2. `tools/update_acceptance_duration_ledger.py JUNIT... --repo <repo> --output orchestrator/tests/acceptance_duration_ledger.json --coverage-against <collection>` で全置換
3. critic は frozen suite のため `--add-only` は使用不可
4. 新規 5 node と改名済み critic node の実測 duration が必要
5. 所有外の `test_update_acceptance_duration_ledger.py` にある critic exact-set hash も追随が必要

今回の rename だけを反映した critic 集合は、静的計算では `121 / c4b9a37fd0a0c0f90e91222ed0db4a181510a94856cb2f246b025da8c5e68168` です。実測値は流用・捏造していません。

## 4. 例外種別の是正 (受理集合が変わらないことの根拠)

[artifact_admission.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:665) の非空 exact `str` 検査はそのままで、失敗時の型だけを `TypeError` から `ArtifactAdmissionError` へ変更しました。

非 COMMIT record と records 非所属 COMMIT の caller misuse は [同:656-664](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/campaign/artifact_admission.py:656) で引き続き `TypeError` です。したがって採用 7 述語と受理集合は不変です。

負例は [test_artifact_admission.py:1450](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2061-wal-admission/orchestrator/tests/test_artifact_admission.py:1450) に追加しました。

## 所見ごとの closed / partial / regressed 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| B-01 `_resolve_duplicate()` 閉包漏れ | closed | snapshot 契約と helper を共有実装へ結線 |
| B-02 legacy 実 WAL の旧期待値 | closed | 拒否側へ変更し、正規 receipt の正例を追加 |
| B-03 duration ledger | partial | 実測・生成器実行が不能のため未変更 |
| 例外種別の是正 | closed | 証拠不足だけ `ArtifactAdmissionError` 化 |
| regressed | なし | 静的に確認した範囲ではなし |

## 実走した pytest の nodeid と結果

実走済み pytest はありません。

`tools/run_tests.py` で exact 4 node を指定しましたが、Pegasus の `qstat -Q` が `Unknown user-id` となり `rc=16`、`child_started=false` でした。直接 pytest には迂回していません。

非 pytest 検査:

- 変更 5 file の `py_compile`: 成功
- production/test module の import smoke: 成功
- `git diff --check`: 成功

## 未実走・未完の範囲

- 変更した全 pytest node
- `_resolve_duplicate` の既存回帰群
- duration ledger の実測生成
- ledger 更新後の exact node-set hash gate
- 親が提示した 3 test group の再走

## 所有外への波及可能性 (静的列挙)

- `p3_s4_loop_sort.py` と `p3_s4_loop_trigger_gating.py` は共有 `_resolve_duplicate` の re-export により動作だけ追随します。編集していません。
- `p3_b4_closed_critic.py` は `p3_s4_loop.py` と `artifact_admission.py` の source bytes を closure に含めます。
- `campaign_lock.py` の verifier closure は `artifact_admission.py` の変更により identity が変わりますが、既存 artifact bytes は変更していません。
- `acceptance_duration_ledger.json` と、所有外の `test_update_acceptance_duration_ledger.py` の critic exact-set hash は親による実測後の追随が必要です。