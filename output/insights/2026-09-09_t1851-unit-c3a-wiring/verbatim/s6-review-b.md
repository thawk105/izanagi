## 総括

静的レビューでは、受入前に解消すべき real 所見が 4 件ある。最重要は、competing session に canonical classifier が拒否する合成 probe payload を記録する点と、campaign が launcher の module attribute 経由で adapter 境界を迂回する点である。  
行番号 pin、perf inventory、凍結 23 bytes、`FORMULA_ID`、v4 consumer の fail-closed 性は維持されている。  
既存 test の反転、緩和、削除、skip、xfail、deselect は無いが、親が名指ししていない既存 fixture 変更が 1 箇所ある。  
pytest、campaign、性能測定は実行していない。

## 所見 RB-1 — competing session が不可能な probe payload を記録する

**real、[実測]、重大**

production の competing 分岐は、launcher が実測した raw probe を捨て、`{"rc": 0, "stdout": "", "stderr": "", "competing": True}` を合成して journal/session へ渡す。  
根拠: `orchestrator/campaign/s8b_floor_campaign.py:8954-8969`。

しかし canonical classifier は `rc == 0` かつ空 stdout を `inconsistent-output` として拒否する。  
根拠: `orchestrator/calibrator/runner.py:327-365`、`orchestrator/campaign/s8b_floor_campaign.py:1695-1706`。

`verify_floor_artifact` と holdout inspector は competing exemption で bool しか見ないため、この不可能な組を拒否しない。  
根拠: `orchestrator/campaign/s8b_floor_stats.py:453-466`、`orchestrator/campaign/s8b_holdout_admission.py:6608-6615`。

成果物影響: production journal/result が実際には観測していない probe bytes を証拠として保持し、それでも v5 self-check を通過できる。

推奨: competing 分岐でも launcher が封印した実 `probe_before` をそのまま記録できる契約に直し、合成 tuple を除去するまで受入れない。

## 所見 RB-2 — adapter 非依存の AST 境界を module attribute 経由で迂回している

**real、[実測]、重大**

campaign は直接 import を避けつつ、次のように launcher の module attribute から adapter、profile、core へ到達している。

- `s8b_floor_campaign.py:8702-8704`
- `s8b_floor_campaign.py:8785`
- `s8b_floor_campaign.py:8922-8926`
- `s8b_floor_campaign.py:9014-9017`

既存 guard は import 名、AST `Name`、文字列に `s8b_attempt_registry` が現れるかだけを検査するため、この間接参照を検出しない。  
根拠: `orchestrator/tests/test_s8b_attempt_registry.py:2245-2291`。

成果物影響: campaign が registry profile、core canonicalization、prefix capture の直接 consumer となり、「campaign は sealed adapter を公開されない」という既存の所有境界を実質的に失う。

推奨: `launcher.attempt_registry` / `launcher.profile8b` 経由を除去し、裁定済みの狭い owner surface だけを使う。既存境界を緩める方向では解消しない。

## 所見 RB-3 — 複数 clean attempt の adapter 修正が提供報告に存在しない

**real、[実測]**

`out-s5-b.md:106-124` は、reserve・classify・observation の plain profile 再検証を未解決 blocker と報告している。`out-s5-a2.md` は ordinal 修正のみ、`out-fix1.md:3-12` は launcher test のみを報告している。

一方 HEAD には、三つの transition で `_terminal_validating_profile()` を注入する追加変更がある。

- `s8b_attempt_registry.py:2557-2585`
- `s8b_attempt_registry.py:2782-2844`
- `s8b_attempt_registry.py:3034-3063`

対応する新設 test も `test_s8b_attempt_registry.py:4947-5040` に 3 件あるが、指定された報告 4 本のどれにも収録されていない。

成果物影響: 二件目以降の clean attempt の受理を左右する adapter 変更について、所有者報告と受入根拠が欠落している。

推奨: この追加修正の実装主体、意図、実走結果を親が明示的に回収するまで受入 evidence に数えない。

## 所見 RB-4 — 親が名指ししていない既存 fixture 変更が 1 箇所ある

**real、[実測]**

親裁定は launcher 側では旧 `:1490` の `_v2_terminal_from_opened()` だけを追加許可している。  
根拠: `s4-adjudication.md:62-78`。

差分はそれとは別に、既存 test 内の局所 builder を次のように変更している。

