## 所見

実測時点では `s8c_schedule.py` と専用テストは未存在で、HEAD は `38f173c...` の clean tree。以下は plan と現行コードの静的照合結果です。

### C05-AST-001

- id: C05-AST-001
- 深刻度: major
- 対象: [stage2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:52)、[s8c_preregistration_evidence.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:291)、[s8c_preregistration_evidence.py:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:312)
- 主張: `_functions`、`_strings`、`_live_called_names` は名前と呼出しだけを確認する。`regenerate` 等を `pass` にし、`verify_schedule` から空関数を呼ぶだけでも通る。C02/C04 と同じ AST token-only 型だが、C05 固有に hash 比較の意味と返り値の消費を証明できない。
- 反証されうる条件: C05 evaluator が関数本体のデータフロー、外部 bytes と live hash の比較、返却 cell の launch への伝播まで検査し、空実装・再束縛 fixture を拒否すること。
- 成果物影響: 将来登録時に実体のない schedule verifier が存在扱いとなり、誤った cell 順序の certified 結果、材料レポート、試行台帳を許す可能性がある。

### C05-NC-002

- id: C05-NC-002
- 深刻度: major
- 対象: [stage2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:85)、[stage2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:128)
- 主張: `initial_state_sha256` を1 bit反転すると、`verify_schedule` は先に `artifact_bytes == regenerate(master_seed)` で赤になる。直接呼ぶ shared verifier も赤になるが、`verify_schedule` から shared verifier の呼出しを削除してもテストは通る。負の対照は単一理由ではない。
- 反証されうる条件: exact verifier を通過させた入力で shared hash verifier のみを壊す fixture、または exact/shared の各 error reason と live call を分離して検査すること。
- 成果物影響: 現行は exact 層が拒否するため受理集合は変わらないが、shared initial-state gate の検出力を証明できず、将来 exact 層が弱まった際に誤状態の schedule を通す。

### C05-BIND-003

- id: C05-BIND-003
- 深刻度: blocker
- 対象: [stage2-plan.md:147](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:147)、[p3_autonomous_workload_trial.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:293)、[axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/axis_trigger_gating.py:23)、[s8c_arm_inputs.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_arm_inputs.py:186)
- 主張: planned search-space preimage は auditor 向け `DESIGNATED_SOURCE_CONTEXT`、payload key hash、`trial_registry.HOLDOUT_BINDINGS` だけで、実際の template bytes、`TEMPLATE_PATCH`、emitter、`GATING_SPEC`、権威である `s8b_holdout_freeze.HOLDOUTS` と `DERANGEMENT` を含まない。実際の axis/template や holdout authority を変えても hash が変わらない経路がある。
- 反証されうる条件: search space の定義を本当にその三つへ限定し、実 template と holdout authority を別の独立 consumer が必ず同じ schedule 入力へ束縛すること。
- 成果物影響: 事前登録時と異なる variant universe または holdout descriptor で実走しても同じ schedule hash を報告し、certified 選択、材料レポート、試行台帳の search-space 参照を誤らせる。

### C05-IMPORT-004

- id: C05-IMPORT-004
- 深刻度: blocker
- 対象: [stage2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:11)、[stage2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:57)、[p3_autonomous_workload_trial.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:39)、[s8c_preregistration_evidence.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:913)
- 主張: 新 module が p3 の定数を import し、production wiring で p3 が新 module を import すると循環する。top-level import なら p3 の定数定義前に参照し得る。function-local import なら現在の resolver は module-level import しか束縛せず、到達性を拾えない。
- 反証されうる条件: 両者が共有する leaf authority module へ定数を移すか、循環を作らず resolver も実際の import 形を証明できる構成にすること。
- 成果物影響: production consumer が import 不能または UNSATISFIED となり、正式系列、certified 選択、材料レポート、試行台帳が生成できない。

### C05-LAUNCH-005

- id: C05-LAUNCH-005
- 深刻度: blocker
- 対象: [stage2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:57)、[contract-condition-5.json:204](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/excerpts/contract-condition-5.json:204)、[p3_autonomous_workload_trial.py:2437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:2437)
- 主張: evaluator は `run_trial` から `verify_schedule` と `consume_schedule` への call edge だけを見る。artifact path の `load_schedule`、検証済み `ScheduleCell` の launch への伝播、実際の workload loop への束縛を検査しない。現在の p3 は `selected` workload を直接 loop しており、schedule を消費していない。
- 反証されうる条件: `run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch next cell` の値伝播と順序を検査し、検証結果を無視する fixture を拒否すること。
- 成果物影響: verifier を呼ぶだけで実際の順序を使わない経路が通り、実走 cell と schedule index の不一致が certified 結果、材料レポート、試行台帳へ入る。

### C05-STATE-006

- id: C05-STATE-006
- 深刻度: minor
- 対象: [stage2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:162)、[p3_autonomous_workload_trial.py:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:1242)、[p3_s4_loop.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_s4_loop.py:704)
- 主張: `inspect.getsource` は関数内の整形やコメント変更でも hash を変える。実際の初期状態が `[]` のままでも、旧 schedule 全 cell が exact/shared の双方で拒否される。開始状態の意味より source formatting を過剰に凍結している。
- 反証されうる条件: 初期状態の定義が意図的に source bytes そのものであり、任意の整形変更を新 schedule 発行へ結び付ける規約があること。
- 成果物影響: 無害な refactor 後に既存 schedule が使えず、正式実走・certified 結果・材料レポート・台帳の生成が停止する。

