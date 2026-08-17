## 1. file:line 粒度の変更計画

行番号は現 HEAD 基準である。

### producer

[orchestrator/campaign/p3_autonomous_workload_trial.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:39)

- `:39-48`
  - `s8b_ratified_freeze.load_ratified_freeze` を直接 import する。C01 の declared call が実際の loader へ到達できる形にする。

- `:188-192`
  - 既存 `WORKLOADS` は探索専用集合として内容を一切変えない。
  - 直前または直後へ次を新設する。
    - `EXPLORATORY_WORKLOAD_PROFILE = "exploratory"`
    - `FORMAL_WORKLOAD_PROFILE = "formal"`
    - `WORKLOAD_PROFILE_CHOICES`
    - `FORMAL_PILOT_SCOPE = "formal-holdout-rr80-rr20"`
  - 正式比率の axis literal は置かない。

- `:305` 付近の内部 dataclass 群
  - `_FormalWorkloadProfile` を新設する。
  - field は `holdouts: Mapping[...]`、`sha256: str`、非公開 seal。
  - `RatifiedFreeze` 自体には `holdouts` field がなく、現 API は `document` と `sha256` なので、`ratified.document["holdouts"]` をこの producer 内部型へ一度だけ投影する。
  - `_FORMAL_PROFILE_SEAL` と exact-type/seal 検査も同位置へ置き、`main` から `run_trial` へ同じ snapshot を渡す際の偽造や二重ロードを防ぐ。

- `:620-636`、3 sink の直前
  - `_load_formal_workload_profile()` を新設する。
    - `load_ratified_freeze(ROOT)` を呼ぶ。
    - `ratified.document["holdouts"]` の key 集合が `trial_registry.HOLDOUT_WORKLOADS` と完全一致することを確認する。
    - `ratified.sha256` と holdout mapping を `_FormalWorkloadProfile` に束縛する。
  - `_workload_inputs(workload, formal_profile)` を新設する。
    - 探索時は既存 `WORKLOADS[workload]` と formal 値なしを返す。
    - 正式時は `formal_profile.holdouts[workload]` の `ycsb`、holdout 全体、`formal_profile.sha256` を返す。
  - callable 注入や別名 decoy を介さず、`main` / `run_trial` から loader まで静的に到達可能な通常 call にする。

- `:637-674` `_campaign_for`
  - optional keyword `formal_holdout` と `ratified_sha256` を追加する。
  - 探索 branch は現在の `records=100_000`、`threads=4`、`pilot_scope="exploratory-ycsb-abc"`、spec、search tag をそのまま通す。
  - 正式 branch 内に直接 `1_000_000` と `48` を書き、ratified entry の `records` / `threads` がそれらと一致しなければ `AutonomousTrialError` とする。
  - `formal_holdout["ycsb"]` と `workload_flags` も一致検査し、実際の search config には freeze 由来値を入れる。
  - 正式 branch の campaign identity に `ratified_freeze_sha256`、正式 `pilot_scope`、正式用 spec/search tag を含める。探索 campaign ID の preimage には一切追加しない。

- `:677-684` `_perf_for`
  - 同じ optional formal 入力を追加する。
  - 正式 branch 内に `1_000_000` / `48` の literal と freeze 値との fail-closed 照合を直接置く。
  - 照合後は freeze entry の値で `PerfConfig` を作る。
  - 探索 branch は現値のまま。

- `:687-695` `_descriptor_for`
  - `_perf_for` と同じ形式で正式 entry を照合する。
  - `projected_input` の `records`、`threads`、`ycsb` を ratified entry から作る。
  - 正式 scale literal はこの関数内にも直接置く。共通定数や共通 validator だけへ逃がさない。

- `:698-728` `_prepare_campaign_identity`
  - optional `_FormalWorkloadProfile` を受ける。
  - `_workload_inputs` で一つの entry を解決し、その同じ entry と SHA を `_descriptor_for`、`_campaign_for` へ渡す。
  - 引数省略時は従来どおり `WORKLOADS` を使うため、既存の直接 caller を壊さない。

