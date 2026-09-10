## 実装した内容

実装済みです。pytest は dispatch 障害により未実走のため、状態は「実装済み・未実走」です。

- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:327)
  - source を `<base>/<name>-src` へ配置。
  - `fetchcontent_base_dir=$prebuild_source_root` に統一。
  - proposal/fixture 両分岐へ receipt option を追加。

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:172)
  - non-symlink regular file を inode 固定で読む receipt loader を追加。
  - 10 field exact schema、canonical path、3 source、config hash、toolchain、型を検査。
  - exact 5 値を fixture/proposal 両経路へ配線。
  - `--no-build` / `--emit-planner-context` 併用を rc=2 で拒否。

- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:240)
  - keyword-only 5 引数を追加。
  - authorization/layout/WAL/source 解決前に all-or-nothing と `env_contract` 必須を検査。
  - 指定時だけ `evaluate_options` へ追加。

- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:883)
  - `evaluate` / `_prepare_evaluation_core` に同じ 5 値 gate を追加。
  - 指定時だけ production `buildcache.build_v2` の `common` へ追加。

- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop.py:7690)
  - reader、CLI、共有鎖、既定互換、R1、production argv probe を追加。

- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:252)
  - copy destination/base equality と両 driver 分岐の連続 fragment を追加。

`buildcache.py`、docs、registry、qsub `-v`、required env は変更していません。`git add` / `git commit` / `git merge` も実行していません。

## 段 4 裁定との対応表

| 裁定 | 対応 |
|---|---|
| プラン1 / C1 | job の base と `*-src` 配置を一致 |
| プラン2 / C3・C4 | exact-schema receipt loader、symlink拒否、config再hash |
| プラン2 / C5・C9 | fixture/proposal 両方の production `build_v2` / `_v2_commands` probe |
| プラン2 / C8 | 両 driver 起動 fragment を連続 pin |
| プラン3 / C2・C6 | `run_campaign` 冒頭 gate、指定時のみ forwarding |
| プラン4 / C6 | pipeline 冒頭 gate、指定時のみ `common` 追加 |
| プラン5 | `buildcache.py` 無変更 |
| プラン6 / C4〜C9 | 正負例、既定互換、R1 pin、mutation test |
| C7 | copy destination/base 復帰変異を契約テストへ追加 |
| C10 | 親担当のため docs は未変更 |

## 新設した test と変異対応

- M1: `test_registered_fragment_mutants_have_one_static_failure[prebuild-copy-destination]`
- M2: 同 `[prebuild-base-equality]`
- M3: 同 `[proposal]`
- M4: 同 `[fixture]`
- M5: `test_prebuild_receipt_loader_rejects_config_hash_mismatch`
- M6: `test_prebuild_receipt_loader_rejects_nonexact_top_level_keys[extra]`
- M7: `test_prebuild_receipt_loader_rejects_symlink_receipt_file`
- M8・M11・M12: `test_prebuild_reaches_production_build_v2_and_v2_commands_in_both_main_routes[fixture|proposal]`
- M9: `test_prebuild_receipt_cli_rejects_routes_without_a_build[no-build]`
- M10: `test_run_campaign_rejects_invalid_prebuild_tuple_before_side_effects[...]`
- M13: `test_pipeline_rejects_invalid_prebuild_tuple_before_build_or_wal[...]`
- M14: `test_default_prebuild_values_do_not_enter_loop_evaluate_options` と `test_default_prebuild_values_do_not_enter_pipeline_build_v2_kwargs`

追加の C4 負例は source 名の重複・欠落、noncanonical/source symlink/config symlink、field 型不正を覆います。R1 は `test_terminal_variant_still_skips_prebuild_transport_without_build` で固定しました。

M5/M6/M7 の検査除去では `Failed: DID NOT RAISE ValueError`、M8〜M14 では downstream side-effect 到達または exact kwarg/define 欠落で赤化しました。確認後、全変異を復元済みです。

## 現行挙動を変えた箇所・変えていない箇所

変更した受理集合:

- valid receipt CLI を受理。
- full 5 値を共有 API で受理。
- receipt 指定時は OTHER site でも v2 build へ到達。
- 部分 tuple は `TypeError` や WAL abort へ進まず、入口 `ValueError`。
- receipt symlink、不整合 schema/path/hash/type を拒否。
- receipt と非 build CLI の併用を rc=2 で拒否。

変更していない挙動:

- receipt 未指定 caller の kwargs、configure argv、cache identity。
- `dependency_prefix` の Pegasus site 条件。
- correctness gate、quarantine、condition gate の述語と順序。
- terminal variant の duplicate skip（R1）。
- `pbs_jobid` は非空 schema 検査のみで job 束縛なし（R2）。
- FetchContent 内容の完全な build identity 束縛なし（R3）。
- unknown site、admission registry、qsub 環境契約。

揮発する `pbs_jobid` と configure/build argv の3 fieldを変更しても、loader の exact 5 値期待が変わらないことも直接確認しました。

## 波及可能性の静的列挙

共有 `campaign.loop.run_campaign` は16 file・20 callです:

- `b10_backoff_shape_sweep`、`backoff_extended_sweep`、`backoff_repro`、`backoff_sweep`
- `demo`×2、`p2_2`、`p3_kickoff`×2、`p3_s4_loop`
- `p3_s4_loop_sort`、`p3_s4_loop_trigger_gating`、`p3_s4_red`×2
- `paper_story_a1_paired`×2、`paper_story_a2_certification`
- `s6_sort_sweep`、`s8a_trigger_sweep`、`sanity_silo`

`pipeline.evaluate` は5 callです:

- `loop`
- `screening_driver`
- `s1_direct_comparison`
- `s8b_oracle_driver`
- `qualification/t126_driver`

`build_v2` は5 file・6 call siteです:

- `pipeline`×2
- `backoff_requested_us`
- `backoff_overthrottle`
- `b10_backoff_shape_sweep`
- `backoff_extended_sweep`

波及候補の consumer/meta test は `test_campaign.py` の certified-writer caller inventory と balanced build wrapper、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py`、`test_buildcache_v2.py`、各 direct pipeline caller testです。caller inventory exact 検査、registry exact 検査、test 名一意性、追加 test が既存 module 同様 xdist unmarked であることは直接検査済みです。

## 実走した範囲・できなかった範囲

実走できたもの:

- 新規22 parametrized case、契約 mutation 4 case、job static/stage/shell syntaxを module import後に直接呼出し: すべて `DIRECT_CALL_PASS`
- production fixture/proposal probe: `build_v2` exact 5 kwargsと4つの configure defineを捕捉
- mutation M1〜M14: 全て期待どおり赤化
- caller inventory、registry exact、test 名一意性、xdist静的検査: `DIRECT_CALL_PASS`
- 既存 compute/default compatibility test: `DIRECT_CALL_PASS`
- `py_compile`
- `git diff --check`

pytest は未実走です。

- `tools/run_tests.py ... -k prebuild -q` → rc=16
- `tools/run_tests.py --collect-only ...` → rc=16
- 両方とも `qstat -Q preflight rc=1`、`child_started=false`
- queue 状態も ENA/STS 不明で、test child は1件も開始されていません

したがって pytest 緑とは報告せず、「実装済み・未実走」です。

## 総括

段4裁定のプラン1〜6、C1〜C9を実装し、R1〜R3・F1〜F2には手を入れていません。変更は許可された6 fileだけで、docs/C10とcommitは親に残しています。作業ツリーには復元済みの最終差分のみがあり、pytest dispatch が復旧するまでは closed 扱いにできません。