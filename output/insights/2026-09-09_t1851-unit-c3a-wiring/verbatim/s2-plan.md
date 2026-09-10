## 総括

現状の契約と既存テストを保持したまま実装できる C3 plan は成立しない。`FloorAttemptReservation.consumption_marker` を launcher の pre-probe 前に用意すると、既存 holdout inspector の competing 規則に必ず反する。  
さらに v2 slot の `measurement_ordinal` と terminal evidence の `retry_ordinal` 束縛が食い違い、planned と retry の双方で sealed terminal を構築できない。  
最低 9 file に波及するため 5 file 仮定は棄却し、C3a/C3b 分割を推奨する。ただし C3a 着手前に契約 erratum と marker 消費規則の裁定が必要である。  
静的読解と `rg` のみを行った。pytest、campaign、性能測定は実行していない。

## 変更計画 (file:line)

現状では以下をそのまま実装へ渡してはいけない。先頭 2 項が未裁定 blocker である。

- `orchestrator/campaign/s8b_holdout_admission.py:4349-4392,5082-5103,6577-6582,6733-6741`

  - `validate_floor_attempt_consumption_marker()` は `consume_attempt_ticket()` が marker を永続化した後でなければ capability を発行できない。
  - 一方、inspector は pre-probe competing session に marker があると `attempt-ledger-coverage-mismatch` で拒否する。
  - v2 だけ「launcher が registry 予約のため消費した competing attempt」を認めるのか、launcher API を二段化して probe 後に marker を発行するのか、裁定が必要。前者は受理集合変更、後者は launcher 契約変更である。

- `orchestrator/campaign/s8b_terminal_evidence.py:760-792,1140-1160`

  - `_campaign_plaintext()` は `retry_ordinal` を非負整数に限定するが、campaign の planned session は `None`。
  - `_assert_authoritative_identity()` は `campaign_record.retry_ordinal == reservation.slot_id[4]`、つまり v2 `attempt_ordinal` を要求する。
  - registry は `orchestrator/campaign/s8b_attempt_registry.py:2534-2538` で v2 reserve の `attempt_ordinal != 0` を拒否し、`:2367-2370` では holdout marker の campaign retry 軸を `measurement_ordinal` へ束縛する。
  - 正しい候補は planned を `None`、retry を `slot_id[3]` に束縛することだが、契約 v3.1 §1.5 と既存 test fixture に反する。erratum 無しには変更しない。

blocker 解消後の producer 側変更案は次のとおり。

- `orchestrator/campaign/s8b_floor_campaign.py:90-164,6024-6086,6215-6385,6507-6538,6705-6870,7795-7838,7840-8018`

  - launcher/profile/registry/scheduler accounting module を import。
  - 新設:

    ```python
    @dataclass(frozen=True, slots=True)
    class _FloorAttemptRegistryPlan:
        profile: object
        binding: s8b_attempt_profile.S8BAttemptBinding
        genesis: s8b_floor_attempt_launcher.FloorAttemptRegistryGenesis
        slots_by_key: Mapping[
            tuple[str, int, int],
            s8b_attempt_profile.S8BV2AttemptSlot,
        ]

    def _build_floor_attempt_registry_plan(
        *,
        protocol: Mapping[str, object],
        cells: Sequence[Mapping[str, object]],
        schedule: Sequence[Mapping[str, object]],
        freeze_sha256: str,
        protocol_sha256: str,
    ) -> _FloorAttemptRegistryPlan

    def _floor_measurement_capture(
        *,
        cell: Mapping[str, object],
        binary: str,
        contract: _env_contract.ExecutionEnvironmentContract,
        protocol: Mapping[str, object],
        expected_use_perf: bool,
        observation_admission: object,
    ) -> s8b_floor_attempt_launcher.FloorMeasurementCapture

    def _floor_terminal_builder(
        *,
        seq: int,
        round_no: int,
        cell: Mapping[str, object],
        kind: str,
        retry_ordinal: Optional[int],
        attempt_id: str,
        trigger: Optional[str],
        artifact_binary: str,
        protocol: Mapping[str, object],
        contract: _env_contract.ExecutionEnvironmentContract,
        perf_preflight: object,
        mode: str,
    ) -> Callable[
        [s8b_floor_attempt_launcher.OpenedFloorAttempt],
        s8b_floor_attempt_launcher.FloorAttemptTerminal,
    ]
    ```

  - `_Runner.__init__()` に `repo_root: Path`、`campaign_run_id: str`、`run_relpath: str`、`attempt_registry_plan: _FloorAttemptRegistryPlan | None` を追加。
  - `run():6507-6538` で実際に emit した `campaign-start` または `resume-start` record、その canonical SHA-256、process identity を保持する。
  - `_run_session():6215-6385` は injected `measure_fn` の既存 test 経路を残し、default production 経路だけ `launch_floor_attempt()` へ送る。launcher が返した `terminal.campaign_record` と同じ object 内容だけを `_emit()` する。
  - `assemble_result():6705-6870` に keyword-only `attempt_registry: Mapping[str, object] | None = None` を追加。非 null の production 経路だけ schema v5 と `attempt_registry` を出し、既存 injected test 経路は v4 のまま維持する。
  - `:7795-7838` の finalize-pending と `:7962-7986` の通常 finalize の双方で、production のみ `capture_attempt_registry_prefix()` を実行し、同じ proof を assembly と既設 live inspector に渡す。
  - `test_ccbench_spawn_sites.py` の行番号 pin を変えないため、`:4707` と `:8636` 以前は総行数を保存する。大きい新 helper は `main():8550-8653` の後、`if __name__ == "__main__"` の前へ置く。

