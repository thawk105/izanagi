## 1. 規模の実測

[実測] current tree の直接 test 面は、`test_attempt_registry_core_s8b_profile.py` が 55 関数 / 86 node、`test_s8b_attempt_registry.py` が 47 関数 / 74 node、`test_attempt_registry_core_equivalence.py` が 9 関数 / 16 node、合計 **111 関数 / 176 node** である。各 `pytest.mark.parametrize` の case 数を掛け、複数 decorator は直積にした。例は `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:400-432,603-621,1792-1849,2066-2067,2140-2160`、`orchestrator/tests/test_s8b_attempt_registry.py:423-424,677-693,753-875,922-934,1329-1330,1902-1906`、`orchestrator/tests/test_attempt_registry_core_equivalence.py:497-569`。

[実測] private/shared symbol の consumer は直接面の外にもある。`DomainProfile` / `TransitionPolicy` の S8C constructor は `orchestrator/campaign/trial_registry.py:2113-2164`、core の private `_load_registry_bytes` 直接 consumer は同 `:2342-2352`、`record_attempt_terminal` consumer は同 `:3294-3376` にある。`test_trial_registry.py` は 189 関数 / 225 node であり、前 wave と同じ漏れを避けるため全 225 node を閉包へ含める。

[実測] その他の consumer は、holdout の v1 profile/full replay `orchestrator/campaign/s8b_holdout_admission.py:5576-5624` を通る 15 node、B1 marker capability `orchestrator/campaign/s8b_holdout_admission.py:303-368,5082-5103,5140-5227` を通る 57 node、scheduler loader `orchestrator/campaign/s8b_scheduler_accounting.py:319-337` の 1 node、campaign の実 registry recovery helper `orchestrator/tests/test_s8b_floor_campaign.py:11363-11455` の 1 node、launcher の adapter consumer `orchestrator/campaign/s8b_floor_attempt_launcher.py:444-520,637-644` に対する 12 node である。

[実測] 下表の既存回帰 node は群ごとに重複する。A2' 全体の既存回帰 union は **487 node** である。内訳は直接 176 + trial 225 + launcher 12 + holdout 72 + scheduler 1 + campaign 1 である。pytest は実行せず、静的展開だけを用いた。

| 群 | production 追加 | production 変更 | production 削除 | 既存回帰 node | 新設 node |
|---|---:|---:|---:|---:|---:|
| [推測] E1 raw facts / sealed projection / evidence carrier | 300–420 | 150–210 | 0–20 | 430 | 40–50 |
| [推測] E2 台帳専用 4 語 | 20–35 | 10–20 | 0 | 176 | 10–14 |
| [推測] E3 schema 別 exact profile validator | 80–120 | 70–100 | 20–40 | 419 | 20–28 |
| [推測] E4 publish / marker / claim v3 / resume / sealed API | 350–470 | 260–340 | 40–80 | 143 | 35–45 |
| [推測] 重複 hunk 除去後の A2' 合計 | 700–900 | 500–650 | 60–110 | 487 union | 95–120 union |

[実測] E4 の主変更 block だけで、claim `orchestrator/campaign/s8b_attempt_registry.py:1017-1184`、locked update / create / reserve `:1190-1485`、classification / marker / terminal `:1488-2011`、resume `:2053-2367` の約 1,350 行を横断する。さらに同 file には `S8BAttemptSlot` / `S8BSlotIdentity` / v1 layout の hard-coded 参照が 29 行ある (`:122,163-171,319,459,975-976,1020,1035,1043,1061,1114,1178,1335-1337,1370,1393-1396,1434,1494-1499,1753,1886,2057-2060`)。

[推測] 見積りが外れるなら、前 wave と同じく**上振れ**する。主因は、現在の 8 signature では運べない raw-facts carrier、`repetition_evidence` の production 配線、分類 policy の固定、terminal row への再 replay 可能な fact envelope、claim v2/v3 二系統の型分岐、29 件の v1 hard-code 保存である。親の 800–1,000 LOC はこれらを含んでいないため、200–650 LOC 程度の上振れ余地がある。

## 2. (P1-a) — 1 wave 判定と分割

[推測] **(P1-a) は refuted** と判定する。A2' は 1,260–1,660 changed LOC、95–120 新設 node、487 既存回帰 node の規模であり、前 wave の約 900 LOC より大きい。

