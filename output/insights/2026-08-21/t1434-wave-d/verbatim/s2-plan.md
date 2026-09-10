## (P1) 実装可否の検証結果

結論は、装置面は実装する、ただし実験証拠の状態は引き続き `inconclusive` とする、である。

- §5.2 は今回の4面を明示的な実装項目としている。Wave A の汎用 normalizer も存在するため、未配線のまま残すより、`_validate_schedule` から実経路へ接続する方が仕様に一致する。
- §5.3 の task catalog、独立 oracle ledger、cache 制御、price snapshot、独立 custodian、power simulation は本 wave の範囲外であり、実装後も6条件は成立しない。
- §12.1 の判定表は、条件未達時の扱いを「実装停止」ではなく `routing_evidence_status = inconclusive` と規定している。同一 owner の masking は `apparatus_diagnostic` に限定する。
- 反対方向の論拠も確認した。装置実装が実験証拠や model 品質の証明を意味すると誤解されるなら停止すべきだが、今回の制約は cache/price の非 null を拒否し、`same-owner-advisory` を維持し、実走と model-only swap を禁止している。このため実装と証拠主張は分離できる。
- `_load_adjudication` は [tools/codex_reasoning_ab.py:5159](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5159) で packet/verdict/mapping の bijection と freeze/hash だけを検査する。task-specific 化のために本体を変更する必要はない。`mask_strength` の pin (`5187-5188`) は独立 custodian 未実現の証拠なので、変更してはならない。

## 実装単位

4面は同じ正規化済み slot を共有するため、`tools/codex_reasoning_ab.py` とテストを含む単一実装単位とする。`_validate_schedule` だけを先に変更すると、replay、aggregate、packet の入力契約が不一致になる。

1. `_validate_schedule` の schema 配線

   対象は [tools/codex_reasoning_ab.py:5085](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5085)。

   シグネチャは次の形にする。

   `def _validate_schedule(schedule, *, task_manifest=TASK_MANIFEST) -> tuple[list[dict[str, Any]], list[str]]`

   - `schema_version` がない既存 schedule は v2 compatibility view として `LEGACY_SCHEMA_VERSION` を補った非 mutating copy にする。未知 version は拒否する。
   - `normalize_schedule(..., manifest=task_manifest)` を必ず通し、`normalize_legacy_schedule`、`validate_nullable_dimensions`、`_normalize_schedule_slot` の既存検査を live path に接続する。
   - `benchmark_task_id` は `_manifest_task` の canonical ID を使う。`case` と `legacy_case` は Wave C の snapshot/collect 呼出し用 alias として保持する。
   - `stage` は task manifest の値を既定値とし、slot に明示された値が manifest と異なる場合は拒否する。
   - `requested_model` は省略時だけ `MODEL` に補完し、明示値は `MODEL_ALLOWLIST` に対して fail-closed 検査する。`None` や未知 model は拒否する。
   - `cache_condition` と `price_version` は v2 の省略を null に正規化し、v3 は欠落を拒否する。非 null 値は既存の `validate_nullable_dimensions` の拒否をそのまま使う。
   - `expected_schedule_from_manifest(task_manifest, original_schedule)` を呼び、v2 は既存の `LEGACY_EXPECTED_SCHEDULE`、v3 は task_id/arm ごとの動的 count を使う。`len(slots) != 10` と `counts != EXPECTED_SCHEDULE` は除去する。
   - block は引き続き2 slot、`block_order` は `[1, 2]`、同一 task/stage/cache/price の paired block とする。ただし arm 集合は `{"max", "high"}` ではなく schedule から得た2つの arm と比較する。
   - prompt/snapshot の集中検査は `case in {"POS", "NEG"}` ではなく `benchmark_task_id` ごとに行う。submodule state の全体一致検査は維持する。
   - `supervise_pair` の呼出し [3699] と `_replay_manifest` の呼出し [5906] は変更しない。両者が正規化済み schema を受け取ることをテストで確認する。