- `orchestrator/campaign/s8b_floor_contract.py:29-40`

  - `RESULT_SCHEMA = LEGACY_RESULT_SCHEMA` は変更しない。これを v5 にすると、holdout/ratified consumer が default v4 key set と v5 schema を同時要求する。
  - blocker 解消後は次だけを追加する。

    ```python
    PRODUCTION_RESULT_SCHEMA: str = RESULT_SCHEMA_V5
    ```

  - campaign の production assembly はこの名前を使う。D2 までは legacy consumer alias を動かさない。

- `orchestrator/tests/test_s8b_floor_campaign.py:1693-1725` および末尾

  - 既存 `measure_point(use_perf=...)` closed-set 期待値は変更しない。injected core の legacy path を実在させたままにする。
  - production launcher、closed genesis、byte-identical journal emit、v5 proof、finalize-pending、safe cut-6 を新規 node で検査する。

- `orchestrator/tests/test_s8b_floor_contract.py:164-194,376-445` および末尾

  - v4 legacy alias と readable set の既存期待値は変更しない。
  - `PRODUCTION_RESULT_SCHEMA is RESULT_SCHEMA_V5` の正例だけを追加する。

- `orchestrator/tests/acceptance_duration_ledger.json`

  - 新設 node の実測所要だけを add-only で追加する。既存 key の削除、改名、値変更はしない。

## 依存順と段 5 の所有分割

強制順は次のとおり。

1. marker 消費規則の裁定と terminal ordinal erratum。
2. C3a の gate/adapter 整合。
3. C3a の campaign 配線と v5 producer。
4. 焦点 test、受入、変異。
5. C3b の fresh production campaign。
6. 実成果物から gate 値域 receipt を作成。
7. D2 consumer/fixture。

段 5 を 2 子へ分ける場合は直列とし、所有 path を次の素集合にする。

- 子 A、gate 整合:

  - `orchestrator/campaign/s8b_holdout_admission.py`
  - `orchestrator/campaign/s8b_floor_attempt_launcher.py`。裁定が launcher 二段化を選んだ場合だけ
  - `orchestrator/campaign/s8b_terminal_evidence.py`
  - 各対応 test file

- 子 B、A の API 確定後:

  - `orchestrator/campaign/s8b_floor_campaign.py`
  - `orchestrator/campaign/s8b_floor_contract.py`
  - `orchestrator/tests/test_s8b_floor_campaign.py`
  - `orchestrator/tests/test_s8b_floor_contract.py`

`acceptance_duration_ledger.json` は統合後に親が 1 回だけ所有する。C3b はコードを所有せず、Pegasus run と値域 receipt のみを所有する。

## pin 閉包の全列挙

この変更で変更を許される既存凍結成果物は 0 件である。`FROZEN_MANIFEST` の 23 件はすべて byte 不変とする。