- base `test_s8b_floor_attempt_launcher.py:1034`: `"retry_ordinal": 0`
- HEAD `test_s8b_floor_attempt_launcher.py:1034`: `"retry_ordinal": None`

これは `out-fix1.md:10` には報告されているが、親の 4 箇所には追加されていない。反転、緩和、skip ではなく、erratum と同じ向きの fixture 訂正ではある。

成果物影響: test 強度の低下は見つからないが、名指しされた既存期待値不変境界を越えている。

推奨: 親がこの局所 planned fixture を明示的に追加承認するか、許可済み範囲へ収める。

## 所見 RB-5 — 行番号 pin のずれ

**refuted、[実測]**

- `s8b_floor_campaign.py:4707` は現在も `return build_fn(genome, **call_kwargs)`。
- `s8b_floor_campaign.py:8636` は現在も `outcome = run_campaign(`。
- 新 helper は `:8656` 以後。
- `test_ccbench_spawn_sites.py:895-910,2642-2720` の pin 値も 4707 / 8636 のまま。

成果物影響: 行番号 pin に起因する受入赤は無い。

推奨: なし。

## 所見 RB-6 — perf inventory / role guard の drift

**refuted、[実測]**

`_REVIEWED_PERF_FILES` には campaign、launcher、contract、stats が既に含まれる。差分で新しい production file は増えていない。追加行には tracked perf call や perf を条件にする新しい `if` / `while` が無い。

role A/J/O/B の既存箇所も保持されている。

- A: `_assert_perf_mode`、launcher `_checked_reservation_policy`
- J: `assemble_manifest`
- O: `assemble_result`
- B: `s8b_floor_contract.py`

`test_official_perf_closure.py` 自体にも差分は無い。

成果物影響: 静的には AST 集合等値や role guard を崩す追加 perf 述語は無い。

推奨: なし。テスト実走結果は本レビューでは主張しない。

## 所見 RB-7 — 凍結 bytes / `FORMULA_ID` の変更

**refuted、[実測]**

段 2 が列挙した 23 path を `sha256sum` で再計算し、全件が列挙済み hash と一致した。`git diff 21dfbe0f3..HEAD -- output` も空である。

- `s8b_floor_stats.py:51`: `FORMULA_ID = "s8b-floor-stats/v2"`
- `s8b_floor_contract.py:44`: 同じ値
- 両 file と `test_frozen_artifacts.py` に対象差分なし

成果物影響: 凍結成果物と式 identity の drift は無い。

推奨: なし。

## 所見 RB-8 — 新設 test に揮発値が焼き込まれている

**refuted、[実測]**

新設 test の日時、pid、starttime、execution UUID は固定 fixture 値であり、working-tree HEAD や実 pid を期待値としていない。SHA-256 は固定 bytes または同一 test 内で生成した artifact から再導出している。`artifact_sha256` の環境依存実値も追加期待値に無い。

成果物影響: 実行時刻、process、commit による期待値 drift は見つからない。

推奨: なし。

## 所見 RB-9 — v4 freeze consumer が v5 を silent acceptance する

**refuted、[実測]**

両 consumer とも v5 を fail-closed に拒否する。詳細は末尾の専用節に記す。

成果物影響: v5 result が D2 前に誤って holdout / ratified freeze へ取り込まれる経路は見つからない。

推奨: D2 前の到達不能として明記を維持する。

## 行番号 pin 4707 / 8636 の検算

| pin | 現在の実体 | test 側 |
|---|---|---|
| 4707 | `return build_fn(genome, **call_kwargs)` | `_DEFERRED_GATE_MEMBERS` と exact sink 集合が 4707 |
| 8636 | `outcome = run_campaign(` | `_DEFERRED_GATE_MEMBERS` と exact sink 集合が 8636 |

どちらも同じ function scope にある。

- 4707: `<module>.build_cells.invoke_build`
- 8636: `<module>.main`

**判定: refuted、[実測]。pin ずれなし。**

## 既存期待値の変更の全列挙 (許可 4 箇所との照合)

削除または置換された既存 test 行は次の 13 行だけである。

1. `test_s8b_attempt_registry.py` base 255  
   capability helper 呼出しへ `retry_ordinal` を転送。既定値 0 の挙動は同じ。期待値変更ではない。

2. 同 base 336  
   `_sealed_v2_case()` から同引数を転送。既定挙動のための plumbing。

3. 同 base 378  
   `"kind": "planned"` から retry ordinal 条件式へ。既定値 0 では従来どおり `planned`。

