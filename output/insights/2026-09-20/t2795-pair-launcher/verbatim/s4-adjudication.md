# 段 4 裁定 — [T-2795] (i) + [T-2797]/[T-1872] (α) 同 job pair launcher と B-5 §10 共有部品

親 (Claude、2026-09-20 13:50 JST)。入力 = brief.md、codex/s2-plan.md、codex/s3-consult-A.md (正しさ境界・identity)、
codex/s3-consult-B.md (実効性・過剰・実装性)。裁定 inbox の再走査 (第 25 回 D2174、t2724 A/X) は本 wave に触れない。

## §1 所見の裁定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 反映先 |
|---|---|---|---|
| A-M1 非 STOCK の certified を stock 成功に含める | real | 採用 | §2-1 成功条件、負例 test、変異 M7 |
| A-M2 候補用 condition gate を stock に流用 (MeaningCase(-1, bits) は適応枝を検査しない) | real | 採用 | §2-1 gate の stock 形 (A-1 paired `paper_story_a1_paired.py:6894–6918` の先例)、`--isolate-worktree` 必須、変異 M10 |
| A-S1 anomaly 負例を最終 repetition にも | real | 採用 | §2-3 TV test |
| A-S2 campaign.lock の preimage から correctness を復元して照合する test | real | 採用 | §2-3 TL test |
| A-S3 driver rc と測定成功を混同しない負例・文言 | real | 採用 | §2-1 (stock の outcome 出力)、README (親)、TL test |
| A-N1〜N3 brief の一般化の限定 | real (文言) | 採用 | insight README で限定文に直す (§5) |
| B-M1 TJ の driver 呼出し箇所数固定 (`:496–503`、2→3) と fixture fragment (`:915–935`) | real | 採用 | §2-2 |
| B-S1 terminal 復元の二層化を削り、skip は非成功 (rc=1、outcome=skipped) | real | 採用 | §2-1。plan の `_resolve_terminal_result` 新設・`_resolve_duplicate` 変更・変異 7 を削除 |
| B-S2 変異 6 (manifest 落とし) の kill は実 shell の TJ test へ | real | 採用 | §3 M6 |
| B-S3 TJ helper は履歴 + rc + compute-result 内容を返し、新 env を既定環境から除く | real | 採用 | §2-2 |
| B-S4 TV anomaly test は bench 到達可能 (do_bench=True、bench 境界は呼出し禁止) | real | 採用 | §2-3 |
| B-S5 README は追記でなく既存文の置換、qsub fence は 1 個 | real | 採用 (親 docs) | 段 7 |
| B-nit 較正・verify の job body env 3 個 | real (scope) | 採用 = **今回は入れない**。driver CLI だけ実装し、job body 配線は B-5 (β) 試走 wave の launcher 設計で足す | §2-2、§5 |
| B-nit stock 終了時の digest 再生成 | — | **残す** (既存成果物の更新、新台帳ではない) | §2-1 |
| B-nit token/projection の新 test | real (scope) | 採用 = 削る。A-M1 の負例 (非 STOCK certified → 失敗) が分類の実効を担う | §2-3 |
| B-nit `--v` 略記の曖昧化 | real (狭い互換差) | 受容。既定 argv・identity 不変とは別の差として記録する。使用箇所なし | §5 |
| B 閉包 owned_paths | real | 採用 = author は L・J・TL・TJ・TV の 5 file、親は `tools/pegasus/README.md`。pipeline.py / loop.py は変更なし。manifest を 5 file に更新 | child-manifest.json |
| brief アンカーの誤り (perf `:3044`、run_campaign `:2012–2021`、J K2 env `:54–97`) | real | 採用 | §2 は consult B の表を正とする |
| P1 同 campaign、`--stock-control` を identity に焼かない | 支持 (A/B) | 確定 | §2-1 |
| P2 applied template 下の stock | 条件付き (A) | A-M1・A-M2 を満たす形で確定。実 compiler での STOCK 成立は land 後の pair wave で確認し、成立しなければ対照成立と認定しない | §2-1 |
| P3 較正 CLI 2 口 | 支持 | 確定。identity key は `perf_workload` (4 key dict) + `extime` + `reps` + 既存 `records`/`threads` | §2-4 |
| P4 verify opt-in、記録は campaign.lock | 条件付き (A) | 確定 + A-S2 の永続化 test。§5.5 全体の成立とは言わない | §2-4 |
| P5 候補後に stock、候補 rc≠0 でも stock | 条件付き | 確定 (両 rc を 0 初期化、集約 = 候補非零優先) | §2-2 |
| P6 段構成 | 支持 | 段 6 review 2 本 + 変異 matrix + 受入 | — |
| Q1 terminal skip | — | **skipped = 非成功 (rc=1)**。復元しない (B-S1)。fresh layout 運用 | §2-1 |
| Q2 legacy 1 + performance `perf.reps` (5) | — | 可。回数は §5.5 が定めない。β で verifier wall を実測 | §2-4 |
| Q3 較正 2 口同時必須・verify は較正必須 | — | 可 | §2-4 |
| Q4 実 compiler の STOCK 確認は land 後 | — | 可。ただし A-M1・A-M2 は今回実装 | §2-1 |

