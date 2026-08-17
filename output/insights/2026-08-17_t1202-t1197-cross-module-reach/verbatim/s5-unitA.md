実装は完了し、所有 2 ファイルだけを変更しました。commit は作成していません。単位 B の 2 ファイルは触っていません。

変更箇所:

- [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:572)
- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:115)

実装内容:

- canonical `(repo 相対 path, top-level function name)` graph
- relative/absolute import、alias、multi-name `ImportFrom` の exact 解決
- package `__init__.py` shadow、lexical shadow、test-only/non-production target の拒否
- callable default を witness にしない限定 value-flow
- sentinel 解決、単一代入、keyword 伝播、静的 `dict(k=v)` carrier の限定追跡
- 定数偽 branch、未呼出し nested function の除外
- 到達関数全体からの属性収集
- C12 の `main -> run_trial` gate
- module 512、depth 64、state 2048、raw bytes 16 MiB
- `reachability-limit-exceeded` の独立分類
- deterministic frontier/successor
- snapshot と実 HEAD の result/evidence exact 一致検査
- C01/C04/C09/C12 の baseline-first、単一破壊型負例
- missing definition、unimported decoy、caller override、dead branch、nested scope、package/local shadow、entrypoint cut、test-only target の負例

追加 reason の発火条件は次のいずれかです。

- 513 個目の実在 production Python module を読む
- depth 65 の callable state を処理する
- 2049 個目の一意な callable state を処理する
- 読み込む module raw bytes が 16 MiB を超える

いずれも `ERROR / reachability-limit-exceeded` になり、`commit-blob-read-error` には畳みません。

実 tree 最終実測:

| 条件 | module 数 | 秒 | status / reason |
|---|---:|---:|---|
| C01 | 1 | 0.066469 | `UNSATISFIED / workload-projection-mismatch` |
| C02 | 1 | 0.050949 | `EVIDENCE_UNDEFINED / arm-binding-declared-only` |
| C03 | 1 | 0.045253 | `EVIDENCE_UNDEFINED / manifest-registry-proof-undefined` |
| C04 | 55 | 10.705127 | `UNSATISFIED / crash-policy-cell-partial` |
| C05 | 0 | 0.068637 | `EVIDENCE_UNDEFINED / schedule-schema-absent` |
| C06 | 0 | 0.032710 | `EVIDENCE_UNDEFINED / budget-consumer-contract-undefined` |
| C07 | 0 | 0.034669 | `EVIDENCE_UNDEFINED / floor-judge-contract-undefined` |
| C08 | 1 | 0.043485 | `EVIDENCE_UNDEFINED / prereg-binding-proof-undefined` |
| C09 | 55 | 7.861908 | `UNSATISFIED / formal-acceptance-layer3-consumer-absent` |
| C10 | 1 | 0.063021 | `UNSATISFIED / cross-binding-verifier-incomplete` |
| C11 | 2 | 0.116473 | `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` |
| C12 | 56 | 7.822431 | `UNSATISFIED / allocation-enforcement-consumer-absent` |

全条件が期待値どおりで、`reachability-limit-exceeded` はありません。

C12 の実測:

- `env_contract.lookup` と `execution_guard.attest_and_build_receipt` は exact target として到達
- `allow_resume` は到達した `p3_s4_loop_trigger_gating.py` 内で確認
- `single_process` の所在は `env_contract.py:76,152` と `reservation.py:277`
- `reservation.py` の `single_process_required` は実在しない
- 第 2 gate はこの定義不在で短絡するため、実際の terminal reason は単一の allocation consumer 不在
- ただし `.single_process` を使う関数自体は root call graph から到達していません。これは親の属性所在予想との差ですが、現 gate の単一理由性は崩していません

検査結果:

- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 所有 2 ファイルの AST parse: 成功
- 実 HEAD と snapshot の result/evidence exact 一致: 直接診断で成功
- 全 12 条件 golden: 直接診断で成功
- synthetic positive/negative、4 上限境界、cycle、hash seed 決定性: 直接診断で成功

正式 pytest は `tools/run_tests.py` 経由で次を投入しましたが、すべて実行前に `rc=16` で停止しました。

- `test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy`
- `test_s8c_preregistration_predicates.py` 全体
- `test_s8c_preregistration_predicates.py` + `test_plain_runner_coverage.py`

停止理由は Pegasus dispatch の `qstat -Q preflight rc=1` です。従って、緑として報告できる pytest nodeid はありません。

波及可能性:

- `s8c_preregistration.py` が動的に読む registry と ActivationReport evidence/digest
- `s8c_acceptance_receipt.py`、`autonomous_trial_completeness.py`、`trial_registry.py` の report digest consumer
- predicates suite の共有 snapshot helper と synthetic commit fixture
- 新 reason を表示・集計する将来 consumer
- 単位 B 所有の `s8c_preregistration.py` と core fixture 差分は非帰属・未変更

## 総括

- 実装したもの: cross-module exact reachability、限定 value-flow、全上限と新 reason、属性収集、A-02/A-03/A-04/A-05/B08/E-02、positive/negative・golden・snapshot exact テスト。
- 実走した nodeid: なし。`tools/run_tests.py` は pytest 開始前に dispatch infrastructure failure。
- 未実走のもの: predicates pytest 全体、追加全 nodeid、制約 meta-test、単位 B core suite、親の受入全走。
- 想定と違った実測: `.single_process` の所在は確認できたが、その使用関数は C12 root call graph から未到達。第 2 gate は `single_process_required` 定義不在で先に短絡し、単一理由性は維持。
- 波及: ActivationReport evidence/digest とその downstream consumer。certified 集合、契約 JSON、freeze、docs、reservation は不変。単位 B の差分は非帰属。