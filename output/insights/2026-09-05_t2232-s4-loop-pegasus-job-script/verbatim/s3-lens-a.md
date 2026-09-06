## 所見

1. 対象: `s2-plan.md:13-17,45-71,113-132`、`orchestrator/campaign/loop.py:171-215`、`orchestrator/campaign/reservation.py:120-175,223-282`、`tools/pegasus/paper_story_a2_certification.sh:123-228`。プランは `PBS_JOBID` だけを要求し、Pegasus 契約が必要とする 8 個の `IZANAGI_RESERVATION_*`、qstat 由来の開始時刻と期限、boot ID、job script hash を構築しない。また `<output-base>/env/pegasus/claims` の事前 provisioning もない。`pegasus` 契約は `single_process=True` なので、有効な bnode 上でも `reservation.read_binding()` または claim-root 検査で必ず停止する。しかも prebuild receipt は driver 起動前に作られるため、campaign が一件も生成されない失敗走に prebuild receipt だけが残る。成果物への影響: `masstree-prebuild-receipt.json` と非零 `compute-result.json` だけが残り、certified 値、WAL、campaign proof 参照は生成されない。重大度: must-fix。

2. 対象: `s2-plan.md:21,113-134,287-306`、`orchestrator/campaign/p3_s4_loop.py:1525-1539`、`orchestrator/campaign/buildcache.py:881-892,1295-1380,2440-2458,2663-2696`、`external/ccbench/cmake/ThirdParty.cmake:35-55,106-135`。lowercase proxy は継承環境のまま CMake とその子 Git clone に届くが、`_fetchcontent_git_environment()` は clone 用ではなく、既にある masstree の receipt 観測時だけ使われる。現 p3 は FetchContent base、SOURCE_DIR、dependency receipt、archive hashを一つも `build_v2` へ渡さないため、clone 全体の source manifest は build identity に入らない。masstree と googletest は full commit だが、mimalloc は可変な `v2.3.2` tag であり、さらに `$HOME` の global Git config も閉じられていない。成果物への影響: 同じ campaign ID、genome、CCBench pinでも取得した mimalloc bytesと perf 値が変わり得る。binary SHAは結果を識別するが、dependency source の由来は閉じない。重大度: must-fix。

3. 対象: `s2-plan.md:121-132`、`orchestrator/campaign/buildcache.py:1212-1218,1934-1971,2663-2696`、`external/ccbench/cmake/ThirdParty.cmake:66-76`。プランが「unset する全集合」とする環境は閉じていない。特に Autoconf が読む `CONFIG_SITE` が残り、masstree の `./configure` を変更できる。`make`、`ar`、`ranlib`、`git` も CMake toolchain manifestの `cc/cxx/cmake` 外で、path、hash、argvのいずれも build identityやreceiptへ束縛されない。condition gate の CMake/compiler 証拠は、この後の ExternalProject 子 tool を束縛しない。成果物への影響: 同じ configure argvとbuild identityから異なる `config.h`、archive、perf binaryが生成され、受理値が変わり得る。重大度: must-fix。

4. 対象: `s2-plan.md:45-69,136-149,302-306`、`orchestrator/campaign/buildcache.py:823-878,2009-2085`、`tools/pegasus/fetch_third_party.py:360-431,605-679`。prebuild は staged source の canonical directory 性しか検査せず、hydrate receipt、HEAD、tracked/ignored clean、各 source の byte manifestを照合しない。そのまま masstree source 内で `bootstrap.sh`、`configure`、`make` を走らせ、hydrate が要求する clean sourceを汚す。既存の `config.h` と archive があれば fresh build dirでも targetが no-opになり得るため、receiptの build argvは「この環境で生成した」証拠にもならない。receiptには archive hash、source manifest、hydrate receipt hash、toolchain manifestがない。成果物への影響: 任意に変更された staged sourceや以前の生成物から `config_h_sha256` が作られ、durable hydrate rootも再利用不能になる。重大度: must-fix。将来 consumerへ配線するなら、3 sourceのpin付きmanifest、hydrate receipt hash、config/archive hash、toolchain identity、全 argvを一つのreceiptへ束縛し、そのreceipt digestをbuild identityへ入れて消費直前にも再照合する必要がある。

5. 対象: `s1-brief.md:24`、`s2-plan.md:19-22,121-132,298-310`、`orchestrator/campaign/layout.py:370-409,450-482,577-597`。job は `IZANAGI_OFFICIAL_OUTPUT_ROOT` を unset するが、p3 の use class は `exploration` であり、実際に読むのは `IZANAGI_EXPLORATION_OUTPUT_ROOT` である。後者が投入環境に残れば、P4の repo-local outputではなく外部 rootへ切り替わるか、git ancestor検査で停止する。成果物への影響: campaign root、WAL、claim、digestの絶対参照がP4の想定と異なる場所へ移るか、何も生成されない。重大度: must-fix。