- `output/s1-freeze/known_axes_freeze.json` — `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516`
- `output/s1-freeze/measurement_freeze.json` — `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a`
- `output/s8b-freeze/holdout_freeze.json` — `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- `output/s8b-freeze/floor_protocol.json` — `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- `output/insights/2026-07-16_s8b-floor-protocol-package.md` — `150438a4ce2d0e5cab772c3eb9bfa05f44307a5dae5e47a1034778a3e3d9f6ba`
- `output/insights/2026-07-16_s8b-freeze-v2-design-material.md` — `833dce66f4d61e5512298f6075061aa4f714ffba5fd44c4239173ed37ee91835`
- `output/insights/2026-07-16_s8b-floor-protocol-consultations.md` — `d5bf4954e7ab3de657e47f7a7512b9ca13631818a2c1f046bd3dfdba09bcbcc1`
- `output/insights/2026-07-16_s8b-freeze-consultations.md` — `5a8a2dcbcbb74decff502dffe01a389012d086ced2dd6db1f3b948153ccce149`
- `output/insights/2026-07-16_s8b-ruling-prep-consultations.md` — `1a2db02903de83aefb18ce87ee926ec0c7bb5c2d90c4a5bf6dee017148a2a391`
- `output/s8b-freeze/selector_predictions.json` — `5884c83f010f73914fe121e9eb7b2fe047a4739087a984d17287cfa338fd73f1`
- `output/s8b-freeze/selector-runs/envelope_rr20_on.json` — `03518a1c75cc09a36c2bc93487eff4c883e0da88015d04473398623c8a113365`
- `output/s8b-freeze/selector-runs/envelope_rr20_swapped.json` — `4ab24b43901cf52f5ea2e7f650a30eab2e05a3f883d6eb8808d761ca9990ce73`
- `output/s8b-freeze/selector-runs/envelope_rr80_on.json` — `8379a6500e957965d488d3e231aa053e8f65d4639260ba4168b2c14a243858ab`
- `output/s8b-freeze/selector-runs/envelope_rr80_swapped.json` — `6980ad84e7906146a29c0a553ee1847cc12ef7baebc2c3c77c6b3e23576e54f9`
- `output/s8b-freeze/selector-runs/journal.jsonl` — `d41135998cff3047cf792047239a3147a1154929e560b4a2e413e4ac14f9e000`
- `output/s8b-freeze/selector-runs/payload_rr20_on.json` — `bedc2c4961cc91361319a19642472583245342b8df10617fda3512aa0d5bbb55`
- `output/s8b-freeze/selector-runs/payload_rr20_swapped.json` — `f894acc13008681d79ceb0e786f79d562742eee7305c8b4f3056526df61955c2`
- `output/s8b-freeze/selector-runs/payload_rr80_on.json` — `f894acc13008681d79ceb0e786f79d562742eee7305c8b4f3056526df61955c2`
- `output/s8b-freeze/selector-runs/payload_rr80_swapped.json` — `bedc2c4961cc91361319a19642472583245342b8df10617fda3512aa0d5bbb55`
- `output/s8b-freeze/selector-runs/raw_rr20_on.txt` — `28fe26abf5b666952d0b23c05b7a5443455fbdba10e97af307b0b023025143c5`
- `output/s8b-freeze/selector-runs/raw_rr20_swapped.txt` — `9b23d5703596a98070fb9cd7161a35ba162a1dbb0c2173f09af10c0d499700f8`
- `output/s8b-freeze/selector-runs/raw_rr80_on.txt` — `20691240bef7f84215441955279b1cd1a2cda941d7c86062f1aecd2eaae98381`
- `output/s8b-freeze/selector-runs/raw_rr80_swapped.txt` — `925b5e1155509da7bcca0df775622d2cf2f7c04559a7bf462912f8641af42ed3`

pin と trust root は次のとおり。

