# 親が保持する実測事実 (計算ノードの offline 依存供給・hydrate・prepare) — 段 1 で親が照合済み

出所: 親 session の実測記録 (2026-09-09〜2026-09-17 の複数 wave)。repo 内の一次資料は各行に併記。

## 計算ノードと永続 cache

- 計算ノードは外部 network 不在 (2026-09-09、bnode122 / bnode013 で独立確認)。FetchContent を offline 供給なしで
  走らせる build は落ちる。t316 の受領証 `0:999027.nqsv` は S3 に `S3_NETWORK_DNS_NODE_CAPABILITY_UNAVAILABLE`。
- 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache/` には `gflags glog googletest masstree mimalloc` があり、
  masstree に `config.h` と `libkohler_masstree_json.a` が**本日 (2026-09-17) も実在**、`git status --porcelain --ignored`
  は 40 行 (ignored な旧 build 生成物)。`git status --porcelain --untracked-files=all` は空 (ignored は出ない) ので、
  t316 の `_git_source_identity` は cache を `clean_including_untracked: true` と記録した (受領証 `0:999027.nqsv`)。
- `fetch_third_party.py verify` は既定 `reject_ignored=False` で ignored を検査しない。`reject_ignored=True` を渡すのは
  hydrate 経路だけ (`tools/pegasus/fetch_third_party.py` の `_hydrate`)。
- masstree の build は `add_custom_command` (`external/ccbench/cmake/ThirdParty.cmake`) で `bootstrap.sh` / `configure` /
  `make` / `ar` を **source dir の中で**走らせ、`config.h` と archive を source dir に書く。OUTPUT がその 2 file なので、
  実在すれば custom command は再実行されない (DEPENDS なし)。これが cache 直指しで sandbox 内 (ro-bind) の build が
  通っていた機序であり、同時に cache を汚す機序でもある。
- `p3_s4_loop_pegasus.sh` は `THIRDPARTY_SOURCE_ROOT` を scratch へ `cp -a` し、複製先 masstree に `config.h` が
  あれば `refuse "scratch masstree source is not fresh"` で止める (rc=2)。cache 直指しは他経路では停止条件。

## hydrate

- 正しい供給は `python3 tools/pegasus/fetch_third_party.py hydrate --repo-root <repo> --cache-root <cache>
  --staging-root <dst>`。出力 JSON の `source_root` が staging root。layout は `<dst>/<source_name>`
  (masstree / mimalloc / googletest / gflags / glog の 5 本、D2084 で gflags / glog が加わった)。
- hydrate は `git clone --no-hardlinks --no-checkout` + pin checkout で tracked file だけを置く。2026-09-10 実測で
  hydrate 出力は `config.h` 無し・`.o` 0 件。各 source は `_verify_source(..., reject_ignored=True)` を通る。
- `_load_policy` (hydrate の前提) は `<repo>/tools/pegasus/policy.json` の `third_party_sources` 3 本 (name / source_name /
  url / fetchcontent_ref / pin) と `gflags_source_url` / `gflags_expected_head` / `glog_*`、および
  `<repo>/external/ccbench/cmake/ThirdParty.cmake` の `set(CCBENCH_<NAME>_REPO "...")` / `set(CCBENCH_<NAME>_TAG "...")`
  literal との同期を要求する (`orchestrator/campaign/silo_ladder_rung1.py` の `third_party_policy`)。
  → 配線テストの fixture repo でこの CLI を実走させるには、fixture の policy.json と ThirdParty.cmake を fixture の
  git repo の HEAD に揃えて書く必要がある。
- 所要: login node → NFS home 宛で `cp -a` masstree 21.3 秒・3 本合計 85 秒 (hydrate 済み全体 40 MiB)。計算ノードの
  `/scr` 宛はこれより速い (mocc_trace_pilot.sh は `timeout 20` で回している)。
- 過去 wave の hydrate 出力は再利用しない (submit-tree ごと撤去されて消える)。
- **本 wave の実測 (2026-09-17 21:58 JST、login node、宛先 Lustre `/work/1/SFC/tanab/dev-wave-jobs/.../probe-hydrate/thirdparty-src`):**
  上記 CLI を worktree の `--repo-root` で 1 回通して rc=0、**所要 15.75 秒**、出力 JSON の 5 source は
  masstree b3c5d054 / mimalloc 02a2f5df / googletest f8d7d77c / gflags e171aa2d / glog 8f9ccfe7 (policy の pin と一致)、
  出力の `masstree/config.h` は不在。記録: 同 dir の `hydrate.json` / `hydrate.stderr` / `hydrate.rc`。

## prepare_masstree_fetchcontent

- `orchestrator/campaign/buildcache.py:2034`。`ccbench_dir` (絶対 dir)、`fetchcontent_base_dir` (canonical 絶対 dir、
  prebuild の build dir `<base>/izanagi-masstree-prebuild` と `-DFETCHCONTENT_BASE_DIR=<base>` に使う)、
  `expected_toolchain_manifest` (`buildcache.observed_toolchain_manifest(cc, cxx)` の戻り)、`configure_timeout_s` /
  `target_timeout_s` (正整数)、`site` (None なら `site_policy.current_site()`)、`dependency_prefix` (`-DCMAKE_PREFIX_PATH`)、
  `masstree_source_dir` / `mimalloc_source_dir` / `googletest_source_dir` (3 本同時指定、canonical 絶対 dir)。
  configure → `cmake --build <base>/izanagi-masstree-prebuild --target masstree_build -j <site jobs>` を走らせ、
  `MasstreeFetchContentPreparation(fetchcontent_base_dir, build_dir, configure_argv, build_argv)` を返す。
- `_run(..., site=)` は `require_heavy_work_site` で **PEGASUS_LOGIN / PEGASUS_SUSPECT を拒否**する。計算ノード
  (bnode hostname) は PEGASUS_COMPUTE、pytest では `orchestrator/tests/conftest.py` の autouse `_declare_default_test_site`
  が hostname を `test-host`、`_has_nqsv` を False に中和するので OTHER → 拒否されない。
- SS2PL runner (T-2644、2026-09-17) の実測: pristine staging に対する `masstree_build` warm-up は計算ノードで 13 秒。
- CCBench configure は `find_package(gflags)` / `find_package(glog)` を要するので、prepare の configure にも
  `dependency_prefix` (gflags / glog の install prefix) が要る。t316 では outside の `<scratch>/s6-outside/install`。

## 緑の 2 例の形

- A-2 (`orchestrator/campaign/paper_story_a2_certification.py:679-720`、`tools/pegasus/paper_story_a2_certification.sh:340-356`):
  親が login で hydrate → `IZANAGI_A2_THIRD_PARTY_SOURCE_ROOT` で渡す → job が `cp -a <root>/<name> <scratch>/fetchcontent/<name>-src`
  → `_verify_pristine_floor_dependency_sources(base)` → `patchharness.checkout` + `applied` の内側で
  `prepare_masstree_fetchcontent(ccbench_dir=variant_root, fetchcontent_base_dir=base, *_source_dir=<base>/<name>-src, …)`
  → `capture_define_inputs(variant_root, stock_root, configure_args=(-DCMAKE_PREFIX_PATH, -DFETCHCONTENT_BASE_DIR, -DFETCHCONTENT_SOURCE_DIR_* ×3))`。
- backoff_sweep driver 段 (`orchestrator/campaign/backoff_sweep.py:437-465`): `tempfile.TemporaryDirectory` を base に
  `prepare_masstree_fetchcontent(ccbench_dir, fetchcontent_base_dir=base, …)` (source dir 指定なし = network fetch、login 用)
  → `_require_backoff_condition_gate(..., configure_args=(-DFETCHCONTENT_BASE_DIR=base,))`。
- 2026-09-07 の insight `output/insights/2026-09-07_t2228-driver-gate-liveness/README.md` が、通らなかった 3 箇所と
  通った 2 例の差を「関門の configure へ準備済み FetchContent base を渡すか」に帰着させている。

## t316 の sandbox bind (現行)

- `SandboxProfile.argv`: `--ro-bind` を `/usr` 系・`/bin`・`readonly_roots` (cache と T139 deps root、S6 では
  requested 木も) に、`--ro-bind <scratch>/empty-tmp /tmp`、`--bind <scratch> <scratch>` (rw)。`TMPDIR=<scratch>/tmp`。
- `_s6_requested_checkout` は `TMPDIR` 未設定 / `/tmp` 配下のとき `scratch.parent` の下に使い捨て木を作る
  (scratch の rw bind に覆われない兄弟)。
- `run_probe` は `scratch = mkdtemp(prefix="t316-<jobid>-", dir=<SCRATCH_ROOT>)`、SCRATCH_ROOT は `.pbs` で
  `${TMPDIR:-/scr}`。本番受領証の scratch は `/scr/t316-0_999027.nqsv-wr6pkekl`。
