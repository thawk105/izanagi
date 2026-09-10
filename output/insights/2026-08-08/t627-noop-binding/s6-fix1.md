F1〜F6を指定4ファイルの段5差分へ反映しました。すべて未実走のため、closed 判定は行いません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial（実装済み・未実走） | terminal serial の `== 3` assert を復元 |
| F2 | partial（実装済み・未実走） | 実物 pegasus g1→g2で述語だけをFalse化。旧clocks差fixtureも別nodeで維持 |
| F3 | partial（実装済み・未実走） | 3-env全行列、全env同時+1正例、3件目False負例を追加 |
| F4 | partial（実装済み・未実走） | hash再利用public経路とsame-generation/hash差替えprivate gate pinを追加 |
| F5 | partial（実装済み・未実走） | 先頭False→後続Trueでも全callback到達後に先頭失敗を維持するnodeを追加 |
| F6 | partial（実装済み・未実走） | production precondition／defense-in-depthコメントと外側catalog層のdocstringを追加 |

### 追加・変更したtest node

| Node | 検出対象 |
|---|---|
| `test_transition_accepts_three_record_forward_chain` | staleなterminal `activation_serial` |
| `test_transition_accepts_three_env_simultaneous_plus_one` | 3件同時+1を拒否する集約実装 |
| `test_transition_three_env_matrix_matches_d228_rule` | `max`／`sum`等による集約縮退 |
| `test_transition_rejects_when_third_changed_env_successor_is_false` | `changed[:2]` への量化縮退 |
| `test_transition_checks_generation_change_even_when_hash_is_reused` | hash-only変化分類。別envの+1でno-op偶然赤を避け、callback列で欠落を検出 |
| `test_transition_gate_rejects_same_generation_hash_substitution_when_other_env_advances` | generation-only変化分類。外側registry gateを迂回したdefense-in-depth pin |
| `test_transition_preserves_first_failure_when_later_successor_is_true` | 後続Trueによる`first_failure`消去 |
| `test_production_successor_adapter_returns_false_when_is_valid_successor_is_false` | 解決済み実物edgeでの述語返り値破棄 |
| `test_production_successor_adapter_returns_false_for_resolved_invalid_contract` | 解決成功後、実物述語が自然にFalseとなるclocks差経路 |
| `test_transition_rejects_env_set_change_before_calling_predicate` | 外側catalog照合層が実際の拒否所有者であることをdocstringで明示 |

### 静的な波及範囲

所有外の直接callerは次に閉じています。

- `env_contract._load_authority_snapshot`
- `tools/issue_env_contract_activation.py`
- leaf内部の`load_activation_state → validate_activation_records`

共有fixtureでは`orchestrator/tests/conftest.py`が`GENERATIONS`とcatalogを同時差替えします。adapterは呼出し時のmodule globalを読むため、既存fixtureとの分裂はありません。

間接consumerとして`execution_guard.py`、`silo_ladder_rung1.py`、`qualification/contract.py`、floor／freeze系があります。波及候補のconsumer testは主に以下です。

- `test_env_contract.py`
- `test_campaign.py`
- `test_s8b_floor_campaign.py`
- `test_silo_ladder_rung1_driver.py`
- `test_silo_ladder_rung1_evidence.py`
- `test_p3_s4_loop_trigger_gating.py`
- `test_s8b_oracle_report.py`
- `test_s8b_ratified_verify.py`
- `test_env_attestation.py`

### 検査と未実施事項

静的検査結果：

- 指定4ファイルのAST parse成功
- test node 59件、重複なし
- `git diff --check`成功
- 変更ファイルは指定4ファイルのみ
- docs、初期activation record、head定数に差分なし
- activation leafに禁止import／env固有literalなし

期待して赤くなるfinding集合は空です。実装不能項目はありません。

pytestは指示どおり実行しておらず、緑は主張しません。docs編集とgit commitも行っていません。

## 総括

F1〜F6はすべて実装済み・未実走です。親による計算ノード実走と再レビュー後にのみclosed判定できます。