2. slot 次元の共通化

   `_validate_schedule` の直後、または aggregate/replay 共通領域に `_slot_dimensions` 相当の内部 helper を追加する。

   返す値は少なくとも次の canonical fields とする。

   `benchmark_task_id`, `stage`, `requested_model`, `cache_condition`, `price_version`, `oracle_kind`, `legacy_case`, `case`, `arm`

   aggregate の直接 fixture のように canonical field がない場合だけ、`case` alias と `MODEL`/null の compatibility fallback を使う。live replay では `_validate_schedule` の出力を authority とし、attempt 側の metadata で上書きしない。

3. `_aggregate_verified` と token/reliability ledger

   対象は [tools/codex_reasoning_ab.py:5515](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5515)。

   シグネチャは次のように keyword-only の task manifest を追加する。

   `def _aggregate_verified(..., *, task_manifest=TASK_MANIFEST)`

   - `len(final_attempts) == 10` は、`set(final_attempts) == {slot_id for slot in slots}` に置換する。
   - `case == "POS"` は task の `oracle_kind == "positive"`、`case == "NEG"` は `oracle_kind == "negative"` に置換する。
   - primary ledger、false-finding ledger、reliability ledger は、少なくとも `(benchmark_task_id, stage, requested_model, cache_condition, arm)` 単位で分離する。
   - `known_finding_ids` は `KNOWN_FINDINGS` 全体ではなく `known_finding_ids_for_manifest(task_manifest, benchmark_task_id=...)` で task ごとに検査する。mapping reveal 前の `_validate_verdict_row` は blind のため全 task の union 検査に留め、exact な task 検査は `_aggregate_verified` で行う。
   - `"POS_PRIMARY"` と `"NEG_ADJUDICATED_FALSE_FINDING"` は既存の互換 label として残してよいが、分岐条件は文字列の case 判定ではなく `oracle_kind` とする。
   - positive の `k/n` は各 axis の最終 attempt を分母に残し、post-treatment failure も ITT の分母から除外しない。reference arm は schedule の first-seen arm から導出し、`max_k/high_k == 3` の意味論を動的な `k/n` 比較へ置換する。
   - `resources` のキー列挙 [5630-5645] に `benchmark_task_id`, `stage`, `requested_model`, `cache_condition`, `price_version` を追加する。値は schedule authority から補完し、attempt が持つ矛盾値は理由に追加する。
   - `_aggregate_token_usage_observations` [5441-5512] も同じ axis ledger に変更する。`by_arm_case` は default reasoning fixture の互換 projection としてのみ生成し、動的 task では axis 別結果を返す。
   - 既存出力との非破壊性のため、単一 task・単一 stage/model/cache の legacy schedule では、`primary_judgment_ledger`、`post_treatment_reliability`、decision の旧 arm projection を維持し、別名の axis ledger を追加する。

4. `_replay_manifest` の dimension binding

   対象は [tools/codex_reasoning_ab.py:5898](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5898)。

   シグネチャは次の形にする。

   `def _replay_manifest(manifest_path, sessions_root, *, task_manifest=TASK_MANIFEST)`

   - [5906] の `_validate_schedule` 呼出し結果を唯一の slot authority とする。
   - 成功 attempt、prelaunch failure、replay failure の全分岐で、slot 由来の `benchmark_task_id`, `stage`, `requested_model`, `cache_condition`, `price_version` を attempt view に付与する。
   - `collect_run` の呼出し [6134-6146] は変更しない。特に D614 で land 済みの `expected_requested_model=slot.get("requested_model", MODEL)` は再編集しない。
   - `identities` [6243] は `{"POS": set(), "NEG": set()}` を廃止し、`(benchmark_task_id, stage, requested_model, cache_condition, price_version)` 単位の map にする。model が違う slot を同一 task の identity concentration に誤って混ぜない。
   - `verify_manifest`/`aggregate_manifest` [6267-6295] は replay と aggregate の合成だけを維持し、必要なら keyword-only の `task_manifest` を透過させる。独自 CLI axis は追加しない。

