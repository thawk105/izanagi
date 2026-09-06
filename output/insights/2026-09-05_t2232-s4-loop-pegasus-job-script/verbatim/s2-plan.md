## プラン

- `tools/pegasus/p3_s4_loop_pegasus.sh:1-12` を新設する。
  - `#!/bin/bash`
  - `#PBS -A SFC`
  - `#PBS -q gen_S`
  - `#PBS -b 1`
  - `#PBS -l elapstim_req=03:00:00`
  - `#PBS -N izs4loop`
  - 「親が raw `qsub` する compute-only job body であり、投入器ではない」と明記する。形は `paper_story_a1_paired.sh:7-10`。
  - `set -Eeuo pipefail`、`umask 077`。

- `p3_s4_loop_pegasus.sh:14-39` に `refuse()`、必須環境検査、compute-only gate を置く。
  - 必須集合は `PBS_JOBID`、`PBS_NODEFILE`、`PBS_O_WORKDIR`、`IZANAGI_S4_REPO_ROOT`、`IZANAGI_S4_EXPECTED_HEAD`、`IZANAGI_S4_EVIDENCE_ROOT`、`IZANAGI_S4_THIRDPARTY_SOURCE_ROOT`。
  - `IZANAGI_S4_PROPOSAL_PATH` と `IZANAGI_S4_FIXTURE_VALUE` は任意。
  - 欠落時は `p3 S4 loop job refused: missing required environment: <name>`、rc=2。
  - `hostname` が `^bnode[0-9]+([.].*)?$` に一致しなければ `P3 S4 loop job body is compute-only`、rc=2。これは root 解決、trap、scratch、receipt より前に置く。

- `p3_s4_loop_pegasus.sh:41-66` で環境を sanitize する。
  - `ss2pl_lock_study.sh:90-102` の unset 群を写し、`IZANAGI_OFFICIAL_OUTPUT_ROOT` と、buildcache が環境から読む `IZANAGI_B10_BINARY_PATH_POLICY` も unset する。
  - proxy は `a5_second_boot_backoff_sweep.sh:32,219-222` と同じ literal を lowercase 2 変数へ export する。
  - bootstrap PATH は `/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin`。

- `p3_s4_loop_pegasus.sh:68-108` で path と durable output を確定する。
  - `repo=$(cd "$IZANAGI_S4_REPO_ROOT" && pwd -P)`、`evidence_root=$(cd ... && pwd -P)`、`thirdparty_root=$(cd ... && pwd -P)`。
  - `git rev-parse --path-format=absolute --git-common-dir` と `${git_common_dir%/.git}` を使い、`evidence_root` が `repo` または git-common repository root と同一・配下なら `p3 S4 loop job refused: evidence root resolves inside a repository`、rc=2。形は `b10_backoff_shape_campaign.sh:33-45`。
  - `result=$evidence_root/compute-result.json` が既存または symlink なら rc=2。
  - `pbs_jobid_path_component=${PBS_JOBID//:/_}`。
  - `finish()` は `.compute-result.${pbs_jobid_path_component}.tmp` を書き、`ln "$tmp" "$result"` で create-only publish する。schema は `p3-s4-loop-compute-result/v1`、field は `schema_version`、`driver_rc`、`pbs_jobid`。形は A-2 の `paper_story_a2_certification.sh:46-67`。

- `p3_s4_loop_pegasus.sh:110-151` に `resolve_python()` と interpreter-only shim を置く。
  - 候補は `python3.10 /usr/bin/python3.10 /bin/python3.10`。
  - Python 3.10 exact と `orchestrator.campaign.p3_s4_loop` の import を確認し、`sys.executable` の realpath を `PY` にする。失敗文言は `Python 3.10 capable of importing the P3 S4 loop is required`、rc=2。
  - `scratch_base=/scr/$USER/p3-s4-loop-pegasus`、`scratch=$scratch_base/${pbs_jobid_path_component}`。base のみ `mkdir -p`、job leaf は `mkdir` 一発で create-only。既存なら `scratch root is not fresh`、rc=2。
  - `TMPDIR=$scratch`、`shim_dir=$scratch/python-shim`、`ln -s "$PY" "$shim_dir/python3"` の 1 本だけを作る。
  - final PATH は `$shim_dir:/usr/bin:/bin` に、実在する `/opt/nec/nqsv/bin`、`/system/tool/bin` だけを後置する。`ss2pl_lock_study.sh:105-141` の形であり、shim directory に `cmake`、`cc`、`c++`、`gcc`、`g++`、`make` は置かない。