4. 同 base 386  
   `"retry": False` から `bool(retry_ordinal)` へ。既定値 0 では従来どおり false。

5. 同 base 387  
   `slot.attempt_ordinal` から `retry_ordinal or None` へ。親許可の attempt-registry fixture。

6. 同 base 480  
   transplant 軸 `[4]` から `[3]` へ。親許可の transplant 負例。

7. `test_s8b_floor_attempt_launcher.py` base 1034  
   `retry_ordinal: 0` から `None`。親の exact 許可外。RB-4。

8. 同 base 1477  
   `kind="planned"` から measurement ordinal 条件式へ。既存既定入力では同じ。

9. 同 base 1489  
   `retry=False` から measurement ordinal 条件式へ。既存既定入力では同じ。

10. 同 base 1490  
    `slot_id[4]` から planned `None` / retry `slot_id[3]` へ。親許可の launcher planned helper。

11. 同 base 1500  
    `trigger=None` から retry 条件式へ。既存既定入力では同じ。

12. `test_s8b_terminal_evidence.py` base 128  
    slot の measurement / recovery 軸を `(0,2)` から `(2,0)` へ。親許可の terminal fixture。

13. 同 base 164  
    `slot_id[4]` から `slot_id[3]` へ。親許可の terminal fixture。

`test_s8b_floor_campaign.py` は既存行を削除せず、新設 test と自走入口だけを追加している。

反転、緩和、既存 test 削除、skip、xfail、deselect は **0 件**。

## 所有外 consumer への波及

| 変更面 | repo 内 consumer | 判定 |
|---|---|---|
| terminal ordinal leaf | `s8b_terminal_evidence.py` 内部、launcher、`test_s8b_terminal_evidence.py`、`test_s8b_attempt_registry.py` | fixture の既定値は訂正済み。未修正の `slot_id[4]` 束縛は検索上 0 件 |
| adapter reserve/classify/observation | production caller は launcher のみ。直接 test consumer は `test_s8b_attempt_registry.py` と `test_s8b_floor_attempt_launcher.py` | profile 伝播は三 transition に入ったが、提供報告に無い。RB-3 |
| 新 launcher API | production caller は `s8b_floor_campaign.py:8954,9045` のみ。ほかは launcher/campaign test | 既存 `launch_floor_attempt()` の署名は不変 |
| campaign `_Runner` / `_run_campaign_core` | `run_campaign()`、own tests、`test_s8b_freeze_io.py`、`test_s8b_ratified_freeze.py`、`test_pegasus_floor_tools.py`、`test_s8b_ratified_verify.py` | optional 引数の既定値は legacy 経路を保存。ただし adapter 間接依存は RB-2 |
| `assemble_result` | campaign 内 2 call と own tests | `attempt_registry=None` は v4、非 null は v5 |
| holdout admission | result consumer ではなく attempt-ledger consumer | competing marker 規則は変更されず、no-marker branchを受理 |
| floor stats | v4/v5 両対応、v5 は live prefix 再取得 | schema 別 exact key と prefix 等値を維持 |
| holdout / ratified freeze | v4 exact consumer | v5 は fail-closed。silent acceptance なし |
| `attempt_registry_core.py` | adapter が validating profile を渡す。core 自体は差分なし | plain v2 profile の sealed-terminal 拒否は維持 |
| AST / meta tests | perf closure、spawn-site pin、floor-stats caller exact set、contract alias、terminal signature、holdout inspector signature | 静的 drift なし。ただし adapter import guard は RB-2 の間接参照を見逃す |
| test fixture consumer | `test_s8b_floor_stats.py` が registry test helperを、`test_s8b_dependency_prefix_bridge.py` が campaign fixtureを利用 | helper の既定引数は互換。追加の静的破損は見つからない |

## 新設 test nodeid の全列挙と件数

合計 **31 nodeid**。`acceptance_duration_ledger.json` の現 HEAD 登録は **0 / 31**。

`test_s8b_attempt_registry.py`、5 件:

1. `orchestrator/tests/test_s8b_attempt_registry.py::test_durable_replay_binds_measurement_ordinal`
2. `orchestrator/tests/test_s8b_attempt_registry.py::test_durable_replay_rejects_recovery_ordinal_substitution`
3. `orchestrator/tests/test_s8b_attempt_registry.py::test_two_clean_v2_attempts_reserve_classify_and_begin_observation`
4. `orchestrator/tests/test_s8b_attempt_registry.py::test_second_clean_reservation_rejects_tampered_terminal_evidence`
5. `orchestrator/tests/test_s8b_attempt_registry.py::test_plain_v2_profile_rejects_transition_after_sealed_terminal`