5. `make_packets` の動的 count と盲検境界

   対象は [tools/codex_reasoning_ab.py:6298](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:6298)。

   シグネチャは `make_packets(..., *, task_manifest=TASK_MANIFEST)` とする。

   - manifest の schedule descriptor があれば読み込み、`_validate_schedule` と `expected_schedule_from_manifest` から期待 slot ID/count を得る。
   - `len(grouped) != 10` [6309] は、期待 slot ID 集合との一致および動的合計 count の検査に置換する。schedule を持たない旧 packet fixture には、attempt manifest の distinct slot ID を使う legacy fallback を残す。
   - public の `packet-state.json` の packet row は引き続き `{"packet_id", "filename"}` のみとする。packet body に task/model/stage/cache/price の header を追加しない。
   - private mapping は既存の `packet_id`、`run_id`、`slot_id`、digest binding を維持する。public/private の対応は packet ID 集合と digest で検査する。
   - `mask_strength: "same-owner-advisory"` は [6366]、[6377]、[6385] の全箇所で維持する。独立 custodian を示す新ラベルには変更しない。
   - aggregate/verify/make-packets の CLI [6768-6779] に task/cache/model/stage flag は追加しない。これらは frozen manifest/schedule の値であり、CLI から再指定すると artifact と引数の二重 authority になる。`--expected-model` の dest [6748] も変更しない。

## 発見した追加ハードコード

全体 grep のうち、親 brief に明記されていなかった D 面の追加箇所は次の通り。

- [5537] `len(final_attempts) == 10`。aggregate 完了判定の追加 cardinality hardcode。schedule slot ID 集合との一致に変更する。
- [5444-5446] `_aggregate_token_usage_observations` の `arm -> {"POS": 0, "NEG": 0}`。token observation も task/stage/model/cache axis に変更する。
- [5587-5599] `max_k/high_k` と固定値 `3` による4分岐。動的な positive ledger の `k/n` と schedule 順の reference arm に置換する。
- [5610] decision reason の `max={...}/3 high={...}/3`。動的 arm と各 axis の `k/n` 表示に変更する。
- [5622-5628] reliability の `for arm in ("max", "high")`。axis ledger から動的に生成する。
- [5659] `reliability["high"] > 0`。固定 high を使わず、axis ごとの escalation 候補へ変更する。
- [5127-5132] の `len(rows) != 2`、`block_order in {1,2}`、隣接 index 検査は cardinality だが、paired block の不変条件なので維持する。arm 名だけを動的化する。
- [5252-5255] と [6635-6642] の reader 2人分の bijection は adjudication 契約そのものであり、task axis の hardcode ではないため変更しない。

grep で残る POS/NEG/max/high は、D 面の未処理漏れではない。

- [62-171]、[209-215]、[2261] は byte 同一を要求された POS/NEG の凍結 manifest/legacy compatibility。
- [833] は legacy snapshot の artifact allowlist。
- [3119] は argv 中の reasoning effort 検査で、Wave C/B 所有面。
- [6712]、[6739] は legacy CLI selector/effort selector であり、今回の aggregate/verify/make-packets CLI には追加変更しない。

## テスト計画

pytest は実行せず、以下を新規 nodeid 案として追加または既存 fixture に対する直接検査として実装する。

- `orchestrator/tests/test_codex_reasoning_ab.py::test_validate_schedule_wires_manifest_normalizer`  
  `_validate_schedule` が v3 normalizer、task alias、dynamic counts、nullable dimension 検査を実際に通ることを検査する。
- `::test_validate_schedule_preserves_legacy_reasoning_fixture`  
  `_schedule` [320-348] の schema version/requested_model/cache/price 未指定 fixture が従来どおり受理されることを検査する。
- `::test_validate_schedule_rejects_live_non_null_cache_or_price`  
  Wave A の fail-closed 検査が live `_validate_schedule` 経路でも発火することを検査する。
- `::test_validate_schedule_accepts_dynamic_task_and_arm_counts`  
  既存 `test_manifest_schedule_and_findings_are_dynamic` [1373-1422] の alpha/beta manifest と low/high 等の schedule が、10 slot 固定なしで受理されることを検査する。
- `::test_aggregate_verified_uses_oracle_kind_not_case`  
  legacy_case が POS/NEG でない positive/negative task を用い、primary と false-finding の意味論が `oracle_kind` から決まることを検査する。
- `::test_aggregate_verified_separates_task_stage_model_cache_axes`  
  task、stage、requested_model、cache_condition を変えた rows が pooled されず、resource/primary/reliability ledger に別行で現れることを検査する。
- `::test_aggregate_verified_has_dynamic_completion_cardinality`  
  10 slot 未満の valid dynamic schedule が `len==10` により失敗せず、欠落 slot のみ不完全になることを検査する。
