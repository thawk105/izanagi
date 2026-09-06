## 実装した内容

- [tools/pegasus/p3_s4_loop_pegasus.sh:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/p3_s4_loop_pegasus.sh:1) を新設し、mode `755` に設定した。
  - `:1-164`: PBS envelope、必須 env、PATH sanitize 前の compute-only gate、環境 sanitize、repo 外 evidence gate、create-only compute result、Python 3.10 resolver と単独 shim。手本は [paper_story_a2_certification.sh:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/paper_story_a2_certification.sh:1) と [ss2pl_lock_study.sh:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/ss2pl_lock_study.sh:90)。
  - `:166-315`: expected HEAD、superproject clean、`p3_s4_loop.PIN` exact gate、A-2 型 reservation block、`output/env/pegasus/claims` provisioning。手本は `paper_story_a2_certification.sh:123-275`。
  - `:317-435`: hydrate source 3本の tracked-clean 確認と scratch 複製、fresh `config.h` gate、Masstree prebuild、canonical create-only receipt、2経路の driver argv。
- [test_p3_s4_loop_job_contract.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_p3_s4_loop_job_contract.py:1) を新設した。
  - `:21-303`: heredoc 除去、token 化した submitter 検査、静的 fragment・禁止構成検査。
  - `:306-703`: M1〜M16、shim 8種、CMake env 注入、旧 `python3` resolver、login sentinel、stdin `bash -n`、登録簿、README、mode の契約。
  - `:706-712`: `_run()` と `__main__`。手本は `test_paper_story_a2_job_contract.py:39-339` と `test_paper_story_a1_job_contract.py:1105-1203`。
- [admission_registry.json:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/tools/pegasus/admission_registry.json:106) に裁定どおりの `dispatch-required` entry を挿入した。
- [test_hooks.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_hooks.py:2590) と [test_hooks.py:2745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2232-s4-loop-pegasus-job-script/orchestrator/tests/test_hooks.py:2745) に class と4-field golden を各1件挿入した。
- 指定外ファイル、docs、`output/`、`external/` は編集していない。commit・add・stash も実施していない。

## 変異 M1〜M16 の対応表

| 変異 | 殺すテスト | 赤理由と一意性 |
|---|---|---|
| M1 | `test_login_host_refuses_before_sanitize_or_sentinels` | compute-only 文言が消える。hostname marker は有、sentinel は無なので理由を特定できる。 |
| M2 | `test_registered_fragment_mutants_have_one_static_failure[expected-head]` | `job contract missing: expected-head` の1理由。 |
| M3 | 同 `[clean-tree]` | `job contract missing: clean-tree` の1理由。 |
| M4 | 同 `[campaign-pin-import]` | `job contract missing: campaign-pin-import` の1理由。 |
| M5 | `test_pbs_jobid_path_sanitization_is_load_bearing` | `${PBS_JOBID//:/_}` の欠落で停止し、期待写像も `0_945411.nqsv` に固定。 |
| M6 | `test_registered_fragment_mutants_have_one_static_failure[evidence-outside-repo]` | repo/common-root を含む一体の fragment が欠けた1理由。 |
| M7 | `test_interpreter_resolver_hides_an_old_bare_python3` | shim/bare-PATH 変異で旧 `python3` marker と `OLD-PYTHON3` が現れる1理由。 |
| M8 | `test_forbidden_build_tool_shim_mutants_are_rejected[cmake]` | `forbidden-shim-entry` の1理由。8種すべて同じ層で検査。 |
| M9 | `test_registered_fragment_mutants_have_one_static_failure[prebuild-scratch-copy]` | `job contract missing: prebuild-scratch-copy` の1理由。 |
| M10 | 同 `[receipt-create-only]` | `"x"` から `"w"` への変異を `receipt-create-only` の1理由で検出。 |
| M11 | `test_no_build_mutant_has_one_negative_failure` | 置換は `build-authority` 欠落、追加は `forbidden-no-build` と変異形ごとに単一理由。 |
| M12 | `test_job_body_has_no_submitter_invocation` | token 化検査の `qsub-invocation` だけで検出。4種の負例も個別確認済み。 |
| M13 | `test_job_body_is_registered_only_as_dispatch_required` | exact dict 不一致。ただし既存 `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` も反応するため、裁定どおり冗長で一意ではない。 |
| M14 | `test_static_contract_orders_all_job_stages` | 順序不一致。login harness の hostname marker も反応するため、C10/C12由来で一意ではない。 |
| M15 | `test_registered_fragment_mutants_have_one_static_failure[reservation]` | `job contract missing: reservation` の1理由。 |
| M16 | 同 `[claim-root]` | `job contract missing: claim-root` の1理由。 |

