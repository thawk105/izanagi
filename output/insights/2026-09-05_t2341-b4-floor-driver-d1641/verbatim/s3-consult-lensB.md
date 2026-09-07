read-only sandbox のため、指定先 `s3-lens-b.md` へは書き込めませんでした。以下が完成稿です。

# [T-2341] 段 3 consult — レンズ B

## blocker

### 所見 1 — base / sort は plan の合格述語へ到達不能

(a) [実測] plan は全候補に `checks.campaign_identity.site_projected_cfg.status == "measured"` を要求するが、`site_projected_cfg` を生成するのは trigger 分岐だけである。base / sort は常に `null` になり、P2 の優先順で base を選べない。

(b) [実測] `s2-plan.md:240-252`、`orchestrator/campaign/p3_b4_wiring_probe.py:1727-1766`。既存 `t1769-dogfood/{base,sort}.json` も `site_projected_cfg=null`、trigger だけが status を持つ。compute node の強制自体は `tools/pegasus/dispatch_compute.py:1582-1585` にある。

(c) [実測] 放置すると合格集合が事実上 trigger だけへ縮み、base / sort が配線検査に合格しても §5 の受理集合から消え、記入される driver と軸が変わる。

(d) [推測] probe を全 driver 共通の site field を出す schema へ直すか、base / sort は `site_projected_cfg is null` を正規形として扱い、別途 dispatch receipt の `bnode` を evidence と束縛する。後者なら receipt の path/hash も §5.1.2 と値セルへ入れる。

(e) [実測] 対応: P2、P5、P6。

## must-fix

### 所見 2 — commit 1 で未生成 evidence path を逐語記載すると check_docs が赤になる

(a) [実測] 事前登録文書は living doc であり、存在しない `output/.../base.json` のような literal path を commit 1 に書くと、evidence を commit 2 で生成する前に `check_docs.py` の実在検査へ掛かる。逆に evidence を先に生成すると §5.1 (i) の先行 commit 条件を破る。

(b) [実測] `tools/check_docs.py:146`、`:1115`、`:6668-6735`、`s2-plan.md:223-239`、`s1-brief.md:39-44`。また、H4 は `docs/phase3-b4-reflux-ablation-preregistration.md:542` の `## 6` 直前へ置く plan が正しい。brief の「対象 driver item の直後」は残りの §5.1 bullets を 5.1.2 配下へ入れてしまう。

(c) [実測] 放置すると commit 1 の docs 検査が通らないか、順序を逆転させて pre-freeze evidence を受理する経路になる。

(d) [推測] commit 1 では root directory と `{driver}.json` / `{driver}.json.sha256` の合成規則として固定し、存在しない完全な `.json` path literal を作らない。commit 2 の値セルでは、生成済み 3 path と hash を逐語記載する。配置は plan どおり §6 直前とする。

(e) [実測] 対応: P5、P6、S-A。

### 所見 3 — not_run 理由と campaign 単位判定の変異帰属が欠ける

(a) [実測] plan は `error="sample_dropped"` を要求するが、その削除・旧理由への復帰を殺す変異が台帳候補にない。また、1 campaign の 1/20・2/20 だけでは、全 window を合算して 5% 判定する誤実装を殺せない。

(b) [実測] `s2-plan.md:153-168`、`:173-191`、`:201-217`、`orchestrator/campaign/floor_pair_driver.py:1619-1637`、`:1997-2052`。T-2166 は probe 後に期待 node を確定する手順を要求している (`refs/t2166-README.md:46-63`)。

(c) [実測] 放置すると、10% 欠測の campaign が別の完全 campaign と合算されて床値を生成できる。また summary の欠測理由が旧文言へ戻っても監査が緑のままになる。

(d) [推測] 次を追加する。

- campaign A = 20 planned / 2 dropped、campaign B = 20 / 0 の test。全体では 5% だが A は 10% なので不採用を要求する。
- `sample_dropped` を別文字列へ戻す変異と、更新後 `test_measure_exception...` の exact error assertion。
- 変異 probeで実際の赤 node を観測後、期待 node を固定する。推測した node をそのまま本台帳へ入れない。

(e) [実測] 対応: P4。

### 所見 4 — n=59 × 3 pair の実値と empty-stratum 到達条件が test 計画にない

(a) [実測] plan の 1/20・2/20 は抽象境界として正しいが、D1641 の実値 `59 × pair 数` に対する pair 合算を固定しない。さらに empty-stratum 正例は pair 数が少ないと 5% 超過 gate が先に発火して到達不能になる。

