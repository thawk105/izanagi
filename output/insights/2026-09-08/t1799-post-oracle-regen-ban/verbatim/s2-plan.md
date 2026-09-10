## 実測で答えた 4 問

1. **post-oracle build の論理的な build edge は 1 本、コード上の起動 arm は 2 本、再生成を可能にする状態は 3 系統ある。**

   call graph は次の 1 本へ収束する。

   `sort_best` の PASS receipt を確認する [s8b_floor_campaign.py:4371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4371) → post-oracle binding を組み立てる [s8b_floor_campaign.py:4441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4441) → exact `buildcache.build_v2` を要求する [s8b_floor_campaign.py:4455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4455) → `_invoke_build()` [s8b_floor_campaign.py:4497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4497) → `build_v2()` [buildcache.py:2938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2938) → `_build_v2_impl()` [buildcache.py:3080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:3080) → fresh miss の `cmake --build` [buildcache.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2705)。

   `site is None` と site 指定時の arm が [buildcache.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2705) と [buildcache.py:2708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2708) にあるが、同じ `build_cmd` を起動する排他的な 2 arm であり、論理 edge は 1 本である。その target は `ycsb_silo.exe` [buildcache.py:2002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2002) で、`ccbench_masstree` の依存を通じて `masstree_build` [ThirdParty.cmake:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:78) に到達する。OUTPUT が再構築対象になれば、source root 内で `bootstrap.sh`、`configure`、`make`、`ar`、`ranlib` が走る [ThirdParty.cmake:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/external/ccbench/cmake/ThirdParty.cmake:66)。

   再生成を可能にする状態は以下の 3 系統である。

   - **同じ根の時間窓。** 最後の build 前材料 assert は [buildcache.py:2703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2703)、build は 2705–2711、build 後 assert は [buildcache.py:2790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2790)。2703 の後に OUTPUT が欠落または再構築対象になれば、`cmake --build` が再生成できる。再生成 bytes が同一なら、前後の hash 照合は通る。

   - **検査根 A と実効 build 根 B の食い違い。** 前段の assert は常に `A/masstree-src` を見る [buildcache.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:987)。一方、CMakeCache の非空 `FETCHCONTENT_SOURCE_DIR_MASSTREE` が B なら B が優先される [buildcache.py:1094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1094)。A の 3 回の assert は全部通り、B で build が走り、A の build 後 assert も通る。実効根不一致が検出されるのは build 後の [buildcache.py:2793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2793)–2807 である。

   - **共有 base の別 writer。** `prepare_masstree_fetchcontent()`、束縛なし `build_v2()`、または ambient toolchain で同じ base を選んだ legacy `build()` が、oracle 後に OUTPUT を作り直せる。post-oracle build と競合すれば上記の 2703–2790 の窓に入る。別 writer が同一 bytes を再生成した場合も hash だけでは行為を拒否できない。

   cache hit は [buildcache.py:2565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2565)–2641 から build を呼ばずに返るため、再生成 edge ではない。

2. **現行 official floor の引数は同じ根になるが、`build_v2` の post-oracle API 全体では食い違う入力が実在する。**

   official floor では source が `base/<name>-src` から構造的に導出される [s8b_floor_campaign.py:2637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:2637)。binding の base も `dependency.source_root.parent` [s8b_floor_campaign.py:2242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:2242)、build の masstree override も `fetchcontent_base / "masstree-src"` [s8b_floor_campaign.py:4460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4460) である。

   しかし `build_v2` では、次の組が現行 validation を通って configure と build に到達する。

   ```text
   post_oracle_dependency_binding.fetchcontent_base_dir = /tmp/A
   fetchcontent_base_dir                              = /tmp/A
   masstree_source_dir                               = /tmp/B/masstree-src
   mimalloc_source_dir                               = /tmp/B/mimalloc-src
   googletest_source_dir                             = /tmp/B/googletest-src
   ```

   A と B の全 directory が canonical non-symlink directory で、A の材料が binding と一致していればよい。SOURCE_DIR validation は 3 本同時指定だけを要求し [buildcache.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:848)、`source_dirs["masstree"] == A/masstree-src` は要求しない [buildcache.py:2435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2435)。configure argv には A と B の両方が出る [buildcache.py:1940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:1940)–1971。

   したがって「検査根と build 根は常に同じ」とは言えない。現在の一致検査は [buildcache.py:2801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2801)–2807 にあるが、build 後なので D984 の禁止には遅い。

