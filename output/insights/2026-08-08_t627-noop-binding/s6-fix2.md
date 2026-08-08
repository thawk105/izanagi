G1〜G4 の修正を [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:47) に実装しました。production 側への追加変更はありません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 | partial（実装済み・未実走） | 4 env の正例、4件目 downgrade、4件目 predicate=False を追加。N ≥ 5 の既知残穴を docstring に明記 |
| G2 | partial（実装済み・未実走） | hash 再利用 edge の predicate=False 負例と、他 env 据置の単独正例を追加 |
| G3 | partial（実装済み・未実走） | 非 bool→True、例外→Trueでも最初の失敗と cause を保持する node を追加 |
| G4 | partial（実装済み・未実走） | missing／extra を独立 node に分割。extra は exact `ActivationRecordError` を検査 |

`closed`／`regressed` と判定した所見はありません。

### 追加・変更した test node

| Node | 殺す誤実装 |
|---|---|
| `test_transition_accepts_four_env_simultaneous_plus_one` | 4件同時 +1 を拒否する `sum(deltas) in {1,2,3}` 型集約 |
| `test_transition_rejects_fourth_env_downgrade` | 先頭3件だけ数値条件を見る `changed[:3]` 型縮退 |
| `test_transition_rejects_when_fourth_changed_env_successor_is_false` | 4件目の predicate 結果を捨てる量化縮退 |
| `test_transition_rejects_generation_change_with_reused_hash_when_successor_is_false` | hash 再利用時に predicate を観測用に呼ぶだけで返り値を捨てる実装 |
| `test_transition_accepts_generation_change_when_hash_is_reused_and_other_env_is_unchanged` | hash 再利用 edge の過剰拒否、および別 env の変化による偶然赤 |
| `test_transition_preserves_first_non_bool_failure_when_later_successor_is_true` | 先行する非 bool 失敗を後続 `True` で消去する実装 |
| `test_transition_preserves_first_exception_when_later_successor_is_true` | 先行例外を後続 `True` で消去する実装。`__cause__` も固定 |
| `test_transition_rejects_missing_env_before_calling_predicate` | 外側 catalog 照合層の missing-env 診断順序。docstring で診断 pin と明記 |
| `test_transition_rejects_extra_env_fail_closed_before_calling_predicate` | extra-env で `KeyError` 等を漏らす fail-open／非ラップ実装 |

旧 combined node `test_transition_rejects_env_set_change_before_calling_predicate` は、期待を維持したまま最後の2 node に分割しました。

### 静的な波及範囲

所有外の直接 caller は追加検出されませんでした。既存の呼出経路は次に閉じています。

- `env_contract._load_authority_snapshot`
- issuer の `validate_activation_records` 呼出し
- leaf 内部の `load_activation_state → validate_activation_records`

共有 fixture では `orchestrator/tests/conftest.py` が `GENERATIONS` と `_REGISTERED_CONTRACT_CATALOG` を同時に monkeypatch します。今回追加した4-env catalogは当該 test module 内だけです。

間接 consumer として波及可能性があるのは `execution_guard.py`、`silo_ladder_rung1.py`、`qualification/contract.py`、floor／freeze 系です。関連 consumer test 候補は以下です。

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

- 指定4ファイルの AST parse 成功
- test node 67件、重複なし
- 指定9 node の欠落なし
- `git diff --check` 成功
- 差分ファイルは指定4ファイルのみ
- docs、初期 activation record、head 定数代入行に変更なし
- git commit なし

実装できなかった項目はありません。ただし、裁定どおり N ≥ 5 の truncation は既知の残穴として意図的に残しています。

pytest は指示どおり実行していません。親の199 passedは修正前の基準であり、今回の差分について緑は主張しません。dev-wave の author 契約に従い、docs編集・commit・実走を行わず静的検査までに留めました。

## 総括

G1〜G4はすべて実装済み・未実走です。親による計算ノード実走と再レビュー後にのみ `closed` 判定できます。