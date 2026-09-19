# 段 1 実測の所在と profile 要約 (親が計算ノードで取得)

## 所在
- file 単独走 (`-n 12`、bnode130、request 10737): `/home/SFC/tanab/.claude/jobs/28fa456a/tmp/stage1c/durations-<file>.log` (`--durations=0 --durations-min=0.2` の setup/call/teardown 別一覧) と `junit-<file>.xml`。集計は `python3 /home/SFC/tanab/.claude/jobs/28fa456a/tmp/agg_durations.py /home/SFC/tanab/.claude/jobs/28fa456a/tmp/stage1c`
- 代表 node の cProfile 単独走 (xdist 無し、bnode020、request 10741): `/home/SFC/tanab/.claude/jobs/28fa456a/tmp/stage1p/<name>.prof` と `<name>.log`。上位表示は `python3 /home/SFC/tanab/.claude/jobs/28fa456a/tmp/prof_top.py <prof> 40`
- git command の素の所要 (bnode020、負荷なし、wave worktree = Lustre): `/home/SFC/tanab/.claude/jobs/28fa456a/tmp/stage1p/git_probe.log`

## git probe (単独、秒)
- `git status --porcelain=v1 -z --untracked-files=all` 4.96 / `git diff --binary --no-ext-diff HEAD --` 2.41 / `submodule status --recursive` 0.15 / `submodule foreach status` 0.43 / `submodule foreach diff` 0.13 → `_tree_and_submodules_fingerprint` 1 回 ≈ 8.1 s (preflight の 8〜12 s/node と一致)
- `git ls-files -s -- output` 0.01 / `git status --porcelain -- output` 3.44 (→ `_real_output_snapshot` の `_status_paths_for_output` 分)
- `git archive HEAD | tar -x` 3.89 (ScratchTree 1 本、856 MB / 28,158 file、うち output/ 733 MB / 25,185 file)

## cProfile 要約
### floor_measure = test_s8b_floor_campaign.py::test_measure_runtime_error_records_launch_failure (5.8 s 級の代表、約 90 node)
- 9.9 s (profile 下) のうち 9.1 s が production `s8b_floor_campaign._run_session` → `measure_attempt` → `s8b_holdout_admission.consume_attempt_ticket` :4349 → `_recover_floor_attempt_ledger_locked` :5314 → `_floor_attempt_recovery_candidate_locked` :5230。98 attempt × 98 row = 9,604 回の `_canonical_floor_attempt_ledger_row` (:4670) で `_read_ledger` 9,707 回、json dumps/loads 各 16 万回。
- **fixture 費用ではなく production の attempt ledger 回復が attempt 数に対し二乗**。fsync 663 回 = 0.06 s、subprocess 18 回 = 0.03 s で無視できる。本 wave の 4 型では消えない = 残る律速 (裁定パッケージ候補: production 側の改善は別 wave)。

### floor_snapshot = test_s8b_floor_campaign.py::test_official_fresh_issues_certificate_and_binds_wall_ledger (55〜65 s 級の代表、10 test)
- 39.1 s (profile 下) のうち 29.5 s が `_real_output_snapshot` 2 回 (`git_indexed_output_snapshot` :564)。内訳: `_digest` (test_s8b_floor_campaign.py:1773) 25,185 回 = 15.6 s (**process 内 `_INDEX_BLOB_SHA256_CACHE` が空の初回に全 file を sha256**、2 回目は cache hit)、`_status_paths_for_output` :515 2 回 = 7.1 s (`git status -- output`)、`git_ignored_output_snapshot_rules` :320 2 回 = 2.8 s、`_walk_entries` :1752 2 回 = 3.2 s。
- 残り 9.6 s は `_run_campaign` (上の floor_measure と同じ production の attempt ledger 回復)。
- 修正型の当てはめ: before を module scope で 1 回 (型 i)、rules/index/walk の同一入力を worker 内で 1 回 (型 ii)、digest cache を session 共有 (型 iv、blob sha → sha256 は純関数)。

### floor_public_preflight = test_s8b_floor_campaign.py::test_public_official_preflight_accepts_versioned_protocol (30 s 級、5 test)
- 39.3 s のうち `_protocol_binding_public_preflight` (:15733) が実 repo を `git clone --no-hardlinks` (本体 + ccbench) して tmp に real repo を作り、production `clean_scan_digest` → `s8b_holdout_freeze.search_repository` (:592) を 4 回 (2 preflight × 独立 2 scan) = 26.8 s、うち file 読取 `_read_search_text` 114,188 回 = 3.3 s、`_scan_one` 12 回 = 15.1 s (python)、subprocess 122 回 = 11.7 s。
- clone (実 repo 読取 + 複製) は型 (iv) の候補だが、各 test は clone を commit/checkout で変えるので copy が要り、copy ≈ clone。scan 自体は production の意味。→ 局所修正の余地は小さい (plan で判定)。