- `:731-800` `_trial_launch_admission`
  - optional formal profile を受け、登録済み campaign binding の再導出にも正式 descriptor/campaign を使う。
  - 実行側だけ正式化し、manifest 照合側が探索 campaign ID を計算する分裂を防ぐ。
  - profile 省略時の既存登録・探索 admission は不変。

- `:2021-2131` `_finish_trial`
  - profile snapshot を受け、各 workload の `_run_workload` 呼び出しへそのまま渡す。反復途中で loader を再実行しない。

- `:2398-2505` `_run_workload`
  - profile を受け、`_workload_inputs` から同一 holdout entry を一度解決する。
  - その entry を `_prepare_campaign_identity` と `_perf_for` の両方へ渡す。
  - `result["workload_flags"]` も freeze 由来の同じ YCSB mapping にする。

- `:2845-2985` `run_trial`
  - `workload_profile: str = EXPLORATORY_WORKLOAD_PROFILE` を追加する。
  - `main` から渡された sealed `_FormalWorkloadProfile` があれば再利用し、programmatic formal caller ならここで一度だけロードする。
  - 正式時の `selected` は `formal_profile.holdouts` 内、探索時は `WORKLOADS` 内でなければ拒否する。
  - 同じ profile を admission 再導出と `_finish_trial` に渡す。

- `:3298-3426` `main`
  - `--workload-profile {exploratory,formal}` を追加し、既定を literal `"exploratory"` にする。
  - `--workloads` の既定 `list(WORKLOADS)` は維持する。正式実行は `--workload-profile formal --workloads rr80` または `rr20` を明示し、profile を workload 名から暗黙推定しない。
  - 正式 profile を一度ロードし、その同一 sealed object を `_trial_launch_admission` と `run_trial` に渡す。
  - 探索時は loader を呼ばない。

### producer tests

[orchestrator/tests/test_p3_autonomous_workload_trial.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:335)

- `:335-377` 付近へ3 sink の正式投影テストと fail-closed テストを追加する。
- `:899-923` 付近へ profile CLI 既定が literal `"exploratory"` である AST tripwire を追加する。
- `:938-980` の探索統合テストを、loader 非呼出しと三つの探索 scale が不変である回帰検査として補強する。
- `:4703-4814` 付近へ CLI profile の伝播テストを追加する。
- `:5595-5676` の holdout admission 順序テストは維持し、明示 profile なしで正式値を推測しないことを確認する。

### C01 snapshot

[orchestrator/tests/test_s8c_preregistration_predicates.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/tests/test_s8c_preregistration_predicates.py:139)

- `:151` の current-repository C01 tuple だけを、親による実測後に更新する。
- `:1869` の `nc_c01_perf_scale_regression` 期待値は `workload-projection-mismatch` のまま維持する。これは現状 snapshot ではなく、perf sink を探索 scale へ戻す変異を殺す oracle である。

以下は編集しない。

- `s8c_preregistration_evidence.py::_evaluate_c01`
- `s8b_holdout_freeze.py`
- `s8b_ratified_freeze.py`
- `output/s8b-freeze/` 配下
- floor 値表、freeze 世代、pin

したがって generator source hash の再同期は不要である。

## 2. (P1)〜(P4) への賛否

- (P1) 賛成。
  - 正式 axes は必ず `load_ratified_freeze` の戻り値から得る。
  - ただし `RatifiedFreeze` に新しい `holdouts` property や field は追加しない。既存 field は `document`、`sha256`、世代情報であり、producer 内部の `_FormalWorkloadProfile` が `document["holdouts"]` を実体として保持する方が変更面を狭くできる。
  - 同 wrapper の `.holdouts` と loader 戻り値の `.sha256` を実際に到達可能な処理で使うため、C01 用の token-only コードにはならない。

- (P2) 賛成。
  - `1_000_000` と `48` は三つの sink 各々の関数本体へ置く必要がある。`_evaluate_c01` は `_integers(functions[name])` を個別に見るため、共通定数や helper だけでは不合格になる。
  - 各 sink で freeze 値を literal と比較し、通過後は freeze 値を出力へ使う。これにより二重管理は恒真ではなく drift detector になる。