- `p3_s4_loop_pegasus.sh:153-196` に repository と pin の gate を置く。
  - `IZANAGI_S4_EXPECTED_HEAD` は 40 桁 lowercase hex、`git rev-parse HEAD` と exact 一致。
  - superproject は `git status --porcelain --untracked-files=no --ignore-submodules=all` が空であることを要求する。
  - `ccbench_dir=$repo/external/ccbench`。
  - `"$PY" -B -c 'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)'` で campaign pin を取得し、`HEAD^{commit}`、`${campaign_pin}^{commit}`、full SHA equality、literal prefix、CCBench tracked clean を A-2 `paper_story_a2_certification.sh:230-275` と同型で確認する。
  - submodule 除外は必要である。現 HEAD の gitlink は `511c953…` だが、loop の frozen pin は `028f34d` (`p3_s4_loop.py:110`, `pin.py:28,33`) であり、CCBench を後者へ置くと通常の superproject `git status` は dirty になるためである。

- `p3_s4_loop_pegasus.sh:198-263` で masstree を事前構築し、receipt を create-only で保存する。
  - `fetchcontent_base_dir=$scratch/fetchcontent-base` を `mkdir` で新規作成する。
  - `prebuild_receipt=$evidence_root/masstree-prebuild-receipt.json` は事前に非存在を確認する。
  - inline Python から次を exact に呼ぶ。

```python
expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
    *buildcache.compilers_for_current_site()
)
prepared = buildcache.prepare_masstree_fetchcontent(
    ccbench_dir=ccbench_dir,
    fetchcontent_base_dir=fetchcontent_base_dir,
    expected_toolchain_manifest=expected_toolchain_manifest,
    configure_timeout_s=900,
    target_timeout_s=900,
    masstree_source_dir=os.path.join(thirdparty_root, "masstree"),
    mimalloc_source_dir=os.path.join(thirdparty_root, "mimalloc"),
    googletest_source_dir=os.path.join(thirdparty_root, "googletest"),
)
```

  - 3 directory 同時指定と canonical directory 検査は `buildcache.py:823-878,2035-2051` が持つ。
  - `config_h_path=$thirdparty_root/masstree/config.h` が non-symlink regular file であることを確認し SHA-256 を計算する。
  - `open(receipt, "x")`、canonical JSON、flush、`os.fsync()`。field は `schema_version="p3-s4-loop-masstree-prebuild/v1"`、`fetchcontent_base_dir`、`config_h_path`、`config_h_sha256`、`configure_argv`、`build_argv`。
  - job result と prebuild receipt のどちらにも overwrite 経路を作らない。

- `p3_s4_loop_pegasus.sh:265-278` で loop を起動する。`PYTHONDONTWRITEBYTECODE=1` を export し、後述の argv だけを使う。`p3_s4_loop.py`、`buildcache.py`、policy、oracle、proof artifact は編集しない。

- `orchestrator/tests/test_p3_s4_loop_job_contract.py:1-270` を新設する。
  - `:1-22` imports と `REPO`、`JOB`、`REGISTRY`、`README`。
  - `:24-126` `_assert_static_job_contract()`。
  - `:128-175` static contract と不正 job source を投入する load-bearing mutant tests。
  - `:177-215` resolver harness。
  - `:217-245` login-host refusal harness と PBS job ID mapping。
  - `:247-265` registry exact entry、README fence、executable bit。
  - `:267-270` repository plain-runner 用 `_run()`。

- 既存ファイルは次の位置だけを変更する。
  - `tools/pegasus/admission_registry.json:106`、現 `paper_story_a1_paired.sh` entry の直前。
  - `orchestrator/tests/test_hooks.py:2590`、class golden の `paper_story_a1_paired.sh` の直前。
  - `orchestrator/tests/test_hooks.py:2744`、entry golden の `paper_story_a1_paired.sh` の直前。
  - `docs/pegasus-runbook.md:508`、投影表の `paper_story_a1_paired.sh` 行の直前。
  - `tools/pegasus/README.md:32`、宣言表の `smoke_probe.sh` 行の直前。
  - `tools/pegasus/README.md:300` 以降に新しい §7 を追記する。
  - `tools/pegasus_admission_registry.py` は変更不要。field 順序と class 閉集合は同 file `:20-21,101-116` が既に受理する。

