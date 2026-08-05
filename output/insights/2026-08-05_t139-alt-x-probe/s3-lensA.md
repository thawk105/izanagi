判定は NO-GO です。投入前に解消すべき blocker が 4 件あります。

## 所見

[blocker] 性能 binary に検証専用 identity symbol を強制残存させており、規律 1 の「検証専用 metadata は完全除去」に反する。

根拠: [CLAUDE.md:58-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/CLAUDE.md:58)、[t139_positive_control.patch:27-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:27)、[s2-plan.md:134-142](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:134)、[nm-mode2.txt:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/nm-mode2.txt:795)。

影響: `modeX < stock` の throughput は、CC の差だけでなく `used + volatile + default visibility` で強制配置した検証用 `.data` symbol の link/layout 効果も含み、受理値を「CC 本来の差」と名乗れない。

最小修正: identity global を削除し、arm/macro は保存した `compile_commands.json` と `CMakeCache.txt` の外部 receiptから識別する。旧 raw では `main` 等の address は偶然同じだったが、将来 build の無影響保証にはならない。

---

[blocker] dependency を検査後も共有 `/work` working treeから直接 buildするため、pin 検査と実消費 bytes の間に TOCTOU がある。

根拠: 検査後に `GFLAGS_SOURCE=<root>/gflags` 等をそのまま使う設計 [s2-plan.md:169-180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:169)、現 build は source pathを直接 `cmake -S` へ渡す [t139_positive_control_probe.pbs:41-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:41)、ignored bytes を検査しないことも既知 [s2-plan.md:217-220](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:217)。

影響: 検査直後の変更または ignored/generated sourceを binary が取り込んでも `dependency-witness.tsv` は `clean=1` と記録でき、dependency identity、throughput、参照 pin が一致しなくなる。

最小修正: 検査した pinを `git archive <pin>` で job-local stageへ展開し、その immutable snapshotから buildする。tree SHA/archive SHAも witnessへ記録する。これで ignored bytes と検査後 working-tree 変更を同時に排除できる。

---

[blocker] 48 worker の「初回 commit」だけでは飢餓を検出できず、brief の liveness 保証が偽陽性になる。

根拠: brief は「飢餓を liveness で検出」と断言する [brief.md:64-65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:64)。marker は `local_commit_counts_ == 0` の初回だけ [t139_positive_control.patch:45-49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:45)、driver は各 marker が1回あったかだけを見る [t139_positive_control_probe.sh:49-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:49)。worker は終了まで transaction を反復する [runner.hh:190-194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/common/runner.hh:190)。

影響: 各 worker が冒頭に1回だけ commitし、その後1 workerが mutex再取得に負け続けても 288/288 となり、飢餓した modeXを受理できる。

最小修正: liveness-only buildで複数の非重複時間窓ごとに per-worker commit deltaを出し、全 workerが各窓で進捗することを事前固定する。少なくとも終端 countだけでなく時間窓を持たせる。

なお「恒真」という疑い自体は refuted。marker は実際の `commit()` 成功後にしか出ず、0 commit workerは現検査でも落ちる。問題は初回後の飢餓を見ないこと。

---

[blocker] 段2の stripe 関数は追補が必須化した先頭窓を混ぜず、同一長・共通 suffix 族を完全に1 stripeへ潰す。

根拠: 追補は先頭窓・末尾窓・長さを必須とする [brief-addendum.md:44-46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief-addendum.md:44)。提案コードが読むのは末尾最大8 byteと長さだけ [s2-plan.md:50-71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:50)、総括も `bounded suffix mixer` と明記する [s2-plan.md:382-383](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:382)。

独立再計算では、提案式の YCSB 0〜99,999 は `50051/49949` だが、`warehouse/10000..99999/district` は `0/90000`。末尾8 byteと長さが全件同じだからである。

影響: 現 YCSB の分割自体は均等だが、実装 bytes が親 briefで事前定義した modeXと一致せず、generic `transaction.cc` 上では modeXが実質 mode1になる record族を残す。

最小修正: boundedな先頭窓と末尾窓と長さを混ぜ、YCSB、空 key、共通 suffix・同一長、複数 Storage の固定 fixtureを事前登録する。

---

[major] `nm-witness.tsv` は `ADD_ANALYSIS` 不在を検査せず、trace symbol 0件も「trace code完全除去」の十分証拠ではない。

根拠: witness列と条件は mode symbol と `izanagi_trace` だけ [t139_positive_control_probe.sh:34-45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:34)。`ADD_ANALYSIS` は別の CMake値で、既定0・liveのみ1 [Options.cmake:14-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/cmake/Options.cmake:14)、[t139_positive_control_probe.sh:35-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:35)。