scope 外 real (実装せず設計メモ・insight に記録): stock 先行 (planner 前) の順序選択 env、B-5 の block stock 配置、
較正・verify の job body 配線、実 argv の独立 receipt。いずれも DW-G04 (発火 artifact / 計測 ID が無い) で設計メモに留める。

## §2 plan v2 (実装仕様 — author への確定指示。行番号は consult B の「正しいアンカー表」の現物)

### §2-1 driver: stock 評価口 (`orchestrator/campaign/p3_s4_loop.py`)

1. argparse (`:2797–2854`) に `--stock-control` (`store_true`) を足す。`--value` の既定 20.0・受理域・`_assert_coder_value_domain` は不変。
2. 排他 (`supplied` 集合 `:2855–2864` を使い、`--record-agent-output` の既存排他 `:2865–2879` の**後**、B4 / knowledge 検査より前で `ap.error`)。
   署名: `stock ∧ X → error` の X = `run_iteration` / `value` (明示指定) / `emit_planner_context` / `no_build` / `coder_role` /
   `b4_reflux_ablation` / `coder_build_authority ≠ None` (`--allow-coder-derived-build`: stock の build は coder 由来でない) /
   `¬isolate_worktree` (`--stock-control requires --isolate-worktree`: 別の pinned-clean stock root が要る、A-M2)。
   error 本文は `--stock-control cannot be combined with --<flag>` (isolate は `requires`)。
   **通る正例:** `--stock-control --isolate-worktree --fetchcontent-prebuild-receipt R [--knowledge-manifest M --knowledge-classification C --knowledge-de-novo-claim false] [--calibrated-perf --perf-workload W [--verify-performance]]`。
   `--knowledge-manifest` は許す (同 campaign の identity `:1611–1618` に必須)。`--coder-role` は渡さない (`:3013–3023` の必須条件は `run_iteration` を含むので発火しない)。
