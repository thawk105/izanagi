NO-GO

## 総括

静的レビューで must-fix を4件確認した。特に `84ce492c` は、digest chain の述語本体を残した一方、公開 completeness と persisted-file verifier から呼び出しを外しているため、「検査項目は1つも減らしていない」という説明は成立しない。さらに、chain verifier の権威ある `run_root` が未使用で、別 run の artifact を束縛できる。

pytest は実行していない。親実測の 721 passed / 0 failed は否定しないが、新規 test file の meta-test 違反はその焦点走では検出されていない。

### 所見1 [real / must-fix] `84ce492c` で completeness の検査集合が減っている

根拠: `047e1d26` 時点では `assert_autonomous_trial_completeness` が `_check_arm_digest_chain` を直接呼んでいた。現 tip では `orchestrator/campaign/autonomous_trial_completeness.py:2532-2553` からその呼び出しが消え、chain は `trial_registry.assert_trial_registry_acceptance` の `orchestrator/campaign/trial_registry.py:2831-2841` だけから呼ばれる。

下流では、producer 自身が `orchestrator/campaign/p3_autonomous_workload_trial.py:2683-2686` で completeness だけを呼び、persisted-file API も `orchestrator/campaign/autonomous_trial_completeness.py:2957-2970` で completeness だけを呼ぶ。この2経路では、arm exact keys、descriptor、campaign lock、proposal、invocation、provider payload/envelope、origin terminal digest の全 chain 検査が失われた。

テストも `orchestrator/tests/test_autonomous_trial_completeness.py:853-919` で、公開 completeness を通す `_verify` から独立 helper `_verify_digest_chain` へ差し替えられており、呼び出し欠落を隠している。exploratory に余分な `arm_execution` を足した形も、公開 completeness では拒否されなくなった。

成果物影響: producer-side 検査と offline persisted-file verifier が digest 不整合 report を通し、registry acceptance まで破損が検出されない。独立 verifier の保証が縮小する。

### 所見2 [real / must-fix] 権威ある `run_root` が未使用で、別 run の artifact を受理できる

根拠: `_check_arm_digest_chain` は `run_root` を受け取るが、`orchestrator/campaign/autonomous_trial_completeness.py:708-710` の引数を本文で一度も参照しない。代わりに report 内の非権威な `campaign_root` から `artifact_run_root = campaign_root.parent.parent` を作る (`:837-845`)。proposal と provider の path 検査にはこの再導出値を渡している (`:902-922`)。

そのため `campaign_root`、proposal path、provider path を同じ別 tree へまとめて差し替えれば、`_bound_regular_bytes` の「run root 内」検査 (`:444-468`) は攻撃者が選んだ root に対して成立する。既存の outside-path test は proposal path だけを変えるため、この同時変異を殺さない (`orchestrator/tests/test_autonomous_trial_completeness.py:983-1017`)。

実 build でも不整合がある。proposal producer は常に `run_root/proposals` に書く (`orchestrator/campaign/p3_autonomous_workload_trial.py:3091-3119`) が、build campaign は `output/.../exploration/campaigns/<id>` に置かれる (`orchestrator/campaign/layout.py:479-487`)。現 verifier はその親から `.../exploration/proposals` を要求するため、正式 build の正規 proposal を拒否する。

成果物影響: acceptance が別 trial tree の proposal/provider bytes を現在 trial の証拠として受理でき、反対に正規 registered build artifact は proposal path 不一致で受理不能になる。

### 所見3 [real / must-fix] 新規 test file が plain-runner meta-test 契約に違反する

根拠: `test_plain_runner_coverage.py` は全 `test_*.py` を列挙し、自走 harness または allowlist 登録を必須にする (`orchestrator/tests/test_plain_runner_coverage.py:44-74`)。新規 `orchestrator/tests/test_s8c_arm_inputs.py` は `:189-192` で終わり、`__main__` / `pytest.main` がない。`orchestrator/tests/README.md:129-182` の allowlist にも存在しない。

従って meta-test を走らせれば `test_s8c_arm_inputs.py` が offender になる。素の `python3 orchestrator/tests/test_s8c_arm_inputs.py` は0件実行で正常終了しうる。

成果物影響: arm resolver・freeze artifact の検査を実行したつもりで0件実行する偽緑が成立し、全体 acceptance の制約 meta-test も赤になる。

### 所見4 [real / must-fix] `OriginProducerInputs.enforcement_arm` を削除し、親裁定に反している

根拠: 正本は `/home/SFC/tanab/.claude/jobs/557e4ec2/tmp/t1311/s4-adjudication.md:96-103` で「削除しない」と明記する。現実装の dataclass は `orchestrator/campaign/p3_autonomous_workload_trial.py:332-341` から field を削除している。これは typed public boundary `run_origin_trial` が受け取る型でもある (`:3634-3658`)。