影響: performance armを誤って `ADD_ANALYSIS=1` で buildしても現 nm条件は通り、counter処理込み TPSを受理できる。

最小修正: `transaction.cc` と `ccbench_common` の実 compile argvを保存し、performanceは `TRACE=0/ADD_ANALYSIS=0`、livenessは `TRACE=0/ADD_ANALYSIS=1` を exact検査する。nmは補助証拠に下げる。

---

[major] 親 brief の「CASを1回だけ実行」は stock semantics と一致しない。

根拠: briefの断言 [brief.md:64-65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:64) に対し、stockは内側の無限 loopでCAS失敗後に再試行し得る [transaction.cc:158-184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/cc/silo/transaction.cc:158)。CASは失敗時に `expected` を参照更新する [atomic_wrapper.hh:63-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/include/atomic_wrapper.hh:63)。段2自身は正しく「loop iteration当たり1回」と書いている [s2-plan.md:121-125](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:121)。

影響: 「transaction/record当たり総計1回」を凍結すると、stock-equivalent実装が不変条件違反になるか、実装子が再試行を削ってabort/取得挙動を変える。

最小修正: 「stock loop 1 iteration当たり同じCAS式をちょうど1回。追加CASなし。動的再試行回数はstockと同じ」に統一する。

---

[major] `policy.json` の pin閉包は結論こそ安全側だが、live pin・歴史 snapshot・commit相対 identityの分類が不完全。

根拠:

- 実際の live current-binding は rung1 JSONとvalidator [silo_ladder_rung1.json:41-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:41)、[silo_ladder_rung1.py:3511-3531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/orchestrator/campaign/silo_ladder_rung1.py:3511)。
- 親の列挙にない T293 の2成果物も同じ policy SHAを固定する [probe.json:6-12 (881946)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t293-perf-site/0_881946.nqsv/probe.json:6)、[probe.json:6-12 (881960)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t293-perf-site/0_881960.nqsv/probe.json:6)。producerも expected SHAを比較する [t293_perf_site_probe.py:194-224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t293_perf_site_probe.py:194)。
- T126は各 receiptのcommit blob群とlive policyを照合する commit相対 identity [identity.py:130-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/orchestrator/qualification/identity.py:130) であり、repository-wideの恒久SHA定数ではない。
- registryは所在 inventoryにすぎない [tools/pegasus/README.md:15-21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/README.md:15)。`FROZEN_MANIFEST`のexact 23件にも policyはない [test_frozen_artifacts.py:38-85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/orchestrator/tests/test_frozen_artifacts.py:38)。

影響: 今回はpolicy無編集なので bytesは変わらないが、将来の移行時にT293参照を落とし、実在receiptが0件のT126まで「恒久凍結」と過大評価して一般復旧を不必要に封鎖する。

最小修正: `rung1=live current binding`、`T293=歴史 snapshot`、`T126=receipt/commit相対 identity（現receipt 0）`、`registry=inventory`、`FROZEN_MANIFEST=対象外` の表へ直す。role/key名、review ledger、generator-source hashによる追加pinは独立検索で見つからなかった。

---

[nit] 親 brief の権威根拠が D126 の「未裁定」のままで、既に成立した D162 を引いていない。

根拠: briefはD126だけを根拠にする [brief.md:19-20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:19)。現行D162はproducerによる適格性宣言を禁止し、独立validatorだけを権威と確定済み [decisions.md:8003-8025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/docs/decisions.md:8003)。ただし機械化は0/9でconsumer hookも未成立 [decisions.md:8049-8055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/docs/decisions.md:8049)。

影響: 現受理集合は変わらないが、段7で「権威境界未裁定」と誤記したり、`verdict.tsv` を将来の適格性状態として流用する余地が残る。

最小修正: D162を現行権威として明記し、`verdict.tsv` はこのstudyだけの内部判定で、qualification receipt/decision/consumer入力ではないと固定する。

## 独立裏取り・refuted

- refuted — exactなmodeX wrapperがSiloのserializabilityを変える疑い。CASのlvalue・`expected`・`desired`はstockと同一で、mutex外のvalidation・epoch取得・write/unlockも残る [transaction.cc:170-192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/cc/silo/transaction.cc:170)、[transaction.cc:437-492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/cc/silo/transaction.cc:437)、[transaction.cc:557-682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/cc/silo/transaction.cc:557)。mutex保持中は非blocking CASだけで、record lock待ちはなく、mutexも一つしか保持しないため待ちcycleは構成されない。残る問題は上記の飢餓検査。