- (P3) 賛成。
  - `--workload-profile` と `run_trial(workload_profile=...)` を明示 selector とし、既定は探索。
  - workload 名だけから正式 mode を推測しない。正式 caller は profile と rr80/rr20 の選択を明示する。
  - 探索既定の ycsb-a/b/c、100,000 records、4 threads は変えない。

- (P4) 賛成。ただし更新対象を限定する。
  - `:151` の実 repo snapshot は、producer を含む commit に対する実測後に更新する。
  - `:1869` は負の変異 oracle なので更新しない。
  - 実測が予測と違う場合、期待値を合わせる前に loader reachability、`.holdouts` / `.sha256` 利用、各 sink literal を再検査する。

## 3. テスト nodeid 案と殺す誤実装

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_formal_profile_binds_ratified_holdout_to_campaign_perf_and_descriptor`
  - ratio だけ hardcode する、scale が一つ以上の sink で探索値のまま、descriptor だけ別 entry を使う誤実装を殺す。

- `...::test_formal_profile_scale_mismatch_fails_closed_in_each_sink[campaign]`
- `...::test_formal_profile_scale_mismatch_fails_closed_in_each_sink[perf]`
- `...::test_formal_profile_scale_mismatch_fails_closed_in_each_sink[descriptor]`
  - AST を通すだけの unused literal、上流一箇所だけの照合、特定 sink の照合漏れを殺す。

- `...::test_formal_profile_ycsb_mismatch_fails_closed_in_each_sink[campaign|perf|descriptor]`
  - `WORKLOADS` の axes と ratified entry を混成する実装、別 holdout の axes を渡す実装を殺す。

- `...::test_run_trial_formal_profile_uses_one_ratified_snapshot_for_admission_and_execution`
  - admission と実行で loader を二度読みし、異なる世代や SHA を使いうる TOCTOU を殺す。

- `...::test_run_trial_default_profile_never_loads_ratified_freeze`
  - 探索既定を正式へ倒す実装、探索を freeze の可用性へ依存させる実装を殺す。

- `...::test_workload_profile_cli_default_is_literal_exploratory_by_ast`
  - computed default、formal default、環境依存 default を殺す。

- `...::test_main_forwards_explicit_formal_profile_and_holdout`
  - CLI selector が `run_trial` または admission identity へ伝播しない実装を殺す。

- 既存 `...::test_no_build_campaign_identity_binds_shared_policy_context`
  - formal metadata を無条件追加して探索 campaign ID を変える誤実装を殺す。

- 既存 `...::test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`
  - 探索 workload 集合、descriptor、100,000 / 4 の既存経路破壊を殺す。

- 改訂 `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
  - 実 repo の C01 遷移が plan と異なる場合に検出する。

- 既存 `...::test_noop_and_token_only_fixtures_never_satisfy[nc_c01_perf_scale_regression-C01]`
  - `_evaluate_c01` の scale 条件緩和、perf sink の正式 literal 消失を殺す。