[実測] 親候補の「E1+E2+E3 を先、E4 を後」は production 整合条件を満たさない。E3 が v2 を受理すると、`create_attempt_registry()` は `_assert_profile` 後に protocol を渡さず `_entry_paths()` を呼ぶ (`orchestrator/campaign/s8b_attempt_registry.py:1343-1350`)。一方 v2 profile の root は `{protocol_sha256}` を含む 2 段 path である (`orchestrator/campaign/s8b_attempt_profile.py:516-523`)。E4 の path dispatch より先に E3 を開けば、v2 が誤った 1 段 destination へ進む。

[実測] E3 の前に E1+E2 だけを置けば、adapter の 5 gate は引き続き v2 を拒否する (`orchestrator/campaign/s8b_attempt_registry.py:519,1343,1376,1410,2082`)。したがって v1 production は動作を変えず、v2 write path は未開通のまま保てる。

[推測] 規模上の境界は次が最小である。

| checkpoint | 内容 | production 整合 |
|---|---|---|
| [推測] A2α | E1+E2、二つの sealed terminal API、launcher-owned fact carrier。E3 はまだ v1-only | v1 unchanged、v2 public mutation は全拒否 |
| [推測] A2β | E3、generation publish、marker update、claim v3、v2 resume | v2 を path・claim・marker と同時に開く |

[実測] ただし現在の `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` は v2 の理由集合が空であることを明示的に要求する (`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2172-2216`)。E2 と「既存期待値を変えない」を同時に満たす実装は存在しない。

[推測] 従って分割の必須 3 条件は、(1) production 整合は上の A2α/A2β なら満たす、(2) 既存 test green は空集合 pin の扱いが未裁定で現状満たせない、(3) 後半 signature は raw-facts handoff の補正後なら固定可能、という判定になる。現状のまま実装へ進める分割案ではなく、ユーザー裁定後の条件付き境界である。

[実測] 両 checkpoint とも land 対象ではない。D1341 は配線と proof-chain 束縛を同じ変更単位で land するよう要求する (`rulings-verbatim.md:122-135`)。

## 3. (P1-b) — 台帳専用 literal

[推測] **(P1-b) は real** と判定する。D1113 は四つの意味区分と「台帳専用の閉じた語彙」を承認済みであり (`rulings-verbatim.md:1-15`)、literal の綴りだけでは新しい意味区分を追加しない。親 plan で確定してよく、literal 選択だけをユーザー裁定へ戻す必要はない。

[推測] 採る literal は次の 4 語とする。

| launcher/raw cause | 台帳専用 literal | sealed record の比較対象 |
|---|---|---|
| [推測] post-probe competition | `measurement_environment_conflict` | `excluded_reason == "competing_process"` |
| [推測] execution unavailable | `measurement_execution_unavailable` | `excluded_reason == "launch_failure"` |
| [推測] incomplete/nonfinite sample | `measurement_sample_incomplete` | `excluded_reason == "nonfinite_or_partial_output"` |
| [推測] CV threshold exceeded | `measurement_dispersion_exceeded` | `excluded_reason == "performance_anomaly"` |

[推測] 実装上は frozen word を key とする `dict[frozen_reason, ledger_reason]` を作らない。launcher-owned facts から private cause enum を導出し、`cause -> ledger literal` を hard-codeする。sealed record 側も `valid` / `excluded_reason` を導出入力にせず、その record 内の probe・throughput・execution・rep facts から同じ cause を独立再計算し、最後に自己申告 field と比較する。

[推測] 意味上は 1 対 1 でも、凍結語そのものは新軸を開く capability にならない。`excluded_reason` を反転しても raw cause が変わらず validator が拒否するため、D1113 が懸念した「既存 field の権限増加」は復活しない。

[実測] 閉集合は四層で強制する。定数と factory は `orchestrator/campaign/s8b_attempt_profile.py:525-533,629-662`、genesis と profile 集合の exact equality は `orchestrator/campaign/attempt_registry_core.py:690-702`、terminal の retryable/terminal-failure 排他は同 `:934-977`、adapter の expected profile exact comparison は `orchestrator/campaign/s8b_attempt_registry.py:387-444` に置く。E1 の cause switch に default branchを持たせず、未知 cause は拒否する。

[実測] v2 は classification receipt の frozen reason と terminal の ledger reason が異なるため、現行 `require_terminal_reason_equals_classification=True` (`orchestrator/campaign/s8b_attempt_profile.py:652-662`) のままでは四語すべてが `orchestrator/campaign/attempt_registry_core.py:1297-1304` で拒否される。v2 factory だけこれを `False` にし、classification echo は `:1289-1296` で保持し、ledger reason の正当性は E1 validator に移す。v1 は `True` のまま変えない。

## 4. (P1-c) — E1 と D1113 の両立