`test_s8b_floor_attempt_launcher.py`、12 件:

6. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_planned_terminal_rejects_nonnull_retry_ordinal`
7. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_retry_terminal_rejects_recovery_ordinal_substitution`
8. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_probe_floor_attempt_preconditions_runs_owned_probe_once_and_seals_only_competing`
9. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_probe_floor_attempt_preconditions_rejects_unissued_capability_without_probe`
10. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_floor_attempt_rejects_reused_pre_probe_before_effects`
11. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_floor_attempt_rejects_unissued_or_spoofed_pre_probe[caller-constructed]`
12. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_floor_attempt_rejects_unissued_or_spoofed_pre_probe[spoofed-type]`
13. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_floor_attempt_rejects_a_different_capability_origin`
14. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_floor_attempt_does_not_repeat_pre_probe`
15. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_clean_matches_existing_terminal_and_classification`
16. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_launch_probed_competing_skips_capture_and_matches_existing_terminal`
17. `orchestrator/tests/test_s8b_floor_attempt_launcher.py::test_probed_certified_wrapper_fixes_sealed_adapter_and_public_signatures`

`test_s8b_floor_campaign.py`、11 件:

18. `orchestrator/tests/test_s8b_floor_campaign.py::test_default_production_attempt_uses_certified_launcher_once`
19. `orchestrator/tests/test_s8b_floor_campaign.py::test_registry_plan_declares_exact_planned_and_retry_slot_closure`
20. `orchestrator/tests/test_s8b_floor_campaign.py::test_registry_plan_maps_round_to_zero_based_repetition`
21. `orchestrator/tests/test_s8b_floor_campaign.py::test_certified_campaign_rejects_unissued_consumption_marker`
22. `orchestrator/tests/test_s8b_floor_campaign.py::test_journal_emits_launcher_terminal_record_byte_identically`
23. `orchestrator/tests/test_s8b_floor_campaign.py::test_default_production_result_is_v5`
24. `orchestrator/tests/test_s8b_floor_campaign.py::test_production_v5_self_check_rejects_prefix_head_mismatch`
25. `orchestrator/tests/test_s8b_floor_campaign.py::test_v5_prefix_covers_every_consumed_non_competing_session`
26. `orchestrator/tests/test_s8b_floor_campaign.py::test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row`
27. `orchestrator/tests/test_s8b_floor_campaign.py::test_injected_measurement_core_retains_noncertifying_legacy_path`
28. `orchestrator/tests/test_s8b_floor_campaign.py::test_finalize_pending_replays_live_v5_prefix`

`test_s8b_terminal_evidence.py`、3 件:

29. `orchestrator/tests/test_s8b_terminal_evidence.py::test_planned_terminal_binds_none_retry_ordinal`
30. `orchestrator/tests/test_s8b_terminal_evidence.py::test_planned_terminal_rejects_nonnull_retry_ordinal`
31. `orchestrator/tests/test_s8b_terminal_evidence.py::test_campaign_retry_binds_measurement_ordinal_not_recovery_ordinal`

## v4 consumer の到達不能の判定

**fail-closed な到達不能。silent acceptance は refuted、[実測]。**

`s8b_holdout_freeze.py`:

- `:1431-1433` は schema 引数を省略し、legacy v4 key set を取得する。
- `:1437-1438` で v5 の追加 `attempt_registry` keyを拒否する。
- 仮に key 検査を越えても `:1439-1442` で `RESULT_SCHEMA`、つまり v4 を要求する。
- `_validate_floor_inputs()` は `:2052` から実際に呼ばれる。

`s8b_ratified_freeze.py`:

- `:2360-2362` は schema 引数を省略し、v4 exact keysを取得する。
- `:2375` の `_exact_keys()` で v5 を拒否する。
- この検査は `:3274-3278` で v5-aware shared verifier より先に呼ばれる。
- 仮に越えても `:2404-2409` で v4 schema を要求する。

`s8b_floor_stats.py` は意図どおり v5 を読めるが、prefixを live registry と比較する verifier であり freeze consumer ではない。`s8b_holdout_admission.py` も top-level result consumer ではない。

したがって production v5 result は自己検査までは到達するが、D2 前の holdout / ratified freeze には取り込めない。