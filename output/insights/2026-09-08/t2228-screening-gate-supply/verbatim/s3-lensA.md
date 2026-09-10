## 偽の緑

- **refuted / nit** — `config.h` 不在時の skip と等価な経路はない。preprocess/configure の失敗は赤 record へ変換され、family admission は全 supply record が緑でなければ通らず、screening helper も `admitted=False` を例外にする。`orchestrator/campaign/condition_meaning_gate.py:2548`、同`:2557`、同`:4058`、`orchestrator/campaign/screening_driver.py:194`

- **refuted / nit** — tested macro が owner TU へ届かない入力も、従来どおり `preprocess-bytes-identical` で赤になる。base 追加だけではこの判定を回避できない。`orchestrator/campaign/condition_meaning_gate.py:2612`

- **real / should-fix** — screening の meaning 腕は全 request で `declaration=None` のため常に `unestablished` であり、それでも admission は通る。これは既存仕様で今回の弱化ではないが、供給後の緑を「runtime meaning まで確認済み」と表現してはならない。`orchestrator/campaign/screening_driver.py:188`、`orchestrator/campaign/condition_meaning_gate.py:3295`、同`:4059`

## 受理集合の変化

- **real / must-fix** — brief の「受理集合を変えない」「赤入力は赤のまま」は文字どおりには成立しない。本変更の目的そのものが、manifest がある request を「dependency 未準備による赤」から、後続の supply 判定結果へ進めることである。正しい不変条件は「判定式は不変、環境起因の前段赤だけを除去する」である。`brief.md:23`、同`:30`、`s2-plan.md:124`

- **real / must-fix** — 変化する集合は厳密には次である。`requests != ()`、manifest あり、prepare 成功、従来の family が FetchContent の未準備に由来する supply 赤であり、共有 base 後は全 supply が緑かつ meaning が非赤となる呼出しである。現行 backoff grid では `BACKOFF_FIXED=-1` が2 genome、`2,5,10,25,50,100` が各1 genomeの計8件である。特に実測で止まったのは最初の baseline `-1` である。`orchestrator/campaign/backoff_sweep.py:58`、同`:60`、同`:198`、`output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:44`

- **real / should-fix** — はみ出しは `config.h` だけではない。共有 base は masstree の生成 headerに加え、masstree、mimalloc、googletest の FetchContent population 全体を変える。したがって offline fetch の configure failureや他の dependency 不在で赤だった環境も赤から先へ進みうる。これらも「base 未供給」に含めるなら整合するが、「`config.h` 欠落だけ」とする主張には一致しない。`external/ccbench/cmake/ThirdParty.cmake:42`、同`:106`、同`:130`、`orchestrator/campaign/buildcache.py:2044`

- **refuted / nit** — manifest `None` の s6/s8a は実効的な対照であり、P1 の条件は全 domain request に対する恒真条件ではない。両 caller は manifest を渡していない。`orchestrator/campaign/s6_sort_sweep.py:421`、`orchestrator/campaign/s8a_trigger_sweep.py:523`

## 木の同一性

- **refuted / nit** — CCBench source 木については計画どおり揃えられる。`SourceEvidence.source_root` は canonical rootで、同じ値を prepareとgateへ渡せる。後続 pipeline は source evidenceを再解決して caller値と完全一致を要求するため、別のsource rootへ静かにずれる経路はない。`orchestrator/campaign/source_digest.py:2344`、同`:2365`、`orchestrator/campaign/pipeline.py:1145`、同`:1152`

- **real / should-fix** — 同一なのは CCBench source 木だけで、dependency 木ではない。screening baseは関門直後に削除され、後続 `pipeline.evaluate` へ一切渡らない。後続 build は独自の FetchContent状態または既存build cacheを使う。したがって `config.h` bytes非束縛はD1666と同じであり、screeningだけ論理的に悪化はしないが、genomeごとに別baseを作るため時間方向の差異は増える。`s2-plan.md:142`、同`:145`、`orchestrator/campaign/pipeline.py:1282`、同`:1298`

- **real / should-fix** — stock腕はstock木自身で準備したdependencyではなく、patched木を `-S` にして準備したbaseを使う。現在のbackoff patchは `cmake/Options.cmake` と `include/backoff.hh` だけを変更し、`ThirdParty.cmake` は変えないため、現行pinでは実害を示せない。ただしstock比較が独立に束縛するのはowner code rootであってdependency provenanceではない、と明記すべきである。`patches/silo-backoff-fixed.patch:1`、同`:28`、`orchestrator/campaign/condition_meaning_gate.py:1825`

- **real / should-fix** — D1666の「同一toolchainから生成」という説明はhelperだけでは保証されない。manifestはtop-level CMake compilerへ設定されるが、masstreeのcustom commandは `./configure` と `make` をCC/CXX指定なしで実行し、subprocessは親環境を継承する。生成 `config.h` のcompiler入力はmanifestに束縛されない。`orchestrator/campaign/buildcache.py:2045`、`external/ccbench/cmake/ThirdParty.cmake:67`、`orchestrator/campaign/buildcache.py:3524`、`verbatim-d1666.md:19`