- `test_frozen_artifacts.py:41-88` の `FROZEN_MANIFEST`、`:93-117` の独立 key set、`:119-151` の held/keep 分割、`:187-248` の byte/key/count test。
- `output/s8b-freeze/floor-protocols/e576e9cd...--511c9538....json` は resolver が扱う versioned trust root。`FORMULA_ID` とともに不変。
- `s8b_floor_stats.py:51` と `s8b_floor_contract.py:44` の `FORMULA_ID` は変更しない。
- `test_official_perf_closure.py:44-96` の `_REVIEWED_PERF_FILES` は campaign/contract/launcher/stats を登録済み。`:178-203` の role `A/J/O/B` と `:297-385` の guard、`:533-560,905-912` の AST 集合等値を維持する。新しい perf 述語や直接 call は作らない。
- `test_s8b_floor_campaign.py:1693-1725` は `measure_point(use_perf=...)` と `build_portable_run_cmd()` の exact call inventory。
- `test_ccbench_spawn_sites.py:210-225` は campaign/launcher の process-site count、`:895-910,2642-2720` は owner role `wave t2027`、scope、行番号 `4707` と `8636` を pin する。
- `test_reflux_formal_consumer.py:2285-2378` は `attempt_registry_core.py` を AST 走査し、`aborted=False` keyword と `OriginSealed(False, ...)` を拒否する。core は変更対象にしない。
- `test_s8b_terminal_evidence.py:390-403` は public signature と relative import 集合を exact pin する。
- `test_env_contract.py:79-100` は campaign を env-neutral role として登録し、Pegasus 固有 literal の追加を拒否する。
- `s8b_holdout_admission.py:143-150` の observation role 名 `floor_campaign` は claim/ledger の key 値。変更しない。
- `acceptance_duration_ledger.json` は test nodeid 全体を key 名で pin する。新規 node は add-only 登録が必要。
- real-repo test は `conftest.py:2041-2048` から xdist group `real-repo` を受け、許可 group 名は `test_real_repo_serialization.py:249-257` に pin される。新規 test は一時 repo を使い、この inventory を増やさない。
- 候補となる production/test file の現 whole-file SHA-256 を exact 検索したが、repo 内の独立 whole-file hash pin は 0 件だった。これは上記の AST、行番号、role、nodeid pin が無いことを意味しない。

## producer write-path

blocker 解消後の production 経路が書く file 種は次のとおり。

- campaign run directory  
  `output/env/<env>/calibration/s8b-floor-<mode>/<run-id>/`

  - `launch_certificate.json`
  - `journal.jsonl`
  - `manifest.json`
  - `.result.json.pending`
  - `.result.md.pending`
  - `result.md`
  - `result.json`。production は v5

- binary/build 系

  - `output/env/<env>/binaries/<binary-sha256>`
  - build tree、phase marker、sort-SWO dependency/pass/preflight/postflight diagnostic
  - `.tmp.<pid>` 形式の create-only staging。publish 後に除去

- shared holdout admission root  
  Git common dir 配下 `izanagi/s8b-holdout-admission-v1/`

  - `ledger.lock`
  - `ledger.jsonl`
  - `attempt-ledger.jsonl`
  - `measurement-generation-claims/<digest>.claim`
  - `measurement-generation-consumed/<claim>-<attempt-hash>.json`
  - resume 時の `refreeze-disqualifications/...`

- C3 で新たに到達する attempt registry

  - `floor-attempt-registries/<freeze-sha256>/<protocol-sha256>/registry.jsonl`
  - 同 generation directory と `.staging-*`
  - `floor-attempt-registry-receipts/classification-claims/<address>.json`
  - `floor-attempt-registry-receipts/<receipt-sha256>.json`
  - `floor-attempt-registry-receipts/external-evidence/<digest>.json`
  - `floor-attempt-registry-receipts/terminal-evidence/<digest>.json`

- Pegasus submit/job wrapper

  - `output/env/pegasus/floor/attempts/submissions/<nonce>/` の preflight stdout/stderr/rc、`qsub.*`、`submit-receipt.json`
  - job attempt directory の interpreter、qstat、hostname、toolchain、failure、receipt 類
  - repo 外 evidence root の `checkpoint.jsonl`
  - campaign の `run-linked` checkpoint record

- C3b 記録

  - 新規 insight 内の `gate-input-values.json`
  - human-readable README
  - job ID、commit、run directory、全参照 file の SHA-256 を載せる。fake や injected seam の値は混ぜない。

## gate 入力の実在と値域