- 既存 `orchestrator/tests/test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
  - 正式三軸 literal の source 混入、0 hit snapshot 破壊、陽性対照消失を殺す。

正式 fixture の比率文字列は既存テストと同様に `"8" + "0"` / `"2" + "0"` で構築し、source 上へ完全な三軸 literal を置かない。

## 4. repo scan invariant を壊さない根拠

scan は `s8b_holdout_freeze.py:507-515` のとおり file ごとに三軸を照合し、同じ file で `rratio ∧ zipf_skew ∧ rmw` が成立した場合だけ conjunction hit にする。

- producer
  - 既存 `WORKLOADS` には `zipf_skew=0.9`、`rmw=0` と探索 rratio 50/95/100 がある。
  - 追加するのは workload label `rr80` / `rr20`、profile 名、正式 scale、動的な `formal_holdout["ycsb"]` 参照だけ。
  - `"ycsb_rratio": "80"`、`"ycsb_rratio": "20"`、`ycsb_rratio=80`、`ycsb_rratio=20` は入れない。
  - よって rr80/rr20 の `rratio` 軸が不成立で、既存 skew/rmw と conjunction しない。
  - rr50 の既存陽性対照は `WORKLOADS` を維持するため消えない。

- producer test
  - skew/rmw の fixture があっても、rratio 値は文字列連結または ratified fixture helper 経由にする。
  - source bytes 上に三軸の完全表記を同居させないため、per-axis count と conjunction hit を増やさない。

- C01 snapshot test
  - 追加・変更するのは status/reason と nodeid だけで、三軸 literal は入らない。

`trial_registry.py:52-53` には既に正式 rratio があるが skew/rmw がない。scan は別 file の軸を合成しないため、producer の skew/rmw と conjunction しない。`s8b_holdout_freeze.py` と freeze 成果物は無変更である。

## 5. C01 の予測と最小実走

予測は次の遷移である。

`UNSATISFIED / workload-projection-mismatch`
→ `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`

理由は、三つの sink の scale 条件、`main` から `run_trial` と sink への到達、ratified loader call、reachable な `.holdouts` / `.sha256` がすべて通ると、`_evaluate_c01:1441-1445` の終端がこの tuple を返すためである。`SATISFIED` にはならず、zero-satisfied 契約も維持される。

最小手順は次のとおり。

1. producer 変更だけを含む一時 commit を作る。`current_commit_snapshot` は worktree ではなく HEAD の blob を読むため、未 commit 差分では測れない。
2. `:151` を旧期待値のまま、runner 経由で次を実行し、意図的な差分から実測 tuple を得る。

```bash
python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review
```

3. 実測が予測どおりなら `:151` のみ更新し、同 nodeid を再実行する。
4. 緩和がないことを次の nodeid で確認する。

```bash
python3 tools/run_tests.py 'orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c01_perf_scale_regression-C01]'
python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates
```

ここでは実走しておらず、緑は主張しない。

## 6. 既存 consumer への波及

探索側の呼び出し列は次のまま維持する。

`main`
→ `workload_profile="exploratory"`、`workloads=list(WORKLOADS)`
→ `_trial_launch_admission(..., formal_profile=None)`
→ `run_trial(..., formal_profile=None)`
→ `_finish_trial`
→ `for workload in selected`
→ `_run_workload`
→ `WORKLOADS[workload]`
→ `_prepare_campaign_identity`
→ `_descriptor_for` / `_campaign_for`
→ `_perf_for`

この経路では全 optional formal 引数が `None` なので、以下が現状どおりになる。

- workload: `ycsb-a`, `ycsb-b`, `ycsb-c`
- records: `100_000`
- threads: `4`
- `pilot_scope`: `exploratory-ycsb-abc`
- ratified loader: 非呼出し
- 既存 campaign identity preimage: 不変

正式側だけが次の枝へ入る。

`main` または programmatic `run_trial`
→ `_load_formal_workload_profile`
→ `load_ratified_freeze(ROOT)`
→ `_FormalWorkloadProfile.holdouts / .sha256`
→ admission campaign ID 再導出
→ workload 反復
→ 同一 ratified entry を campaign / perf / descriptor へ渡す。

既存の `_descriptor_for(flags)`、`_perf_for(flags)`、`_prepare_campaign_identity(...)` の直接 caller は optional 引数省略で探索 semantics を維持する。探索側 records / threads の引上げ、formal claim の自動成立、report の certified 扱いは行わない。

## 総括

変更対象は producer、producer テスト、実測後の C01 snapshot の三面に限定する。正式 rr80/rr20 は ratified freeze から動的に取得し、三つの sink 各々で 1,000,000 records / 48 threads を fail-closed 照合する。探索 ycsb-a/b/c @ 100,000 / 4 は既定・identity・loader 非依存を含めて維持する。`s8b_holdout_freeze.py`、ratified loader、凍結成果物、C01 判定式は編集せず、source hash pin の再同期や再凍結も不要である。