(b) [実測] D1641 は `refs/D1641.md:20-23`、分母案は `s2-plan.md:27-29`、test 案は `:120-126`、session status の実 field は `floor_pair_driver.py:1604-1616`、`:1716-1773`。`pre_probe_competing` 等は `_probe_once:1501-1532` と `_run_planned_session:1718-1750` から実際に生成可能である。

(c) [実測] 放置すると分母を pair ごとに 59 とする誤実装が、8/177 を誤って不採用にし、床値と受理集合を狭める。逆向きの分母誤りでは 9/177 が生成され、受理集合を広げる。

(d) [推測] 次を固定する。

- 正例: 3 pair × 59 = 177 planned、8 dropped。`8 × 20 = 160 <= 177` なので生成可能。
- 負例: 177 planned、9 dropped。`9 × 20 = 180 > 177` なので `not_generated_dropped_fraction_exceeded`。
- empty stratum: 20 pair × 1 sample で 1 pair を全 drop。全体は exact 5% だが 1 stratum が空なので `not_generated_empty_stratum`。3 pair 構成では 1 stratum 全欠測が 59/177 となり、empty status より threshold status が優先する。

(e) [実測] 対応: P4。

### 所見 5 — HEAD、main、queue は brief の時点値から変わっている

(a) [実測] worktree は clean だが、HEAD は `97ee3cd3a49e...`、現在の local main は `103c32e30d09...` で一致しない。現在の queue probe は RUN 1 / PRR 1 を再現せず「観測不能」を返した。

(b) [実測] `s1-brief.md:3`、`:30`、`:34-35`。`git merge-base main HEAD` は HEAD 自身で、HEAD は main の祖先である。

(c) [実測] 放置すると probe evidence の `source.repository_head` が現在の main より古い参照へ束縛される。queue 不可なら P5 により §5 は未記入のまま止まる。

(d) [推測] S-A 前に main を取り込み、3 編集面の overlap と clean 状態を再検査する。S-B 直前にも queue を再観測し、RUN/PRR 数を不変事実として文書化しない。

(e) [実測] 対応: P5。HEAD 同一性と overlap は P なしの起動前条件。

## nit

### 所見 6 — 赤 test の 3 / 40 は正しいが「source 上 42 test」は誤り

(a) [実測] source 上は 51 test function、parameter 展開後は 140 node である。plan の直接赤 3 node、failure-policy fixture 更新漏れ時の transitive 赤 40 node は現物と一致する。

(b) [実測] `test_floor_pair_driver.py:423-1886`、`s2-plan.md:59`、`:74-109`。`REQUIRED_FIELD_PATHS` は現在 69 case である。

(c) [実測] fixture を更新しないと 40 node が failure-policy parse で早期に落ち、校正、実行、finalize の狙った検査へ到達しない。

(d) [実測] fixture 未更新時の 40 node は次のとおり。

```text
01 test_tracked_calibration_declared_sha_mismatch_is_rejected_for_sha_only
02 test_mutation_04_calibration_projection_gates_have_single_reason_inputs[threads]
03 test_mutation_04_calibration_projection_gates_have_single_reason_inputs[workload]
04 test_mutation_04_calibration_projection_gates_have_single_reason_inputs[records]
05 test_mutation_14_rejected_calibration_is_rejected_for_quality_only
06 test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only
07 test_calibration_none_mode_rejection_is_explicit_and_intentional
08 test_build_receipt_uses_real_binary_admission_validator_and_binds_sha
09 test_build_receipt_binary_sha_and_trace_mutations_fail_closed[record-binary-sha]
10 test_build_receipt_binary_sha_and_trace_mutations_fail_closed[receipt-trace]
11 test_mutation_19_source_commit_must_equal_loaded_head
12 test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order
13 test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks
14 test_login_and_suspect_are_rejected_before_output_reservation[PEGASUS_LOGIN]
15 test_login_and_suspect_are_rejected_before_output_reservation[PEGASUS_SUSPECT]
16 test_mutation_17_site_detection_requires_fail_closed_evidence
17 test_live_site_must_equal_spec_site_before_output_reservation
18 test_run_window_orders_pre_measure_post_and_records_all_sessions
19 test_measure_exception_still_runs_post_probe_and_closes_remaining_plan
20 test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure
21 test_mutation_06_live_env_mismatch_rejects_before_output_reservation
22 test_mutation_10_exclusive_create_rejects_existing_path_before_measurement
23 test_runtime_head_must_complete_source_commit_three_way_binding
24 test_output_open_uses_all_five_required_flags
25 test_production_adapter_artifact_finalizes_from_raw_medians
26 test_finalizer_revalidates_complete_header_and_terminal_contract[header.format]
27 test_finalizer_revalidates_complete_header_and_terminal_contract[header.loaded_head]
28 test_finalizer_revalidates_complete_header_and_terminal_contract[header.runtime_head]
29 test_finalizer_revalidates_complete_header_and_terminal_contract[header.randomization_algorithm]
30 test_finalizer_revalidates_complete_header_and_terminal_contract[header.seed_hex]
31 test_finalizer_revalidates_complete_header_and_terminal_contract[terminal.status]
32 test_mutation_18_recorded_multiple_pair_sample_order_must_match_plan
33 test_mutation_07_one_noncomplete_session_makes_whole_floor_missing
34 test_nonfinite_measurement_is_recorded_incomplete_not_serialized_as_nan
35 test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped
36 test_mutations_09_and_13_forged_production_named_high_measure_is_rejected
37 test_finalizer_rejects_duplicate_session_id_even_when_set_matches
38 test_summary_is_exclusive_create
39 test_cli_execute_window_selects_the_named_production_adapter
40 test_validate_only_prints_plan_without_reserving_output
```

