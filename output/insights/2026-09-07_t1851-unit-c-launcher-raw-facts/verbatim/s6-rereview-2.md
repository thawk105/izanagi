| 件 | 修正の現物 | 検査 node と単一理由性 | 判定 |
|---|---|---|---|
| A-1 | [実測] Mapping → `dict`、list / tuple → `tuple`、その他 → identity は [launcher:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:493) に実装済み。 | [実測] `test_capture_uses_checked_kwargs_snapshot_after_source_mapping_mutates` は [test:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:851) で、検査後の first probe 中に `extra_env` と `numactl` を変更し、capture が変更前の独立値を受け取ることを直接検査する。他の予約値は valid であり、失敗理由は snapshot の別名だけ。 | **closed** |
| A-3 | [実測] callable 固有 gate は [launcher:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:529)。callable `dict` subclass と protocol / receipt の負例は [test:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:85) と [test:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:982)。 | [実測] `test_reservation_policy_rejects_each_untrusted_selector` の protocol / receipt 各 parameter は、callable gate を外すと digest、receipt exact-shape、`use_perf` 等値を通る。拒否 regex は `^reservation policy contains a callable$` に固定され、別 gate の message mismatch に依存しない。 | **closed** |
| R-1 | [実測] `test_private_rep_sink_snapshot_occurs_after_token_open` の [test:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:824) が、3 record 全体を 6 key の値まで exact tuple 比較する。 | [実測] fake が private sink に書く値は [test:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:202)。record の欠落、追加、値変更はいずれも同じ exact assertion だけで検出され、public `rep_observations` が別値である検査も維持されている。 | **closed** |
| R-2 | [実測] observed 申告は [test:1162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:1162) で non-null digest / primary value を持ち、未記録と未封印は `:1170-1175` で検査する。 | [実測] `test_open_failure_cannot_be_reported_as_observed` は fully-valid observed payloadを用いるため、拒否理由は [launcher:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:835) の open-failure contradiction gateだけ。 | **closed** |

### A-1 の型契約

[実測] `_CERTIFIED_MEASUREMENT_KEYWORDS` のうち container を取る値は `workload`、`extra_env`、`numactl` である。[runner:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:803) では前二者が `Optional[Dict[str, str]]`、`numactl` が `Optional[Sequence[str]]` であり、独立 `dict` と `tuple` はそれぞれ適合する。

[実測] nested function `open_measurement_point` は [runner:933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:933) でこれらを引数として再受領せず、capture 済み state と私有 sinkを閉包する。launcher は open 後に sink を snapshot するため、今回の変換と deferred open の契約衝突はない。

[実測] identity を保つべき `holdout_observation_admission` と `calibration_observation_capability` は dataclass objectであり、Mapping / list / tuple ではないため [launcher:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:505) から同一 object のまま返る。capability 系が `dict` 化される経路はない。

[実測] A-1 node の mutation は policy snapshot 後、`probe_before` 実行中に発生し、fake capture は変更前の `{"MODE": "checked"}` と `("numactl", "--cpunodebind=0")` を観測している。

### A-3 の静的追跡

[実測] protocol case は `_CallableDict({"reps": 3})` と、その同じ内容から作った binding digestを使用する。callable gateを除けば Mapping 検査、canonical digest等値、positive reps、receipt由来 `use_perf=True` の全検査を通る。

[実測] receipt case は exact 9 key の available receiptである。[perf_preflight.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/perf_preflight.py:179) の正規化を通り、pilot modeかつ measurement `use_perf=True` なので後続拒否はない。

### R-1 / R-2 の強さ

[実測] R-1 の比較は tuple 長、各 mapping の exact key集合、`returncode`、`counter_status`、`missing_perf_events`、`perf_raw`、`throughput` の全値を一括固定する。fix2前と同等以上である。

[実測] R-2 の `report_sha256` は `_terminal` 由来で non-null、追加された `observation_sha256` と `primary_value` も non-nullであり、[core:1032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1032) の observed null matrixに適合する。

[実測] recorder は reserve 時に exact `deferred_output_reader` を保持する ([test:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:145))。実 adapterも同じ readerを stateへ保持し ([adapter:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2037))、observation開始時に呼ぶため、拒否直後の未封印検査は実装と整合する。

### fix3 の新規持ち込みと所有境界

[実測] fix3 の全変更は次の5群だけで、4件に対応しない変更は0件である。

- [実測] A-1: production snapshot helperと既存nodeのnested mutation拡張。
- [実測] A-3: `_CallableDict` fixtureと2つのdownstream-valid parameter。
- [実測] R-1: 緩い key / index assertionをexact tuple assertionへ強化。
- [実測] R-2: valid observed値、recorder保持、未記録・未封印assertion。
- [実測] testの削除、skip / xfail、新規fail-open、受理期待の反転、assertion緩和はない。

[実測] fix3 patchは所有2 fileのみで、production +13 / -1、test +59 / -12。統合作業 treeの `git diff 04f06d032` は指定snapshotとSHA-256 `748fe1bad4c817a45bf0cfd27b4df7d929cd292cd7aec777925674e3a87aefa3` で一致する。

[実測] `test_official_perf_closure.py` は統合差分では先行fix1の変更を含むが、fix3差分には含まれない。2 guard逐語は [test_official_perf_closure.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_official_perf_closure.py:300) とlauncher現物で一致する。

[実測] `test_ccbench_spawn_sites.py:212` の `_owned_post_probe` pinは1のまま。adapter / core / profile / campaign / calibrator は baseから無変更である。

### 変異 M1〜M12

| ID | 現物 node | fix3での変化 |
|---|---|---|
| M1 | `test_pre_probe_competition_terminalizes_without_capture` `:771` | [実測] 改名・分割・内容変更なし |
| M2 | `test_private_rep_sink_snapshot_occurs_after_token_open` `:812` | [実測] node名不変。R-1対応で値検査のみ強化 |
| M3 | `test_v2_profile_is_rejected_before_any_registry_side_effect` `:892` | [実測] 変更なし |
| M4 | `test_certified_api_owns_classification_authority` `:917` | [実測] 変更なし |
| M5 | `test_reservation_rejects_protocol_not_bound_to_binding` `:958` | [実測] 変更なし |
| M6 | `test_use_perf_must_be_derived_from_receipt` `:970` | [実測] 変更なし |
| M7 | `test_pre_probe_competition_classifies_as_competing` `:1017` | [実測] 変更なし |
| M8 | `test_external_evidence_digest_binds_both_probes` `:1035` | [実測] 変更なし |
| M9 | `test_probe_result_requires_exact_keys` `:1068` | [実測] 変更なし |
| M10 | `test_capture_exception_terminalizes_with_stage_capture` `:1082` | [実測] 変更なし |
| M11 | `test_reservation_rejects_reps_not_equal_to_protocol` `:1119` | [実測] 変更なし |
| M12 | `test_open_failure_yields_empty_repetition_evidence` `:1132` | [実測] 親裁定どおり一切変更なし |

## blocker

[実測] 新規所見なし。

## must-fix

[実測] 新規所見なし。

## nit

[実測] 新規所見なし。所見 R-3 以降は発生しない。

## 総括

- [実測] 4件は closed 4 / partial 0 / regressed 0。
- [実測] 新規所見は blocker 0 / must-fix 0 / nit 0。
- [実測] M1〜M12 のnode名は全件不変。M2だけassertion強化、M12は無変更。
- [実測] pytestは制約どおり本レビューでは未実走。
- [実測] 判定は **GO**。