| launcher 引数 | campaign の実値源 | 状態 |
|---|---|---|
| `FloorAttemptReservation` | `repo_root` は `_run_campaign_core():7318-7321`、binding は freeze/protocol/schedule digest (`:7373-7389`)、cell/run/manifest は `:7382-7400,7661-7670`、claim digest は `CellHoldoutAdmission.measurement_generation_claim_digest` (`s8b_holdout_admission.py:1911-1940`)、start identity は emit 済み campaign/resume-start | **構成不能**。`consumption_marker` を launcher probe 前に作ると competing branch の inspector 契約を破る |
| `FloorAttemptRegistryGenesis` | `cells` と `schedule` (`:7382-7388`)、protocol の `n_sessions=8`、`retry_slots_per_cell=2` | blocker 解消後は構成可能。候補閉包は 12 cell × repetition 0..7 × measurement ordinal 0..2 × recovery ordinal 0 = 288 slot、cell budget は 10 |
| `FloorMeasurementCapture` | runtime binary、cell の records/threads/workload、env contract の clocks/numactl、protocol の extime/reps、perf receipt、`consume_attempt_ticket()` が返す実 observation admission | marker timing blockerを除けば構成可能 |
| `post_probe` | `floor_post_probe_capability():348-350` | 構成可能。launcher 所有の固定 `pgrep` capability |
| `classified_at` | production `now_fn` (`s8b_floor_campaign.py:7313`) の `lambda: now_fn().isoformat()` | 構成可能。registry classification と terminal の時刻は実走成果物から min/max/count を記録 |
| `terminal_builder` | `OpenedFloorAttempt.measurement/failure/probe_before/probe_after/repetition_evidence/duration/binary digest` (`launcher.py:1080-1134`) と cell/protocol/contract | **構成不能**。現契約では planned の `retry_ordinal=None` と retry の measurement ordinalを sealed evidence に運べない |

静的に確定している current frozen domain は、official、Pegasus、12 cells、records 1,000,000、threads 48、reps 5、extime 5、workload は rr20/rr80 × skew 0.9 × rmw 0 である。probe rc、competing、throughput、failure counter、classified time、terminal status は未実測であり、値域として報告しない。

実 campaign 後の `gate-input-values.json` には、各入力について exact type、key set、列挙値、数値 min/max、件数、出所 artifact path と SHA-256 を記録する。terminal evidence、external evidence、registry row、result v5 prefix proof、live inspector の同一 proof を相互参照する。

## 変異候補 (内容 / 期待 kill node)

blocker 解消後に 1 件ずつ走らせる候補である。各候補は 1-3 node の kill を狙う。

1. default path を `launch_floor_attempt()` から旧 `measure_fn` へ戻す / `test_default_production_attempt_uses_certified_launcher_once`
2. genesis から retry slot を 1 個除く / `test_registry_plan_declares_exact_planned_and_retry_slot_closure`
3. slot の `repetition` を `round` のままにする / `test_registry_plan_maps_round_to_zero_based_repetition`
4. schedule-row digest から `measurement_ordinal` を除く / `test_registry_plan_schedule_row_digest_binds_all_five_axes`
5. fake または injected campaign を gate 値域 receipt に許す / `test_gate_input_receipt_requires_default_production_path`
6. holdout marker を未発行 object で代替する / `test_certified_campaign_rejects_unissued_consumption_marker`
7. launcher terminal の copy を変更して journal へ emit する / `test_journal_emits_launcher_terminal_record_byte_identically`
8. registry prefix を最後の terminal 前に capture する / `test_v5_prefix_covers_every_emitted_session_terminal`
9. production result の schema を v4 に戻す / `test_default_production_result_is_v5`
10. result の prefix head を別の有効 64hex へ差し替える / `test_production_v5_self_check_rejects_prefix_head_mismatch`
11. campaign retry を `attempt_ordinal` へ再束縛する / `test_campaign_retry_binds_v2_measurement_ordinal`
12. finalize-pending で保存済み proof を信頼し live recapture を省く / `test_finalize_pending_replays_live_v5_prefix`
13. classified clock と terminal clock に別 callable を使う / `test_campaign_passes_one_classified_clock_to_launcher`
14. safe cut-6 で同じ session terminal を二重 emit する / `test_cut6_replay_emits_one_registry_and_journal_terminal`

## 5 file 上限の判定

5 file 仮定は棄却する。最低でも次の 9 file が必要である。