[実測] 二つの裁定は非同値である。D1113 は canonical bytes からの機械導出を要求する (`rulings-verbatim.md:6-15`)。前 wave 段 4 は、返す status / reason / primary value を launcher-owned raw facts から導出し、sealed record は比較専用とした (`s4-adjudication.md:42-68`)。

[推測] 両立形そのものは存在する。次の二重導出を採る。

1. [推測] `raw_projection = classify(probe_outcome, classification_receipt, throughputs, execution_failures, repetition_evidence, policy)` とする。
2. [推測] `sealed_projection = classify(raw subfields decoded from canonical sealed bytes, policy)` とする。ただし戻り値としては使用しない。
3. [推測] `raw_projection == sealed_projection`、`serialize_session_line(sealed_session_record) == raw_output_bytes`、および `valid` / `excluded_reason` / `session_median` の自己申告が raw projection と一致することを要求する。
4. [推測] terminal row には raw projection を書き、sealed projection は比較結果としてのみ使う。

[推測] この形では返却値の直接 source は raw facts である一方、受理された値は canonical bytes からも一意に再導出できるため、両裁定を同時に満たす。

[実測] しかし固定された二つの sealed API は `observation` / `failure`、`sealed_session_record`、`finished_at` しか受けない (`verbatim/s2-plan.md:304-315`)。現行 handle state にあるのは classification receipt bytes と raw-output digestまでであり、probe、throughputs、execution failures、rep evidence、policy は保持しない (`orchestrator/campaign/s8b_attempt_registry.py:163-185`)。

[実測] raw facts が揃うのは launcher が captured token を open した後である (`orchestrator/campaign/s8b_floor_attempt_launcher.py:614-628`)。その後 adapter に渡す既存 terminal call は self-reported terminal fieldsだけである (`:633-644`)。したがって固定 8 signature のままでは二重導出を実装できない。

[推測] **(P1-c) は「理論上両立可能だが、現境界では refuted」**である。ユーザー裁定には次の択一を返すべきである。

- [推測] 推奨: 新設 sealed API 二つを、`probe_outcome` / `throughputs` / `execution_failures` / `repetition_evidence` の keyword-only 引数を持つ形へ補正する。classification receipt は handle 内の durable bytesを adapter が供給し、policy は承認済み定数から作る。
- [推測] 代案: 8 signature を維持し、新しい `bind_s8b_terminal_evidence(...) -> evidence-bound handle` を第 9 境界として追加する。
- [推測] 非推奨: sealed record 内の自己申告だけから返却 projection を作る。これは前 wave 段 4 を破る。
- [推測] 非推奨: canonical bytes 比較を捨てて raw projection だけを信頼する。これは D1113 を破る。

## 5. (P1-d) — 5 入力の実在と到達値

| 入力 | owner / 生成点 | current production の到達値 | 判定 |
|---|---|---|---|
| [実測] `probe_outcome` | launcher の `_owned_post_probe()` が `{rc,stdout,stderr,competing}` を生成する (`orchestrator/campaign/s8b_floor_attempt_launcher.py:238-267`) | [実測] 成功時の `rc` は 0 または1。`rc=1` は空 stdout/stderr・`competing=False`、`rc=0` は非空 stdout で own PID 以外があれば true。その他は例外 (`orchestrator/calibrator/runner.py:327-379`) | [実測] 実在・到達可能 |
| [実測] `classification_receipt` | core `_receipt_payload()` が exact mapping を作り (`orchestrator/campaign/attempt_registry_core.py:1663-1715`)、adapter が canonical bytes と claim を publishする (`orchestrator/campaign/s8b_attempt_registry.py:1648-1723`) | [実測] pre-observation reason は launcher precedence により `None` / `competing_process` / `launch_failure` (`orchestrator/campaign/s8b_floor_attempt_launcher.py:378-385,590-610`) | [実測] 実在・到達可能 |
| [実測] `throughputs` | token open 後、runner が `ScalePoint.throughputs` へ appendする (`orchestrator/calibrator/runner.py:933-1053`、型は `orchestrator/calibrator/model.py:54-76`) | [実測] 長さ 0..reps、各要素は `float`。parser は通常の NaN/Inf literal を None にするが、float 変換結果の正値性・有限性はここでは検査しない (`orchestrator/calibrator/benchparse.py:39-63`) | [実測] 値は実在するが adapter へ未配線 |
| [実測] `execution_failures` | runner が `OSError` だけを `MeasurementLaunchFailure` に sanitizeする (`orchestrator/calibrator/runner.py:54-90,659-679`)。launcher は `{exception_type,errno,message}` に射影する (`orchestrator/campaign/s8b_floor_attempt_launcher.py:321-359`) | [実測] 現行 launcher では `rep_observations=None` のため最初の pre-open launch failure で loop が切れ、長さは 0 または1 (`orchestrator/calibrator/runner.py:847-908`)。timeout・parse error等の post-open `open_error` はこの sequence に入らない (`orchestrator/campaign/s8b_floor_attempt_launcher.py:614-623`) | [実測] 狭い範囲だけ到達可能 |
| [実測] `repetition_evidence` | runner は caller が non-None sink を渡した場合だけ `rep_observations` を生成する (`orchestrator/calibrator/runner.py:938-1050`) | [実測] production launcher の allowlist は `rep_observations` を含まず (`orchestrator/campaign/s8b_floor_attempt_launcher.py:32-46`)、明示指定も拒否する (`:408-425`; test pin `orchestrator/tests/test_s8b_floor_attempt_launcher.py:600-645`)。`_capture()` も内部 sink を作らない (`orchestrator/campaign/s8b_floor_attempt_launcher.py:429-441`) | [実測] **到達不能** |

