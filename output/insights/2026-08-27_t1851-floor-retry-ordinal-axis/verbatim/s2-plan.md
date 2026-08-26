## 現状の把握

- 親 brief の読みどおり、「先に固定する理由」は当該測定の除外理由ではなく、**次の `remeasurement_ordinal` を開く理由**である。`performance_anomaly` は測定後に [`assess_session()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:6017) から導出されるため、この区別は必須。
- campaign の `retry_ordinal` は [`_authorized_retry_ordinals()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:5820) が cell-wide に管理する。一方、registry の `attempt_ordinal` は repetition 内の連続 prefix であり、[`attempt_registry_core.py:1081-1119`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1081) が直前 terminal/recovery を要求する。現在の二つは同じ番号軸ではない。
- trusted launcher は registry reservation を capture より先に置いているが、現在は production floor campaign から未接続である。D1007 も明記しており、実コードでも campaign は [`self.measure_fn()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:5976) と [`measure_point()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:7585) を直接呼ぶ。
- registry は pre-production であり、commit 済み 8b run row の field 実測はできない。検証は canonical synthetic rows と状態遷移テストで行う。
- `S8B_RETRYABLE_FAILURE_REASONS` は [`s8b_attempt_profile.py:395`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_profile.py:395) の `frozenset()` を維持する。

## 設計の択一と推し

結論は、**(b) slot 同一性を変えず、start event 側に第二軸を置く案を推す**。ただし「schema 据え置き」は採らず、`s8b-floor-attempt-registry/v2` へ上げる。

| 観点 | (a) slot identity に追加 | (b) event に追加、推奨 |
|---|---|---|
| genesis 事前登録 | slot の完全 cross-product が必要。repetition が決まる前の cell-wide retry ordinal を slot へ割り当てにくい | genesis に許可 ordinal 集合を明記し、実際の repetition/attempt との対応だけを start で固定できる |
| primary prefix | [`_assert_slot_layout()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:483) と [`attempt_ordinal` 前駆検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1081) を二次元化する必要がある | `attempt_ordinal` の prefix はそのまま。隣に cell-wide remeasurement prefix 検査を足す |
| identity consumer | holdout、scheduler、adapter、claim path が全て 5-tuple 化 | 4-tuple のまま |
| 動的な割当 | 「global retry 1 がどの round で発火するか」を genesis slot だけでは確定できない | ordinal 集合だけ genesis で固定し、round への割当は理由付き start で確定 |
| 8c equivalence | S8B 専用変更に閉じれば維持可能だが、core の二次元 slot layout が大きい | optional secondary-axis policy を 8b profile にだけ設定し、8c bytes を変えずに済む |

(a) の具体的波及面は以下。

- [`s8b_attempt_profile.py:27-143`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_profile.py:27): tuple alias、dataclass、exact keys、parse/serialize、`slot_id()`、`series_key()`。
- [`attempt_registry_core.py:483-509`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:483)、[`539-584`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:539)、[`1062-1119`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1062): genesis uniqueness、row-to-slot lookup、前駆 ordinal。
- [`s8b_attempt_registry.py:163-251`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:163)、[`766-901`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:766)、[`1109-1220`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1109): handle fingerprint、row match、classification claim address/key、全 `slot_id` signature。
- [`s8b_holdout_admission.py:4200-4205`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4200)、[`4241-4311`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4241)、[`4470-4477`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4470): recovery evidence と exact slot match。
- [`s8b_scheduler_accounting.py:319-350`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_scheduler_accounting.py:319): public slot tuple と start lookup。
- launcher の [`FloorAttemptReservation.slot_id`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:53) と genesis membership。
- 全 `S8BAttemptSlot` constructor fixture。

推奨する (b) では、上記の slot identity、holdout の `:4304/:4470`、scheduler の `:349` は変更しない。

ただし `/v1` 据え置きは不可。profile は exact key 表であり [`S8BSlotCodec.parse()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_profile.py:64)、core は genesis/row の exact keys を [`_parse_genesis()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:654) と [`_parse_row()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:741) で固定している。field を足して `/v1` を再定義するのは schema version の意味を壊す。実 artifact が無いので migration は不要だが、版は `/v2` にする。