## 起動 argv と環境

proposal 指定時の完全な argv は次である。

```bash
"$PY" -B -m orchestrator.campaign.p3_s4_loop \
  --allow-coder-derived-build \
  --isolate-worktree \
  --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"
```

proposal 無指定時は次である。

```bash
"$PY" -B -m orchestrator.campaign.p3_s4_loop \
  --allow-coder-derived-build \
  --isolate-worktree \
  --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"
```

`--isolate-worktree` は使用する。`p3_s4_loop.py:2131-2133,2222-2231` の既存 opt-in で、CCBench の変更を使い捨て worktree に閉じ、build cache のみ固定 base に残す。専用 detached superproject は campaign output の隔離、同 flag は CCBench の apply/build 隔離という別の責務である。`--no-build` と env-tag 引数は使わない。

export する全集合は以下である。

- `PATH`。bootstrap 値と、interpreter shim を先頭にした final 値。
- `TMPDIR=$scratch`
- `PYTHONDONTWRITEBYTECODE=1`
- `http_proxy=http://10.120.96.1:8080`
- `https_proxy=http://10.120.96.1:8080`

unset する全集合は以下である。

- `CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS`
- `LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH`
- `COMPILER_PATH GCC_EXEC_PREFIX`
- `CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE`
- `CMAKE_GENERATOR CMAKE_GENERATOR_INSTANCE CMAKE_GENERATOR_PLATFORM CMAKE_GENERATOR_TOOLSET`
- `CMAKE_PROJECT_INCLUDE CMAKE_PROJECT_INCLUDE_BEFORE CMAKE_PROJECT_TOP_LEVEL_INCLUDES`
- `CMAKE_C_COMPILER_LAUNCHER CMAKE_CXX_COMPILER_LAUNCHER`
- `PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS`
- `IZANAGI_OFFICIAL_OUTPUT_ROOT IZANAGI_B10_BINARY_PATH_POLICY`
- `GIT_* CCACHE_* SCCACHE_* DISTCC_* ICECC_*` は exported environment を列挙して unset。

proxy は必要である。`p3_s4_loop.py:171-190` の condition gate は configure args を渡さず、`p3_s4_loop.py:1525-1539` からの campaign build も FetchContent base/source dirs を渡さない。`pipeline.py:1237-1287` から `build_v2` へも同値は届かず、`buildcache.py:1940-1951` では未指定時に FetchContent define が空になる。CCBench は `external/ccbench/cmake/ThirdParty.cmake:35-55,106-136` で HTTPS Git repository を宣言しているため、loop 本体は clone 経路へ入る。

## config.h 事前構築の線引き

本 wave で行うのは、hydrate 出力の `.source_root` 配下にある `masstree`、`mimalloc`、`googletest` を explicit SOURCE_DIR として `prepare_masstree_fetchcontent` に渡し、scratch base 上で `masstree_build` を一度成功させるところまでである。`buildcache.py:2044-2085` が実効 configure/build argv を返し、CCBench の `ThirdParty.cmake:57-78` が masstree source root の `config.h` を生成物としている。

receipt は次を束縛する。

- scratch 内の canonical `fetchcontent_base_dir`
- hydrate 済み masstree 内の canonical `config_h_path`
- `config_h_sha256`
- `configure_argv`
- `build_argv`
- schema version

ただし、この成果を loop が消費する seam はない。condition gate は `capture_define_inputs(source_root)` を configure args 無しで呼び (`p3_s4_loop.py:171-190`)、campaign も dependency prefix 以外の FetchContent 情報を渡さない (`p3_s4_loop.py:1525-1539`)。したがって prebuild receipt は「事前構築がこの環境で成功した」証拠であり、後続 build の dependency binding でも offline 化でもない。`p3_s4_loop.py` への消費配線は本 waveでは提案・実装しない。