[実測] sealed session record 自体には `throughputs`、`exec_failures`、`rep_observations`、`rep_integrity_failures`、`probe_before`、`probe_after` が存在する (`orchestrator/campaign/s8b_ratified_freeze.py:262-269`)。ただしその record は campaign `_finish_session()` が組み立てる自己申告である (`orchestrator/campaign/s8b_floor_campaign.py:6182-6218`)。

[実測] `FloorAttemptTerminal.campaign_record` は現在どこからも読まれず、launcher は `raw_output_bytes` と同じ record であることも確認しない (`orchestrator/campaign/s8b_floor_attempt_launcher.py:125-142,628-644`)。

[推測] 到達可能にするには launcher `_capture()` が private `rep_observations` sink を必ず作り、token と一緒に保持する必要がある。open 後に `throughputs`、structured open/launch failures、`{"reps_expected": 5, "observations": (...)}` を exact mapping に正規化する。caller の `keyword_arguments` へ `rep_observations` を開放してはならない。

[実測] classification policy の固定値は既に `APPROVED_REPS=5` の再輸出と `APPROVED_SESSION_CV_MAX="0.10"` にある (`orchestrator/campaign/s8b_approved.py:41-58`)。新しい caller 選択値にせず、`S8BClassificationPolicy` の exact singleton をこれらから構築できる。

[推測] **(P1-d) は refuted** である。現状の `repetition_evidence` を要求する validator は恒真な保証になるため実装してはならず、先に launcher-owned sink と adapter handoff を到達可能にする必要がある。

## 6. E1 / E2 の file:line 実装 plan

[推測] `orchestrator/campaign/attempt_registry_core.py:15,168-195` で `field` を importし、次を加える。

```python
retryable_terminal_opens_next_attempt: bool = field(
    default=True, kw_only=True
)

terminal_row_validator: Callable[[Mapping[str, Any]], None] | None = field(
    default=None, kw_only=True
)
```

[推測] `orchestrator/campaign/attempt_registry_core.py:1106-1144` で、前 slot が retryable terminal でも `retryable_terminal_opens_next_attempt is False` なら recovery `attempt_ordinal` を開かない。v1/S8C の default `True` は現行挙動を保存する。

[推測] `orchestrator/campaign/attempt_registry_core.py:1310-1315` で既存 classification equality と null matrix の後に `terminal_row_validator(row)` を呼ぶ。v1/S8C の `None` は完全な no-op とする。

[推測] `orchestrator/campaign/s8b_attempt_profile.py:490-504` で v2 terminal schemaだけに、`sealed_session_record` と durable raw-fact envelopeを追加する。v1 `_S8B_EVENT_KEYS` は 1 byte も変えない。

[推測] `orchestrator/campaign/s8b_attempt_profile.py:525-556` に四 literal、private cause enum、`S8BClassificationPolicy`、`S8BTerminalProjection` を置き、`serialize_session_line()` の直後 `:556-568` に境界どおりの `derive_s8b_terminal_projection(...)` を置く。

[推測] `derive_s8b_terminal_projection()` は、competition → execution unavailable → rep/sample incomplete → dispersion → observed の順で raw projection を作る。invalid 四形は `retryable-failure` + 台帳専用 reason + `primary_value=None`、valid は `observed` + reason None + raw median とする。

[推測] `orchestrator/campaign/s8b_attempt_profile.py:629-672` の v2 factoryは、`retryable_reasons` を四語、`require_terminal_reason_equals_classification=False`、`retryable_terminal_opens_next_attempt=False`、`terminal_row_validator=_assert_s8b_v2_terminal_row` とする。v1 factory `:577-626` は defaults のままにする。

