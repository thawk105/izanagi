## 総括

production 配線、v5 result、prefix capture、legacy v4 維持まで実装しました。変更は所有された2 path のみです。  
新設11 node のうち10件は通過しましたが、複数 clean attempt の2件目で所有外 adapter の replay 欠陥が発火します。  
安全な所有内回避はないため未完了です。`git add`、commit、docs 編集はしていません。  
行番号 pin 4707 / 8636 と関連 meta-test は維持しています。

## 配線前と配線後の順序 (file:line で対)

配線前:

`strict_probe():6244` → competing 分岐 `:6245-6256` → marker 消費を含む wrapper → `self.measure_fn():6262`

配線後:

`production 分岐:6242` → `probe_floor_attempt_preconditions():8954` → competing なら marker・launcher なし `:8960-8972` → clean のみ `consume_attempt_ticket():8989` → marker 検証 `:8992` → `launch_probed_floor_attempt():9045` → launcher terminal をそのまま emit `:9059-9063`

finalize:

- finalize-pending: prefix captureとv5 assembly `:7809-7815` → live verifier `:7817`
- 通常 finalize: 最終 session 後の prefix captureとv5 assembly `:7962-7968`

## 実装した内容

- exact 288-slot registry planを構築。
  - 12 cells × 8 rounds × planned/retry 3 ordinals
  - `repetition = round - 1`
  - planned は measurement ordinal 0、retry は1または2
  - recovery ordinalは0
- launcher-owned pre-probeをmarker消費より先に実行。
- competing branchではmarker、attempt ledger、registry rowを作らず、実holdout inspectorで受理。
- clean branchだけmarkerを消費し、certified launcherへ渡す。
- launcher terminalの同一dictをjournalへemit。
- productionだけ`RESULT_SCHEMA_V5`と`attempt_registry`を出力。
- injected `measure_fn`およびmodule-level `measure_point` test seamはv4経路を維持。
- test fileへ指定コマンド用の自走入口を追加。

## 新設した test (nodeid / 正例・負例)

正例:

- `test_default_production_attempt_uses_certified_launcher_once`
- `test_registry_plan_declares_exact_planned_and_retry_slot_closure`
- `test_registry_plan_maps_round_to_zero_based_repetition`
- `test_journal_emits_launcher_terminal_record_byte_identically`
- `test_default_production_result_is_v5`
- `test_v5_prefix_covers_every_consumed_non_competing_session` — 所有外 blockerで失敗
- `test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row`
- `test_injected_measurement_core_retains_noncertifying_legacy_path`
- `test_finalize_pending_replays_live_v5_prefix`

負例:

- `test_certified_campaign_rejects_unissued_consumption_marker`
- `test_production_v5_self_check_rejects_prefix_head_mismatch`

planned ordinal 0は最初のlauncher testで`retry_ordinal=None`のterminalまで到達します。competing testは実`inspect_floor_holdout_admission_evidence()`を通しています。

## 実走結果 (command と passed/failed の実数)

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
499 passed, 6 failed, 3 skipped / 508 collected
```

6 failureはmodule-level `measure_point` test seamの誤分類でした。修正後の該当再走:

```text
6 passed, 0 failed
```

最終状態の新設test:

```text
10 passed, 0 failed
```

複数clean attempt被覆:

```text
test_v5_prefix_covers_every_consumed_non_competing_session
0 passed, 1 failed
```

関連meta-test:

```text
test_ccbench_spawn_sites.py                 44 passed
test_official_perf_closure.py               7 passed
live verifier caller exact test             1 passed
schema alias identity tests                 2 passed
adapter import boundary test                1 passed
test_acceptance_schedule_order.py          79 passed, 1 warning
```

最終状態の全508 nodeは、既知blockerが確定したため再全走していません。

## 行番号 pin の保存の検算 (4707 / 8636)

- `s8b_floor_campaign.py:4707` = `return build_fn(genome, **call_kwargs)`
- `s8b_floor_campaign.py:8636` = `outcome = run_campaign(`
- `test_ccbench_spawn_sites.py`: 44/44 passed

新helperはすべて8636より後ろの`8672-9063`に配置しました。

## 所有外への波及可能性 (静的列挙)

- `s8b_attempt_registry.py:2557-2588`
  - `_evidence_by_digest`を受け取るが未使用。
  - `core.reserve_attempt_slot(... profile=profile)`がplain v2 profileで既存sealed terminalを再拒否。
- 同じ形がclassification `:2779-2847`、observation-start `:3028-3056`にもあり、reserveだけ直すと次段で再発火する可能性があります。
- `test_s8b_floor_attempt_launcher.py:1490`には既知のplanned ordinal旧fixtureが残っています。
- 新規11 nodeの`acceptance_duration_ledger.json`追記は親のadd-only所有事項です。
- holdout/ratified freezeのv5 consumer配線はD2まで未接続です。

## 残った懸念

blockerのexact failureは次です。

```text
[s8b-v2-terminal] v2 terminal requires the sealed evidence API
```

1件目のsealed terminal後、2件目のclean attempt予約時に発火します。production campaignは通常複数clean sessionを持つため、この状態を完了扱いにはできません。A2所有面でadapterのreserve・classify・observation transitionへvalidated evidence profileを伝播した後、当該1 nodeと全508 nodeの再走が必要です。