8c の [`_S8CSlotCodec.attempt_ordinal()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/trial_registry.py:1998) は変更しない。8c profile では secondary-axis policy を `None` とし、[`test_attempt_registry_core_equivalence.py:436-470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_attempt_registry_core_equivalence.py:436) の legacy/core/facade byte equality を維持する。

## file:line 粒度のプラン

1. [`s8b_attempt_profile.py:22-60`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_profile.py:22)

   - schema を `/v2` へ上げる。
   - `S8BAttemptSlot`、`S8BSlotIdentity`、codec exact keys は変更しない。
   - `S8B_REMEASUREMENT_REASONS_BY_SOURCE` を追加する。legacy と recovery を別集合として保持し、flat union だけで判定しない。
   - genesis に次の exact policy を追加する。

     ```json
     {
       "remeasurement_ordinals": [1, 2],
       "remeasurement_reasons_by_source": {
         "legacy-failed-session": [
           "competing_process",
           "launch_failure",
           "nonfinite_or_partial_output",
           "performance_anomaly"
         ],
         "verified-registry-recovery": [
           "node_failure",
           "scheduler_external_interruption"
         ]
       }
     }
     ```

   - start event に nullable な exact 4-field union を追加する。

     ```text
     remeasurement_ordinal
     remeasurement_reason
     remeasurement_source
     remeasurement_evidence_sha256
     ```

   - `make_s8b_domain_profile()` の入力へ `retry_slots_per_cell` を追加し、genesis ordinal 集合を `range(1, retry_slots_per_cell + 1)` から一度だけ作る。
   - [`S8B_RETRYABLE_FAILURE_REASONS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_profile.py:395) は変更しない。

2. [`attempt_registry_core.py:167-195`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:167)

   - `DomainProfile` に optional な、domain-independent の secondary reservation policy を追加する。
   - policy は serialized field 名、source ごとの理由集合、source evidence 種別、budget key、recovery evidence の単回使用規則を immutable に保持する。
   - 8c profile は `None` のため、既存 event bytes と public facade signature を変えない。

3. [`attempt_registry_core.py:654-738`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:654)、[`1402-1510`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1402)

   - genesis policy を exact parse/build する。
   - ordinal は重複なし、昇順、`1..N` の完全 prefix とし、profile の `retry_slots_per_cell` と完全一致させる。
   - 理由表も profile の source 別集合と完全一致させる。caller 提供の集合は受け取らない。
   - genesis は create-only かつ hash chain の先頭なので、走行中に ordinal を追加する API は作らない。

4. [`attempt_registry_core.py:844-930`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:844)、[`1062-1130`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1062)

   - start の 4-field union を fail-closed に検査する。
   - planned start は4 field 全て `None`。
   - retry start は4 field 全て非 nullで、ordinal が genesis 集合内、cell-wide で重複せず既使用集合が prefix。
   - `remeasurement_reason` は選択 source の集合にだけ属することを要求する。
   - legacy evidence は canonical trigger session bytes の digest、recovery evidence は検証済み recovery event/receipt の digestとして区別する。
   - [`attempt_ordinal` の直前 slot 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1081) は残す。ただし S8B secondary reservation が完全に検証された場合だけ、`terminal-failure` から次の primary attempt を開ける。これは `retryable_failure_reasons` を広げる処理にしない。
   - output-derived terminal reason を記録する必要があるため、[`terminal reason equality`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1264) は「observation 後かつ S8B の閉集合内」の場合だけ例外を許す。8c の equality policy は不変。

5. [`attempt_registry_core.py:1539-1593`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1539)

   - `reserve_attempt_slot()` に secondary reservation object を追加する。
   - S8B retry slot では理由付き reservation が無ければ start を生成しない。
   - reason は start と同じ hash-chained row に入り、別 event や後続 setter は設けない。
   - start と `pre-observation-seal` を現在どおり一候補として返し、全 replay 後にのみ永続化させる。

6. [`s8b_attempt_registry.py:315-448`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:315)、[`1109-1205`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1109)

   - `_assert_profile()` に新 policy の object identity、閉集合、ordinal 上限を追加する。
   - facade の `reserve_attempt_slot()` は raw な後書き用文字列ではなく、一回の reservation 引数として4 field を受け、core へそのまま渡す。
   - retry slot の reason 欠落、planned slot への reason 混入、source/reason の cross-over を `_atomic_update()` 前に拒否する。
   - [`_atomic_update():1003-1045`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1003) の replay、strict extension、`os.replace`、parent fsync を耐久化境界として維持する。
   - [`resume_attempt():1765-2071`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1765) には reason 引数を追加しない。start row から読むだけにし、resume 時の後付けを構造的に不可能にする。
   - slot identity と classification claim address は変更しない。

7. [`s8b_holdout_admission.py:217-230`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:217)、[`4554-4740`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4554)

   - `FloorRetryAuthorization` に `reason`、`evidence_sha256` を加える。`source` は現行二択のまま。
   - legacy branch は一意な planned `valid is False` completion の canonical bytes と `excluded_reason` から reason/digest を作る。
   - recovery branch は full core replay 後の recovery row と standalone scheduler receipt から reason/digest を作る。
   - reason を caller や campaign から自由入力させない。
   - [`_attempt_ids():1194-1202`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:1194) は `n_sessions + retry_slots_per_cell` の消費 ticket 数として維持する。これは registry genesis の `remeasurement_ordinals` と別物だが、非 zero ordinal の最大数は同じ `retry_slots_per_cell` に束縛する。
   - [`make_s8b_domain_profile():4447-4451`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4447) に同じ protocol 値を渡す。
   - 推奨案では [`slot_identity 照合:4304-4310`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4304) と [`4470-4477`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4470) は変更しない。

8. [`s8b_floor_attempt_launcher.py:53-76`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:53)、[`444-469`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:444)

   - `FloorAttemptReservation` に remeasurement reservation を持たせ、`_reserve()` から facade へ渡す。
   - `FloorAttemptRegistryGenesis` は、各 cell/repetition について `attempt_ordinal=0..retry_slots_per_cell` の既存 primary slot 全体と、別途 genesis policy を固定する。
   - pre-probe competing のように capture を行わない session も、planned/retry slot の durable start と terminal を残せる no-capture branch を同じ launcher 内へ置く。別の reservation writer は作らない。

9. [`s8b_floor_attempt_launcher.py:548-645`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:548)

   - 機械的支配点は `_launch_floor_attempt()` とする。
   - 順序を次で固定する。

     ```text
     genesis exact replay
       -> reason付き start の atomic publish + parent fsync
       -> pre-probe/no-capture 分岐
       -> _capture()
       -> classification/open/terminal
     ```

   - `_reserve()` が返らなければ `_capture()` へ到達しない。
   - production/test wrapper の双方をこの private core だけへ接続する。

10. [`s8b_floor_campaign.py:5727-6151`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:5727)、[`7568-7645`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:7568)

   - production default measurement を launcher へ接続し、現在の直接 `measure_point()` 呼び出しを certified path から除く。
   - planned start は remeasurement field 全 null。
   - retry start は既存 `retry_ordinal` を registry start の `remeasurement_ordinal` に写し、`FloorRetryAuthorization` の source/reason/evidence を渡す。
   - `attempt_ordinal` は従来どおり同じ cell/round 内の retry start 順から導出する。
   - `_authorized_retry_ordinals()` は runtime に使用済みの campaign ticket 集合であり、常に genesis の `{1..retry_slots_per_cell}` の subsetかつ prefix とする。genesis 自体をこの runtime 集合から作り直してはならない。
   - no-capture pre-probe failure も launcher で terminal 化してから既存 session row を emit する。
   - journal/result schema へ第二軸 field を重複追加しない。journal の既存 `retry_ordinal` と registry start の値を live inspection で照合する。
   - test-only injected `measure_fn` は refreeze 不適格 seam のままだが、production certified path の代替 writer にはしない。

11. 変更しない consumer

   - [`s8b_scheduler_accounting.py:319-350`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_scheduler_accounting.py:319): 4-tuple identity のまま。
   - [`trial_registry.py:1930-2002`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/trial_registry.py:1930): 8c codec、`attempt_index` semantics と bytes は不変。
   - `s8b_floor_contract.py`、`s8b_ratified_freeze.py`、`floor_liveness.py`: journal/result の既存形を変えないため production edit は不要。テストは回帰 canary として走らせる。

## 支配点と、後から緩められないことの論証

支配点は [`s8b_floor_attempt_launcher._launch_floor_attempt():582-590`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:582)。`_reserve()` の atomic publish と fsync が完了した後でのみ `_capture()` を呼ぶ。

現在の production 呼び手数は次のとおり。

- start event の production constructor: **1箇所**。[`attempt_registry_core.py:1564-1576`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1564)。
- `core.reserve_attempt_slot` の production reference: **2箇所**。
  - 8b adapter: [`s8b_attempt_registry.py:1171`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1171)
  - 8c facade: [`trial_registry.py:3013-3023`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/trial_registry.py:3013)
- S8B adapter の `reserve_attempt_slot` production caller: **1箇所**。launcher の [`_reserve():454`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:454)。
- launcher `_reserve()` caller: **1箇所**。[`_launch_floor_attempt():586`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:586)。
- launcher `_capture()` caller: **1箇所**。[`_launch_floor_attempt():589`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:589)。
- `_launch_floor_attempt()` への wrapper: **2箇所**。production [`launch_floor_attempt():660`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:660) と test-only [`_launch_floor_attempt_for_test():688`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_attempt_launcher.py:688)。双方とも同じ順序を通る。

後書きを塞ぐ理由は以下。

- reason は hash-chained start row の一部であり、別の update event を schema に作らない。
- 同じ slot の二度目の start は [`assert_registry_rows():1075-1076`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1075) と [`reserve_attempt_slot():1552-1557`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/attempt_registry_core.py:1552) の双方で拒否される。
- adapter は candidate が旧 bytes の strict extension でない場合、[`s8b_attempt_registry.py:1018-1024`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_attempt_registry.py:1018) で拒否する。
- resume API は reason を受け取らず、既存 start row を読むだけ。
- production campaign から direct measurement を除き、静的 inventory test で今後の bypass 追加も拒否する。

D880 の XOR は次を保持する。

- legacy predicate は [`_is_canonical_failed_planned_trigger():4573-4577`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4573) の「planned かつ `valid is False`」から広げない。
- consume 時は [`len(trigger_sessions) + len(recovery.candidates) != 1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4606) を変更しない。
- trigger 選択時も [`len(recoveries) + len(legacy) > 1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_holdout_admission.py:4714) を変更しない。
- reason/source の検査は候補件数を数えた**後**に行い、候補 predicate に含意されて候補が消える形にしない。
- recovery authority が空である現状も維持する。

理由の閉表は次のとおり。

| source | 受理理由 | 必須 evidence |
|---|---|---|
| ordinal なし | reason/source/evidence は全て `None` | planned start |
| `legacy-failed-session` | `competing_process`、`launch_failure`、`nonfinite_or_partial_output`、`performance_anomaly` | 一意な planned `valid is False` session の canonical digest。reason はその `excluded_reason` と一致 |
| `verified-registry-recovery` | `node_failure`、`scheduler_external_interruption` | full replay 済み recovery row と同一 bytes の standalone scheduler receipt |

通る正例:

- planned session が `performance_anomaly` で terminal になった後、その canonical session digest、source `legacy-failed-session`、reason `performance_anomaly`、`remeasurement_ordinal=1` を start に atomic publishし、その後にだけ capture する。

落ちる負例:

- legacy 向き、発火目的: source `legacy-failed-session`、reason `node_failure`。legacy 集合外として拒否。
- legacy 向き、時点指定: 正しい `performance_anomaly` でも、source digest 欠落または start publish 失敗なら `_capture()` 前に拒否。
- recovery 向き、発火目的: source `verified-registry-recovery`、reason `performance_anomaly`。recovery 集合外として拒否。
- recovery 向き、時点指定: `node_failure` でも standalone receipt が無い、authority が未登録、または recovery row と digest が違えば、session-start の認可前に拒否。
- 共通の後書き負例: capture 後に同じ slot へ別 reason の start を appendし直すと duplicate-start/replay gate で拒否。

## テスト閉包

| test file | 改訂内容・保証 |
|---|---|
| [`test_attempt_registry_core_s8b_profile.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:296) | `/v2` genesis policy、ordinal prefix、source別理由表、planned null union、legacy/recovery の正負、`S8B_RETRYABLE_FAILURE_REASONS` 空を固定 |
| [`test_s8b_attempt_registry.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_attempt_registry.py:267) | reason付き start の atomic durability、exact retry、改変・二重 start・resume 後書き拒否 |
| [`test_s8b_floor_attempt_launcher.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_floor_attempt_launcher.py:268) | `genesis -> reserve/fsync -> capture` の順序、reserve 拒否時 capture 0 回、pre-probe no-capture branch |
| [`test_s8b_holdout_admission.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_holdout_admission.py:1647) | D880 legacy/recovery XOR、candidate count、source別 reason/evidence、recovery authority 空、retry ordinal 上限 |
| [`test_s8b_floor_campaign.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_floor_campaign.py:10591) | recovery fixture の `/v2` 化、planned/statistical/recovery の番号対応、`performance_anomaly` 後の予約、resume での再発行拒否 |
| [`test_attempt_registry_core_equivalence.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_attempt_registry_core_equivalence.py:436) | 原則変更不要。8c legacy/core/facade bytes、public signatures、core 内 8c literal 不在を untouched canary として実走 |
| [`test_s8b_scheduler_accounting.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_scheduler_accounting.py:195) | 新 profile factory 引数を fixture へ渡し、4-tuple slot lookup が変わらないことを固定 |
| [`test_s8b_floor_contract.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_floor_contract.py:327) | campaign `retry_ordinal` の上限・一意性・prefix が genesis 集合と同じ `retry_slots_per_cell` へ束縛される canary |
| [`test_s8b_ratified_verify.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_ratified_verify.py:1373) | journal/result schema を増やさず、既存 retry authorization と historical reverify が維持されることを確認 |
| `test_s8b_floor_stats.py` | 4理由の正本と `rep_integrity_failure` が exclusion class 専用であることの回帰確認 |
| `test_s8b_protocol_builder.py` / `test_s8b_approved.py` | `retry_slots_per_cell` と4理由の approved source が変わらないことを確認 |