## 登録と投影

`tools/pegasus/admission_registry.json:106-111` に挿入する entry は逐語で次とする。

```json
"tools/pegasus/p3_s4_loop_pegasus.sh": {
  "class": "dispatch-required",
  "reason": "PBS P3 stage 4 loop build, verification, and benchmark job body",
  "primary_gate": "PBS allocation and job-body site preflight",
  "evidence": "static job-body classification"
},
```

`test_hooks.py` では以下を同期する。

- `:2590` に `"tools/pegasus/p3_s4_loop_pegasus.sh": "dispatch-required",`
- `:2744` に上記 4-field entry と同じ dict。
- `test_hooks.py:3446-3453` が registry 全 entry と両 literal golden の exact 一致を要求する。

`docs/pegasus-runbook.md:508` には次を挿入する。

```markdown
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `dispatch-required` | `static job-body classification` |
```

`tools/pegasus/README.md:32` には次を挿入する。

```markdown
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `qsub-job-body` | `dispatch-required` |
```

README の新節は current EOF `:298` の後へ置き、専用 detached checkout、CCBench の `p3_s4_loop.PIN`、hydrate JSON の `.source_root`、repo 外 evidence root、primary worktree 投入禁止を明記する。タグ付き fence の文面案は次である。

````markdown
## 7. P3 段 4 loop job body を投入する

`tools/pegasus/p3_s4_loop_pegasus.sh` は親が直接 `qsub` する job body であり、投入器ではない。
`REPO_ROOT` は固定 SHA の専用 detached checkout とし、main または primary worktree から投入しない。
`THIRDPARTY_SOURCE_ROOT` には `fetch_third_party.py hydrate` の出力 JSON の `.source_root` だけを使う。
同じ attempt directory は再利用しない。

```bash
# admission-site: qsub-job-body
REPO_ROOT=/absolute/path/to/dedicated-detached-checkout
EXPECTED_HEAD=0123456789abcdef0123456789abcdef01234567
THIRDPARTY_SOURCE_ROOT=/absolute/path/from-hydrate-source_root
EVIDENCE_ROOT=/absolute/path/outside-all-repositories
ATTEMPT=unique-attempt-id
mkdir -m 0700 "$EVIDENCE_ROOT/$ATTEMPT"
qsub -v IZANAGI_S4_REPO_ROOT="$REPO_ROOT",IZANAGI_S4_EXPECTED_HEAD="$EXPECTED_HEAD",IZANAGI_S4_EVIDENCE_ROOT="$EVIDENCE_ROOT/$ATTEMPT",IZANAGI_S4_THIRDPARTY_SOURCE_ROOT="$THIRDPARTY_SOURCE_ROOT" -o "$EVIDENCE_ROOT/$ATTEMPT/job.stdout" -e "$EVIDENCE_ROOT/$ATTEMPT/job.stderr" tools/pegasus/p3_s4_loop_pegasus.sh
```

実 proposal を渡す場合だけ `-v` の値へ
`IZANAGI_S4_PROPOSAL_PATH=/absolute/path/to/proposal.json` を追加する。
fixture 経路は `IZANAGI_S4_FIXTURE_VALUE` 無指定時に値 20 を使う。
````

`check_docs.py` の対応は次である。

- `:4100-4149` が canonical loader から registry を読む。
- `:4404-4438` が runbook §7.0 の `(path,class,evidence)` 集合完全一致を要求する。
- `:4541-4587` がその投影検査を一意な §7.0 表へ適用する。
- `:4754-4785` が README 宣言表の path、site、class を registry と照合する。
- `:4590-4679` がタグを fence 先頭に要求し、`qsub-job-body` path が同じ行の `qsub` 引数であることを要求する。
- `:4788-4802` が README 本文で言及した既知 path の宣言表掲載を要求する。
- `-o` と `-e` の存在自体は `check_docs.py` の保証外なので、新 contract test で固定する。

## テスト計画

- `test_job_body_static_contract`
  - PBS directive、必須 env、compute regex、expected HEAD、分離した clean/pin gate、resolver、shim、PATH、PBS ID 写像、repo 外 evidence、prebuild、receipt、proxy、build opt-in、isolate flagのいずれかが欠落したら赤になる。
  - `qsub`、`--no-build`、CMake/compiler wrapper、launcher assignment、`CMAKE_PREFIX_PATH=` が入っても赤になる。

