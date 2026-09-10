## 実装したもの

- [s8c_schedule.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:51): schema、generator、ARMS、HOLDOUTS、authority key 集合。
- [s8c_schedule.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:167): 厳密な authority 検証と digest。
- [s8c_schedule.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/campaign/s8c_schedule.py:269): 生成、load、strict decode、exact/shared 検証、consume。
- [test_s8c_schedule.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:97): 指定された再生成、seed 順序、authority、負の対照、index 検査。
- [test_s8c_schedule.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-c05-schedule-consumer/orchestrator/tests/test_s8c_schedule.py:240): 自走 harness。

公開 API:

```python
validate_authority(authority) -> None
search_space_digest(authority) -> str
initial_state_digest(authority) -> str
regenerate(master_seed, *, authority) -> bytes
load_schedule(path) -> bytes
verify_exact_schedule_bytes(artifact_bytes, *, master_seed, authority) -> None
verify_shared_search_space_and_initial_state(
    schedule, *, expected_search_space_sha256,
    expected_initial_state_sha256
) -> None
verify_schedule(artifact_bytes, *, master_seed, authority) -> Schedule
consume_schedule(
    artifact_bytes, *, master_seed, authority, schedule_index
) -> ScheduleCell
```

## authority の key 集合

`SEARCH_SPACE_AUTHORITY_KEYS`:

- `arms`, `holdouts`: arm と holdout の軸。
- `designated_source_context`: designated source context。
- `descriptor_bindings`, `holdout_bindings`: descriptor と holdout の束縛。
- `gating_spec`: gating 仕様。
- `role_contracts`, `role_files`: role 契約と role source。
- `role_payload_allowlist`: role payload 許可集合。
- `workloads`: workload authority。

`INITIAL_STATE_AUTHORITY_KEYS`:

- `initial_role_metrics`: 初期 role metrics。
- `whiteboard`: 世代 0 の初期 whiteboard。
- `descriptor_binding`: 初期 descriptor binding。
- `attempt_policy`, `stop_policy`: attempt と停止方針。
- `gating_snapshot`: 初期 gating snapshot。
- `baseline`: baseline authority。
- `leakproof_context`: leakproof 実行 context。

両集合は閉じた `frozenset` で、全 union の欠落・余剰・型違反を拒否します。

## 恒真でないことの論証

- テスト 5 は全 authority key を一つずつ変更し、対応する digest が変わることを確認します。
- digest preimage は対象 key 集合全体を `canonical_json_bytes` へ渡すため、authority の変更を無視する既定路はありません。
- テスト 7 は artifact bytes を変更せず、期待 initial-state hash の先頭 byte だけを 1 bit 反転します。shared 検証は拒否し、同じ artifact の exact 検証は通します。
- `verify_schedule` は exact/shared の両方を live に呼び、`consume_schedule` は `verify_schedule` を live に呼びます。

## 実走状況

pytest、mutation、受入走は未実走です。親が実施します。AST parse、禁止 import/name、編集対象の静的確認のみ実施しました。commit は作成していません。

## 波及

- 所有外の production caller や `_evaluate_c05` は未変更です。
- 後続 caller は全 authority key union を供給する必要があります。
- schedule artifact や共有 fixture は追加していません。
- 既存テスト、docs、契約 JSON、凍結成果物は変更していません。

## 総括

単位 A の schedule consumer と専用テストを実装しました。  
authority は引数供給かつ strict validation です。  
exact/shared の二層検証と cell ordinal の区別を固定しました。  
pytest は未実走で、親へ委譲します。