[実測] fixture 更新後に挙動変更だけで赤になる既存 node は次の 3 件である。

```text
test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order
test_measure_exception_still_runs_post_probe_and_closes_remaining_plan
test_mutation_07_one_noncomplete_session_makes_whole_floor_missing
```

[実測] supersede してよいのは旧 policy ID、window-global stop、1 欠測即全体不採用、v1 schema、旧 spec hash による HMAC golden だけである。create-only、HEAD/blob/source 束縛、固定 probe argv、upper >= 1、live site/env、production adapter 非差込、plan 順・ID/count exact 検査は維持対象で、plan はこれらを壊していない。

[実測] T-2166 の build receipt trace / binary sha は transitive 赤の列挙には含まれるが、新設変異の単独証拠には数えられていない。`refs/t2166-README.md:56-63` と整合する。

(e) [実測] 対応: P3、P4。

### 所見 7 — schema v2 判断は正しいが plan の consumer grep は summary に偏っている

(a) [実測] `floor-pair-summary/v1`、`floor-pair-window/v1`、`floor-pair-spec/v1` を読む production consumer は repo 内にない。test も定数 `F.SPEC_SCHEMA` を使うだけで、旧 literal を読む consumer ではない。

(b) [実測] 現物の一致は `floor_pair_driver.py:48-51` と `test_floor_pair_driver.py:187` のみ。`docs/`、`tools/`、`orchestrator/`、`tests/` を全検索した。`test_ccbench_spawn_sites.py` と `test_official_perf_closure.py` は source inventory consumer で、JSON schema consumer ではない。

(c) [実測] shape を変えて v1 のままにすると、将来の reader が旧 window terminal、旧 failure policy、旧 summary と誤認する。v2 なら現在の受理集合や床値は変えず、成果物の意味だけが正しく識別される。

(d) [実測] `SPEC_SCHEMA`、`WINDOW_SCHEMA`、`SUMMARY_SCHEMA` をすべて v2 に上げる plan を採用する。`WINDOW_FORMAT_ID` と `SUMMARY_FORMAT_ID` は JSON / JSONL serialization 自体が変わらないため据置きでよい。最終記録には summary だけでなく 3 schema 全部の grep 結果を書く。

(e) [実測] 対応: P3、P4。

### 所見 8 — §5 関門は閉じたままだが、残る sentinel は 9 ではなく 8 cell

(a) [実測] 提案値セルは `_RESERVED_SENTINEL_RE` に掛からず、`_EXPECTATION_ROW_RE` は model snapshot 行だけに適用される。対象 driver 行を埋めた後も 8 value cell に `未記入` が残るため admission は閉じる。

(b) [実測] 表は `docs/phase3-b4-reflux-ablation-preregistration.md:154-167`。全 cell の sentinel 検査は `p3_b4_admission_record.py:645-676`、expectation regex は `:103-118`。`p3_b4_analysis_prereg_consumer.py:301-345` は §5.1.1 だけを読み、§5 表や §5.1.2 を読まない。

(c) [実測] 対象 driver 行だけを記入しても実走関門は開かず、床値や主実験の受理集合は変わらない。変わるのは §5 の 1 参照だけである。

