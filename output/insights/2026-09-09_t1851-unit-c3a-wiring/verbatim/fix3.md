## 総括

4 所見を指定 4 file 内で閉じました。inspector、marker 規則、one-shot、issuer 検査は緩めていません。  
最終実走は合計 864 passed / 0 failed / 3 skipped です。  
編集は所有 path のみで、docs 編集、git add、commit はありません。  
行番号 pin 4707 / 8636、禁止属性 0 件、結合文字 0 件を確認済みです。

## F-1 の直し方と検算 (実 raw が記録されることの実測)

[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/orchestrator/campaign/s8b_floor_attempt_launcher.py:709) に `read_floor_attempt_pre_probe()` を追加しました。

- launcher 発行、owner identity、capability seal、公開 competition bit を再検査。
- raw 4-field の immutable copy を返す。
- seal の `used` は変更せず、読み取り後も `launch_probed_floor_attempt()` を一度実行可能。
- campaign は合成 tuple を削除し、取得した実 raw を値不変の `dict` として session / journal に記録。

実測 probe `{rc: 0, stdout: "competitor", stderr: "", competing: True}` と、session および journal の4 field が完全一致しました。

## F-2 の直し方と検算 (certified 経路の crash cut test)

cut-6 verdict が true の replay だけに「既存 consumption marker」bit を伝播しました。[certified session](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/orchestrator/campaign/s8b_floor_campaign.py:8866) が competing pre-probe を観測した場合は、次の exact reason で停止します。

```text
cut6_replay_pre_probe_competing_existing_marker
```

certified crash-cut test では以下を実測しました。

- marker 作成後、attempt ledger 追記前に crash。
- marker 1 件、attempt ledger row 0 件。
- resume の competing probe で上記理由を返す。
- session completion、`result.json`、`result.md` は作られない。

## F-3 の再照準と検算 (古い prefix を載せる変異が赤になることの実測)

[test_v5_prefix_covers_every_consumed_non_competing_session](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/orchestrator/tests/test_s8b_floor_campaign.py:15097) を通常 campaign finalize 経路へ再照準しました。

- clean session 2 件を実際に terminal 化。
- `outcome["result"]["attempt_registry"]` を取得。
- 最終 live registry の全行数と chain head に一致することを検査。
- 正例は terminal 2 件、live/result とも `row_count=11`。

1 件目 terminal 後の prefix を producer に返す変異も実走しました。

```text
result row_count = 6
live row_count   = 11
1 failed, 0 passed, 510 deselected
```

期待どおり `result registry row_count is stale` で赤になり、検算後は負例 test の通常形へ戻しています。

## F-4 の狭い surface (新しい関数名と、除去した間接参照の全列挙)

[launcher の狭い surface](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix3/orchestrator/campaign/s8b_floor_attempt_launcher.py:349) は次のとおりです。

- `prepare_floor_attempt_registry_plan`
- `floor_attempt_registry_plan_slot_ids`
- `floor_attempt_registry_genesis`
- `require_floor_attempt_registry_slot`
- `floor_attempt_reservation`
- `capture_floor_attempt_registry_prefix`
- `read_floor_attempt_registry`
- `serialize_floor_session_record`
- `canonical_floor_payload_sha256`
- named error type `FloorAttemptRegistryError`

campaign から除去した間接参照:

- `launcher.attempt_registry`
- `launcher.profile8b`
- `adapter.core`
- `launcher.attempt_registry.capture_attempt_registry_prefix`
- `launcher.profile8b.serialize_session_line`
- `launcher.attempt_registry.core.canonical_json_bytes` の observation 用参照
- 同 run-start 用参照
- `launcher.attempt_registry.S8BAttemptRegistryError`
- `plan.profile.slot_codec` と `plan.slots_by_key` の直接消費

AST 検査で `attempt_registry` / `profile8b` / `core` 属性参照は 0 件です。

## 新設した test (nodeid / 正例・負例)

新設:

- `test_s8b_floor_attempt_launcher.py::test_pre_probe_raw_snapshot_is_immutable_and_does_not_consume_seal`
  - 正例: raw 等値、read 後の launch 成功
  - 負例: snapshot 書換え拒否
- `test_s8b_floor_campaign.py::test_certified_cut6_existing_marker_competing_probe_aborts_without_result`
  - 負例: certified M+A- replay の competing を exact reason で停止
- `test_s8b_floor_campaign.py::test_v5_prefix_assertions_kill_first_terminal_stale_result_proof`
  - 負例: 1 件目 terminal 後の stale prefix を検出
- `test_s8b_floor_campaign.py::test_campaign_has_no_indirect_registry_profile_or_core_attributes`
  - 負例: 禁止された間接属性参照を AST で検出

再照準・強化:

- `test_v5_prefix_covers_every_consumed_non_competing_session`
- `test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row`

## 実走結果 (command と passed/failed の実数)

| command | 結果 |
|---|---:|
| `PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py` | 74 passed / 0 failed |
| `PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py` | 508 passed / 0 failed / 3 skipped |
| `PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py` | 152 passed / 0 failed |
| `PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py` | 79 passed / 0 failed |
| `PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py` | 44 passed / 0 failed |
| `PYTHONPATH=. python3 orchestrator/tests/test_official_perf_closure.py` | 7 passed / 0 failed |

`git diff --check` と対象 4 file の `py_compile` も成功しました。

## 残った懸念

指定範囲内の未解消所見はありません。campaign harness の既存 3 skipped は pass として数えていません。差分は所有 4 path のみで、staging は空です。