### C05-GEN-007

- id: C05-GEN-007
- 深刻度: major
- 対象: [stage2-plan.md:95](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:95)、[stage2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:128)、[phase3-8c-preregistration.md:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/phase3-8c-preregistration.md:135)
- 主張: `artifact_bytes == regenerate(master_seed)` 自体は自己 hash 比較ではない。しかし同じ未凍結 `regenerate` 実装を producer と verifier が共有し、schema に generator version/hash がなく、P2 で artifact も commit しないため、独立した事前登録証明にならない。
- 反証されうる条件: generator source hash と version、事前 commit 済み artifact、master seed、arm 順序を同じ発効単位で固定すること。
- 成果物影響: 現状は fail-closed で正式成果物を作れない。後から seed/artifact を固定すれば、結果後に順序を変えた schedule を certified 結果、材料レポート、台帳へ紛れ込ませ得る。

### C05-CONSUME-008

- id: C05-CONSUME-008
- 深刻度: major
- 対象: [stage2-plan.md:22](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:22)、[stage2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:38)、[trial_registry.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/trial_registry.py:65)
- 主張: `consume_schedule` は bytes、seed、index だけを受け取り、呼出し履歴を保持しないため、同じ index の二重消費や別 index の欠落を検出できない。strict decoder が検出できるのは artifact 内の重複だけである。
- 反証されうる条件: 「duplicate index」が artifact 内だけを意味することを明記し、別途 registry が launch ごとの one-to-one 使用を fail-closed で検査すること。
- 成果物影響: 実走では同一 cell の重複実行や cell 欠落が起こり得て、試行台帳の schedule index、材料レポートの cell 集計、certified 選択の受理集合が変わる。

## 親 brief への攻撃

1. 「登録・契約反転・世代発行は不可分」は、正式 activation の束としては同意する。契約の `machine_checkable` は現状 false で、registry dispatch はその値で分岐するため、契約だけを反転すれば evaluator が無くて error、registry だけを追加すれば現行 `_evaluate_undefined` の理由が変わる。ただし status はどちらも `EVIDENCE_UNDEFINED` であり、拒否理由を意味変更とみなさない解釈も可能である。phase 本文が拒否理由の変更も version bump 対象としているため、親の保守的な裁定が妥当。

2. 「本 wave は改訂単位ではないので世代発行不要」は、契約 JSON、freeze record、artifact、§5、production wiring を変更しない限り同意する。新 module と未登録 evaluator だけでは現行 C05 の受理集合は変わらない。ただし production wiring、artifact commit、契約反転、または evaluator dispatch を land する時点では、世代発行を不要とはできない。

3. gate 入力の「実在」は同意する。`DESIGNATED_SOURCE_CONTEXT`、allowlist hash、`HOLDOUT_BINDINGS` は実在する。しかし「妥当な束縛先」は反証される。actual template/emitter/GATING_SPEC と、`s8b_holdout_freeze` を読む arm-input authority が preimage に入っていないため、存在確認を意味的な authority 確認に拡張してはいけない。

4. `verify_exact_schedule_bytes` の計画式は `artifact_bytes` と `regenerate(master_seed)` の比較であり、自己生成 hash 同士の比較ではない。この点は反証されない。ただし generator version と artifact の外部凍結が無いため、独立性の欠落は別所見である。

5. seed の装飾化は、計画どおり order hash の preimage に `master_seed` を含め、異なる seed の `cells` 順序まで assert するなら反証される。cell 集合が固定でも seed は順序を束縛する。テストが bytes 差だけを確認する実装なら固定順序バグを見逃すため、順序差の assert を明示的に固定すべき。

6. 規律 2 への直接抵触は確認できない。`SATISFIABLE_CONDITION_IDS`、既存 `NEGATIVE_CONTROL_CASES`、既存期待値を変えない計画は妥当である。ただし C05 を別集合へ置くことで、C05 の no-op AST fixture が共通 meta-test から外れるため、専用の空実装・再束縛対照を追加しなければならない。

## 裁定パッケージ候補

- p3 と schedule module の循環を解く leaf authority と、`run_trial` から launch までの到達性・値伝播をどう証明するか。
- search-space hash に axis template、emitter、`GATING_SPEC`、holdout freeze、arm-input freeze を含めるか。
- `inspect.getsource` を初期状態の正本とするか、意味的な canonical state/source closure へ置き換えるか。
- 契約反転、evaluator 登録、DECIDER_VERSION、freeze g8、generator hash、§5 seed、schedule artifact、production loader、registry/report/ledger 配線を一つの activation wave とすること。
- C05 専用の AST token-only、exact/shared 分離、launch 未消費、seed 固定順序、generator self-reference 対照。

## 総括

現行 scope は正式系列を起動可能にせず、これは brief の裁定どおりです。  
ただし planned hash の束縛先と production reachability は正しさ境界を満たしていません。  
特に search-space authority、循環 import、launch 消費未証明、negative control の mask は land 前に解くべきです。  
pytest、build、mutation matrix は実走していません。