[推測] `orchestrator/campaign/s8b_attempt_registry.py:163-185` の v2 stateには durable raw-fact envelopeを保持する。ただし、固定 sealed APIだけでは値を注入できないため、4節のユーザー裁定が先決である。

## 7. E3 の設計

[実測] current `_assert_profile()` は可変 budget/authorityを読み、必ず v1 `make_s8b_domain_profile()` を再構築する (`orchestrator/campaign/s8b_attempt_registry.py:316-355`)。その後 schema/layout/codec/callable identityを exact 比較する (`:356-448`)。

[推測] 現行比較本体を `_assert_exact_profile(profile, expected)` へ機械抽出し、schema identityでだけ factoryを分ける。

```python
if profile.schema is profile8b.S8B_SCHEMA_PROFILE:
    expected = profile8b.make_s8b_domain_profile(...)
elif profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE:
    expected = profile8b.make_s8b_v2_domain_profile(...)
else:
    fail_closed()
_assert_exact_profile(profile, expected)
```

[推測] schema の hostile `__eq__` を避けるため `is` で dispatchする。schema/layout/codec/functionは identity、文字列・tuple・frozenset・boolは exact type + exact valueで比較する現行規則を保存する。

[推測] exact comparisonには次を必須で足す。

- [推測] `profile.terminal_row_validator is expected.terminal_row_validator`
- [推測] `type(transition.retryable_terminal_opens_next_attempt) is bool`
- [推測] `transition.retryable_terminal_opens_next_attempt is expected_transition.retryable_terminal_opens_next_attempt`

[実測] `_assert_profile` の direct call site は全 5 件である。handle path `orchestrator/campaign/s8b_attempt_registry.py:519`、create `:1343`、read `:1376`、reserve `:1410`、resume `:2082`。同 symbol の production 全体検索ではこの定義と 5 call 以外にない。

[実測] `DomainProfile(...)` と `TransitionPolicy(...)` の production constructor は現在それぞれ 3 件である。v1 factory `orchestrator/campaign/s8b_attempt_profile.py:599-616`、v2 factory `:645-662`、S8C `orchestrator/campaign/trial_registry.py:2113-2164`。このうち「変更せず壊してはならない caller」は v1 と S8C の各 2 件であり、上記 keyword-only defaults がそれを保存する。

[推測] v1 受理集合は、現行 v1 exact comparatorを同じ条件式のまま helperへ移すことで保存する。新設 node `test_schema_dispatch_preserves_exact_v1_profile_acceptance_matrix` を、canonical profile、可変 budget/authority 正例、既存 14 mutation、new field 2 mutationの parametrize nodeとして置く。

[実測] 既存の中心 node は `test_adapter_rejects_every_mutable_frozen_profile_surface[...]` (`orchestrator/tests/test_s8b_attempt_registry.py:753-884`) と `test_adapter_allows_only_budget_and_recovery_authority_values_to_vary` (`:906-919`) である。v1 lifecycle の全 74 adapter nodeと real launcher adapter node `orchestrator/tests/test_s8b_floor_attempt_launcher.py:510-597` を回帰閉包に含める。

[推測] v1 を 1 mm も変えない保証は、「旧 comparator本体を再実装せず抽出する」という code identity、上記 exact mutation matrix、既存 adapter 74 nodeの三つで固定する。

## 8. E4 の 8 signature

[実測] 下表の current call-site 全数は、worktree 内の全 `*.py` に対して symbol 名を production/test双方で検索し、定義行を除外して数えた。private symbol は公開 API 表に頼らず名前そのもので検索した。