## 恒真な保証

- **real / must-fix** — 計画中の正例は、productionのmissing-header層を殺せない。現行 `supplied` fixtureは `FETCHCONTENT_BASE_DIR` を変数へ代入するだけで、headerやtargetに使わない。prepareをstubして実supply evaluatorを呼んでも、helperが実際には `config.h` を生成できない、またはbaseがproduction CMakeに効かない実装のまま緑になる。`orchestrator/tests/fixtures/condition_meaning_gate/supplied/CMakeLists.txt:3`、`s2-plan.md:156`、同`:157`

- **real / must-fix** — 特に実測で最初に落ちたstock baseline `BACKOFF_FIXED=-1` を、prepared base付きの実stock腕で通す正例がない。計画の具体的負例は値5で、stock入れ子検査は寿命とcall順のstub検査に留まる。screeningが本番baselineで依然赤でも、計画した単体検査群が全緑になりうる。`s2-plan.md:150`、同`:161`、`output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:50`

- **real / should-fix** — `without_manifest`、`no_requests`、既存 `accepts_real_runtime_genome_value` は意図的な非発火検査なので、新しい供給が全く効かなくても緑になりうる。負例はadmission無視の変異には有効だが、供給の生死確認にはならない。`s2-plan.md:159`、同`:160`、同`:164`

- **real / should-fix** — D1666回帰2件もprepareとgateを共にstubしてargv/rootを比較する検査であり、実helperの生成物は見ていない。official perf、spawn、certified-writer inventoryは今回変更しないsurfaceを数えるだけなので、供給が壊れていても緑のままである。`orchestrator/tests/test_backoff_sweep.py:90`、同`:100`、同`:235`、`orchestrator/tests/test_official_perf_closure.py:132`、`orchestrator/tests/test_ccbench_spawn_sites.py:751`、`orchestrator/tests/test_campaign.py:5364`

- **refuted / nit** — `effectuation-ignored` 負例は恒真ではなく、base追加時だけfamily赤を無視するM12を殺せる。ただしmissing-header修正の正例には数えられない。`s2-plan.md:158`、同`:210`

## 失敗の扱い

- **refuted / nit** — prepareのconfigure失敗とtimeoutは `MasstreeFetchContentError` に包まれ、target失敗も同様に例外となる。成功扱いへ倒れる分岐はない。`orchestrator/campaign/buildcache.py:2068`、同`:2074`

- **refuted / nit** — 計画どおりprepareは `evaluate_candidate` のcandidate-abort捕捉より前にあるため、失敗はWALの「関門通過」やcandidate abortにはならず、呼出し全体を停止する。baseとstock checkoutもcontext managerで閉じる。`orchestrator/campaign/screening_driver.py:555`、同`:562`、`orchestrator/campaign/patchharness.py:370`

- **real / should-fix** — prepare成功も関門失敗もWALへ記録されない。したがって誤って「通過」と記録されることはないが、prepare失敗はretryable abortにも分類されず、途中まで進んだworkload全体が例外終了する。これはP4の明示方針と一致するものの、成果物から原因を読むことはできない。`orchestrator/campaign/screening_driver.py:538`、同`:555`、同`:589`、`s2-plan.md:120`

## 観測者効果

- **real / must-fix** — per-genome prebuildは測定直前にconfigureとmasstree buildを行うが、baselineだけ `do_settle=True`、各候補は既定Falseである。候補のscreening benchはsettleなしで走るため、CPU温度、周波数、page cacheの影響がbaselineと非対称になり、TPSがscreening閾値を跨げばscreen-rejected集合とcertified選択が変わる。`orchestrator/campaign/backoff_sweep.py:258`、同`:267`、同`:297`、`orchestrator/campaign/screening_driver.py:484`、`orchestrator/campaign/pipeline.py:790`、同`:1665`

- **refuted / nit** — repositoryの共有 `build-variants` cacheへprepareが直接書く経路はない。prebuild directoryは一時base配下で、後続build cacheとは別である。`orchestrator/campaign/buildcache.py:2040`、`orchestrator/campaign/pipeline.py:1288`

- **real / nit** — subprocess環境は明示的にsanitizeされず継承され、CCBenchはccacheを自動検出する。今回の `masstree_build` はcustom Makefileなのでccache汚染を現物から断定できないが、環境変数とHOME側cacheが無関係であるという保証もない。成果物への具体的影響を示せないためmust-fixにはしない。`orchestrator/campaign/buildcache.py:3524`、`external/ccbench/CMakeLists.txt:20`

## 親 brief への反証

