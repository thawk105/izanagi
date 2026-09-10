実装済み・未実走です。pytest、commit、docs 編集は行っていません。

### 変更内容

- [env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:257)
  - `_RegisteredSuccessorPredicate` を追加。
  - `_validate_activation_transition` を新設。
  - env ごとの exact `+1`、全 env 据置 no-op、全 changed env の successor 判定を実装。
  - callback の例外、非 exact-bool、`False` を `ActivationRecordError` で fail-closed。
  - `validate_activation_records`／`load_activation_state` に既定値なし keyword-only predicate を追加。
  - leaf から `env_contract` は import していない。

- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:395)
  - `_resolve_activation_entry` を追加し、row の型・env・generation・hash を exact 解決。
  - `_is_valid_activation_successor` を追加し、`is_valid_successor` の返り値をそのまま返却。
  - adapter は呼出し時の module-global `GENERATIONS` を参照。
  - `_load_authority_snapshot` から adapter を必須注入。

- [issue_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/tools/issue_env_contract_activation.py:206)
  - issuer の既存 loader 呼出しへ production adapter を注入。
  - issuer 固有の遷移判定は追加していない。

- [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:509)
  - synthetic successor と chain helper を追加。
  - 段2の14 node、段4 N1〜N11、既存4件の再著述を反映。
  - N8 は `GENERATIONS` を差し替え、実物の `is_valid_successor` が自然に `False` を返す形。
  - N9 は「`is_valid_successor` が呼ばれない」ことの観測に代替 seam がないため、同関数の spy を使用。

### Test node 対応

| 裁定 | Test node |
|---|---|
| 段2-1 | `test_transition_accepts_one_plus_one_with_other_env_unchanged` |
| 段2-2 | `test_transition_accepts_multiple_simultaneous_plus_one` |
| 段2-3 | `test_transition_rejects_all_env_noop` |
| 段2-4 / N1 | `test_transition_rejects_noop_in_middle_of_chain` |
| 段2-5 | `test_transition_rejects_skip_even_when_successor_predicate_accepts` |
| 段2-6 | `test_transition_rejects_downgrade_even_when_successor_predicate_accepts` |
| 段2-7 | `test_transition_rejects_compensating_plus_two_minus_one` |
| 段2-8 | `test_transition_rejects_plus_one_when_bound_contract_successor_is_false` |
| 段2-9 | `test_successor_predicate_receives_exact_generation_hash_rows` |
| 段2-10 | `test_record_rejects_registered_generation_with_wrong_contract_hash` |
| 段2-11 | `test_transition_rejects_non_bool_successor_result` |
| 段2-12 | `test_transition_wraps_successor_exception_fail_closed` |
| 段2-13 | `test_production_successor_adapter_resolves_bound_generation_entries` |
| 段2-14 | `test_issue_main_rejects_noop_without_publishing` |
| N2 | `test_transition_accepts_three_record_forward_chain` |
| N3 | `test_transition_rejects_when_second_changed_env_successor_is_false` |
| N4 | `test_successor_predicate_is_called_once_for_each_changed_env` |
| N5 | `test_transition_rejects_compensating_plus_one_minus_one` |
| N6 | `test_transition_matrix_matches_d228_rule` |
| N7 | `test_transition_rejects_skip_when_catalog_order_is_not_generation_order` |
| N8 | `test_production_successor_adapter_returns_false_when_is_valid_successor_is_false` |
| N9 | `test_production_successor_adapter_rejects_rows_that_do_not_resolve` |
| N10 | `test_validate_activation_records_requires_successor_predicate` |
| N11 | `test_transition_rejects_env_set_change_before_calling_predicate` |

既存再著述：

- `test_chain_intentionally_does_not_enforce_generation_delta_predicates` は上記独立 node 群へ置換。
- `test_downgrade_preserves_pegasus_g2_for_historical_resolution` は `test_forward_activation_preserves_pegasus_g1_for_historical_resolution` に改名・再構成。
- `test_issue_main_success_prints_required_head_and_inactive_warning` は pegasus g2 前進へ変更。
- `test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart` は正当な前進 suffix と head 不一致診断へ再構成。
- `test_production_loader_passes_source_head_constants_to_leaf` に adapter identity の検査を追加。

### 受理集合

変更前は、正しい schema／registry／head であれば no-op、skip、downgrade、`(+2,-1)` 相殺、途中 no-op を受理していました。

変更後も bootstrap、部分 `+1`、複数 env 同時 `+1`、`g1→g2→g3` は受理します。一方、no-op、skip、downgrade、相殺、不正 successor、非 bool、callback 例外を拒否します。既存の env 集合・registry pair・chain・head 拒否は維持しています。

### 所有外への波及

`rg` で direct caller は次に閉じています。

- production: `env_contract._load_authority_snapshot`
- issuer: `tools/issue_env_contract_activation.py`
- leaf 内部: `load_activation_state → validate_activation_records`
- direct test caller: `test_env_contract_activation.py` のみ

静的な consumer／fixture 波及：

- `orchestrator/tests/conftest.py`
  - synthetic `GENERATIONS` と catalog を同時差替えする。serial 1 のため callback は未発火だが、adapter は差替え後の global を読むので分裂しない。
- `orchestrator/campaign/execution_guard.py`
  - 検証済み `ActivationState` を再照合する consumer。変更不要。
- `orchestrator/campaign/silo_ladder_rung1.py`
  - 両変更 module を runtime binding に含み、4箇所の `lookup("pegasus")` が間接 consumer。今後生成する source binding hash は変わる。
- `orchestrator/qualification/contract.py`
  - 両 module を code identity に含む。
- `s8b_floor_campaign.py`、`s8b_ratified_freeze.py`
  - `resolve_by_contract_sha256` の downstream。forward chain でも ever-active 集合を保持する。
- consumer tests:
  - `test_env_contract.py`
  - `test_s8b_floor_campaign.py`
  - `test_silo_ladder_rung1_driver.py`
  - `test_t126_pegasus_tools.py`
  - `test_t419_probe_causality.py`

### 静的検査

- 4ファイルの AST parse: 成功
- leaf の禁止 campaign/orchestrator/calibrator import: 0件
- leaf の禁止 env 固有 literal: 0件
- predicate の既定値: なし
- predicate 未指定 caller: N10 の意図的な2箇所だけ
- test node: 52件、重複なし
- `git diff --check`: 成功
- 変更ファイル: 指定された4ファイルのみ
- activation head 定数、初期 record、docs: 未変更
- commit: 未作成

親 docs 未 land に由来して期待する赤集合は静的には空集合です。したがって親の計算ノード実走で発生する赤は、すべて回帰または新規 finding として扱う必要があります。

## 総括

段4 plan v2、署名で定めた gate、段2の14 node、N1〜N11、既存4テストの再著述を実装しました。実装できなかった項目はありませんが、環境制約に従い pytest と meta-test は未実走です。状態は「実装済み・未実走」です。