3. `build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)` (coder_authority=None。policy `_new_policy()` は authority に依存しないので identity は候補と同じ)。`_assert_single_tenant()`、`assert_pinned_clean(fixed_sub, PIN)`、`bind_admission_policy`、`_prepare_knowledge_campaign` (`:3037–3042`) は候補と同じ順で通す。knowledge receipt は同 body なら既存を受理する (`knowledge_manifest.write_receipt` の同一 bytes 許容)。
4. worktree context (`:3046–3055`) の後、proposal 分岐 (`:3058`) の**前**に stock 分岐を置き、新関数 `_run_stock_control_resolved(cfg, perf, sub, layout, contract, resolved_site, *, stock_root, cache_root, build_context, **fetchcontent_options) -> Dict` を呼ぶ。planner / coder / state / `drive_iteration` / `_run_one_iteration_resolved` / quarantine / `_check_attribution_before_quarantine` / `project_whiteboard` / checkpoint save / `LoopState` 作成 (`:3137`) に到達しない。
5. 新関数の順序: exact `BuildRunContext` 確認 → `genome = Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})` → `layout.ensure()` → `ident.ensure_resumable_attempts(cfg, layout, admission_policy=build_context.policy)` → `with applied(TEMPLATE_PATCH, PIN, sub):` → **stock 形の condition gate** → `run_campaign(cfg, [genome], perf, contract.env_tag, contract.clocks_per_us, numactl=list(contract.numactl), ccbench_dir=sub, cache_root=cache_root, authorization_contract=env_contract.authorize(contract.env_tag), build_context=build_context, declared_use_class=DECLARED_USE_CLASS, backoff_grammar_version=..., **campaign_options)` (候補 `:1996–2021` と同じ環境・依存 options)。
6. **condition gate の stock 形 (A-M2):** `_require_condition_gate(source_root, genome, *, configure_args=(), stock_root: Optional[str] = None)` を拡張し、`genome.flags["BACKOFF_FIXED"] == -1` のとき `stock_root` 必須 (None なら `ValueError`)、`capture_define_inputs(source_root, stock_root=stock_root, configure_args=...)`、`make_define_request(driver_id="orchestrator.campaign.p3_s4_loop", macro="BACKOFF_FIXED", requested_value=-1, default_value=-1, stock_comparison=True)`、`MeaningCase(-1, None, expected_selected_branch=condition_meaning_gate.STOCK_ADAPTIVE_BRANCH)`。候補 (`value ≥ 1`) の既存経路は bytes 不変。stock_root = `fixed_sub` (`os.path.join(root, "external", "ccbench")`、`assert_pinned_clean` 済み。`--isolate-worktree` 下では `sub` と別 tree)。拒否時の evidence 書出し・例外は既存と同じ。
7. **成功条件 (A-M1):** `summary.results` の `r` について `r.certified and not r.aborted` **かつ** `r.variant == variant_id(genome)` (= STOCK token、`pipeline.variant_id` の既定) **かつ** WAL の BUILD_START record (`wal.records_by_stage(layout, r.variant)`) の `src_token == source_digest.STOCK` — のとき `outcome="certified-stock"`、rc=0。それ以外: `aborted` (rc 1)、`non-stock-source` (certified でも source が STOCK でない、rc 1)、`skipped` (`summary.skipped > 0`、terminal 既存 = fresh layout でない、rc 1、`summary.skipped_variants[0]` があれば ID を報告、無ければ ID を書かない)、`identity-skipped` (rc 1)。source を復元後 tree から再解決しない。WAL を書かない。
8. stdout: `=== 段 4 stock control (stock_root=..., isolate_worktree=True) ===`、`  outcome=<...> variant=<...> fitness_tps=<...> verdict=<...>`、`  campaign dir: <layout.root>`。「pair 成立」とは書かない (対照成立の判断は両 attempt の WAL outcome、A-S3)。
9. digest 再生成: `outcome != "skipped"` かつ WAL に admitted record があるとき、`:3164–3176` と同じ `require_admitted_campaign(..., CERTIFIED_ACCEPTANCE)` → `make_critic_digest(..., identity_projection=make_critic_identity_projection(view))` で `s4_loop_digest.txt` を上書き。checkpoint / whiteboard は触らない。
10. `_resolve_duplicate` (`:1794–1864`) は変更しない。

### §2-2 job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) と TJ

1. `required_env` (`:17–24`) 不変。`:97` の後 (repository path 解決より前) に `IZANAGI_S4_STOCK_CONTROL` の受理: 未設定または `0` → off、`1` → on、それ以外 (設定済み空値を含む、`${IZANAGI_S4_STOCK_CONTROL-0}` で判定) → `refuse` (rc=2)。較正・verify の env は**足さない**。
2. `stock_identity_argv=()`: K2 が要求されていれば `--knowledge-manifest`、任意の `--knowledge-classification` / `--knowledge-de-novo-claim` を `k2_argv` (`:77–93`) と同じ値で入れる。`--coder-role` は入れない。`k2_argv` は proposal 専用のまま。
3. `:580–593`: `candidate_rc=0; stock_rc=0` を初期化。proposal / fixture の既存 Python 呼出しは bytes を保ち末尾に ` || candidate_rc=$?` を付ける (fragment は各末尾を含む一意な形)。stock off なら `exit "$candidate_rc"`。on なら
   `"$PY" -B -m orchestrator.campaign.p3_s4_loop --isolate-worktree --fetchcontent-prebuild-receipt "$prebuild_receipt" "${stock_identity_argv[@]}" --stock-control || stock_rc=$?`
   (`--allow-coder-derived-build` は渡さない)。その後 `echo "p3 S4 pair: candidate_rc=$candidate_rc stock_rc=$stock_rc"`、最終 `if [[ $candidate_rc -ne 0 ]]; then exit "$candidate_rc"; fi; exit "$stock_rc"`。`set -Eeuo pipefail` (`:9`) と EXIT trap (`:138–157`) は不変。`driver_rc` は job 全体の集約 rc。