| signature | 実装位置 / 消費 symbol | 変更する既存 call site 全数 |
|---|---|---|
| [推測] `_publish_registry_generation_create_only(...)` | `s8b_attempt_registry.py:933-968` の `_publish_create_only` 後。`_ensure_durable_directory`、`_publish_create_only`、`_fsync_directory` を消費 | [実測] create の `_publish_create_only` 1 件 `:1360-1362` を schema dispatchへ変更 |
| [推測] `_atomic_update_with_consumption_marker(...)` | `_atomic_update()` 後 `:1307-1328`。`_run_prelock_snapshot_hook`、`admission._locked`、`marker.use`、`_atomic_update_locked` を消費 | [実測] reserve の `_atomic_update` 1 件 `:1463-1469` を v2 branchで変更 |
| [推測] `reserve_attempt_slot(..., consumption_marker=None)` | `:1389-1485`。v1 branchは既存 `_atomic_update`、v2 branchは marker wrapper | [実測] external production caller 1 件 `s8b_floor_attempt_launcher.py:454-469`、direct test helper 1 件 `test_s8b_attempt_registry.py:217-225`。defaultにより既存 v1 callerのテキスト変更は0 |
| [推測] `record_sealed_attempt_terminal(...)` | legacy terminal `:1908-1960` の後。core terminal、session serializer、E1 deriveを消費 | [実測] current production terminal callerは launcher 1 件 `s8b_floor_attempt_launcher.py:637-644`。ただし固定 signatureのまま変更するのは raw handoff 不足で不可 |
| [推測] `record_sealed_classified_failure_terminal(...)` | legacy failure terminal `:1963-2010` の後。classification artifacts、core terminal、E1 deriveを消費 | [実測] existing production caller 0、existing test caller 0。legacy API の test callerは `test_s8b_attempt_registry.py:635` 1 件で変更しない |
| [推測] `resume_attempt(..., consumption_marker=None, ...)` | `:2053-2367`。generation path、claim v2/v3 reader、marker.use を schema dispatch | [実測] production caller 0、test caller 4 件 `test_s8b_attempt_registry.py:1178,1206,1244,1475`。defaultsにより v1 call変更0 |
| [推測] `_slot_address_payload_v3(*, binding, slot)` | v1 helper `:1017-1028` の隣。binding codecと v2 slot codecを消費 | [実測] existing v1 payload callは全3件 `:1039,1075,1132`。それぞれを slot type dispatchへ変更 |
| [推測] `_assert_legacy_consumed_marker(...)` | current `_assert_consumed_marker` `:1749-1795` を renameし、内容は不変 | [実測] call site は全2件 `:1825,2338`。v1 は rename先、v2 は marker capability pathへ分岐 |

[推測] create/read/reserve/resume の `_entry_paths()` 呼出し `s8b_attempt_registry.py:1346,1378,1428,2115` は、v2 のときだけ `protocol_sha256=binding.protocol_sha256` を渡す。classification/observation/terminal/recovery の handle pathも stateに保存した generation pathを使い、v1 の 1 段 pathを再計算しない。

[推測] claim v3 は `_CLASSIFICATION_CLAIM_SCHEMA` / `_CLAIM_KEYS` (`s8b_attempt_registry.py:53-68,1089-1107`) を v1用として残し、新しい schema/key setを追加する。v3 addressは freeze/protocol/schedule binding、freeze-holdout/configuration/repetition/measurement/attempt ordinal、schedule-row digestを含める。

[推測] `_classification_claim_path()` の call siteは全2件 `:1117-1119,1690-1692`、`_claim_document()` は1件 `:1664-1676`、`_classification_claim()` は3件 `:1510-1514,1690-1692,2157-2159` である。すべて slot typeによる v2/v3 dispatchへ変え、v1 claim v2 readerとfilename digestは保存する。

[推測] marker wrapperでは prelock hookを lock 前に1回だけ実行し、`marker.use(..., repetition=slot.repetition, attempt_ordinal=slot.measurement_ordinal)` の action内から `_atomic_update_locked` を呼ぶ。B1 markerの第4軸が journal retry ordinalであることは `orchestrator/campaign/s8b_holdout_admission.py:4961-5001` に固定されている。

[推測] `_atomic_update_locked` 冒頭には live lock guardを足す。ただし marker.useにも `orchestrator/campaign/s8b_holdout_admission.py:5172,5220-5227` の再検査があるため、変異は片側 SURVIVED と多層同時 KILLED の対で測る。

## 9. 変異事前登録