現在の production inventory test は [`test_s8b_attempt_registry.py:1584-1599`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/tests/test_s8b_attempt_registry.py:1584) で campaign/admission の2 fileをハードコードしており、glob 在庫検査ではない。これを `orchestrator/campaign/*.py` の glob 走査へ拡張し、次を固定する。

- `s8b_attempt_registry` を importできるのは launcher だけ。
- S8B production で adapter の `reserve_attempt_slot` を呼べるのは launcher だけ。
- `capture_measure_point` を呼べるのは launcher だけ。
- floor campaign は public launcher だけを呼び、`measure_point` の certified direct call を持たない。
- `core.reserve_attempt_slot` の production references は trial facade と S8B adapter の2箇所だけ。

## 規模見積もり

概算の変更行数。テスト fixture の schema field 追加を含む。

| file | 見積もり |
|---|---:|
| `s8b_attempt_profile.py` | 70-100 行 |
| `attempt_registry_core.py` | 130-190 行 |
| `s8b_attempt_registry.py` | 60-100 行 |
| `s8b_holdout_admission.py` | 90-150 行 |
| `s8b_floor_attempt_launcher.py` | 80-140 行 |
| `s8b_floor_campaign.py` | 180-300 行 |
| `s8b_scheduler_accounting.py` | 0-5 行 |
| `trial_registry.py` | 0 行 |
| `s8b_floor_contract.py` | 0-20 行 |
| `test_attempt_registry_core_s8b_profile.py` | 150-220 行 |
| `test_s8b_attempt_registry.py` | 120-180 行 |
| `test_s8b_floor_attempt_launcher.py` | 100-160 行 |
| `test_s8b_holdout_admission.py` | 150-230 行 |
| `test_s8b_floor_campaign.py` | 180-280 行 |
| equivalence / scheduler / contract / ratified tests | 合計 50-100 行 |
| 合計 | 約 1,360-2,075 行 |

