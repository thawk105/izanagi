実装済み・未実走です。所有6ファイルだけを変更しました。docs編集、git add/commit、qsub、測定投入は行っていません。

変更ファイル：

- [policy](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/orchestrator/campaign/paper_story_a2_certification.v2.json)：`scheduler.nodes`だけ5へ変更。
- [certification test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/orchestrator/tests/test_paper_story_a2_certification.py)：literal pin 2箇所、6呼出しのhost fixture、A-2/A-6の正負例を更新。protocol pinは維持。
- [job contract test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/orchestrator/tests/test_paper_story_a2_job_contract.py)：5node nodefile、exact qsub argv、両study・unset/親lock指定・別job scratchの継承試験を追加。
- [job body](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/tools/pegasus/paper_story_a2_certification.sh)：`mkdir -p "$scratch_base"`直後に固定`bench.lock`のexportを追加。採否未決の候補です。
- [probe Python](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/t2489_lock_probe.py)、[PBS](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/t2489_lock_probe.pbs)：rank0/rank1間の通知同期、別processのreal `bench_lock`、create-only JSON保存を実装。

新policy SHA256は`f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c`です。共通policy fixtureは5nodesのまま、単一nodeは専用test内だけで明示しています。既存のpin・staged source・source roleの拒否理由とpredicate観測assertは維持しました。

親投入用argvです。先にqueue状態を確認し、次の出力directoryを**新規作成**してください。再投入では別directoryを使います。

```bash
qsub -A SFC -q gen_S -b 2 \
  -l elapstim_req=00:05:00 -N t2489-lock \
  -v T2489_REPO_ROOT=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author,T2489_PROBE_OUT=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/probe-20260919a \
  -o /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/probe-20260919a/job.stdout \
  -e /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/probe-20260919a/job.stderr \
  /work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/t2489_lock_probe.pbs
```

probeは候補pathを実job bodyの検証済み代入行から取得します。同node候補間の保持中拒否・解放後成功、別node候補間の成功、default間の同node/別node拒否を要求します。交差path両方向は観測として保存し、成功を失敗扱いしません。defaultの事前取得が拒否された場合はinconclusive非0です。

観測の限界：

- 継承harnessのgit・hostname・qstat・mkdir/cp・compute-preflightと最終workloadはstub/captureです。環境到達確認であり、排他証拠ではありません。
- probeは同一予約内の別process・別scratchを検証します。独立scheduler job間の名前空間共有、workerや他launcherとの全面的排他、性能改善は証明しません。
- 45秒の待機上限はprobe専用です。production timeoutは変更していません。

変異anchor／親実走nodeid（以下のファイル名は`orchestrator/tests/`配下）：

- **M1**：policyの`nodes: 5→1`
  `test_paper_story_a2_certification.py::test_p1_a2_default_policy_bytes_and_protocol_are_unchanged`
- **M2**：driverの`_validate_verify_fanout_hosts`内`len(hosts) != expected`拒否の無効化
  `test_paper_story_a2_certification.py::test_verify_fanout_hosts_reject_invalid_binding[a2-too-few]`、`[a2-too-many]`、`[a6-too-few]`、`[a6-too-many]`
- **nodefile閉包**：
  `test_paper_story_a2_job_contract.py::test_m9_job_body_rejects_nodefile_sibling_count_mismatch`全6ケース
- **M3/M4・候補採用時のみ**：export削除／`$scratch/bench.lock`置換
  新設`test_paper_story_a2_job_contract.py::test_job_body_fixed_lock_reaches_run_workload_across_job_scratch`全4ケース

テスト関数の改名はありません。host負例のparam IDを明示し、studyのparameterを追加しました。関連meta-testは以下で、すべて未実走です。

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

所有外への波及は、共通job bodyを使うA-6 policy、policyからargvを生成するsubmitter、既存receipt fixture、duration ledgerのparameter IDです。plot consumerは凍結artifactを参照するため、そのbytesを更新していません。

Python 3ファイルとcapture wrapperのAST解析、policy hash確認、`git diff --check`は完了しました。pytest、meta-test、変異、probe、全走は未実施で、テストの緑は報告していません。`bash -n`はPreToolUse hookがdispatch-required実行体として拒否したため未確認です。親docsによる期待赤はなく、今後の赤は回帰として調査対象です。

## 総括

nodes=5の整合変更とlock候補・probeを実装しました。親による正規テストと計算ノード実測、lock採否判断が残っています。