- `test_static_contract_orders_gate_resolver_prebuild_and_driver`
  - compute-only gate、trap、resolver、scratch/shim、pin、prebuild、receipt、loop launch の順序が崩れたら赤になる。

- `test_forbidden_build_tool_shim_mutants_are_rejected`
  - job source の shim directory に `cmake`、`c++`、`gcc` の symlink または script 作成行を 1 本ずつ注入し、`_assert_static_job_contract` が拒否しなくなったら赤になる。これは contract helper 自体の弱体化変異も殺す。

- `test_external_evidence_and_build_opt_in_mutants_are_rejected`
  - repo 外比較を除去した source、`--allow-coder-derived-build` を除去した source、`--no-build` を加えた source が拒否されなければ赤になる。

- `test_interpreter_resolver_prepends_selected_path_for_child_processes`
  - tmp の `python3.10` を選択させ、production resolver と shim 部分を実行し、`PY`、`command -v python3`、子 process の `sys.executable` が同じ実体にならなければ赤になる。候補集合へ正しい版だけを入れて版数を再確認する恒真検査にはしない。

- `test_pbs_jobid_path_sanitization_is_load_bearing`
  - `0:945411.nqsv` が `0_945411.nqsv` にならない、または job source が生の `PBS_JOBID` を scratch path に使えば赤になる。

- `test_login_host_refuses_before_scratch_or_receipts`
  - `hostname` stub を `pegasus01` にし、`subprocess.run([str(JOB)])` で rc=2、compute-only 文言、scratch 非生成、`compute-result.json` 非生成、prebuild receipt 非生成の全てを見る。拒否位置が後退したら赤になる。

- `test_job_body_is_registered_only_as_dispatch_required`
  - registry の path または 4 field の 1 byte でも違えば赤になる。

- `test_readme_tagged_qsub_fence_routes_stdout_and_stderr_outside_repo`
  - 対象 path を含む fence が一意でない、先頭 tag が違う、対象が同一行の `qsub` 引数でない、`-o "$EVIDENCE_ROOT/$ATTEMPT/job.stdout"` または `-e .../job.stderr` が欠ければ赤になる。

- `test_job_body_mode_is_executable`
  - executable bit が無ければ赤になる。

受入時は direct `pytest` ではなく次を使う。

```bash
bash -n tools/pegasus/p3_s4_loop_pegasus.sh
python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_job_contract.py -q
python3 tools/run_tests.py orchestrator/tests/test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes -q
python3 tools/check_docs.py
```

resolver と login refusal は新規 test file の該当 node を個別指定してもよい。今回の read-only 段ではいずれも実走していない。

## 変異候補

1. job の host regex を `^pegasus` も許すよう変更する。`test_login_host_refuses_before_scratch_or_receipts` が殺す。
2. expected HEAD の比較を削除する。`test_job_body_static_contract` が殺す。
3. superproject tracked-clean gate を削除する。`test_job_body_static_contract` が殺す。
4. CCBench pin を `p3_s4_loop.PIN` ではなく `pin.CURRENT_PIN` から読む。`test_job_body_static_contract` が import fragment と full-resolution fragmentの差で殺す。
5. CCBench full HEAD と resolved pin の equality を削除する。`test_job_body_static_contract` が殺す。
6. `${PBS_JOBID//:/_}` を `$PBS_JOBID` に戻す。`test_pbs_jobid_path_sanitization_is_load_bearing` が殺す。
7. evidence root の repo/common-root 比較を削除する。`test_external_evidence_and_build_opt_in_mutants_are_rejected` が殺す。
8. `python3` shim を削除、または bare `python3` を PATH 先頭にする。resolver harness が殺す。
9. shim directory に `cmake` symlink を追加する。`test_forbidden_build_tool_shim_mutants_are_rejected` が殺す。
10. `googletest_source_dir`、`mimalloc_source_dir`、`masstree_source_dir` のいずれかを除去する。static contract が殺す。
11. prebuild receipt の `open(..., "x")` を `"w"` に変える。static contract が殺す。
12. `--allow-coder-derived-build` を `--no-build` に置換する。build-opt-in mutant test が殺す。
13. `--isolate-worktree` を削除する。static contract が殺す。
14. job body 内へ `qsub` を追加する。static contract の negative check が殺す。
15. contract helper から CMake/compiler shim の禁止判定を削除する。注入 mutant を使う `test_forbidden_build_tool_shim_mutants_are_rejected` が殺す。
16. contract helper から `--no-build` の禁止判定を削除する。`test_external_evidence_and_build_opt_in_mutants_are_rejected` が殺す。
17. registry class を `local-ok` に変える。新規 registry exact test と `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` が殺す。
18. registry の `reason` または `primary_gate` を変える。両 exact-entry test が殺す。
19. proxy export の片方を削除する。static contract が殺す。
20. README fence から `-e` を削除する。新規 README contract test が殺す。