- `::test_aggregate_token_usage_is_not_pos_neg_max_high_fixed`  
  [5444-5446] の固定 map を mutation しても、task/dimension ledger が検査を殺すことを確認する。
- `::test_replay_binds_identity_by_task_stage_model_cache`  
  同一 task の異なる model/cache を identity concentration に誤って混ぜないことを検査する。
- `::test_replay_passes_schedule_requested_model_to_collect_run`  
  既存 [5928-6055] を維持し、D614 の唯一の越境行を変更していないことを回帰確認する。
- `::test_make_packets_uses_dynamic_schedule_cardinality_and_keeps_public_blind`  
  3 slot 等の synthetic schedule で packet count が動的になり、public state に model/stage/task/price がなく、private mapping の packet/digest binding が残ることを検査する。
- `::test_load_adjudication_keeps_same_owner_advisory_pin`  
  [5187-5188] の label pin が変更されず、独立 custodian 化を偽装しないことを検査する。

## 既存テストへの波及

期待値を変更せざるを得ない既存 nodeid は、互換 projection を採用する限り「なし」。

特に次は旧値を維持する。

- `test_verify_replays_complete_fake_codex_experiment` [5850-5873] の max/high primary、10 resource、`POS_PRIMARY`。
- `test_zero_component_total_only_aggregate_counts_by_arm_and_case` [6674-6695] の legacy `by_arm_case` projection。
- `test_m9_post_treatment_failure_remains_in_denominator` [6720-6735]。
- `test_f3_2_pair_invalidated_post_treatment_occurrence_is_reliable` [6781-6815]。
- `test_false_finding_is_derived_and_decision_fields_are_typed` [6845-6865]。
- `test_pos_neg_submodule_initialization_state_mismatch_is_rejected` [4490-4501]。
- `test_mapping_custodian_blocks_pre_freeze_reveal_and_packet_sha_join` [7300-7341]。

これらには新しい axis ledger や public-field 不在の assertion を追加するが、既存の legacy projection の期待値は変えない。

## 危険

- v3 schedule を誤って v2 fallback に流すと、cache/price 欠落を受理してしまう。version の分岐、未知 version、v3 欠落 field の拒否を直接テストする。
- v3 の `expected_schedule_from_manifest` は観測 schedule から count を導出するため、task catalog や power gate の代替にはならない。dynamic count を受理しても標本数十分とは記録せず、`inconclusive` を維持する。
- attempt 側の model/cache/price を authority にすると、schedule binding を改ざんできる。常に slot を authority とし、矛盾を failure reason にする。
- aggregate で task/stage/model/cache を pooled すると、非劣性や ITT の分母が壊れる。複数 axis synthetic fixture で分離を検査する。
- `oracle_kind` の代わりに alias `case` を再利用すると、task-specific oracle が POS/NEG 固定へ逆戻りする。alpha/beta task と task 固有 finding ID で検出する。
- packet state に dimension metadata を追加すると blind が壊れる。public row の exact key set と private mapping の digest equality を検査する。
- `mask_strength` を独立 custodian 相当へ変更すると、実現していない保証を出すことになる。[5187-5188] の reject pin を残す。
- Wave C の `supervise_pair`、`_supervise_one`、`collect_run`、launch schema、`--expected-model` dest に触れると所有境界違反になる。既存 replay の monkeypatch test と静的 diff で検出する。
- `routing_evidence_status` をコードの成功結果から `confirmatory-go/no-go` と推定してはならない。実装後も status は `inconclusive`、custodian 関連は `apparatus_diagnostic` として段4へ申し送る。

## 総括

本 wave は新しい実験データや cache 制御を作る wave ではない。  
既存の manifest-driven normalizer を `_validate_schedule` の実経路へ接続する wave である。  
その正規化済み task/stage/model/cache 次元を replay、aggregate、packet count へ一貫して運ぶ。  
POS/NEG と max/high は frozen legacy compatibility として値を守るが、D の集計分岐からは除去する。  
`_load_adjudication` の freeze/bijection と `same-owner-advisory` は変更せず、task-specific 検査は reveal 後に行う。  
装置完成後も T-189 の証拠条件は未成立であり、実験結果を routing の証拠として扱わない。