| ID | 消すもの | 期待 | 単一理由性 |
|---|---|---|---|
| [推測] M1a | 新設 sealed producer `s8b_attempt_registry.py:1908-2011` 後の raw projection 呼出しだけ | SURVIVED | core replay validatorが同じ candidateを再検査する |
| [推測] M1b | M1a + `attempt_registry_core.py:1310-1315` に足す terminal validator call | KILLED | 両層を消した時だけ自己申告 valid/reason反転が受理される |
| [推測] M2 | core terminal validator callだけ | KILLED | producerを通らない、正しく rechainした historical rowを `load_attempt_registry` へ直接与える。現行 parse/null matrixは sealed object内部を見ない (`attempt_registry_core.py:892-984`) |
| [推測] M3 | `serialize_session_line(record)` と launcher-owned `raw_output_bytes` の equality | KILLED | 現行 `_captured_state` は raw bytesの hashだけを持ち、record mappingとの対応を検査しない (`s8b_attempt_registry.py:1798-1804`) |
| [推測] M4 | private cause→literal switchの1 arm | KILLED | 別の許可済み ledger literalへ置換すれば null matrixは通る。v2 classification equalityは意図的に falseなので E1 validatorだけが理由すり替えを拒否する |
| [推測] M5 | `_assert_profile` の `terminal_row_validator` identity比較 | KILLED | `dataclasses.replace(v2, terminal_row_validator=None)` を止める他層はない |
| [推測] M6 | `_assert_profile` の `retryable_terminal_opens_next_attempt` exact比較 | KILLED | forged v2 policyによる recovery ordinal開始を profile gate以外は止めない |
| [推測] M7a | `_atomic_update_locked` に足す live-lock guardだけ | SURVIVED | marker経路では `marker.use` と `_current_floor_attempt_consumption_identity_locked` が同じ lockを再検査する (`s8b_holdout_admission.py:5009,5172`) |
| [推測] M7b | M7a + admission側 `:5009,5172` の全三層 | KILLED | inactive/forged lockで actionが実行される counterfactualを直接観測する |
| [推測] M8a | generation publish側の parent symlink検査だけ | SURVIVED | `_read_regular_bytes()` が parent componentを再検査する (`s8b_attempt_registry.py:531-547`)。前 wave M5と同じ構図 |
| [推測] M8b | M8a + `_read_regular_bytes` の parent/no-follow検査 | KILLED | complete generation symlinkが publish対象になる |
| [推測] M9 | v3 expected claim identityの `protocol_sha256` 比較 | KILLED | exact key gateは値を見ず、receipt/core rowにも claim fieldとの equalityはない (`s8b_attempt_registry.py:1123-1173`) |
| [推測] M10 | v3 addressから `measurement_ordinal` を除く | KILLED | measurementだけ異なる2 claimが同じ create-only pathへ衝突する |
| [推測] M11 | marker.useへ渡す ordinalを `measurement_ordinal` から recovery `attempt_ordinal` に変える | KILLED | B1 capability identityが `s8b_holdout_admission.py:4961-5001,5185-5217` で拒否する一層だけ |
| [推測] M12 | resume の v2 marker branchを legacy raw marker readerへ戻す | KILLED | current-generation positive resumeが legacy exact key set `s8b_attempt_registry.py:1749-1795` で拒否される |

[実測] E1にも前 wave M5と同じ多層構図がある。producer derive と replay validatorは同じ candidateを二重検査し、lockは adapter + marker.use + admission identityの三層、generation symlinkは publish helper + `_read_regular_bytes` の二層である。片側変異を無条件に KILLED 登録してはならない。

## 10. 受理集合の方向

| 変更 | 方向 | 承認元 |
|---|---|---|
| [推測] E1 raw fact / sealed bytes equality | v2 を狭める、v1不変 | 前 wave 段4 E1「launcher-owned raw factsから再導出、自己申告は比較のみ」(`s4-adjudication.md:47-68`) |
| [推測] E2 四 ledger reason の retryable受理 | 広がる。同じ語の terminal-failureは狭まる | D1113 (`rulings-verbatim.md:1-15`) |
| [推測] E2 v2 classification reason equalityを false | 広がるが E1 exact validatorで閉じ直す | frozen語を新軸権限に使わない D1113 |
| [推測] E3 exact v2 profile受理 | v2だけ広がる、v1不変 | 前 wave 段4 E3 (`s4-adjudication.md:79-84`) |
| [推測] E4 protocol世代別2段 path | 広がる | D1193 (`rulings-verbatim.md:37-57`) |
| [推測] E4 世代横断budget | 狭まる | D1340 (`rulings-verbatim.md:101-120`) |
| [推測] E4 marker必須 reserve/resume | v2を狭める、v1不変 | 前 wave 段4 E4 (`s4-adjudication.md:86-88`) |
| [推測] E4 claim v3 full binding | v2を狭める、v1 claim v2不変 | 前 wave固定 E4 boundary |
| [推測] E4 sealed terminal API | v2だけ広がる | E1 validatorと同時にだけ開く前 wave段4 E1/E2/E4 |
| [推測] 既存 v1 public API / return types / 1段 path / claim v2 / legacy marker | 不変 | brief 不変条件 (`brief.md:31-49`) |

[推測] 承認元のない拡大は上表にない。特に repetition evidenceを caller argumentとして自由化する案、sealed self-reportだけを権限化する案、v1 profileを v2 validatorへ流す案は実装しない。

## 11. 過剰拒否の正例

[推測] P1 — v1 canonical 正例は、`make_s8b_domain_profile(...)`、4軸 `S8BAttemptSlot(..., attempt_ordinal=0)`、1段 `floor-attempt-registries/<freeze>/registry.jsonl`、claim v2、legacy consumed markerからなる既存 lifecycleである。全 field/defaultは `s8b_attempt_profile.py:577-626` と `s8b_attempt_registry.py:1017-1173,1331-1485` の現形を保つ。