恒真回避として、resolver と login-host は実 shell を動かし、negative contract は明示的な不正 source を注入して例外を要求する。単に「許可候補リストを作り、その全要素が許可条件を満たす」といった検査は置かない。

## P1〜P4 への回答

- P1: 賛成。
  - `p3_s4_loop.py:171-190` は condition gate に configure args を渡さず、`:1525-1539` も FetchContent base/source dirs を campaign へ渡さない。`pipeline.py:1237-1287` にも転送 field がない。本 wave は prebuild receipt までで線を引き、消費 seam は実装しない。

- P2: 賛成。ただし実接続は未測定。
  - CCBench の `ThirdParty.cmake:35-55,106-136` は HTTPS Git FetchContent を持つ。現 p3 経路では explicit SOURCE_DIR が build へ届かないため proxy export が必要である。literal は `a5_second_boot_backoff_sweep.sh:32,219-222` を写す。proxy を compute job の FetchContent/git が実際に honor するかは qsub 未実測のまま残る。

- P3: 賛成。
  - `p3_s4_loop.py:163-165` の wall budget は 3600 秒で、親の既測 build/verify 上限に余裕を加えた 3 時間は妥当。job 名 `izs4loop` は 8 文字である。

- P4: 条件付き賛成。
  - 専用 detached checkout と primary worktree 禁止は、repo 内 `output/exploration/...` を許容するうえで必要。CCBench 側にはさらに `--isolate-worktree` を使う。
  - 条件は、superproject clean を `--ignore-submodules=all` で検査し、CCBench を `p3_s4_loop.PIN=028f34d` と tracked clean で別検査する解釈を親が認めること。現 gitlink `511c953…` と frozen loop pin が異なるため、通常の superproject clean と loop pin は同時には満たせない。

## 残存リスク

- prebuild の `config.h` と scratch base は loop build に消費されず、loop は proxy 経由の別 FetchContent clone に依存する。
- compute node で proxy が Git/CMake に有効か、3 時間で完走するか、`config.h` の生成位置が実機で同じかは未測定。
- hydrate receipt の exact hash、third-party pin、source root と submission の結合は行わない。指定された scope 外の attestation/consumption seam である。
- `EXIT` trap は通常終了を記録するが、SIGKILL、node loss、filesystem failure では compute-result 自体が残らない可能性がある。
- `p3_s4_loop` は一部の aborted outcome でも一般検査を満たせば rc=0 を返し得る。compute-result の `driver_rc=0` は certified verdict を意味しない。
- dedicated detached checkout であること自体は README の運用契約であり、job body は primary-worktree identity を機械照合しない。
- `-o` / `-e` は job body の制御外であり、operator が README の tagged command を使わなければ repo 外転送は保証されない。
- F660 により、この wave では qsub 実測できず、main 着地後の後続 wave まで compute branch は未実測である。

## 総括

A-2 と既存 Pegasus job の形を写し、compute-only、Python 3.10 shim、repo/pin gate、create-only evidence、masstree prebuild、loop 起動を 1 job body に閉じる。
最大の risk は、prebuild が現 p3 build に未消費で loop 本体が proxy clone に残る点である。
実装前に親が裁定すべき点は、frozen CCBench pin と現 gitlink の差を「superproject は submodule 除外 clean、CCBench は別 exact gate」で扱うかどうかである。
本段では書込、pytest、qsub のいずれも実施していない。