## 実走結果

実行:

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_s4_loop_job_contract.py -q
```

結果は `39 passed, 1 failed`。緑の範囲は次の nodeid 群。

- `test_job_body_static_contract` から `test_job_body_has_no_submitter_invocation`
- `test_submitter_guard_accepts_qstat_and_comment_mentions`
- `test_submitter_guard_detects_four_invocation_forms` 全4 case
- `test_interpreter_resolver_hides_an_old_bare_python3`
- `test_pbs_jobid_path_sanitization_is_load_bearing`
- `test_login_host_refuses_before_sanitize_or_sentinels`
- `test_claim_root_uses_the_campaign_pegasus_env_tag`
- `test_job_body_is_registered_only_as_dispatch_required`
- `test_job_body_mode_is_executable`
- `test_job_body_has_valid_stdin_shell_syntax`
- parameterized 範囲: fragment 8、shim 8、CMake env 6 case

唯一の赤は `test_readme_tagged_qsub_fence_routes_both_streams_to_evidence`。親所有の `tools/pegasus/README.md` に段4裁定の fence がまだ投影されていないためで、テストは緩めていない。

`git diff --check`、4ファイルの trailing-whitespace 検査、registry JSON parse は緑。`run_tests.py`、`check_docs.py`、compute 実走は本段では実施していない。

## 所有外への波及

grep で確認した未編集 consumer は以下。

- `orchestrator/campaign/p3_s4_loop.py:110-119,2087-2372`: PIN、Pegasus env tag、job body が起動する CLI。
- `orchestrator/campaign/buildcache.py:1270-1285,1838-1843,2009-2085`: toolchain 観測と Masstree prebuild。
- `orchestrator/campaign/loop.py:198-229`、`reservation.py:120-175`: reservation 8変数と claim root の実消費。
- `tools/pegasus_admission_registry.py:120-136`、`hooks/guard_bash.py:237-319`: registry loader と login admission。
- `tools/check_codex_hooks.py:33-46`、`test_codex_hooks.py:32-38,722-768`、`test_codex_worker_launch.py:2315-2325,3720-3729`: registry の HEAD blob 束縛。統合 commit 前は review 起動を拒否し得る。
- `tools/check_docs.py:4100-4149,4404-4438,4541-4587,4754-4802` と `test_check_docs.py:1577-1696`: runbook・README 投影の consumer。親の docs 更新までは赤になる。
- `test_plain_runner_coverage.py:44-86`: 新規 `test_*.py` の集合列挙。新規 file は `_run()`/`__main__` を持つため契約を満たす。
- `test_paper_story_a1_job_contract.py:1792`、`test_paper_story_a2_job_contract.py:340`、`test_a5_second_boot_job_contract.py:353`、`test_acceptance_nproc_study.py:2741`: 共有 registry の既存 consumer。

## 総括

裁定 plan v2 の1〜4を指定4ファイルだけに実装し、job body は mode 755 である。
自走 contract は実装面39件が緑で、親所有 README 投影の1件だけが意図どおり赤のまま残る。
M13とM14は裁定上の冗長検査により赤理由を単一化できない。
親は docs 投影後に焦点走・全走・hook/docs 検査を行い、統合 commit 後の段6で再確認する必要がある。