(d) [実測] brief の「他 9 行」を「残る 8 value cell」へ直す。値セルの evidence path/hash や選択規則は consumer が意味検証しないことも明記する。

(e) [実測] 対応: P2、P6。

### 所見 9 — generic dispatch は機械的に実行可能だが、3 driver は別 process にする

(a) [実測] `--task generic` は `--` を除いた argv を shell=False で実行し、cwd は repo root、環境は clean allowlist である。evidence target は driver ごとに create-only である。

(b) [実測] `dispatch_compute.py:154-160`、`:1311-1321`、`:1406-1417`、`:1563-1596`、`:1623-1637`、`:4482-4495`。probe は `p3_b4_wiring_probe.py:1494-1502` と `:2022-2026`。

(c) [実測] 同じ interpreter から `main()` を 3 回呼ぶと 2 回目で停止し、3 evidence が揃わない。別々の `python3 -m ...` process なら `_MAIN_CLAIMED` は共有されず問題ない。

(d) [実測] plan の 3 dispatch command を別 job として実行する。開始前に 6 target が不存在であることを確認する。途中まで生成された場合は同じ slug を削除して再実行せず、新しい凍結 slug へ戻す。

(e) [実測] 対応: P5、P6。

### 所見 10 — S-C は 1 commit に収まるが見積りは楽観的

(a) [推測] production は net +120〜160 行、test は追加 test を含め net +220〜320 行程度になる。2 file に局在するため 1 実装子・1 commit は可能だが、plan の合計 +180〜255 行は小さめである。

(b) [実測] 主変更面は `floor_pair_driver.py:48-69`、`:205-210`、`:883-902`、`:1619-1870`、`:1899-2196` と `test_floor_pair_driver.py:185-293`、`:949-982`、`:1287-1353`、`:1539-1810`。

(c) [推測] 見積り不足自体は床値を変えないが、campaign-local test や 177 境界 test が省略されると誤った受理集合を残す。

(d) [推測] 欠測 scope だけなら 1 commit、fix 3 巡以内で妥当。ただし所見 1を probe schema 変更で直す場合は `p3_b4_wiring_probe.py` が第三の実装面となるため、S-C と分離する。

(e) [実測] 対応: P4、P5。

## 裁定パッケージ候補

### 所見 11 — 「同一セッション」の逐語と現行 PlannedSession が衝突する

(a) [実測] D1641 は参照点を対ごとの同一セッション内で測るとするが、現行 driver は candidate 2 role と reference を別々の `PlannedSession` にする。

(b) [実測] `refs/D1641.md:16-19`、`floor_pair_driver.py:1218-1253`、`s2-plan.md:271-275`。

(c) [実測] 放置すると 3 時点の session median から D を作り、同一低水準 session 内参照を使う場合と床値が変わりうる。

(d) [推測] B案として compound session へ再設計するか、A案として 3-role block を裁定上の「同一標本セッション」と読む用語訂正を D1641 に追記する。測定前に裁定する。

(e) [実測] 対応: P1、P4。

### 所見 12 — 欠測修正だけでは D1641 完全適合にならない

(a) [実測] target/axis、PerfConfig の extime/reps/ycsb_max_ope、s8b journal、成果物名 5 要素は現行 driver が機械検査しない。plan がこれらを別 wave 候補へ出した判断は正しい。

(b) [実測] `s2-plan.md:7-20`、`:277-281`、`FloorPairSpec` は `floor_pair_driver.py:219-235`、top-level exact schema は `:1105-1125`、output path は `:779-827` と `:905-919`。

(c) [実測] 放置すると、別軸・未校正項目・命名不足・別 journal の成果物でも spec の他条件だけで床値 summary を生成でき、§5 が意図しない成果物を参照しうる。

(d) [推測] 測定開始前の follow-up wave で schema/validator を拡張するか、各項目を人手レビュー責任とする明示裁定を行う。「欠測修正で D1641 完全適合」とは記録しない。

(e) [実測] 対応: P1。

## 総括

- [実測] blocker: 1 件。
- [実測] must-fix: 4 件。
- [実測] fixture 更新後に直接赤となる既存 test: 3 node。
- [実測] fixture を更新しない場合の transitive 赤: 40 node。
- [実測] source は 51 test function、現行 collection は 140 node。
- [実測] schema v2 化は妥当で、外部 JSON consumer は 0 件。
- [推測] S-C 欠測 scope は 1 実装子・1 commit・fix 3 巡以内に収まる。
- [推測] ただし見積りは plan より大きく、probe schema 修正を混ぜる場合は分離が必要。