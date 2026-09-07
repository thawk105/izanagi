## 所見 (real/refuted 付き)

1. **[real] `build_v2` API では A/B 不一致が現行 validation を通る。**

   - binding は `fetchcontent_base_dir=/tmp/A` を canonicalize するだけで、SOURCE_DIR と比較しない。`orchestrator/campaign/buildcache.py:788-820`
   - explicit `fetchcontent_base_dir` は binding の A と比較されるが、`masstree_source_dir` は別途 directory として検証されるだけである。`orchestrator/campaign/buildcache.py:2404-2444`
   - `_v2_commands()` は `-DFETCHCONTENT_BASE_DIR=/tmp/A` と `-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/tmp/B/masstree-src` を同じ configure argv へそのまま置く。`orchestrator/campaign/buildcache.py:1940-1971`
   - `ThirdParty.cmake` は `masstree_SOURCE_DIR` から archive/config path を作るため、B が custom command の作業 root になる。A へ戻す行はない。`external/ccbench/cmake/ThirdParty.cmake:42-58,66-78`
   - 保存済み実例にも、BASE_DIR と非空 SOURCE_DIR が異なる root として同時に cache へ残っている。`output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/build-rung-perf/CMakeCache.txt:392,407`
   - parser は非空 SOURCE_DIR を BASE_DIR より優先し、DependInfo の output 親とも一致させた後、その realpath を返す。従って上の入力では B を返す。`orchestrator/campaign/buildcache.py:1094-1102,1129-1171`

2. **[refuted] ただし official floor 呼出しに限れば A/B 不一致は起きない。**

   唯一の production caller は、source を常に `<base>/<name>-src` から導出し、binding の base を `source_root.parent`、explicit SOURCE_DIR を同じ `<base>/masstree-src` とする。`orchestrator/campaign/s8b_floor_campaign.py:2637-2641,2204-2247,4460-4471`。したがって新しい build 前 equality は public `build_v2` capability には発火入力があるが、現在の official floor call graph では恒真である。

3. **[real] 書込み不能化は targeted custom command の成功を止める。**

   helper は root 内の全 regular file/directory、root、parent から `0222` を外す。`orchestrator/campaign/s8b_expected_materialization.py:541-611`。通常 user の process が既存 file を開き直す、file を作る、unlink/rename する操作は失敗する。

4. **[real] 正常な up-to-date build は成立する。**

   `masstree_build` は archive/config を OUTPUT とするだけで DEPENDS がない。両方が存在すれば custom command は走らない。`external/ccbench/cmake/ThirdParty.cmake:66-78`。保存済み build log にも、masstree は即 `[0%] Built target`、その後 mimalloc と CCBench だけを build した正例がある。`output/env/pegasus/t139-r4-env-probe/0:896500.nqsv/build-trace1.log:1-28`

5. **[real] 新旧の root equality は同じ述語だが、実行時点が異なる。**

   現行後段も `effective_root == canonical_fetchcontent_base/masstree-src` を要求する。`orchestrator/campaign/buildcache.py:2793-2807`。新規照合は受理集合を変えず、「B で build してから拒否」を「build せず拒否」へ変える。純増例は、A の材料が完全一致し、B の archive が欠落している A/B 入力である。ただし B は oracle が判定した A ではないため、この純増は D984 の同根再生成禁止そのものではなく、誤 root build の副作用を早く止める効果である。

6. **[real、範囲限定] 禁止は command edge の消滅ではなく、書込み成功の拒否として実装される。**

   custom command の起動自体は到達可能だが、最初の source write が失敗し、`cmake --build` が非 0 になる。D984 が明示的に許可した「書込み不能化」はこの意味での禁止である。一方、保護開始は configure 後なので、oracle PASS から context 進入までを含む全時間帯で同一 bytes 再生成を構造的に不可能にする機構ではない。official floor にはその間の late writer edge は見つからないため、仮想 writer 向け追加 gate は推奨しない。

## 機序の検証 — 書込み不能化は何を止め、何を止めないか

