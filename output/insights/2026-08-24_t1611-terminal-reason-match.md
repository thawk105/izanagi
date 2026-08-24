# [T-1611] 8c 理由一致検査の前向き strict 化 — 実測記録と変異台帳

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は実測の妥当性文書
(measurement record) であり、裁定台帳ではない。

- 起点: 裁定正本 D741 (理由一致検査の版境界での必須化)、D735 (遷移 policy の profile 注入)、
  D672 (互換抽出の受理集合不変)。
- 測った checkout: branch `worktree-dev-wave-t1611-terminal-reason-match`。
- 実行環境: Pegasus。テストは計算ノード dispatch。

---

## 1. 何を締めたか

D741 は「次の正式 8c 走行または凍結世代更新より前に、事前分類受領証の失敗理由と terminal の
再走理由の一致検査を必須化する」と決めた。本 wave はその実装である。

締めた関門は 3 つで、いずれも**前向き (forward-only)** である。

| # | 関門 | 新 facade | 締める内容 |
|---|---|---|---|
| 1 | slot 予約 | `reserve_formal_attempt_slot` | 既存の理由不一致 prefix を start 追記の前に拒否する |
| 2 | terminal 追記 | `record_formal_attempt_terminal` | 分類が空のまま retryable 理由を付ける追記を拒否する |
| 3 | 正式 acceptance | `assert_formal_attempt_registry_acceptance` | 理由不一致を含む registry からの新規正式 acceptance を拒否する |

既存の互換 facade 6 本は signature・例外順・出力 bytes を変えていない。strict と互換の差は
**渡す profile 1 個だけ**で、その profile 差は遷移 policy の理由一致 bool 1 個に閉じている。

## 2. なぜ terminal 入口だけでは足りないか

段 2 の初期案は terminal 入口だけを strict にするものだった。段 3 の敵対レンズがこれを real な
不足として棄却した。理由は次の 2 点である。

- 既存 registry に残る理由不一致 prefix が、そのまま次の slot 予約に使われる。予約側が互換のままなら
  不一致の履歴を土台にして新しい試行が始まる。
- 正式 acceptance も互換 profile で registry を読むため、不一致を含む registry から正式受領証が出る。

つまり terminal だけを締めても**受理集合が変わらない**。これは「締めたつもりで何も変わらない」型の
恒真ゲートであり、絶対規律 2 の観点で最も避けるべき形である。

## 3. 事前登録条件の現状 (状態報告のみ)

段 4 は「C03 の評価器を編集して緑へ戻すことは scope 違反」と裁定した。本 wave は評価器・登録・
充足化のいずれも触っていない。最終 commit で判定器を library 経路から 1 回再評価した結果は次のとおり。

| 条件 | status | reason_code |
|---|---|---|
| C01, C02, C04, C06, C07, C09, C10, C11, C12 | `EVIDENCE_UNDEFINED` | `completion-proof-not-machine-checkable` |
| C03 | `UNSATISFIED` | `manifest-registry-proof-undefined` |
| C05 | `EVIDENCE_UNDEFINED` | `schedule-schema-absent` |
| C08 | `EVIDENCE_UNDEFINED` | `prereg-binding-proof-undefined` |

総合は `PREREGISTRATION_NOT_EFFECTIVE`、`freeze_generation` は 10、`decider_version` は
`s8c-decider/v6` で一致。

**C03 だけが `EVIDENCE_UNDEFINED` から `UNSATISFIED` へ変わった。** これは本 wave の変更が
予定どおり効いた結果である。C03 は旧互換 sink を要求するが、正式 acceptance 経路が strict 側へ
移ったため、その要求が満たされなくなった。段 4 の裁定に従い、**dead な旧呼び出しを残したり
評価器を書き換えたりして緑へ戻すことはしていない。** 状態として報告するに留める。

## 4. 変異台帳

権威ある走行は wrapper-attempt 2 である。

- 束縛 commit: `15f974b084bbed415947ffc9ca7488b5f261a4bc`
- spec sha256: `ea9cf82c8f33ba3b16fbcef3f836531cec2a565347f674d5de84bc896d4e7f77`
- baseline: **PASSED**
- 集計: registered 7 / completed 7 / **KILLED 7** / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0 / matching 7
- wrapper 事後検査: `shared_snapshot_matches=true` / `failure=null`

| id | 変異 | 期待 | 結果 | 期待 node 数 | 完全一致 |
|---|---|---|---|---|---|
| m01 | strict profile の理由一致 bool を True から False へ | KILLED | **KILLED** | 10 | はい |
| m02 | formal 予約が渡す profile を互換 profile へ | KILLED | **KILLED** | 2 | はい |
| m03 | formal terminal が渡す profile を互換 profile へ | KILLED | **KILLED** | 3 | はい |
| m04 | formal acceptance が渡す profile を互換 profile へ | KILLED | **KILLED** | 3 | はい |
| m05 | registered 予約 sink を互換 facade へ戻す | KILLED | **KILLED** | 3 | はい |
| m06 | registered terminal sink を互換 facade へ戻す | KILLED | **KILLED** | 5 | はい |
| m07 | acceptance receipt producer の sink を互換 facade へ戻す | KILLED | **KILLED** | 4 | はい |

期待 node は完全集合で登録し、記録 node との完全一致だけを KILLED と数えた。
観測 node は事前の probe 走 (全件 SURVIVED 期待) で集め、本走で照合している。