4. TJ: required fragment (`:154–427`) と mutation matrix (`:611–780`) に新 pin (`stock-default-off`、`stock-mode`、`stock-identity-argv`、`proposal-status-capture`、`fixture-status-capture`、`stock-status-capture`、`pair-status-priority`)。各 fragment は一意で 1 static failure (runner `:782–790`)。**`:496–503` の driver 呼出し箇所数を 2 → 3 に更新** (全呼出しが依存 prefix export・prebuild より後、の条件は維持)。stage-order (`:525–558`) に stock 起動の位置 (proposal / fixture 分岐より後) を足す。fixture fragment (`:915–935`) は挿入が無いので不変。既存 pin (`proposal` / `fixture` / `k2-*`) は削らない。
5. TJ 実 shell helper (`:1153–1324`): driver stub は argv 履歴 (append)・任意 rc・compute-result の内容を返せるようにし、`IZANAGI_S4_STOCK_CONTROL` を既定環境から除く。既存 consumer (`:1327–1379`) は参照方法だけ更新し期待 argv は不変。新 test: `test_default_job_invokes_driver_once` (fixture / proposal / K2 各経路で履歴 1、従来 argv exact)、`test_pair_job_runs_candidate_then_stock` (履歴 2、順序、同 receipt、stock argv に同 manifest / 宣言値、`--coder-role` / `--value` / `--run-iteration` / `--allow-coder-derived-build` 無し、`--stock-control` 有り)、`test_pair_job_runs_stock_after_candidate_failure` ((7,0)/(0,9)/(7,9) → rc 7/9/7、compute-result の driver_rc 一致)、`test_invalid_stock_environment_refuses_before_prebuild` (空値・`2`・`true` は rc=2、compute-result 不在)。`:1382–1390` (k2_argv は proposal 専用) は維持。README の qsub fence (`:1740–1764`) は 1 個のまま (親が既存例を更新)。

### §2-3 TL / TV の test

TL (`orchestrator/tests/test_p3_s4_loop.py`) に追加 (pytest 経由で焦点走。`__main__` harness は既存のまま):
- `test_stock_control_reaches_campaign_under_applied_template`: 新関数を実呼出し、`applied` 内で gate → `run_campaign` の順、genome exact (`BACK_OFF=1`, `BACKOFF_FIXED=-1`)、同 cfg / perf / 契約 / prebuild options。
- `test_stock_control_does_not_touch_loop_state`: 実 `main --stock-control ...`。checkpoint 不在のまま / 既存 bytes 不変、`project_whiteboard` / `save_loop_state` / `drive_iteration` / `_run_one_iteration_resolved` / `quarantine` / `load_proposal_file` は呼ぶと失敗する spy。
- `test_stock_control_cli_rejects_conflicting_modes`: §2-1 項 2 の各 X を parametrize、rc=2 と error 本文、layout / receipt 読込みより前。
- `test_fixture_value_minus_one_remains_rejected`: 実 `main --value -1`、既存値域拒否、`run_campaign` 未到達。
- `test_stock_control_rejects_non_stock_certified_source` (A-M1): `run_campaign` 境界で certified だが `variant != variant_id(genome)` / BUILD_START `src_token != STOCK` の結果を返す fixture → `outcome=non-stock-source`、rc 1。
- `test_stock_control_reports_skipped_without_restore` (Q1): `summary.skipped=1` → `outcome=skipped`、rc 1、`_resolve_duplicate` 未呼出し、whiteboard 不変。
- `test_stock_condition_gate_declares_adaptive_branch` (A-M2): 実 `_require_condition_gate(..., stock_root=...)` を `_REAL_CONDITION_GATE` で通し、`capture_define_inputs` / `evaluate_*` の外部実行だけ模擬して、request の `stock_comparison=True`・`requested_value=-1`・MeaningCase の `expected_selected_branch == STOCK_ADAPTIVE_BRANCH`・`stock_root` の転送を検査。stock_root None は `ValueError`。候補値では従来の bits 宣言 (回帰)。
- `test_stock_and_candidate_share_manifest_campaign_identity`: 両 main 経路で cfg を捕捉、同 manifest なら canonical preimage と layout root が同一、genome は異なる。
- `test_stock_digest_refresh_keeps_checkpoint`: admitted view で digest が stock を含んで再生成、checkpoint 不変。
- `test_calibrated_perf_uses_p2_constants_and_exact_workload`、`test_calibrated_cli_binds_effective_perf_before_layout` (期待値は `p2_2` 定数から独立に組む)、`test_default_cli_preserves_preimage_bytes` (変更前 preimage bytes を fixture 定数で固定; 既存 `:573–604` の golden も不変)、`test_perf_cli_rejects_partial_and_invalid_options`、`test_verify_opt_in_reaches_real_loop_evaluate_options` (実 `loop.run_campaign`、`:8742–8789` 型、extra_correctness に `(PERFORMANCE_TAG, performance_correctness_workload(perf))`、既定は None)、`test_campaign_lock_preimage_reconstructs_performance_correctness` (A-S2: 実 lock の preimage から `records/threads/perf_workload/extime/reps/verify` を読み、`performance_correctness_workload(PerfConfig(...))` の flags / reps が evaluate 境界へ渡ったものと一致)。
- `test_candidate_cli_rc_zero_on_rejected_outcome_is_not_pair_success` (A-S3): 候補 CLI が `outcome=rejected` でも rc=0 の既存契約を固定 (変更しない)。