| 段 | source 側の書込み |
|---|---|
| `cmake -E echo` | stdout のみ。source write なし。`ThirdParty.cmake:68` |
| `bootstrap.sh` | `autoreconf -i` を source root で実行し、`configure`、`config.h.in`、`autom4te.cache` などを生成する。`orchestrator/tests/fixtures/sort_swo_masstree/bootstrap.sh:1-5`、生成物の保存済み実測は `docs/archive/worklog-phase3-0823-842.md:117-124` |
| `configure` | source root の `config.log`、`config.status`、`config.h`、`GNUmakefile`、`stamp-h` などを書く。`configure.ac:5-7,454`、`GNUmakefile.in:73-91` |
| `make` | source root の `.deps/`、`*.d`、`*.o` などを書く。`GNUmakefile.in:25-29,85-91` |
| `ar cr` | `<source>/libkohler_masstree_json.a` を作成または更新する。`ThirdParty.cmake:72,74` |
| `ranlib` | 同じ archive の index を更新する。`ThirdParty.cmake:73-74` |

最も早い書込み process は `bootstrap.sh` 内の `autoreconf -i` である。ただし autoreconf 内部で最初に触る pathname は tool/version/timestamp 判断に依存し、repo の command 列から exact 1 path には固定できない。bootstrap が更新を省いた場合でも、後続 configure、遅くとも `ar cr` が source root へ書く。

masstree について source tree 外へ出力する bypass はない。5 command 全ての `WORKING_DIRECTORY` は `masstree_SOURCE_DIR` で、別 build directory は渡されていない。`ThirdParty.cmake:66-76`。「out-of-tree」とするコメント `ThirdParty.cmake:49-51` は実 command と一致しない。

失敗伝播も閉じている。custom command の recipe に失敗無視指定はなく、make/cmake の非 0 を `_run()` が `RuntimeError` にする。`orchestrator/campaign/buildcache.py:3483-3499`。従って EACCES 後に黙って成功する経路はない。

保証範囲は discretionary mode までである。owner が自ら chmod を戻す actor、privileged actor は対象外と既存 helper 自身が明記する。`orchestrator/campaign/s8b_expected_materialization.py:14-19,847-863`

## 正常経路を壊さないことの根拠 (または壊す証拠)

**[real] 静的には正常経路を壊さない。**

- archive/config の mode 変更は mtime を変えないため、OUTPUT の再構築判定を自ら発火させない。
- up-to-date なら `masstree_build` custom command は 0 command で終わる。保存済み log の正例は `output/env/pegasus/t139-r4-env-probe/0:896500.nqsv/build-trace1.log:1`。
- mimalloc の書込み先は sibling の既存 `<base>/mimalloc-build` である。base 自身の write bit がなくても、writable な既存 child directory 内の作成は可能である。配置は `orchestrator/tests/test_s8b_compiler_input.py:205-219`、実 build は上記 log `:3-21`。
- googletest も configure 時に `FetchContent_MakeAvailable()` される sibling source/build treeであり、`ycsb_silo.exe` target の依存にはならない。`external/ccbench/cmake/ThirdParty.cmake:118-136`
- CMake の top-level build metadata と CCBench object/binary は staging build directory 側へ書かれる。

**[refuted] plan が「real material integration」を実 build の根拠に数えるのは不正確。** `test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured` は材料だけ real root から複製するが、build は `_fake_build_environment()` に差し替える。`orchestrator/tests/test_sort_swo_dependency_material.py:329-412`、fake は CMakeCache/DependInfoと dummy binary を Python で作るだけである。`orchestrator/tests/test_buildcache_v2.py:241-375`。従って protected real CMake build は未実走であり、上の結論は静的機序と保存済み非 protected build logによる。

## 親 brief の誤り

