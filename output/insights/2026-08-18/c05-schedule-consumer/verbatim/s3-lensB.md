静的レビューのみ実施しました。pytest、build、mutation は未実施で、緑とは報告しません。現 HEAD は `38f173cb` です。

## 所見

### B-01

- id: `B-01`
- 深刻度: `blocker`
- 対象: [stage2-plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:103)、[s8b_oracle_manifest.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8b_oracle_manifest.py:39)、[phase3-8c-preregistration.md:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/phase3-8c-preregistration.md:231)
- 主張: 新 schema の `schedule_index=0..5` は、既存の `s8b_oracle_manifest` の反復内 row 添字、`s8b_oracle_n_pilot` の observation `seq`、`s1_direct_comparison` の attempt 添字と同名である。C05 の cell ordinal と既存の観測 row 添字を結ぶ規約がない。
- 反証されうる条件: field を `cell_schedule_index` 等へ改名する、または C05 の添字が既存 manifest row 添字と同一であることを明記し、retry、attempt、observation まで一対一の対応表を追加する。
- 成果物影響: holdout、arm、反復、attempt の対応を誤ると、certified 性能表の cell 集計、受理 status、試行台帳の参照先が変わる。

### B-02

- id: `B-02`
- 深刻度: `blocker`
- 対象: [stage2-plan.md:147](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:147)、[p3_autonomous_workload_trial.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:197)、[p3_autonomous_workload_trial.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:207)
- 主張: `search_space_sha256` の preimage は designated context、payload allowlist、arm、holdout、binding だけであり、実際に role 入力を構成する `ROLE_FILES`、`ROLE_CONTRACTS`、`WORKLOADS`、`GATING_SPEC`、source closure が束縛されない。これらを変更しても hash が同じになり得る。
- 反証されうる条件: search-space の完全な authority closure を canonical bytes として追加し、role source、prompt、workload descriptor、gating、generator source の変更を必ず hash へ反映する。
- 成果物影響: 同じ `search_space_sha256` を参照したまま選択結果、材料レポート、試行台帳の入力実体だけが変わり、certified 結果の束縛が壊れる。

### B-03

- id: `B-03`
- 深刻度: `major`
- 対象: [stage2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:162)、[p3_autonomous_workload_trial.py:2859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:2859)、[p3_autonomous_workload_trial.py:2929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:2929)
- 主張: `initial_state_sha256` は role metrics、空 whiteboard、2 関数の source hash だけだが、実際の初期 role input には descriptor、descriptor binding、attempt/stop policy、gating snapshot、baseline、leakproof context が含まれる。共通 state と cell 固有 input の境界も定義されていない。
- 反証されうる条件: initial state の範囲を明示し、共通 state は全て hash へ含め、cell 固有 descriptor/binding は別の authority digest として各 schedule row に束縛する。
- 成果物影響: 同じ `initial_state_sha256` のまま初期入力が変化し、選択結果、材料レポート、台帳の hash 参照が実行内容を表さなくなる。

### B-04

- id: `B-04`
- 深刻度: `major`
- 対象: [stage2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:9)、[p3_autonomous_workload_trial.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/p3_autonomous_workload_trial.py:39)、[reflux_origin_artifacts.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/reflux_origin_artifacts.py:20)
- 主張: 新 module が p3 の authority を直接 import し、将来 `run_trial -> verify_schedule` を追加すると `p3 -> s8c_schedule -> p3` の cycle になり得る。また private `_canonical_json_bytes` を跨ぎ参照する必要はない。公開の `reflux_origin_artifacts.canonical_json_bytes` が存在する。
- 反証されうる条件: `s8c_schedule` を純粋な下位 leaf とし、p3 を import しない。authority は専用 leaf の immutable object として共有し、公開 helper を使用する。API は例えば `verify_schedule(bytes, *, master_seed, authority) -> Schedule`、`consume_schedule(schedule, *, cell_index) -> ScheduleCell` とする。
- 成果物影響: import cycle や private exception の漏出で production launch が開始前に失敗し、certified 選択、材料レポート、試行台帳が生成されない。

### B-05

- id: `B-05`
- 深刻度: `major`
- 対象: [stage2-plan.md:50](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:50)、[s8c_preregistration_evidence_contract.v1.json:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:193)、[s8c_preregistration_evidence.py:1834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:1834)
- 主張: planned `_evaluate_c05` は artifact path と関数名、AST 上の call edge を見るだけで、実際の committed schedule bytes、6 cell 集合、seed、hash 値を検査しない。さらに bitflip test は exact-byte verifier が先に拒否するため、`verify_schedule` が shared verifier を本当に呼ぶことを単独では証明しない。
- 反証されうる条件: committed artifact fixture を直接検査する evaluator test と、exact-byte call、shared-hash call、`consume_schedule -> verify_schedule` の各 edge を別々に壊す negative control を追加する。
- 成果物影響: C05 登録後も malformed artifact や未束縛 consumer が適切な拒否理由へ到達せず、発効判定と readiness report の理由値が不正確になる。

