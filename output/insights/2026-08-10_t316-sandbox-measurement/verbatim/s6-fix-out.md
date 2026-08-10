偽 GO 経路を fail-closed 化しました。ただし指定テストは実行基盤障害で pytest 開始前に停止したため、所見はすべて「実装済み・未実走」の `partial` 判定です。commit、docs 編集、PBS 操作は行っていません。

## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | 構造化 sentinel の `REACHED` / `DENIED:<errno>` を必須化。sentinel 欠落、未知 errno、bwrap setup failure、timeout は `inconclusive`。 |
| F2 | partial | pidfile を読み、namespace PID・host PID・starttime・token を束縛。生存は `no-go`、identity 不明は `inconclusive`。 |
| F3 | partial | infinite loop を C++ 子孫 PID の消滅確認へ変更。単なる timeout を GO 根拠にしない。 |
| F4 | partial | compute hostname、`PBS_NODEFILE`、`PBS_JOBID`、expected commit/root、clean path、runtime SHAを束縛。login node は拒否。 |
| F5 | partial | outside/inside を別 path 化。`EEXIST` は拒否 errno 集合外で、RW 化時は `no-go`。 |
| F6 | partial | stage ごとに `PARTIAL.json` を fsync 永続化。final は temp→fsync→`renameat2(RENAME_NOREPLACE)`→dir fsync→`COMPLETED`。 |
| F7 | partial | warm-up 分離、6 対の交互・反転順序、中央値/MAD、前後単独性、perf event、単一 process の実効 thread 数を検証。 |
| F8 | partial | runtime/build の両 profile で脅威4種を測定。build profile で `std::system` が成立すれば `no-go`。 |
| F9 | partial | 親から proxy/SSH socket を受け取らない。proxy URI はscheme/host/portのみ。SSH正例は計算ノード内の制御 UNIX socket。 |
| F10 | partial | outside build 正例を追加。CCBench・依存 source の HEAD、tree SHA、dirty/untracked、replace refsを検査。 |
| F11 | partial | Python 3.10 shim を sandbox PATH に配置。Python/cmake/compiler の path・SHA・versionとsandbox解決を記録。numactl/perf欠落は `blocked`。 |
| F12 | partial | 独立 category literal、runner seam、observer→judge→overall、優先順、S4/S6/S7、atomic writerの負テストを追加。 |
| F13 | partial | DNS対象を常に名前解決が必要な `example.com` とし、proxy数値IPと分離。 |
| F14 | partial | profile 固定値を `declared_configuration_*` と明記。 |
| F15 | partial | `r3_1_coverage` で discharge済み／未済みを列挙し、overall GOがR3-1完了を意味しないことを固定。 |

集計: `closed=0 / partial=15 / regressed=0`。未実走なので closed とは申告していません。

編集ファイル:

- [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:80)
- [t316_sandbox_backend_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:8)
- [t316_sandbox_backend_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/policies/t316_sandbox_backend_v1.json:1)
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:23)
- [test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_hooks.py:1293) — 許可された2 entryの追加のみ

検査結果:

- `python3 tools/run_tests.py orchestrator/tests/test_t316_sandbox_probe.py -q`
  - `qstat -Q preflight rc=1`、`run_tests.py rc=16`
  - pytest collection前に停止。実走 nodeid は0件、pass主張なし
- Python AST / JSON、`bash -n`、`git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: `違反なし`

親がcommit後に実行する正確な投入 command:

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure &&
qsub -v IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache,IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps,IZANAGI_T316_EXPECTED_COMMIT="$(git rev-parse HEAD)",IZANAGI_T316_EXPECTED_WORKTREE_ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure tools/pegasus/probes/t316_sandbox_backend_probe.pbs
```

親が渡す環境変数は正確に次の4個です。

- `IZANAGI_PEGASUS_THIRDPARTY_CACHE`
- `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT`
- `IZANAGI_T316_EXPECTED_COMMIT`
- `IZANAGI_T316_EXPECTED_WORKTREE_ROOT`

`HTTPS_PROXY` と `SSH_AUTH_SOCK` は渡しません。`PBS_JOBID`、`PBS_O_WORKDIR`、`PBS_NODEFILE` はPBS固有変数です。現在は対象5ファイルがdirtyなので、そのまま投入すると意図どおり停止します。

静的な波及先:

- caller: PBS job bodyからPython probeへの単一経路。repo内に別のT316 callerはなし
- admission: `tools/pegasus/admission_registry.json` の2 entry、`hooks/guard_bash.py`、共有registry loader
- consumer test: `orchestrator/tests/test_hooks.py`。`test_claude_transport.py` に独立literalなし
- 共有入力: `tools/pegasus/policy.json`、CCBench submodule、third-party cache/dependency roots
- receipt consumer: repo内コードには未確認。将来のinsight/proof参照は `COMPLETED` 必須

残る既知の限界は、計算ノード実走とC++ fixture compileが未実施であること、proxy/numactl/perfや正例対象が無ければ正直に `blocked` / `inconclusive` になること、S7はstock 1 binaryのwall-elapsed比だけで、variant性能、trace run、floor再較正判断を放棄していることです。