repo 内 constructor は `orchestrator/tests/test_p3_autonomous_workload_trial.py:6743` の1件だけで更新済みであり、取り残された内部 caller は見つからなかった。しかし、既存の public callerまたは共有 builder が従来 field を渡すと constructor の `TypeError` になる。issued capability から labelを formal consumerへ渡す実装 (`orchestrator/campaign/p3_autonomous_workload_trial.py:1144-1179`) 自体は存在するが、裁定された入力 schema 保全とは別問題である。

成果物影響: pre-wave の origin producer caller は formal receipt生成前に停止し、origin terminal projection と result evidence が生成されない。

### 所見5 [real / nit] receipt/projection の v1 schema を in-place 変更している

根拠: schema version は引き続き `formal-consumer-receipt/v1` と `OriginTerminalProjection/v1` (`orchestrator/campaign/reflux_formal_consumer.py:87-88`) だが、両 wire record に必須 digest field が追加された (`:356-393`)。全 repo 内 constructorと exact-key consumerは更新されており、tracked output に該当 v1 persisted artifact は見つからなかった。

成果物影響: repo 外または未追跡の旧 v1 decoderとの互換性は失われるが、現在の tracked成果物が壊れる根拠までは得られないため nit。

### 所見6 [real / nit] 新規 artifact が `output/README.md` の所有説明から漏れる

根拠: `output/README.md:24` は `s8c-preregistration/` 全体を condition-freeze の世代台帳として説明する。一方、新規 authority は `output/s8c-preregistration/arm-inputs/` に置かれる (`orchestrator/campaign/s8c_arm_inputs.py:25-29`)。

成果物影響: 現行 verifier の受理値は変わらないが、将来の freeze監査や cleanup が arm-input authority を condition-freeze と誤分類しうるため nit。

### 所見7 [refuted / nit] 凍結面の直接・間接変更

根拠: `ee6ab6d0..HEAD` で、契約 JSON、`s8c_preregistration_evidence.py`、`s8c_acceptance_receipt.py`、`condition-freeze/` の差分は0。`MANDATORY_NON_CERTIFYING_REASONS` も `orchestrator/campaign/s8c_acceptance_receipt.py:23-28,225-230` に保持される。

新規 `arm-inputs/` は condition scanner の `FREEZE_DIR` と generation regexから外れる (`orchestrator/campaign/s8c_preregistration.py:40-59`)。meta invariant も `FREEZE_DIR/` だけを拾う (`orchestrator/tests/test_s8c_preregistration_invariant.py:110-116`) ため、新 directory が既存 freeze manifestへ混入して赤になる形はない。

成果物影響: condition-freeze hash、判定器版、mandatory reason集合は不変。

### 所見8 [refuted / nit] historical pin の置換・削除

根拠: `test_artifact_admission.py` は wave差分0で、指定された `p3-t178` pin は保持される。`test_autonomous_trial_completeness.py:92-219` の pre-T343 / T343 / T428 / T530 定数も残り、current epoch は別定数として追加されている。`_PRE_WAVE_ORIGINLESS_BASELINE` は `orchestrator/tests/test_reflux_originless_compatibility.py:236-268` にそのまま残り、current形を pre-wave形へ明示射影する helperが追加された。

成果物影響: historical campaign ID・originless baselineは上書きされず、current epochだけが追加される。

### 所見9 [refuted / nit] 撤去 helper の孤児

根拠: `_check_registered_terminal_cell_projection` は現 tip、全履歴の対象 commit、test名のいずれにも残っていない。対象4ファイルのAST上、撤去由来の未使用 import候補もなかった。terminal projectionの既存診断は `orchestrator/campaign/trial_registry.py:2790-2804` と `orchestrator/tests/test_trial_registry.py:3094` に残る。

成果物影響: 撤去名を参照する孤児 test/helper/import はない。

### 所見10 [refuted / nit] `bind_trial_arm` 未接続 launch と exploratory の狭化

根拠: registered `run_trial` は bindingがあれば必ず `bind_trial_arm` を呼ぶ (`orchestrator/campaign/p3_autonomous_workload_trial.py:3349-3354`)。さらに registered scopeで capability欠落を `_active_arm_execution` が拒否する (`:800-831`)。`main` と `run_origin_trial` はどちらも `run_trial` へ収束する。

exploratory は `arm_execution=None` なら旧 descriptorと旧 invocation IDを選ぶ (`:773-788,835-869`)。既存 registryがあっても manifestless opt-inを受ける試験も `orchestrator/tests/test_p3_autonomous_workload_trial.py:5806-5825` に残る。したがって、arm_executionを持たない旧探索形の受理集合が狭まった静的根拠はない。

成果物影響: 正規 exploratory report・proposal・invocation shapeは維持される。ただし、余分な `arm_execution` の completeness拒否が消えた問題は所見1に含む。