- **P1: [real/一部 refuted]** 同根の build 前後 window と A/B mismatch は実在する。`buildcache.py:2701-2713,2789-2807`。一方、共有 base の別 writer は public API では構成可能だが、official floor の base は不在 destination を job TMPDIR に排他作成し、prebuild も oracle 前に一度行う。`s8b_floor_campaign.py:3209-3265,3403-3435`。official 経路に late writer があるとの主張は refuted。
- **P2: [real]** 検査根は `<binding base>/masstree-src` 固定、build 根は SOURCE_DIR override 優先である。`buildcache.py:987-1018,1094-1102`
- **P3: [real、ただし費用比較は未計測]** 既存 permission primitive は再利用可能で正常経路とも両立する。「private snapshot より安い」は設計上もっともらしいが、比較実測ではない。
- **P4: [real]** `external/ccbench` は gitlinkであり、現在の pin は `511c9538...`。`.gitmodules:1-4`、floor protocol `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1`
- **DW-G05: [refuted]** 本変更の直接成果物は S8b floor の `sort_best` binary、admission receipt、portable `sort_swo_oracle` recordである。`s8b_floor_campaign.py:4585-4659,4940-4948`。Paper-story A-2/A-6 は別 module が独自 condition gate、job-local cache、`run_campaign()` を使い、S8b floor を消費しない。`paper_story_a2_certification.py:40-65,585-621,3414-3479`。従って brief `:68-73` の「A-2/A-6 certification」への直接影響は誤り。
- **lock 主張: [一部 refuted]** `buildcache.py` が exact closure に含まれ、`s8b_floor_campaign.py` と `sort_swo_dependency_material.py` が含まれないことは正しい。`campaign_lock.py:47-112`。ただし membership 自体が自動的な HEAD gate ではない。新規捕捉時だけ `capture_contract_loader_binding()` が current HEAD と disk を比較し、既存 lock は記録 commit blob と比較する。`contract_loader_binding.py:348-400`
- **「未 commit なら全赤」「buildcache mutation は固有 node が空」: [refuted]** direct `test_buildcache_v2` helper は contract-loader capture を呼ばず、`buildcache.py` 自身にもその import/callはない。`test_buildcache_v2.py:27-48,71-80`、`buildcache.py:29-44,171-205`。従って選んだ焦点 node 次第では buildcache mutation は目的 gate まで到達できる。

## 変異の帰属

- **[real] `sort_swo_dependency_material.py` の新 context を狙う方法は固有 node を作れる。** direct unit test は buildcache 後段を呼ばないため、equality 削除、permission call no-op、restore 削除をそれぞれ直接観測できる。同 file は lock closure 外なので drift mask も発火しない。`campaign_lock.py:49-112`
- **[real、条件付き] equality mutation の integration 入力は既存後段 gate でも赤になる。** 根不一致自体は現行 `buildcache.py:2801-2807` が捕える。従って例外型だけを見る test では新機構の必要性を示さない。plan の `events == ["configure"]` と direct fail-before-yield を固定すれば、「build を起動しなかった」という新しい時点差に帰属できる。
- **[real] permission call no-op の同一 bytes 再書込みは固有である。**既存の前後 manifest/config/archive/HEAD 検査は全て同じ値を見るため赤にならない。permission unit node と「同一 bytes write が成功してしまう」integration nodeだけが落ちる。
- **[real、意味限定] restore mutation の固有 node は作れるが、証明するのは cleanup/exact mode 復元であり、D984 の再生成禁止そのものではない。**
- **[refuted] target 選択理由を「buildcache は mutation 不可能」とする必要はない。** mutation harness は unique anchor の文字列置換と expected node 集合を検査するだけである。`tools/mutation_harness.py:615-634,1079-1093`。どの gate が先に発火するかは選んだ test call graph 次第である。

## 総括

plan の中心である「`cmake --build` 中だけ masstree source root を書込み不能にする」は実効的である。custom command の成功は EACCESで止まり、非 0 が Pythonまで伝播し、up-to-date 正例は sourceを書かず成立する。

修正が必要なのは説明と帰属である。

- root equality は public API では発火するが、現在の official floor callerでは恒真。
- 新旧 equality は同一述語で、純増は受理集合ではなく build 前停止。
- 全 post-oracle 時間帯を不可到達にするのではなく、保護 context 内の成功書込みを禁止する。
- A-2/A-6 成果物影響と「buildcache mutation は必ず drift に吸収される」は誤り。
- `sort_swo_dependency_material.py` を狙う変異自体は有効で、特に同一 bytes 再書込みの no-op mutant は既存 gate に先取りされない。

追加の一般 gateや台帳は不要。file変更、test実走、patch作成は行っていない。