6. 対象: `s2-plan.md:31-36,71,93-109,113-132`。名目上 shim directoryに作るのは `python3` 一本だけで、`cmake/c++/gcc/make/git` が混入する直接経路はない。一方、選択した Python の realpath、内容 hash、versionは compute result、campaign identity、receiptのどこにも束縛されない。また起動は `-B` だけなので、`PYTHONPATH/PYTHONHOME` の unsetだけでは `$HOME` の user-site、`sitecustomize`、`usercustomize` を隔離できない。成果物への影響: 同じHEADとargvでも Python実体またはuser-siteによりdriverの判定と生成WALが変わり、事後にどのinterpreterで受理したか復元できない。重大度: must-fix。

7. 対象: `s2-plan.md:220-235,262-285`、`orchestrator/campaign/buildcache.py:3460-3480`。contract testのshim変異は `cmake/c++/gcc` だけで、`git`、`make`、`nm` を殺さない。特に perf trace検査は bare `nm` をPATHから起動するため、shim内の `nm` が空出力を返すと既裁定のtrace/strip穴を再発できる。production sourceを「python3以外のentryがshim dirに存在しない」とruntimeで検査する契約も計画されていない。成果物への影響: `git` shimならpin/clone source、`nm` shimならtrace-disabled受理集合が変わり、誤ったbinaryが性能値へ到達する。重大度: must-fix。

## 親 brief への指摘

P1の「現行 p3 に消費 seam がない」は `p3_s4_loop.py:171-190,1525-1539` と一致する。ただし「無害な死んだ経路」ではない。prebuildの成功可否がdriver起動を支配し、durable staged sourceを汚し、未束縛入力からreceiptを発行する。現 p3 の性能値へ config.h bytes が直接届かない、という狭い主張だけが正しい。

P2の「cold cloneにはproxyが必要」は静的には妥当だが、「同じliteralを写す」ことはdependency identityの証明ではない。compute Gitがproxyをhonorするか未測定であることに加え、mimalloc tag、global Git config、clone source manifestが未束縛である。

P3の `03:00:00` は運用上の見積りであってコード上の上限ではない。`p3_s4_loop.py:865-883,2043-2083` の3600秒判定はiteration前後にしか発火せず、開始済みbuildを止めない。generic `build_v2` のtimeoutも既定 `None` であるため、「3600秒 + build/verifyが23分以下」という一般化は成立しない。既測23分はcold proxy clone、condition gateの複数configure、新prebuildを含むこのjobの上限ではない。

P4は、checkoutが `/dev-wave-jobs/.../submit-tree` のように `.claude/worktrees` または `.codex/worktrees` を含まなければ、repo-local `output/exploration/...` は `_reject_worktree_container` に拒否されない。逆に「detached checkout」という性質だけでは足りず、配置pathがworktree container内なら拒否される。さらにjobはdetached状態もprimaryでないことも機械検査せず、README契約だけである。

site写像自体には矛盾はない。`site_policy.py:30-46,66-84` は `bnode` hostnameだけで `PEGASUS_COMPUTE` とし、`PBS_JOBID` とNQSV証拠は分類に使わない。したがってshell側host gateを通った正常なbnodeがjob環境のsanitizeによって `OTHER` へ倒れる経路はない。hardware attestationはhostnameではなくCPU、affinity、NUMA、clock、process visibilityを検査する。

argvにも `--no-build`、env-tag、trace macro、verifier変更はない。`--allow-coder-derived-build` は登録済みCLI authorityを発行し、pipelineが `trace=True` と `trace=False` を別buildに固定する。ただし所見7のverifier executable差し替えをcontract testが閉じていない。

親が引用する「shimまで置いて5226 passed」は既存test dispatchでPython子process問題が解消した実測であり、この新jobのreservation、attestation、proxy clone、prebuild、output layoutが動くことまでは一般化できない。

## scope 外だが real な所見

`p3_s4_loop.py:200-204,1540-1555,2266-2289` ではcondition gate recordはiterationの戻り値に載るが、CLIはそれをdurable artifactとして保存しない。D1586によりCMake path、hash、configure argvはgreen record内に存在しても、後日のcampaign consumerが参照できるproof chainには残らない。p3所有の裁定パッケージ候補である。

`--isolate-worktree` の生成先は `patchharness.py:346-378` により `TMPDIR` 配下であり、scratch pathがsource/build evidenceへ現れる一方、`USER` とscratch baseの所有、symlink componentはjob計画で検査されない。現状は同一user内の運用前提で、hardening候補である。

prebuildの `cmake --build` は同期実行であり、完了後にp3が `_assert_single_tenant` を呼ぶ。pgrep patternも `ycsb_.*\.exe` だけなので、通常のcmake/make子processが直前検査へ誤検出される順序問題はない。ただしplain pgrepがcanary付きprobeでない既知限界は残る。

## 総括

最大の欠陥はreservation bindingとclaim-root provisioningの完全欠落であり、現プランのjobは正常なPegasus計算ノードでもcampaign開始前に停止する。
次点は、実loopが未束縛のnetwork FetchContentへ戻り、prebuildだけが未検証sourceを破壊的に触る二重経路である。
親は段4で、検証済みstaged sourceを実build identityへ配線するか、死んだprebuildを削除してnetwork経路を別途attestするかを必ず裁定すべきである。
あわせてexploration output rootの扱いと、detached checkout契約を機械強制するかREADME運用に留めるかを確定すべきである。
本回答は静的検査のみで、pytest、build、qsubは実走していない。