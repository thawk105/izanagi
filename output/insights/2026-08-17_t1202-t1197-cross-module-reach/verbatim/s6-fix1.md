実装は指定 2 ファイルに限定して完了しました。実 tree の 12 条件は指定値を維持しています。ただし公式 pytest と F10 の compute-side 秒計測が dispatch 前に `rc=16` で停止したため、dev-wave 契約に従い全項目を `partial` とします。commit は作成していません。

### 所見ごとの対応表

| 所見 | 状態 | 実装・負例の根拠 |
|---|---|---|
| F1 | `partial` | 限定 carrier、単一 Assign、単一 splat、支配関係、変更 key ごとの block を実装: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1104)。target-key、非 literal key、update/pop/del/ior、literal/expression splat、再束縛、alias mutation、複数 splat負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:664) |
| F2 | `partial` | call 時点より前の binding だけを可視化し、同じ statement block の先行関係を検査: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:990)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1041)。使用後代入負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:897) |
| F3 | `partial` | 位置引数は対応仮引数、`*args` は全 target parameter を hard-block: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1273)。`run_trial(custom_drive)` 負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:840) |
| F4 | `partial` | sentinel `if` の直下唯一 Assign、else なしを要求: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:941)。else・nested conditional 負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:913) |
| F5 | `partial` | module import の binding ambiguity、package 複合文、local import/for/with/except/walrus/global/nonlocal を fail-closed 化: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:435)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:747)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:760)。負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1204)、[predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1274) |
| F6 | `partial` | 全条件の evidence path 14 件を target definition 許可集合にし、C09 の bare-name 比較を廃止: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:129)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1349)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1416)。宣言外 production decoy 負例: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1364) |
| F7 | `partial` | `MODULE_LIMIT == 512` exact assertと、default limitsで65 moduleを通す fixture: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1428)。`512 -> 64` では exact assertと65個目の両方が失敗する形 |
| F8 | `partial` | value-flow fixtureを guard 1 targetだけが依存する形へ変更。allocation の定義不在・call edge不在・属性不在を分割: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:947)、[predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:995) |
| F9 | `partial` | C01/C04/C09/C12へ entrypoint cut、test-only、unimported same-nameを展開。not-called/dead/nested既存 matrixも維持: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1021)、[predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1057)、[predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1089)、[predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1158)。適用不能理由も明記: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1179) |
| F10 | `partial` | commit resolve、raw、AST/function、binding、root graphを1評価内で共有し、EvidenceRefは条件別に再投影: [evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:557)、[evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/campaign/s8c_preregistration_evidence.py:1643)。resolve 1回、blob path重複0、graph cache hit `[False, True, True]` の検査: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1523)。秒のcompute実測が未了 |
| F11 | `partial` | snapshot-vs-HEADは補助検査でありmutation kill根拠ではないとdocstringへ明記し、Git読取をbatch archive化: [predicate tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:68) |

### F10 再走結果

module 数は実 tree で再取得しました。秒は性能計測扱いのため計算ノードへ `--force-dispatch` しましたが、`qstat -Q preflight rc=1` で実行前停止しています。

| 条件 | 走査 module 数 | 秒 | status / reason |
|---|---:|---:|---|
| C01 | 1 | 未実測 | `UNSATISFIED / workload-projection-mismatch` |
| C02 | 1 | 未実測 | `EVIDENCE_UNDEFINED / arm-binding-declared-only` |
| C03 | 1 | 未実測 | `EVIDENCE_UNDEFINED / manifest-registry-proof-undefined` |
| C04 | 55 | 未実測 | `UNSATISFIED / crash-policy-cell-partial` |
| C05 | 0 | 未実測 | `EVIDENCE_UNDEFINED / schedule-schema-absent` |
| C06 | 0 | 未実測 | `EVIDENCE_UNDEFINED / budget-consumer-contract-undefined` |
| C07 | 0 | 未実測 | `EVIDENCE_UNDEFINED / floor-judge-contract-undefined` |
| C08 | 1 | 未実測 | `EVIDENCE_UNDEFINED / prereg-binding-proof-undefined` |
| C09 | 55 | 未実測 | `UNSATISFIED / formal-acceptance-layer3-consumer-absent` |
| C10 | 1 | 未実測 | `UNSATISFIED / cross-binding-verifier-incomplete` |
| C11 | 2 | 未実測 | `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` |
| C12 | 56 | 未実測 | `UNSATISFIED / allocation-enforcement-consumer-absent` |

全条件で `reachability-limit-exceeded` はありません。C12 は第1 gateへ後退せず、実 production の2段 carrier chainを通過しています。

### 検査

成功した静的・直接診断:

- `git diff --check`
- 所有2ファイルの `py_compile`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- snapshot と HEAD の result/evidence exact一致
- 実 tree 12条件 golden exact一致
- F1正例と主要攻撃、F2〜F7、F9全matrix、F10 cache共有の直接synthetic診断

公式 pytest は次の両方が実行前 `rc=16` でした。

- predicatesのF1〜F10焦点 `-k` 走
- `test_s8c_preregistration_predicates.py` + `test_plain_runner_coverage.py` の `--force-dispatch` 走

## 総括

- 対応表の要約: F1〜F11はすべて実装済みで直接診断は期待どおり。ただしdev-wave契約上、公式pytest未実走とF10秒未実測のため全件`partial`。`regressed`は0件。
- 実走したnodeid: なし。pytest開始前のdispatch infrastructure failure。
- 未実走のもの: predicates全nodeid、制約meta-test、親の変異matrix・受入全走、F10のcompute-side秒計測。
- 想定と違った実測: sandboxから予約台帳を更新できずlocal admission不可、さらにNQS socket作成不可で`qstat -Q preflight rc=1`。module数と12条件値は想定どおり。
- 波及: `s8c_preregistration.py` のregistry読込、ActivationReport evidence/digest、`s8c_acceptance_receipt.py`、`autonomous_trial_completeness.py`、`trial_registry.py`、共有snapshot fixtureとconsumer tests。所有外ファイル、契約JSON、freeze、docs、reservation、単位Bの2ファイルは未変更。