### B-06

- id: `B-06`
- 深刻度: `major`
- 対象: [stage2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:26)、[phase3-8c-preregistration.md:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/phase3-8c-preregistration.md:218)、[trial_registry.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/trial_registry.py:65)
- 主張: 6 cell の新 schedule は反復、attempt、run-start receipt、raw output hash、terminal status を持たず、現在の trial registry と acceptance receipt にも `schedule_index` がない。これは §6 前提条件 4・7 の完全 block 復元を満たす full schedule ではない。
- 反証されうる条件: この artifact を明確に cell-level seed schedule と限定し、後続 wave で repetition、attempt、observation、registry、receipt を別 schema で一対一に束縛する。
- 成果物影響: 欠測、retry、reject を含む exact `n` の復元に失敗し、official status、材料レポート、試行台帳の row 参照が変わる。

### B-07

- id: `B-07`
- 深刻度: `minor`
- 対象: [stage2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:26)、[test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_plain_runner_coverage.py:44)、[orchestrator/tests/README.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/README.md:155)
- 主張: 新設 `test_s8c_schedule.py` は現在の pytest-only allowlist に無く、プランにも `__main__` 自走 harness の指定がない。plain-runner meta-test は新ファイルを検出し、harness も allowlist も無ければ赤になる。
- 反証されうる条件: `test_s8c_schedule.py` に実際に test を実行する `__main__` harness を追加するか、allowlist へ追加する。
- 成果物影響: certified 結果、材料レポート、台帳値は変わらないが、受入 gate が赤になり land が止まる。

### B-08

- id: `B-08`
- 深刻度: `nit`
- 対象: [brief.md:113](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/brief.md:113)、[stage2-plan.md:244](/work/1/SFC/tanab/dev-wave-jobs/c05-schedule-consumer/stage2-plan.md:244)
- 主張: brief は t1333 が `test_s8c_preregistration_predicates.py` を所有中と記すが、実測した `git diff --name-only main...worktree-dev-wave-t1333-t1310-workload-profile` は空で、branch tip は main に既に含まれている。現時点の直接所有衝突という記述は stale である。
- 反証されうる条件: branch が進み、再実測で同じ file の未 land 差分が現れる場合。
- 成果物影響: certified 値は直ちに変わらないが、誤った ownership 情報により重複編集や provenance の取り違えが起きる。

静的な既存テスト波及は次の通りです。

- `test_s8c_preregistration_predicates.py:735`、`:1974`、`:2229` は machine-checkable 7 条件、negative control、registry bijection を exact pin する。C05 を false のまま別集合に置く計画は整合する。
- `test_s8c_preregistration_invariant.py:271` は `machine_checkable=true` の行だけ function pin するため、C05 false の間は新 module を検査しない。`WAVE_REQUIRED_PATHS` は下限集合であり、新規 file 数の exact 検査ではない。
- `test_s8c_preregistration_core.py:2164` 以降は contract/evaluator blob の整合を検査する。contract JSON bytes を変えない限り、ここに直接の期待値変更はない。
- `ReasonCode` の全 member 網羅検査は s8c test 群には見当たらず、新 reason code 追加だけで既存 exact 集合が赤になる根拠はない。
- `s8b_oracle_manifest.py:39`、`s8b_oracle_n_pilot.py:888`、`s8b_budget.py:37`、`s1_direct_comparison.py:151` の各 test 群は、将来 production wiring した時点で `schedule_index` の意味衝突を発火させる候補である。

## 並行 wave の衝突表

`git diff --name-only main...<branch>` を指定 branch 全てへ read-only 実行した結果です。

| branch | 重なる file | 衝突の型 |
|---|---|---|
| `worktree-dev-wave-t1348-c09-c10-consumer` | なし | 現 ref で差分なし |
| `worktree-dev-wave-t1352-c07-result-judge` | なし | 現 ref で差分なし |
| `worktree-dev-wave-t1353-c03-c08` | なし | 現 ref で差分なし |
| `worktree-dev-wave-t1363-c06-budget-consumer` | なし | 現 ref で差分なし |
| `worktree-dev-wave-t1333-t1310-workload-profile` | なし | branch tip が main に含まれる。predicate、p3、trial registry の過去変更は既に base 側へ入っている |
| `worktree-dev-wave-t1286-commit-receipt` | `orchestrator/tests/test_p3_autonomous_workload_trial.py` | C05 file との直接衝突ではないが、p3 の fixture/API 前提を同時に変える間接衝突 |
| `worktree-t1283-trusted-launcher` | なし | acceptance launcher、land、wait の基盤変更。C05 file との直接衝突なし |

現 ref では `orchestrator/campaign/s8c_preregistration_evidence.py` の直接所有衝突はありません。predicate file も t1333 の未 land 差分ではありませんが、既存変更を含むため、実装前に現在の file 内容を再確認すべきです。