3. **同じ base を束縛なし writer が共有できる。repo 内に writer API は 3 系統ある。**

   `prepare_masstree_fetchcontent()` の production 呼び手は次のとおり。

   - floor prebuild: [s8b_floor_campaign.py:3422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3422)–3434。同じ floor base を使うが、現行 call order では oracle 前である。
   - backoff sweep: [backoff_sweep.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_sweep.py:366)–377。固有 `TemporaryDirectory`。
   - extended sweep: [backoff_extended_sweep.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_extended_sweep.py:887)–898。固有 `TemporaryDirectory`。
   - A2 certification: [paper_story_a2_certification.py:599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/paper_story_a2_certification.py:599)–615。固有 `TemporaryDirectory`。
   - 段 4 loop job: hydrate 済み 3 source を `cp -a` する [p3_s4_loop_pegasus.sh:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/p3_s4_loop_pegasus.sh:330)–360 後、同じ base で prebuild する [p3_s4_loop_pegasus.sh:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/p3_s4_loop_pegasus.sh:392)–401。

   束縛なし `build_v2` の直接または既定 builder 呼び手は、pipeline の trace/perf 2 build [pipeline.py:1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/pipeline.py:1317)–1348、extended sweep [backoff_extended_sweep.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_extended_sweep.py:285)、overthrottle [backoff_overthrottle.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_overthrottle.py:434)、requested-us [backoff_requested_us.py:1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_requested_us.py:1112)、B-10 sweep [b10_backoff_shape_sweep.py:3131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/b10_backoff_shape_sweep.py:3131)、oracle pilot の既定 `build_fn` [s8b_oracle_n_pilot.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_oracle_n_pilot.py:837) と起動 [s8b_oracle_n_pilot.py:944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_oracle_n_pilot.py:944)、および floor の non-sort cell [s8b_floor_campaign.py:4424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4424) である。

   このうち明示 base を運べる実経路は pipeline である。5 値を受け付け [pipeline.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/pipeline.py:883)–910、束縛なし `build_v2` へ渡す [pipeline.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/pipeline.py:1298)–1307。段 4 loop は receipt の base と source root の一致を要求し [p3_s4_loop.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/p3_s4_loop.py:256)–295、その同じ base を pipeline に渡す [p3_s4_loop.py:1688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/p3_s4_loop.py:1688)–1707。排他 lock はないため、同じ絶対 path の receipt または API 引数を与えれば floor base と共有できる。

   legacy `build()` の直接呼び手には pipeline [pipeline.py:1333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/pipeline.py:1333)、backoff profile [backoff_profile.py:854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/backoff_profile.py:854)、S1 [s1_verify_extime_calibration.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s1_verify_extime_calibration.py:390)、S2 [s2_verify_calibration.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s2_verify_calibration.py:354)、S3 [s3_lock_coverage.py:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s3_lock_coverage.py:258)、S5 [s5_permutation_coverage.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s5_permutation_coverage.py:293)、between-run floor [between_run_floor.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/between_run_floor.py:324)、Pegasus floor scoping [pegasus_floor_scoping.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/pegasus_floor_scoping.py:218) がある。signature に base はない [buildcache.py:3104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:3104) が、configure subprocess は環境を既定で継承する [buildcache.py:3483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:3483)–3496。したがって `CMAKE_TOOLCHAIN_FILE` が同じ `FETCHCONTENT_BASE_DIR` を FORCE する経路は残る。

   official floor の既定 base 自体は、存在しない job-local destination を排他作成して payload を複製する [s8b_floor_campaign.py:3209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3209)–3265。この通常経路に後続 writer はない。ただし public API 上は共有を禁止していない。

