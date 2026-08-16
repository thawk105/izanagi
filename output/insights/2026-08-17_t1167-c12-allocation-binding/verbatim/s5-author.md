実装済み・未実走です。pytest は親担当のため実行しておらず、緑は主張しません。

### 受理・拒否挙動

変更前は、実 repository の C12 が environment gate で先に短絡し、`UNSATISFIED / environment-contract-consumer-absent` を返していました。

変更後は allocation gate が先行し、現行 HEAD では `run_trial` から予約関数へ到達しないため、`UNSATISFIED / allocation-enforcement-consumer-absent` を返します。

helper を通過しても後段の environment gateを経て、終端は従来どおり `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` です。C12 に `SATISFIED` 経路はなく、受理集合は広がりません。`DECIDER_VERSION=v2` と旧世代 record の不一致も fail-closed です。

### 変更範囲

- [s8c_preregistration_evidence_contract.v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:455)
  - 裁定 §4 に従い C12 を `read_binding` / `check_reservation` と job・boot・deadline field に縮小。
  - 存在しない field path、単独性、resume 拒否要求を削除。
  - negative control ID を変更。
  - may-reach が同一 binding の data-flow、launch 前 dominance、例外伝播を証明しないことを明記。
  - semantic hash は `6944a0b0eed75917c9d489dd43c3b58e637f3d85b97203d1dc60d2cf96fbdf29`。

- [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:564)
  - 裁定 §3・§4 に従い `_c12_allocation_binding_verdict` を追加。
  - top-level 2 関数の実在と `run_trial` からの may-reach だけを検査。
  - allocation gate を environment / guard gate より前へ移動。
  - reason code は既存値を再利用。

- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:50)
  - 裁定 §5、D458 に従い `DECIDER_VERSION` を v2 へ更新。

- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:109)
  - 裁定 §3、A7 に従い production registry と helper 直呼びの snapshot tripwire を追加。
  - gap ledger は C12 行だけ変更。他 11 行は HEAD と同一であることを静的比較済み。
  - negative control を新 IDへ差し替え、実 HEAD の `reservation.py` blobを使用。
  - 複数行 block の一致数が1であることと、置換後 bytes の差を assert。

- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:1153)
  - hash pin を更新。
  - 指定5 nodeの版 literalを更新し、変異値は正常値と一致しない v3 に変更して検出力を維持。

### 波及可能性

- 所有外 caller: `effective_at` / `require_effective_preregistration` を使う `trial_registry.py` と `p3_autonomous_workload_trial.py`。status は非充足のままですが、診断 reason と decider version が変わります。
- 共有 fixture: `_snapshot_current_commit`、`_negative_control_case`、`NEGATIVE_CONTROL_CASES`。parametrized node ID は新 ID に変わります。
- consumer test: candidate freeze invariant、zero-satisfied invariant、activation digest、trial registry、reflux origin binding。
- 親所有の docs、g4 record、spool fragmentには触れていません。commit、add、stash、branch操作もしていません。

洗い出した制約 meta-test は次です。

- `test_satisfiable_predicate_requires_negative_control`
- `test_noop_and_token_only_fixtures_never_satisfy[nc_c12_reservation_check_bypassed-C12]`
- `test_current_evidence_contract_hash_is_frozen`
- `test_candidate_freeze_matches_contract_and_generation_chain`
- `test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
- `test_current_repository_snapshot_has_zero_satisfied_predicates`
- `test_contract_does_not_add_a_holdout_axis_conjunction`
- invariant の `WAVE_REQUIRED_PATHS` / holdout scan 制約

静的確認として、4 Python file の AST parse、契約 JSON parse、`git diff --check`、変更ファイル限定、C12内の `SATISFIED` 参照ゼロを確認しました。

期待赤は指定どおり、親が g4 を生成するまでの `test_candidate_freeze_matches_contract_and_generation_chain` です。ほかに静的に予想する赤はなく、発生すれば回帰扱いです。

## 総括

C12 の受理集合を広げず、誤診断を実在する allocation consumer 欠落へ切り替えました。指定5ファイルのみ変更済みで、pytest は未実走です。