## 親 brief への攻撃

### P1

条件付きで同意します。

C05 contract には既に artifact path、consumer path、negative control が定義されています（[contract:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:193)）。したがって `_evaluate_c05` は、非 certifying の準備実装として書く価値があります。ただし未登録なので、現時点の dispatch は変わりません。

「C05 gate が存在する」「C05 が検証済み」と記録してはなりません。static evaluator の実装と、登録前の専用 negative control を残す判断が妥当です。

### P2

同意します。

規範は seed 単独で標本を束縛しないと明記し、generator version、schedule bytes、arm order を同じ改訂単位で固定することを要求しています（[phase3-8c-preregistration.md:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/phase3-8c-preregistration.md:135)、[phase3-8c-preregistration.md:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/phase3-8c-preregistration.md:164)）。

従って、今 wave で artifact と `master_seed` を commit しない判断は正しいです。単体テストの一時 bytes を、実 schedule の証拠として記録してはいけません。

### P3

部分同意です。

「証拠契約を定義する」という狭い達成形としては、未配線を `SCHEDULE_CONSUMER_UNREACHABLE` として表す設計は妥当です。しかし現在は `machine_checkable=false` かつ `_MACHINE_EVALUATORS` 未登録なので、現 HEAD の C05 は引き続き `EVIDENCE_UNDEFINED / schedule-schema-absent` です（[s8c_preregistration_evidence.py:1821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_preregistration_evidence.py:1821)）。

登録後に `UNSATISFIED` になることは、C05 の発効や §6 前提条件 5 の達成を意味しません。

### P4

部分同意に留めます。

`DESIGNATED_SOURCE_CONTEXT`、payload allowlist、arm/holdout binding は有効な束縛先です。しかし、実際の role contract、role file、workload descriptor、gating、baseline、初期 payload が抜けているため、現状の preimage だけでは十分ではありません。

また brief の「同名識別子の二義化なし」は `content_digest_sha256` と `arm_binding_digest_sha256` については概ね正しい一方、`schedule_index` については B-01 の通り反証されます。

## 裁定パッケージ候補

### scope 外だが実際に必要な層

1. **schedule authority 層**  
   generator version、seed、arm order、search-space closure、initial-state closure。

2. **artifact 層**  
   pre-run の committed schedule bytes と `master_seed`。現在 wave では未登録・未記入で正しい。

3. **evaluator 層**  
   `_evaluate_c05`、reason code、artifact/consumer の static 契約検査。これは現 wave の scope。

4. **dispatch/freeze 層**  
   contract の `machine_checkable`、`_MACHINE_EVALUATORS`、negative-control exact 集合、DECIDER bump、次世代 freeze record。scope 外。

5. **production launch 層**  
   `run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch next cell`。scope 外。

6. **manifest/registry/attempt 層**  
   6 cell manifest、append-only registry、repetition、attempt、retry slot、run-start receipt。scope 外。

7. **observation/report 層**  
   observations 側添字、exact `n`、judge、official performance table、selection table、validator reachability。scope 外。

8. **receipt/acceptance 層**  
   process identity、raw output hash、terminal status、content/effective commit、measurement HEAD の三者束縛。scope 外。

特に 4〜8 を実装したふりで wave 内へ取り込まないことが重要です。これらは次の登録・発効 wave の裁定パッケージへ送るべきです。

### 段 7 の記録

- `docs/spool/worklog/` へ fragment を作り、直接 `docs/worklog.md` を編集しない。frontmatter、命名、`## 本文` と `## 次の一手差分` の形式は [docs/spool/README.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/docs/spool/README.md:35) と worklog README に従う。
- insights には brief、stage2 plan、Lens B review、branch 差分、静的テスト棚卸し、未実施項目を残す。pytest/build/mutation は「未実施」と書き、緑を推測しない。
- 実装後は次の趣旨を明記する。

  `s8c_schedule.py と _evaluate_c05 はコードとして存在するが、C05 は machine_checkable=false かつ evaluator registry 未登録であり、schedule artifact、master_seed、production wiring も未登録である。現 dispatch は EVIDENCE_UNDEFINED / schedule-schema-absent。certified 選択結果、材料レポート、試行台帳はこの状態から produce されない。`

- 実際の裁定が下るまでは decisions fragment を決定済みとして書かず、仮説上の問題を failures として記録しない。裁定後に必要なら placeholder 付き fragment を追加する。

## 総括

判定は `NO-GO` です。  
blocker は `schedule_index` の意味衝突と、search-space hash の authority 不足です。  
P1、P2 は条件付きで同意、P3 は未登録状態を明示する限り部分同意、P4 は不十分です。  
指定 branch に現時点の直接 evidence file 衝突はなく、t1286 だけ p3 test の間接衝突があります。  
実装後も C05 は未登録・未発効であり、pytest 未実施を緑とは扱えません。