TV (`orchestrator/tests/test_pipeline_verify_result_retention.py`): 実 `pipeline.evaluate` に実 `performance_correctness_workload(perf)` を `extra_correctness` で渡し、build / trace 実行は既存の模擬境界、verifier は小 fixture trace。`do_bench=True` で bench の外部実行境界を呼出し禁止にする (B-S4)。
- `test_performance_verify_keeps_legacy_and_all_repetitions` (legacy 1 → performance `reps` 回、exact flags、COMMIT の `verify_configs == ["legacy", "performance"]`)。
- `test_performance_anomaly_at_first_repetition_aborts_before_bench`、`test_performance_anomaly_at_last_repetition_aborts_before_bench` (A-S1)、`test_legacy_anomaly_skips_performance_pass`。
- `test_performance_verify_requires_exact_contract_numactl` (空 prefix は通る、異なる非空 prefix は build / verify 前に拒否)。

### §2-4 較正動作点 CLI と verify opt-in (`p3_s4_loop.py`)

1. argparse: `--calibrated-perf` (`store_true`)、`--perf-workload {write-heavy,balanced,read-heavy}` (既定 None)、`--verify-performance` (`store_true`)。片指定は `ap.error("--calibrated-perf and --perf-workload must be supplied together")`、verify 単独は `ap.error("--verify-performance requires --calibrated-perf and --perf-workload")`。
2. `default_perf()` (`:1631–1636`) は不変。直後に `calibrated_perf(workload_name: str) -> PerfConfig` を新設: `PerfConfig(records=p2_2.RECORDS, threads=p2_2.THREADS, workload={**dict(p2_2.WORKLOADS)[workload_name], "ycsb_max_ope": S2_FLAGS["ycsb_max_ope"]}, extime=p2_2.EXTIME, reps=p2_2.REPS)`。値の再定義禁止。`S2_FLAGS` は `pipeline` から import。
3. `cfg = default_cfg(...)` (`:2978–2986`) の直後、`_campaign_cfg_for_site` (`:2988`) の前で perf を確定し、較正 opt-in 時だけ `replace(cfg, search_config={**cfg.search_config, "records": perf.records, "threads": perf.threads, "perf_workload": dict(perf.workload), "extime": perf.extime, "reps": perf.reps})`、verify opt-in 時はさらに `SEARCH_CONFIG_VERIFY_KEY: VERIFY_LEGACY_PLUS_PERFORMANCE`。key 名は `perf_workload` (既存の `workload` key は他 driver で token 文字列 / name 付き dict の意味を持つため二義化を避ける、D75)。指定なしでは key を**一つも**足さない。`--stock-control` は identity に焼かない。
4. `:3044` の `perf = default_perf()` を上で確定した perf に置き換える。emit 経路 (`:2989–3012`) も同じ cfg を使う (emit と評価の identity 一致)。
5. exact correctness の接続は既存: `loop._closed_verify_workloads` (`:153–162`) → `performance_correctness_workload(perf)` → `evaluate(extra_correctness=...)`。pipeline.py / loop.py は変更しない。記録先 = campaign.lock の identity preimage (search_config)。WAL verify record (`workload == {"tag": tag}`) と receipt schema は変更しない。

### §2-5 author の権限・報告

- 編集は L・J・TL・TJ・TV の 5 file だけ。pipeline.py / loop.py / ident.py / source_digest.py / p2_2.py / condition_meaning_gate.py / docs / README は触らない。commit しない。
- 既存 test の期待値は変えない (TJ helper の履歴化に伴う参照方法の更新と、`:496–503` の呼出し箇所数 3、stage-order の追加だけ)。既存 CLI golden (`:573–604`) が赤なら実装側が誤り。
- 実走: `python3 -m pytest orchestrator/tests/test_p3_s4_loop_job_contract.py orchestrator/tests/test_pipeline_verify_result_retention.py -q` と TL の新 test を `-k` で。pytest 不可なら「実装済み・未実走」と書く。build を要する test は書かない。