4. **この repo で安く閉じるのは (b) 判定後の source tree の書込み不能化である。**

   **(a) private snapshot** は実装可能だが高い。

   - oracle PASS 後の位置 [s8b_floor_campaign.py:4371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4371)–4382 で、masstree、mimalloc、googletest の全 source を新しい private base に再複製する必要がある。
   - `_post_oracle_dependency_binding()` の base 導出 [s8b_floor_campaign.py:2242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:2242)、build kwargs [s8b_floor_campaign.py:4441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4441)–4471、postflight の result/base/root 期待値 [s8b_floor_campaign.py:3764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3764) と [s8b_floor_campaign.py:3829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3829)–3875、cleanup lifetime [s8b_floor_campaign.py:4706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:4706)–4726 を連動変更する必要がある。
   - D1663 の `cp -a` [p3_s4_loop_pegasus.sh:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/tools/pegasus/p3_s4_loop_pegasus.sh:330)–346 は安全な前例だが、floor はすでに submission payload を job-local base へ複製している [s8b_floor_campaign.py:3247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_floor_campaign.py:3247)–3251。post-oracle copy は 2 回目の全 tree copyになり、容量、時間、cleanup、provenance の主張が増える。
   - 束縛なし build は変わらないが、post-oracle configure argv の base/source path は変わる。正しい材料の受理集合を保つには複製後の canonical 二根検査と archive hash 再照合が追加で必要であり、最小変更ではない。

   **(b) 書込み不能化** は既存 primitive を再利用できる。

   - [s8b_expected_materialization.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:541)–611 に、全 regular file/directory と親から write bit を外し、fd anchor と tree digest を保持する実装がある。exact mode の復元も [s8b_expected_materialization.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:523)–538 にある。
   - configure 後に実効根を読み、A と一致させてから `cmake --build` の間だけ保護すれば、CMake が base 内の configure metadata を正当に作る挙動を妨げず、材料を再生成する custom command だけを書込み不能にできる。
   - 同じ根を読む束縛なし build は壊れない。保護中に同じ判定済み根へ書こうとする別 build だけが拒否されるが、その書込みは D984 が禁止する対象である。別 base の build、または時間的に重ならない build の受理集合は変わらない。
   - configure argv、cache identity、receipt schema は変えない。post-oracle で「同一 bytes を再生成していたため従来は通った」集合だけが意図どおり縮む。

## plan (file:line 粒度)

- [sort_swo_dependency_material.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:11)–22 に `contextlib`、`Iterator`、既存 `s8b_expected_materialization` primitive の import を足す。

- [sort_swo_dependency_material.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/sort_swo_dependency_material.py:414)–489 の二根検査の直後に、post-oracle 専用の小さい context manager を置く。責務は次の 4 点だけとする。

  1. binding が指す source root と configure 成果物由来の effective root を canonicalize し、exact equality を要求する。
  2. 不一致なら build を一度も起動せず `CanonicalDependencyMaterialError` へ倒す。
  3. 一致した root に `make_snapshot_non_writable()` を適用してから consumer を yield する。
  4. 成功、build 失敗、検査失敗の全経路で `restore_snapshot_permissions()` を `finally` 実行する。

  汎用 flag、skip knob、trace 分岐、台帳、CLI は持たせない。

- [buildcache.py:2701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2701)–2703 の既存 disconnected/material assert の後で、`_masstree_source_root_from_cmake_cache(staging)` を呼ぶ。期待根は従来どおり `canonical_fetchcontent_base/masstree-src` とする。

- post-oracle binding がある場合だけ、上記の専用 context に入って [buildcache.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2705)–2713 の build を起動する。context 内で build 直前と直後にも既存 `_assert_post_oracle_dependency_material()` を呼び、書込み不能化完了後の材料と build 直後の材料を照合する。

- 現在の初期 assert [buildcache.py:2452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2452)、configure 前 assert [buildcache.py:2687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2687)、configure 後 assert [buildcache.py:2701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2701)–2703、build 後 assert [buildcache.py:2789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2789)–2790、既存の build 後実効根照合 [buildcache.py:2793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2793)–2807 は削らず、緩めず、後段 defense-in-depth として残す。

- `effective_root` は configure 直後に得た値を後段 compiler-input と receipt 検査でも再利用する。現行の遅延初期化 [buildcache.py:2717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2717) と [buildcache.py:2794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2794)–2797 は、post-oracle では既に解決済み、束縛なしでは従来どおり遅延解決、となるよう整理する。

- [test_sort_swo_dependency_material.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_sort_swo_dependency_material.py:174) 付近に専用 context の焦点テストを置く。根不一致の fail-before-yield、context 中の write bit 除去、正常時と例外時の exact mode 復元を検査する。

- [test_buildcache_v2.py:1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1138)–1370 の post-oracle 群に integration test を足す。実効根不一致で event 列が `["configure"]` のまま build がゼロであること、build 中の同一 bytes 再書込みが拒否されること、generic build では protection helper が呼ばれず argv が不変であることを固定する。

- **公開 API は変更しない。** `build_v2` の signature [buildcache.py:2938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:2938)–2962、post-oracle binding の key 集合 [buildcache.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/buildcache.py:62)–66、`prepare_masstree_fetchcontent` の signature、CLI、artifact schema は変えない。したがって束縛なし呼び出しの argv は、既存の exact-zero test [test_buildcache_v2.py:1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1199)–1223 と新しい helper 非到達 test の二重で 1 byte 不変を保証する。

