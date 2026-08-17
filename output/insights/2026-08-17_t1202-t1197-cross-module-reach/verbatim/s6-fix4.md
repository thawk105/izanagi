実装を停止しました。指定された負例は現行 production 実装では構成不能です。

根拠:

- C01 は `_declared_call` に `(ratified_path, "load_ratified_freeze")` を渡します。`ratified_path` は `required_evidence` 由来です。[s8c_preregistration_evidence.py:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1371)
- C12 の三 target もすべて `required_evidence` 由来です。[s8c_preregistration_evidence.py:1544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1544)
- C04 も `workload_path` と `trial_registry` の required path だけを渡します。[s8c_preregistration_evidence.py:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1397)
- `declared_paths` は同じ契約の `contract.evidence_paths` です。[s8c_preregistration_evidence.py:1690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1690)

したがって、これらの evaluator では `target[0] in probe.declared_paths` が恒真です。宣言外 decoy を import すると `graph.calls` には decoy path の tuple が入りますが、`_declared_call` に渡される required path の tuple とは一致しません。指定変異後も拒否されます。

直接診断では、指定変異相当の `lambda probe, graph, target: target in graph.calls` を in-process で適用し、宣言外 decoy を実際に import・call しました。結果は変異後も以下のままでした。

```text
C01 UNSATISFIED ratified-generation-reference-absent
C04 UNSATISFIED crash-policy-cell-partial
C12 UNSATISFIED environment-contract-consumer-absent
```

単一理由 baseline は確認済みです。

```text
C01 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C04 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
C12 EVIDENCE_UNDEFINED completion-proof-not-machine-checkable
```

C04 も同じ理由で除外対象です。ただし C01/C12 も同様に構成不能であり、テストだけでは解決できません。到達した call target 自体を `_declared_call` へ渡すよう production evaluator を再設計する裁定が必要です。

`git diff -- orchestrator/campaign/s8c_preregistration_evidence.py` は空、`git status --short` も空です。production、テスト、docs のいずれも変更していません。

## 総括

- 追加した負例: なし。現行 evaluator では指定変異を kill する負例を構成不能
- 変異で落ちることの確認: 逆に、C01/C04/C12 がすべて変異後も同じ exact reason で通ることを直接確認
- 実走した nodeid: なし。診断は in-process fixture 評価
- 未実走のもの: 焦点 pytest、実 tree 12 条件、`reachability-limit-exceeded` 全件確認。実装前提の矛盾により fail-closed 停止