[推測] P2 — v2 observed 正例は、`probe_outcome={"rc":1,"stdout":"","stderr":"","competing":False}`、classification receipt reason `None`、`throughputs=[100.0,101.0,99.0,100.0,100.0]`、`execution_failures=[]`、5件すべて `returncode=0/counter_status="complete"` の repetition evidence、sealed record `valid=True, excluded_reason=None, session_median=100.0` である。statusは `observed`、reasonは None、primaryは100.0で通り続ける。

[推測] P3 — v2 competition 正例は、`probe_outcome={"rc":0,"stdout":"999 ycsb_other.exe\n","stderr":"","competing":True}`、receipt reason `competing_process`、sealed record `valid=False, excluded_reason="competing_process"` である。terminalは `retryable-failure / measurement_environment_conflict / primary=None` とする。

[推測] P4 — v2 partial 正例は、reps_expected=5 に対して `throughputs=[100.0,101.0]`、残り3 repが `returncode=None/counter_status="incomplete"`、sealed reason `nonfinite_or_partial_output` である。terminal reasonは `measurement_sample_incomplete` とする。

[推測] P5 — v2 dispersion 正例は、`throughputs=[1.0,1.0,1.0,1.0,2.0]`、全 rep complete、CVが承認閾値0.10を超え、sealed reason `performance_anomaly` である。terminal reasonは `measurement_dispersion_exceeded` とする。

[推測] P6 — claim/marker正例は、同じ freeze/config/repetitionでも protocol、schedule、measurement ordinal、recovery ordinalが完全一致し、marker.useへ `repetition=slot.repetition` と `attempt_ordinal=slot.measurement_ordinal` を渡す形である。v1の recovery ordinalは従来どおり v1 claim addressに残る。

## 12. (P1-e) — 検査範囲

[推測] **(P1-e) は post-implementation acceptance として real** である。production `launch_floor_attempt()` は定義と test wrapper以外に callerがなく (`orchestrator/campaign/s8b_floor_attempt_launcher.py:548-688`)、新しい Pegasus measurement本走は要求されない。

[推測] 実装後の焦点集合は直接176 node、launcher12 node、marker57 nodeに新設95–120 nodeを加える。consumer acceptanceは既存487 node unionを含める。現在の read-only plan sessionではpytest結果を根拠にしない。

## 総括

- [推測] A2' は **1 waveに収まらない**。規模は約1,260–1,660 changed LOC / 95–120新設node / 487既存回帰node。条件付き境界は A2α=`E1+E2+sealed terminal/raw carrier`、A2β=`E3+残りE4` である。
- [実測] 親候補の `E1+E2+E3 / E4` 分割は、E3が v2を受理した後も create pathが protocolを渡さないため production整合条件を破る (`s8b_attempt_registry.py:1343-1350`; `s8b_attempt_profile.py:516-523`)。
- [推測] (P1-a) refuted。
- [推測] (P1-b) real。literalは親で確定可能で、推奨4語は `measurement_environment_conflict` / `measurement_execution_unavailable` / `measurement_sample_incomplete` / `measurement_dispersion_exceeded`。
- [推測] (P1-c) refuted as written。二重導出なら両立するが、固定 sealed APIが raw factsを運ばない。
- [推測] (P1-d) refuted。`repetition_evidence` は production launcherから到達不能で、execution failure surfaceも現在0/1件の pre-open OSErrorに限られる。
- [推測] (P1-e) real as future acceptance。新しい performance測定は不要だが、このセッションではpytestを根拠にしていない。
- [推測] ユーザー裁定 1: sealed API二つへ raw factsを追加するか、第9の evidence-bound handle APIを追加するか。推奨は、新設 sealed API自体へ keyword-only raw factsを追加する形。
- [推測] ユーザー裁定 2: `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell` の空集合 pin (`test_attempt_registry_core_s8b_profile.py:2205-2206`) を、E2の四語 exact pinへ置き換えることを「テストを甘くする期待値変更」ではなく A1' incomplete-state assertion の明示的 supersede として許すか。許さなければE2は実装不能。
- [実測] 指定された必読5資料はすべて読めた。各全文範囲は `brief.md:1-135`、`rulings-verbatim.md:1-155`、`s4-adjudication.md:1-182`、前 wave `README.md:1-260`、`verbatim/s2-plan.md:1-489`。
- [推測] 確かめていない事実は、pytestの実結果、mutation実走結果、live Pegasusでの具体的な throughput/probe値、実装後の確定LOC/node数である。