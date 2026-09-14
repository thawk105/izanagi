# 実測 1 — t316 probe を計算ノードで走らせた結果 (2026-09-14)

## 投入

worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert` (HEAD
`3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a`、BOUND_PATHS 5 件 clean) から、probe を **1 byte も
変えずに**投入した。

```
qsub -N izdw-t316 -v IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache,IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps,IZANAGI_T316_EXPECTED_COMMIT=3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a,IZANAGI_T316_EXPECTED_WORKTREE_ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert tools/pegasus/probes/t316_sandbox_backend_probe.pbs
```

応答: `Request 996644.nqsv submitted to queue: gen_S.` (rc=0)

## 実行束縛 (receipt の `execution_binding` 逐語)

| field | 値 |
|---|---|
| `PBS_JOBID` | `0:996644.nqsv` |
| `hostname` | `bnode040` |
| `PBS_NODEFILE_entries` | `['bnode040']` |
| `expected_commit` | `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a` |
| `observed_commit` | `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a` |
| `bound_paths_clean` | `True` |
| `login_node_rejected` | `True` |

`runtime_sha256` は `orchestrator/campaign/condition_meaning_gate.py`、
`tools/pegasus/probes/t316_sandbox_backend_probe.py` / `.pbs`、
`tools/pegasus/policies/t316_sandbox_backend_v1.json`、`tools/pegasus/policy.json`、
`runtime_pbs_spool` の 6 件を記録している。

受領証: `output/env/pegasus/t316-sandbox-backend/0:996644.nqsv/receipt.json` (147099 bytes) と
`COMPLETED`。`state` = `complete`。`measurement_id` = `0:996644.nqsv`。
`schema_version` = `t316-sandbox-backend-probe/v1`。
PBS 計測: Created 10:47:23 / Started 10:47:36 / Ended 10:48:03 JST、Elapse 32S。
probe 自身の `elapsed_ns` = 26316472205 (26.3 秒)。

## stage verdicts (逐語)

```
S1 go      S1_INVENTORY_COMPLETE
S2 go      S2_REQUIRED_NAMESPACES_STARTED
S3 go      S3_NETWORK_DNS_NODE_CAPABILITY_UNAVAILABLE, S3_NETWORK_DIRECT_IP_CONTAINED,
           S3_NETWORK_PROXY_CONTAINED, S3_CREDENTIAL_HOME_CONTAINED_BY_ABSENCE,
           S3_CREDENTIAL_SSH_AGENT_CONTAINED_BY_ABSENCE, S3_CREDENTIAL_SSH_DIR_CONTAINED_BY_ABSENCE,
           S3_CREDENTIAL_CODEX_DIR_CONTAINED_BY_ABSENCE, S3_WRITE_HOME_CONTAINED_BY_ABSENCE,
           S3_WRITE_REPO_CONTAINED, S3_WRITE_TMP_CONTAINED, S3_SOURCE_READ_ONLY_CONTAINED,
           S3_SCRATCH_WRITE_ALLOWED
S4 go      S4_ESCAPED_DESCENDANT_TERMINATED
S5 go      S5_RUNTIME_SYSTEM_COMMAND_CONTAINED, S5_RUNTIME_NETWORK_CONTAINED,
           S5_RUNTIME_FILE_WRITE_CONTAINED_BY_ABSENCE, S5_RUNTIME_INFINITE_LOOP_TERMINATED,
           S5_BUILD_SYSTEM_COMMAND_SIDE_EFFECT_OBSERVED, S5_BUILD_NETWORK_CONTAINED,
           S5_BUILD_FILE_WRITE_CONTAINED_BY_ABSENCE, S5_BUILD_INFINITE_LOOP_TERMINATED
S6 blocked S6_BUILD_NOT_ATTEMPTED
S7 blocked S7_PERFORMANCE_NOT_ATTEMPTED
overall: no-go
```

## S6 の観測 (逐語、`observations.S6`)

```json
{"attempted": false,
 "error": {"message": "condition gate rejected t316 CCBench build: supply=red/configure-failed, meaning=unestablished/meaning-witness-undeclared",
           "type": "RuntimeError"},
 "reason": "S6 raised"}
```

## この実測が確定させたこと

1. 本 commit を束縛した t316 実経路の計算ノード probe は**実際に走り、条件関門まで到達した**。
   `_require_condition_gate` が呼ばれ、supply と meaning の両 arm が record を発行し、
   `require_condition_gate_family` が **admit しなかった**。
2. supply arm の terminal は `red`、reason code は `configure-failed`。
   **`stock-inert-preprocess-root-location-only` にも `stock-inert-preprocess-identical` にも
   `stock-inert-mismatch` にも到達していない** — inert 比較そのものの手前で落ちている。
3. meaning arm は `unestablished` / `meaning-witness-undeclared`。probe が
   `declaration=None` を渡すため。`unestablished` は family admission では受理される側なので、
   admission を落としたのは supply の赤である。
4. S6 が例外で止まったため CCBench の build も S7 の性能計測も attempted されていない。

## この実測が確定させていないこと

- `configure-failed` の**原因**。receipt には reason code しか残らず、
  `evidence` は D1849 により受領証へ出されない。CMake の stderr は receipt にも
  job の stdout/stderr にも現れていない (両方とも本 dir に退避済み、該当記述なし)。
- したがって「t316 実経路では inert 緑に到達しない」が**恒久的な性質**なのか、
  **今回の configure 引数・環境に固有の一過性**なのかは、この 1 走では決まらない。