- **refuted / nit** — briefの静的前提のうち、現行gateにbaseがないこと、driver段baseがscreening前に閉じること、callerが4箇所でmanifest供給がbackoffの2箇所だけであること、prepareがmanifest必須であること、source rootがcanonicalであることには反証なし。`orchestrator/campaign/screening_driver.py:177`、`orchestrator/campaign/backoff_sweep.py:366`、同`:393`、`orchestrator/campaign/buildcache.py:2009`、`orchestrator/campaign/source_digest.py:2344`

- **real / should-fix** — briefの「screening赤の原因と一致」はscreening自身のstderrで直接確定されていない。保存evidenceにあるのは `preprocess-failed` までで、`config.h` の原文は主にrepro側から得たものだった。`brief.md:34`、`output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:17`

- **real / nit** — 「20秒程度」はrepo現物では裏取り不能で、D1666の一回測定の引用である。genomeごとの時間予測へ使うなら実測値ではなく概算と扱うべきである。`brief.md:47`、`verbatim-d1666.md:22`

- **refuted / nit** — P1は恒真ではなく、現行call graphではD1733のbackoff経路だけを選ぶproxyとして機能する。ただし将来manifestを導入したcallerにも自動発火するため、永続的なdriver identityではない。`brief.md:51`、`orchestrator/campaign/s6_sort_sweep.py:421`、`orchestrator/campaign/s8a_trigger_sweep.py:523`

- **real / must-fix** — P2のstock checkout入れ子自体は正しいが、per-genome配置によるbaseline/candidate settle非対称を見落としている。これは前節のとおりscreening成果を変えうる。`brief.md:58`、`s2-plan.md:90`、`orchestrator/campaign/backoff_sweep.py:267`

- **real / nit** — P3の `site=None` はdriver段で確定済みのsiteを転送するのではなく、各genomeで `current_site()` を再観測する。通常は同値だが「同じ解決済み値」という主張ではない。`orchestrator/campaign/p2_2.py:244`、`orchestrator/campaign/buildcache.py:1820`、`s2-plan.md:118`

- **refuted / nit** — P4の例外境界は現物と整合し、偽の緑やWAL abortへの誤分類はない。`brief.md:63`、`orchestrator/campaign/screening_driver.py:555`、同`:562`

## 一次資料の限界

- **real / must-fix** — 厳密な「現行の正規入口」をCLIまたはsanctioned launcherと読むなら、D1733の前提は実測されていない。probeは `backoff_sweep.main` ではなく内部のproduction `run_workload` を直接呼んでおり、既存A5 job bodyは `--screening` を付けない。従って「正規入口から到達した」という証拠は崩れる。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1005`、同`:1009`、`tools/pegasus/a5_second_boot_backoff_sweep.sh:589`

- **refuted / nit** — 一方、機能call graphの到達性は実証されている。CLI `main` は引数をそのまま `run_workload` へ渡す薄い入口であり、evidenceのtracebackは `run_workload → _run_screened_workload → measure_baseline → evaluate_candidate → screening gate` を示す。従ってコード上のscreening seamが到達不能という意味ではない。`orchestrator/campaign/backoff_sweep.py:451`、`output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:31`

- **real / should-fix** — observerはdriver段の最初のfamily admissionで停止するため、screening腕の赤record自体を保存していない。evidenceが直接示すのは例外messageの `preprocess-failed` までで、screeningでの `config.h` stderrは推論である。変更後は同じscreening CLI入口で、baseline stock腕のgreen recordまで実測しない限り修正の生死は閉じない。`tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:269`、同`:271`、`output/insights/2026-09-07_t2228-driver-gate-liveness/evidence/attempt-20260907b/sweep.json:20`

## 裁定パッケージ候補 (scope 外の real 所見)

- **real / should-fix** — D1666の既知限界より広い論点として、masstree autotoolsのCC/CXXがmanifestへ束縛されない。helper変更は本waveの編集scope外なので、compiler入力閉包の裁定候補に分離する。`orchestrator/campaign/buildcache.py:2048`、`external/ccbench/cmake/ThirdParty.cmake:69`

- **real / should-fix** — `backoff_repro` は歴史pin `dff0f1e` を要求し、`s1_direct_comparison` はverified freezeを入口で読む。D1733の禁止どおり、本waveでは供給、pin整合、freeze再生成をmust-fixにしない。`orchestrator/campaign/backoff_repro.py:48`、同`:70`、`orchestrator/campaign/s1_direct_comparison.py:1001`

## 総括

**must-fixは4点**である。

1. 「受理集合不変」という偽の不変条件を、意図した赤から先へ進む集合の明示へ直す。
2. prepared baseが実際に必要なheaderを供給し、実測で止まったstock baseline `-1` を通すload-bearing正例を追加する。
3. per-genome prebuild後にbaselineだけsettleされる観測者効果を解消または成果へ影響しないと実測で示す。
4. D1733の「正規入口から到達」を維持するなら、直接helper呼出しではなくscreening CLIまたはsanctioned launcherから再実測する。

判定式のskip化、赤recordの握り潰し、source rootの分裂、prepare失敗の偽通過は現物上refutedである。静的検査のみで、pytestや性能測定は実行していない。