### 期待 node の内訳

**t1611.m01** (strict profile の理由一致 bool を True から False へ)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_profile_differs_only_by_reason_equality_policy`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_profile_rejects_mismatch_that_compat_replays`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_profile_rejects_reason_replacement_before_null_matrix[none-to-preempted]`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_profile_rejects_reason_replacement_before_null_matrix[preempted-to-wall-timeout]`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_profile_rejects_reason_replacement_before_null_matrix[terminal-failure-mismatch]`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_partial_producer_failure_is_fail_closed_without_terminal`
- `orchestrator/tests/test_trial_registry.py::test_formal_acceptance_rejects_mismatch_that_legacy_accepts`
- `orchestrator/tests/test_trial_registry.py::test_formal_reserve_rejects_compat_mismatch_prefix_without_append`
- `orchestrator/tests/test_trial_registry.py::test_formal_terminal_rejects_reason_replacement_without_append`
- `orchestrator/tests/test_trial_registry.py::test_high_level_acceptance_routes_mismatch_to_formal_once_without_receipt`

**t1611.m02** (formal 予約が渡す profile を互換 profile へ)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_trial_registry.py::test_formal_reserve_rejects_compat_mismatch_prefix_without_append`

**t1611.m03** (formal terminal が渡す profile を互換 profile へ)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_partial_producer_failure_is_fail_closed_without_terminal`
- `orchestrator/tests/test_trial_registry.py::test_formal_terminal_rejects_reason_replacement_without_append`

**t1611.m04** (formal acceptance が渡す profile を互換 profile へ)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_trial_registry.py::test_formal_acceptance_rejects_mismatch_that_legacy_accepts`
- `orchestrator/tests/test_trial_registry.py::test_high_level_acceptance_routes_mismatch_to_formal_once_without_receipt`

**t1611.m05** (registered 予約 sink を互換 facade へ戻す)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_modes_route_reserve_and_terminal_only_through_formal_facades[registered-effective]`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_modes_route_reserve_and_terminal_only_through_formal_facades[registered-formal-non-certifying]`

**t1611.m06** (registered terminal sink を互換 facade へ戻す)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_modes_route_reserve_and_terminal_only_through_formal_facades[registered-effective]`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_modes_route_reserve_and_terminal_only_through_formal_facades[registered-formal-non-certifying]`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_registered_partial_producer_failure_is_fail_closed_without_terminal`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_run_trial_routes_exactly_five_terminal_sites_through_formal_helper`

**t1611.m07** (acceptance receipt producer の sink を互換 facade へ戻す)

- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py::test_s8c_formal_entrypoints_and_producers_are_strictly_routed`
- `orchestrator/tests/test_trial_registry.py::test_formal_acceptance_rejects_noncooperating_registry_rebind_without_receipt[parent-parent]`
- `orchestrator/tests/test_trial_registry.py::test_formal_acceptance_rejects_noncooperating_registry_rebind_without_receipt[target-path]`
- `orchestrator/tests/test_trial_registry.py::test_high_level_acceptance_routes_mismatch_to_formal_once_without_receipt`

### 単一理由性

m02 から m07 の赤 node は層ごとに分離している。予約 (m02/m05)、terminal (m03/m06)、acceptance (m04/m07) が互いの node を巻き込まず、profile 側 (m02〜m04) と sink 側 (m05〜m07) も別の node で落ちる。共通して落ちるのは経路の静的検査 `test_s8c_formal_entrypoints_and_producers_are_strictly_routed` の 1 件だけで、これは 3 関門の routing を一括で見る設計上そうなる。m01 だけが根の switch なので 10 node を横断して倒す。

### 走行の履歴

本走は 3 回投入した。**測定は 3 回とも baseline PASSED / 7 KILLED / matching 7 で同一**である。

| 走行 | source root | wrapper 事後検査 | 測定 |
|---|---|---|---|
| wrapper-attempt 1 | 本 wave の worktree | `shared_snapshot_matches=false` で abort | 7 KILLED / matching 7 |
| wrapper-attempt 2 | 本 wave の worktree | `true` | 7 KILLED / matching 7 |
| wrapper-attempt 3 | 独立 clone `/work/1/SFC/tanab/mutation-src-t1611` | `true` | 7 KILLED / matching 7 |

1 回目は条件を変えない再投入 (2 回目) で通ったので、共有木事後検査の失敗は**間欠**である。
3 回目は `--source-repo` に独立 clone を渡し、観測 root を clone 1 本へ dedup させたものである。
共有 checkout から切り離しても同じ測定が出ることを示すが、間欠性が確定した以上、
この切替えは必須ではない。詳細と帰属の切り分けは、本 wave が失敗台帳へ登録した
「変異 wrapper の共有木検査は 2 root を見る」のエントリに置く。

## 5. この記録の限界

- 事前登録 12 条件のうち C03 以外は本 wave の scope 外であり、状態を写しただけである。
- strict profile を名乗る identity は artifact へ永続化していない。凍結世代を跨いだ
  identity の追跡は本 wave では扱わない。
- exploratory 経路は attempt slot を取らないため strict 化の対象外である。この判断は
  「exploratory は正式証拠を生まない」という前提に依存しており、その前提自体は本 wave では測っていない。