### rv_source_blob = test_s8b_ratified_verify.py::test_source_blob_mismatch_rejected (8〜15 s 級、101 node)
- 22.6 s のうち 21.8 s が `s8b_v2_freeze_fixture.in_sealed_fixture_process` (:92) の **fork 子** で走り、profile には映らない (親は waitpid)。**test_s8b_ratified_verify.py の 82 test と test_s8b_ratified_freeze.py の 11 test は fork 子で本体を走らせる** (seal issuance record が PID 束縛で、xdist worker へ持ち帰らないため)。
- 帰結: builder の memo を process 内 dict に置いても fork 子の終了で消える。memo は disk (session 共有 dir + flock、`_T080SharedBases` 同型) に置く必要がある。さらに、copy した repo が「issuance record を持たない process」で後続 (G/A/X commit、`load_ratified_freeze`、`launch_validate`) を通せるかを plan で確認すること。
- builder 内訳 (fork 子のため未計測)。段 1 では git subprocess (`_fixed_git`) 回数と `_run_official_fixture_campaign` の割合が未分離。author は memo 実装時に build 2 回の bytes 同一性を自分で検査すること。

### preflight_local = test_run_tests_preflight.py::test_local_child_test_failure_never_falls_back (8〜12 s 級、19 node)
- 7.4 s / 7.4 s が `tools/run_tests.py:2201 _tree_and_submodules_fingerprint` (subprocess 5 回)。100%。

### codex_verify = test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment (42 s 級)
- 47.3 s のうち 46.2 s が production `TOOL.verify_manifest` (tools/codex_reasoning_ab.py:11646) → `_replay_manifest` → `verify_snapshot` 22 回 → `_git_closure_reasons` (thread 並列、待ち 36 s)。**verify は test の主題** = 短縮対象でない。
- module fixture `benchmark_snapshots` (:860) = 10.3 s / worker: `_build_snapshot_base` :3292 3.4 s (実 repo の pack-objects + checkout + submodule)、`_derive_snapshot_from_base` 2 回 5.8 s、他。file 単独走 (`-n 12`) では setup 合計 135 s = 13 worker × 10〜11 s。→ 型 (iv) session 共有 base + worker copy の候補。
- subprocess 1,905 回 = 6.4 s、`_sha256` 20,266 回 = 1.6 s。

### p3b4_guard_once = test_p3_b4_producer_auth_experiment.py::test_prototype_calls_each_guard_once_from_the_fixed_real_callsite (20 s 級、3 test)
- 10.2 s のうち production `ScratchTree.__enter__` (orchestrator/campaign/p3_b4_producer_auth_experiment.py:1884) 3 回 = 8.8 s (`git archive HEAD | tar -x` 856 MB) と `shutil.rmtree` 4 回 = 2.8 s (150K unlink)。test 本体は 0.1 s 未満。→ 3 test × 3 tree は module scope の候補別 tree (型 i) の候補。wave mutant 8 node と `run_isolated_cases` (13 tree) は production の意味 = 残る律速。

### t1259_r2 = test_t1259_qsub_env_delivery_probe.py::test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal
- 4.9 s のうち module fixture `_clean_detached_source_snapshot_template` (:73) = `probe._repo_snapshot(REPO_ROOT)` (git 3 回) 4.0 s / worker、test 本体 (`observe` + 実 driver subprocess) 0.43 s。既に module scope。台帳の 10〜23 s/node は受入 48 worker 下でだけ出る (real-repo group の単一 worker 直列と飽和) → 局所修正候補なし。

## 段 1 の結論 (費用の種別)
| file | 種別 | 局所修正の当てはめ |
|---|---|---|
| ratified_verify | 同一入力の再構築 (git repo builder、fork 子内) | (ii)+(iv): disk memo + copy (fork 子で消えない置き場) |
| floor_campaign | 実 repo 走査 (`_real_output_snapshot` ×2/test、digest cache 初回 15 s) + production 二乗 ledger 回復 (5.8 s × 90、対象外) + 実 repo clone + production scan (30 s × 5、対象外寄り) | (i) before 1 回化、(ii) rules/index/walk の 1 回化、(iv) digest cache の session 共有 |
| preflight | 実 repo 走査 (`_tree_and_submodules_fingerprint` 100%) | (i)/(iv): 19 node の `_REPO` を小 repo へ or 1 回化 (DW-O14 適合案を plan で 1 つに) |
| codex_ab | 実 repo 走査 × worker 数 (module fixture 10 s) + production verify (対象外) | (iv) session 共有 base + copy |
| p3_b4 | fixture の複製 (production ScratchTree 856 MB × 30+) + python subprocess (run_tests) | (i) 3 test の候補別 tree のみ。他は残る律速 |
| t1259 | 既に module scope。受入下の値は環境効果 | なし |