- **変更しない file:** `s8b_floor_campaign.py`、`sort_swo_oracle.py`、`s8b_expected_materialization.py`、`external/ccbench/cmake/ThirdParty.cmake`、`p3_s4_loop.py`、`p3_s4_loop_pegasus.sh`。submodule pin 更新は不要である。

- 既存 test の破損予測は **0 件**。cache hit test [test_buildcache_v2.py:1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1138)、disconnected OFF test [test_buildcache_v2.py:1339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1339)、generic/post identity 分離 test [test_buildcache_v2.py:1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_buildcache_v2.py:1199)、real material integration [test_sort_swo_dependency_material.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/tests/test_sort_swo_dependency_material.py:329) は、既存 OUTPUT が揃い build が source を書かないため通る想定である。

## 正例と負例

- **正例:** `/tmp/A/masstree-src` に正しい HEAD、tracked files、oracle と一致する `config.h`、既存 `libkohler_masstree_json.a` があり、binding の全 hash が一致する。`post_oracle_dependency_binding=binding_A`、`fetchcontent_base_dir=/tmp/A`、SOURCE_DIR 3 本は省略する。configure 成果物の effective root は `/tmp/A/masstree-src`。書込み不能化後の build は既存 OUTPUT を読むだけなので成功し、終了後に元の mode が復元される。

- **負例 (i)、根の向き:** binding と検査対象は `/tmp/A/masstree-src`、明示 SOURCE_DIR は `/tmp/B/masstree-src` とする。A は完全一致、B は正しい checkout だが archive が欠落している。現行なら A の assert 後に B の custom command が archive を生成し、その後で root mismatch になる。変更後は configure 成果物から B を読んだ時点で A と不一致として拒否し、`cmake --build` は 0 回である。

- **負例 (ii)、同一 bytes の向き:** A の全材料と binding は一致しているが、fake または実 custom command が build 中に `config.h` と archive を truncate して元と完全に同じ bytes を再書込みする。禁止がなければ manifest、config hash、archive hash、HEAD は全て同じなので既存の前後照合を通る。変更後は source tree が書込み不能であるため最初の write open が失敗し、build は拒否される。

## 変異の狙い先

`buildcache.py` は HEAD blob closure に含まれる [campaign_lock.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/campaign_lock.py:49)–112 ため、変異対象にしない。

新しい「effective root は判定根と同一でなければならない」「build 中は判定根を書込み不能にする」という意味は、`CONTRACT_LOADER_RELATIVE_PATHS` に含まれない `sort_swo_dependency_material.py` の新しい専用 context manager に置く。

変異候補は次の 3 行である。

- effective root equality を逆転または削除する行。
- `make_snapshot_non_writable()` を呼ぶ行。
- `finally` で exact mode を復元する行。

特に protection 呼出しを no-op にする変異では、負例 (ii) の「同一 bytes 再書込み」が通るため、この変更だけに固有の test node が残る。buildcache 側の callsite を変異しなくても禁止の意味を直接攻撃でき、drift mask に吸収されない。

## 未解決・親の裁定が要る点

新しいユーザー裁定は不要である。D984 の許可済み手段 (b) を採り、D953/D954 の capability と実効値検査を維持する。

境界として、再利用する permission primitive は同一 uid の協調的 process に対する discretionary-mode 保護であり、owner が自ら chmod を戻す攻撃や privileged actor を sandbox として阻止するものではない。この限界は既に [s8b_expected_materialization.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:14)–19 と [s8b_expected_materialization.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1799-post-oracle-regen-ban/orchestrator/campaign/s8b_expected_materialization.py:860)–863 に明記された既存境界であり、本 plan は同じ意味で D984 の「書込み不能化」を実装する。

## 総括

採用案は **実効根を build 前に判定根へ固定し、その根を `cmake --build` の間だけ書込み不能にする** である。

変更対象は `buildcache.py`、`sort_swo_dependency_material.py`、対応する 2 test file。公開 API、generic build の argv、cache schema、oracle 照合、submodule pin は変えない。private snapshot は D1663 の前例どおり可能だが、2 回目の全 source copy、binding、postflight、cleanup の変更が必要なため採らない。

指示どおり file は変更せず、テストも実走していない。静的な call graph と file:line のみで起草した。