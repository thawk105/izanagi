## 総括

判定は「現プランのままは不採用」です。pytest は実走していません。`SATISFIABLE_CONDITION_IDS` を空のままにする判断と、提示された mutation の reason_code 予測は、静的読解上は妥当です。一方、P1 と coverage、検証手順に must-fix があります。

### must-fix

- **暫定 authority を正式 artifact として commit してはいけない。**  
  `s8c_schedule.py:210-249,317-349` の `validate_authority()` は、18-key、型、空値、canonical JSON を検査するだけで、実際の `WORKLOADS` や role bytes との意味的一致を検査しません。`test_s8c_preregistration_predicates.py:37-95` の fixture は `"descriptor-hash"`、`None` の metrics、架空の role contract を受理できます。これは authority の証明ではありません。

  さらにプランの `s2-plan-output.md:95-115` は `p3.WORKLOADS` を候補にしていますが、実際の `p3_autonomous_workload_trial.py:218-234` は exploratory の ycsb-a/b/c・100k/4 であり、正式 H1/H2 の rr80/rr20・1m/48 (`s8b_holdout_freeze.py:87-103`, `phase3-8c-preregistration.md:199-203`) と一致しません。

  `schedule.v1.json` には authority 本体も provisional marker もなく、`s8c_schedule.py:340-345` は digest しか保存しません。単に docs に「暫定」と書いても、`_evaluate_c05()` は `s8c_preregistration_evidence.py:1632-1637` で artifact の存在しか見ないため、機械的に暫定性を拒否できません。正式 path に置くなら、実 authority の canonical projection と consumer を同じ正本から構築する必要があります。できないなら、artifact／master_seed／C05 activation を T-1380 相当まで延期してください。`phase3-8c-preregistration.md:164-165,226-230` にも反します。

- **旧 bitflip test の収集消失を埋める必要がある。**  
  `test_s8c_preregistration_predicates.py:2697-2738` は `NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES` から移すと実行されません。新しい token-only fixture は AST の到達性しか検査せず、共有 initial-state digest の 1-bit 改変を検出しません。低レベルの同等テストは `test_s8c_schedule.py:228-268` に残りますが、C05 の negative-control と shared-layer verifier の紐付けが失われます。専用 mapping を残すか、C05 専用 test を別名で維持してください。

- **既存 snapshot の期待値更新がプランから漏れている。**  
  artifact を commit する案では、`test_s8c_preregistration_predicates.py:207-240`、特に `:226` の C05 期待値が旧状態の `EVIDENCE_UNDEFINED/schedule-schema-absent` のままです。実装後は、親が主張する `UNSATISFIED/schedule-consumer-unreachable` に更新しない限り赤になります。

- **CLI と library を別の検証手段として扱う記述を修正する必要がある。**  
  CLI は `s8c_preregistration.py:2109-2121` で、公開 library の `activation_report_at()` (`:1897-1902`) をそのまま呼びます。bytes 不一致時の処理は `:1718-1722` の `evaluator-blob-mismatch` であり、実 evaluator 例外時だけ `:1773-1777` の `evaluator-exception` です。したがって `s2-plan-output.md:160-162` の「CLI は使わず library なら確認できる」は一般化できません。新しい evaluator/core bytes と完全一致する candidate commit を作り、その commit に対して production path を検査してください。未 commit の変更を旧 `HEAD` に対して検査した結果を green と扱ってはいけません。

### 条件付きで妥当な点

`_evaluate_c05()` (`s8c_preregistration_evidence.py:1631-1740`) の全 return は `EVIDENCE_UNDEFINED` または `UNSATISFIED` で、`SATISFIED` はありません。registry (`:2718-2735`) も SATISFIED を生成せず、allowlist に無い SATISFIED を ERROR に倒すだけです。従って `SATISFIABLE_CONDITION_IDS = frozenset()` (`:2619`) は変更不要です。

提示 mutation も、consumer module を変更せず `run_trial` の live な `consume_schedule()` 呼出しだけを `return artifact` に変えるなら、`required_calls` (`:1666-1681`) は通過し、required target 検査 (`:1722-1733`) で `schedule-consumer-unreachable` になります。ただし fixture では置換回数を必ず 1 と assert し、`consume_schedule` の `schedule_index` 引数 (`s8c_schedule.py:532-539`) と実行不能な `authority={}` を、AST-only fixture なのか runtime fixture なのか明示してください。

なお、authority 変更を「実質再抽選」とする説明 (`s1-brief.md:96-102`) は過大です。cell order は `s8c_schedule.py:299-314` で seed と固定 `ARMS/HOLDOUTS` のみに依存し、authority は `:317-345` で digest を変えるだけです。正しいリスクは再抽選ではなく、同じ seed でも authority digest と artifact bytes が再現不能になることです。