## §3 変異の事前登録 (DW-M01。実装後に単一理由性を確認し spec 化)

| # | 変異 (位置) | kill する test (1 理由) |
|---|---|---|
| M0 | L の docstring だけ変更 (等価対照) | SURVIVED |
| M1 | stock genome の `BACKOFF_FIXED: -1` → `1` | TL `test_stock_control_reaches_campaign_under_applied_template` (genome 不一致) |
| M2 | stock genome の `BACK_OFF: 1` → `0` | 同上 (BACK_OFF 不一致) |
| M3 | stock 関数の末尾で `project_whiteboard` / checkpoint 保存を呼ぶ | TL `test_stock_control_does_not_touch_loop_state` |
| M4 | stock + `--run-iteration` の排他を外す | TL `test_stock_control_cli_rejects_conflicting_modes` |
| M5 | `_check_attribution_before_quarantine` を `coder.value < 0` で skip | TL `test_fixture_value_minus_one_remains_rejected` |
| M6 | J の stock 起動から `"${stock_identity_argv[@]}"` を落とす | TJ `test_pair_job_runs_candidate_then_stock` |
| M7 | stock 成功条件から STOCK 判定 (`variant_id` / `src_token`) を外す | TL `test_stock_control_rejects_non_stock_certified_source` |
| M8 | 較正 opt-in で `records/threads` を search_config に反映しない | TL `test_calibrated_cli_binds_effective_perf_before_layout` |
| M9 | 指定なしでも `perf_workload` key を足す | TL `test_default_cli_preserves_preimage_bytes` |
| M10 | stock gate の MeaningCase を候補用 bits 宣言に戻す (`stock_comparison=False`) | TL `test_stock_condition_gate_declares_adaptive_branch` |
| M11 | J の `${IZANAGI_S4_STOCK_CONTROL-0}` → `-1` (既定 on) | TJ `test_default_job_invokes_driver_once` |
| M12 | J の proposal 末尾 `|| candidate_rc=$?` を外す | TJ `test_pair_job_runs_stock_after_candidate_failure` (候補失敗で stock 未起動) |
| M13 | J の最終分岐を `exit "$stock_rc"` だけに | TJ 同 test ((7,0) で rc 0) |
| M14 | `--verify-performance` で verify key を焼かない | TL `test_verify_opt_in_reaches_real_loop_evaluate_options` |
| M15 | P の repetition loop: 最初の pass で残り rep を skip (`pipeline.py:2185` 付近) | TV `test_performance_anomaly_at_last_repetition_aborts_before_bench` (test 強化のみの層 → DW-M08 の新旧両走) |

## §4 段 5 の分割

author 1 本 ((1) → (2) → (3) の順、報告を節で分ける)。所有 = L・J・TL・TJ・TV。unit worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795-unit-impl` (base 371674ea6)。

## §5 記録・限定 (段 7 で insight / README へ)

- brief の限定: 「live pin なし」は「凍結 artifact からの bytes pin なし。job 契約 test の逐語 pin は現役で author が更新」と書く。「stock 評価は実走済み」は「stock genome と inert 検査の実装先例 (b10 / A-1 paired) あり、S4 template・compiler・gate での成立は未測定」と書く。編集面重複 0 件は `$CLAUDE_JOB_DIR/tmp/overlap.sh` の走査結果 (worktree 全件、commit 済み + dirty) を添える。
- 本 wave が作らないもの: 初回 planner 前の stock (B-5 §5.4 の系列開始 stock の順序)、block stock、較正・verify の job body 配線、実 argv の独立 receipt、実 compiler での STOCK 成立の証明。pair 結果の「対照成立」は両 attempt の WAL outcome と新規評価の有無で判定し、driver rc や campaign ID から判定しない。
- `--v` 略記は `--verify-performance` 追加で曖昧になる (`--va` / `--val` は従来どおり)。使用箇所なし。
- README (`tools/pegasus/README.md` `:359–371`、`:397–406`): env 表に `IZANAGI_S4_STOCK_CONTROL`、「manifest・宣言値は proposal 分岐だけへ渡す」を「coder-role は proposal のみ、manifest と宣言値は pair 有効時に stock にも渡す」へ置換、候補優先 rc、fresh layout、stock 後の digest 更新、stock は別の使い捨て worktree (同 pin) である旨。qsub fence は既存 1 例を更新。