最大の振れは、campaign の既存 post-measure projection を launcher terminal builder へ移す量と、pre-probe no-capture branch の共通化量による。

## 親 brief への反論

- **P1 は反論しない。** D1007 [`docs/decisions.md:35273-35283`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/docs/decisions.md:35273) は問題を既存 `S8B_RETRYABLE_FAILURE_REASONS` の拡張として説明し、D1032 [`35995-36009`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/docs/decisions.md:35995) がその後に別軸を選んでいる。したがって「外部 scheduler 証拠限定」は recovery/primary retry 集合へ掛かり、統計的 remeasurement axis の legacy reason 表とは別、という親の読みを支持できる。ただし D1032 単体の文法は広くも読めるので、source別閉表を schema/genesis に明示して曖昧さを残さない。
- **P2 は反論する。** slot identity 追加は、cell-wide の `retry_ordinal` がどの repetition で使われるかを genesis 時に知らないという構造に合わない。完全 cross-product は primary ordinal の uniqueness/prefix と衝突し、holdout、scheduler、classification claim address まで不要に変える。event 配置の方が別軸の意味に合う。
- ただし **P2 の event 案の「schema 据え置き」も反論する。** exact key schema へ field を足す以上 `/v2` が必要。
- **P3 は現状認識を補正する。** launcher 内の reserve-before-capture 順序自体は正しいが、現在は production caller 0 件で支配点ではない。D1007 [`35265-35269`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/docs/decisions.md:35265) と、campaign の直接呼び出し [`5976`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:5976)、[`7585-7595`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-floor-retry-ordinal-axis/orchestrator/campaign/s8b_floor_campaign.py:7585) が証拠。T-1851 で production 接続して初めて支配点になる。
- `session-start` fsync は有用な cross-check だが、同じ耐久 registry 内の理由固定ではないため、最終 authority にはしない。

## 未確認・未実走の事項

- filesystem 制約に従い pytest、build、checker は一切実走していない。上記は静的検査だけ。
- 8b floor の commit 済み run artifact は無いため、実 row の reason 値域や `/v1` migration は検証していない。
- 行数は設計段階の概算で、実装時の helper 共通化により変動する。
- recovery authority は空であるため、recovery 正例は synthetic fixture に限られ、production 発火確認はできない。
- schema `/v2` の canonical golden bytes は実装後に fixture から確定する。既存 artifact を根拠に作ってはならない。

## 総括

推奨設計は、slot identity と `attempt_ordinal` を維持し、`remeasurement_ordinal`、source、reason、evidence digest を `/v2` start event に置く形である。ordinal 集合と source別理由表は genesis で固定し、runtime では既存 `retry_ordinal` をその集合の prefix として消費する。

機械的支配点は production 接続後の `_launch_floor_attempt()` で、reason付き start の atomic publishと fsyncが完了するまで capture を呼ばない。D880 の候補件数 XOR、空の `S8B_RETRYABLE_FAILURE_REASONS`、4-tuple slot identity、8c byte-equivalence は全て維持できる。