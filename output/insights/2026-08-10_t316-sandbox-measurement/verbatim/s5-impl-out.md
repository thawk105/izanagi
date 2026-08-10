## 総括

実装済み・未実走です。計算ノード probe の投入、commit、`docs/` 編集は行っていません。

作成・変更ファイル:

- [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1)
  - S1〜S7 の fail-soft 実測、外側正例付き負制御、create-only receipt、trace-disabled S7。
- [t316_sandbox_backend_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:1)
  - 指定 PBS 資源、環境検査、Python 3.10 固定と shim。
- [t316_sandbox_backend_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/policies/t316_sandbox_backend_v1.json:1)
  - 90 分 walltime、各段予算、S7 契約。
- [registry_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/policies/registry_v1.json:1)
  - T316 policy を登録。
- [admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/admission_registry.json:1)
  - probe/PBS を `dispatch-required` で登録。
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:1)
  - S3/S5 の正例失敗、未実行、4 脅威の containment failure、総合 `no-go` を独立検査。

純粋 verdict 核は `tools/pegasus/probes/t316_sandbox_backend_probe.py` の次の関数です。

- `_paired_verdict`
- `_merge_stage_verdicts`
- `verdict_s1`〜`verdict_s7`
- `aggregate_verdicts`

親が投入する正確な command:

```bash
qsub -v "IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache,IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps,HTTPS_PROXY=${HTTPS_PROXY},SSH_AUTH_SOCK=${SSH_AUTH_SOCK}" tools/pegasus/probes/t316_sandbox_backend_probe.pbs
```

親が与える環境変数は次の4個だけです。

- `IZANAGI_PEGASUS_THIRDPARTY_CACHE`
- `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT`
- `HTTPS_PROXY`
- `SSH_AUTH_SOCK`

`PBS_JOBID` と `PBS_O_WORKDIR` は PBS が供給します。

検査結果:

- Python AST、JSON parse、PBS `bash -n`、`git diff --check`: 成功。
- admission registry の共有 loader 読込: 成功。新規2 entry はともに `dispatch-required`。
- verdict 核の直接 smoke: `go`、S5 containment failure の `no-go`、総合 `no-go` を確認。
- `python3.10 tools/run_tests.py orchestrator/tests/test_t316_sandbox_probe.py -q`: `rc=16`。runner の自動 dispatch が `qstat -Q preflight rc=1` で停止し、pytest の収集前だったため実走 nodeid は0件です。
- 指定 meta-test も同じ実行基盤制約のため未実走です。
- `qsub`、`qstat`、`qdel` は直接実行していません。上記 `qstat` は test runner 内部の preflight です。

親 docs／commit 未 land による期待赤:

- `orchestrator/tests/test_check_docs.py`: runbook の admission 投影表に新規2 pathがまだない。
- `orchestrator/tests/test_hooks.py`: admission registry の既存閉集合 fixtureに新規2 pathがまだない。
- `orchestrator/tests/test_pegasus_policy_registry.py`: 新規 policy が未 tracked。親の stage/commit 後に解消予定。
- `orchestrator/tests/test_claude_transport.py::test_committed_policy_matches_independent_literal_hash_and_registry`: policy registry の独立 literal が旧閉集合。
- 既存テストの期待値は指示どおり変更していません。

所有外への波及は、`hooks/guard_bash.py`／`tools/pegasus_admission_registry.py` が新規実行体を login で拒否すること、`tools/check_docs.py` の投影検査、上記 policy registry consumer です。共有 fixture、production sandbox、`external/ccbench`、`docs/` は未変更です。

既知の限界:

- 実計算ノードでは未実走です。直接 network や SSH agent の外側正例が成立しない環境では、仕様どおり `inconclusive` になります。
- S6 は開始時に残り3000秒を要求し、各 build cap の直列和は最大2700秒です。届かなければ `blocked`。
- S7 は残り300秒を要求し、内外各90秒です。S6失敗または残時間不足なら `blocked`。
- S1〜S5の予約900秒、S6最大2700秒、S7最大180秒に対し probe deadlineは5100秒、PBS walltimeは5400秒です。通常は約1320秒の余白がありますが、filesystem遅延や依存 buildのcap超過ではS6/S7が未到達になる可能性があります。
- S7は単一 build・単一対の elapsed overhead 比であり、絶対 throughputやCC性能の主張には使いません。