- refuted — 空 key、異なるStorage、可変長そのものがstripeの正しさを壊す疑い。提案式は値だけから決まる安定写像で、collisionしても最終排他はrecord CASが担う。壊れるのはserializabilityではなく、共通suffix族での性能機序。

- 限定して支持 — 旧patchはsubmodule `d706650…`に適用可能。read-only相当の `git apply --check` はrc=0だった [CCBench HEAD:1](/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-t139-alt-x-probe/modules/external/ccbench/HEAD:1)、[t139_positive_control.patch:1-8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:1)。これは未作成のmodeX patchのcompile成功までは証明しない。

- refuted — `/home/...` 不在がprobeだけという疑い。`/home`は共有FS [pegasus-runbook.md:461-464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/docs/pegasus-runbook.md:461) で、rung1もpolicyの絶対pathを直接読む [silo_ladder_rung1.sh:441-473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/silo_ladder_rung1.sh:441)。一般再現経路にも掛かるという親の限定は正しい。

- refuted — YCSB key表現の疑い。`SimpleKey<8>`を使い、`assign_as_bigendian`で生成する [ycsb.hh:44-48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/include/ycsb.hh:44)、[ycsb.hh:113-120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/include/ycsb.hh:113)、[workload.hh:17-27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/include/workload.hh:17)。低位byteは末尾側で正しい。

- refuted — J=1からcluster間分散を推定できるという疑い。実体はrequest 877859の1 jobで、5 repは同job内反復にすぎない [decisions.md:6196-6207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/docs/decisions.md:6196)、[throughput.tsv:1-31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/throughput.tsv:1)。

- 限定して支持 — gflags/glog cloneは現在detached pin一致・cleanで、repo worktreeにも差分はなかった [gflags HEAD:1](/work/1/SFC/tanab/izanagi-thirdparty-deps/gflags/.git/HEAD:1)、[glog HEAD:1](/work/1/SFC/tanab/izanagi-thirdparty-deps/glog/.git/HEAD:1)、[policy.json:36-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/policy.json:36)。ただし一般`verify-deps`/rung1は未復旧であり、投入時のsnapshot raceはblockerのまま。

- refuted — login側のfalse-sharing観測が構造的に誤りという疑い。libstdc++11のmutexは40-byte native mutexを持ち [std_mutex.h:55-67](/usr/include/c++/11/bits/std_mutex.h:55)、glibc x86-64のmutex sizeは40・alignment memberはlong [pthreadtypes-arch.h:23-27](/usr/include/x86_64-linux-gnu/bits/pthreadtypes-arch.h:23)、[pthreadtypes.h:67-72](/usr/include/x86_64-linux-gnu/bits/pthreadtypes.h:67)。前回compute binaryのgateも64-byte境界に配置されていた [nm-mode2.txt:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/nm-mode2.txt:115)。原因帰属までは未証明という親の留保も正しい。

- 限定して支持 — 前回compute buildもGNU 11.4だった [configure-mode2.log:1-16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/configure-mode2.log:1)。したがってlogin値との乖離は前回jobでは観測されないが、将来allocationへの一般化はできない。`alignas(64)` wrapper＋stride static_assertはnamespace-scope配列にも効き、workerからの初回利用はmain開始後なのでstatic初期化順序cycleもない [s2-plan.md:40-48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:40)、[runner.hh:172-194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/external/ccbench/common/runner.hh:172)。

- refuted — probe outputが既にIzanagiのpromotion gateとして消費される疑い。production consumerはなく、現権威文書自身がpromotion consumer 0件・機械化0/9とする [decisions.md:8035-8055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/docs/decisions.md:8035)。内部verdictを将来流用しないことが条件。

## 総括

- 判定: NO-GO。検証用identityの性能binary残存、dependency snapshotのTOCTOU、飢餓の偽陽性、stripe案と親追補の不一致がある。
- blocker件数: 4件。
- refuted: exact wrapperのserializability/deadlock破壊、stripe collisionによる正しさ破壊、liveness検査の恒真性、旧patch不適用、YCSB key表現誤認、J=1でのcluster分散推定、既存promotion consumerの存在。
- 裁定パッケージ候補: probe外のgflags/glog一般調達をimmutable snapshot契約として整備するか、共有policyのlocatorを正式rebindするか。D162のqualification mechanizationは発火条件未成立のため引き続きscope外。
- 実走: pytest、build、qsub、性能計測は実行しておらず、緑は主張しない。