1. `orchestrator/campaign/s8b_floor_campaign.py`
2. `orchestrator/campaign/s8b_floor_contract.py`
3. `orchestrator/campaign/s8b_holdout_admission.py`
4. `orchestrator/campaign/s8b_terminal_evidence.py`
5. `orchestrator/tests/test_s8b_floor_campaign.py`
6. `orchestrator/tests/test_s8b_floor_contract.py`
7. `orchestrator/tests/test_s8b_holdout_admission.py`
8. `orchestrator/tests/test_s8b_terminal_evidence.py`
9. `orchestrator/tests/acceptance_duration_ledger.json`

marker 規則を launcher 二段化で解く場合は、さらに以下が必要になる。

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

campaign の行数を保存できなければ `orchestrator/tests/test_ccbench_spawn_sites.py` の line pin にも届くが、既存期待値変更禁止に従い、これは編集せず production sink 行を保存する。

したがって C3a「配線・v5 producer」と C3b「実 campaign・値域記録」への分割を推奨する。ただし分割だけでは blocker は解消しない。C3a の前に、marker timing と ordinal の 2 件を裁定・erratum で閉じる必要がある。

## test 計画 (正例 / 負例)

正例、新設のみ:

- `test_registry_plan_declares_exact_planned_and_retry_slot_closure`
- `test_default_production_attempt_uses_certified_launcher_once`
- `test_injected_measurement_core_retains_noncertifying_legacy_path`
- `test_journal_emits_launcher_terminal_record_byte_identically`
- `test_default_production_result_is_v5`
- `test_v5_prefix_covers_every_emitted_session_terminal`
- `test_finalize_pending_replays_live_v5_prefix`
- `test_cut6_replay_emits_one_registry_and_journal_terminal`
- `test_campaign_retry_binds_v2_measurement_ordinal`
- `test_production_result_schema_alias_is_v5_without_changing_legacy_alias`
- C3b: fresh default campaign の result、registry、terminal evidence、live inspector が同じ prefix を示す非 pytest receipt

負例、新設のみ:

- 未発行 marker に置換したら `test_certified_campaign_rejects_unissued_consumption_marker` が赤。
- genesis から planned/retry slot を 1 個抜いたら `test_registry_plan_declares_exact_planned_and_retry_slot_closure` が赤。
- slot の五軸または schedule digest を変えたら `test_registry_plan_schedule_row_digest_binds_all_five_axes` が赤。
- launcher の戻り record を journal 前に変えたら `test_journal_emits_launcher_terminal_record_byte_identically` が赤。
- v5 proof を terminal 前に capture したら `test_v5_prefix_covers_every_emitted_session_terminal` が赤。
- proof の row count/head/generation を変えたら `test_production_v5_self_check_rejects_prefix_head_mismatch` が赤。
- production を v4 へ戻したら `test_default_production_result_is_v5` が赤。
- injected `measure_fn` または fake registry を値域 receipt に混ぜたら `test_gate_input_receipt_requires_default_production_path` が赤。
- cut-6 replay で terminal を二重記録したら `test_cut6_replay_emits_one_registry_and_journal_terminal` が赤。
- competing marker 規則を裁定と逆向きに実装したら、新設する admission の対になる正例・負例の片方が赤。
- planned `None` または retry measurement ordinal の束縛を外したら、新設する terminal evidence の対になる正例・負例が赤。

既存 `RESULT_SCHEMA is LEGACY_RESULT_SCHEMA`、既存 use-perf call inventory、既存 frozen hash、既存 test node の期待値は変更しない。

## 実装しないと判断したもの

- blocker を隠したままの campaign 配線
- fake registry、injected `measure_fn`、単独 `measure_point()` を実値域と数えること
- `RESULT_SCHEMA` の global v5 化。D2 前に行うと holdout/ratified consumer の v4 key contract と矛盾する
- `FORMULA_ID` の改版
- 23 凍結成果物と versioned floor protocol の再発行
- launcher 外で perf 述語を新たに直接呼ぶこと
- `attempt_registry_core.py` の変更、`aborted=False`、`OriginSealed(False, ...)`
- journal TOCTOU の追加防壁
- 既存 test 期待値の変更
- pytest、campaign、Pegasus job の実走。read-only 段のため未実行