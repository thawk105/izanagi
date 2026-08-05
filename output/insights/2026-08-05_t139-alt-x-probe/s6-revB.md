判定は **NO-GO**。静的検査で blocker 5 件、major 2 件です。pytest・build・self-check 実行・qsub・性能計測は行っていません。

## V/P 対応表

| 項目 | 裏取り | 根拠 |
|---|---|---|
| V-1.1 | 合致 | `tools/pegasus/probes/t139_positive_control.patch:8-12` |
| V-1.2 | 合致 | `tools/pegasus/probes/t139_positive_control.patch:20-30`、`tools/pegasus/probes/t139_positive_control_probe.sh:299-308` |
| V-1.3 | 合致 | `tools/pegasus/probes/t139_positive_control.patch:24-29` |
| V-1.4 | 合致 | `tools/pegasus/probes/t139_positive_control.patch:31-58` |
| V-1.5 | **不一致**。境界が走行開始でなく最初の成功 commit 起点 | `tools/pegasus/probes/t139_positive_control.patch:68-77`、`external/ccbench/common/runner.hh:294-298` |
| V-1.6 | 合致 | `tools/pegasus/probes/t139_positive_control.patch:90-113`、`external/ccbench/cc/silo/transaction.cc:158-183` |
| V-2.1 | 合致 | `tools/pegasus/probes/t139_positive_control_probe.sh:268-309` |
| V-2.2 | **部分**。恒真ではないが `transaction.cc` しか検査しない | `tools/pegasus/probes/t139_positive_control_probe.sh:191-211`、`:278-295` |
| V-2.3 | 合致 | `tools/pegasus/probes/t139_positive_control_probe.sh:343-357` |
| V-2.4 | 合致。30 cell exact-one | `tools/pegasus/probes/t139_positive_control_probe.sh:56-100` |
| V-2.5 | 構造検査は合致。窓の意味は V-1.5 により不一致 | `tools/pegasus/probes/t139_positive_control_probe.sh:30-53`、`:328-336` |
| V-2.6 | 合致 | `tools/pegasus/probes/t139_positive_control_probe.sh:214-232`、`:315-327`、`:382-383` |
| V-2.7 | witness 出力自体は合致 | `tools/pegasus/probes/t139_positive_control_probe.pbs:57-89`、`:119-124` |
| V-2.8 | **不一致**。副次診断の parse が primary を gate する | `tools/pegasus/probes/t139_positive_control_probe.sh:366-377` |
| V-2.9 | fixture は静的に合致。実走結果は未確認 | `tools/pegasus/probes/t139_positive_control_probe.sh:103-158` |
| V-3.1 | 合致 | `tools/pegasus/probes/t139_positive_control_probe.pbs:50-71` |
| V-3.2 | **部分**。通常の working-tree TOCTOU は閉じるが replace refs を許す | `tools/pegasus/probes/t139_positive_control_probe.pbs:69-87` |
| V-3.3 | 合致 | `tools/pegasus/probes/t139_positive_control_probe.pbs:35-46` |
| V-3.4 | cap 算術は合致 | `tools/pegasus/probes/t139_positive_control_probe.pbs:16-25`、`:128-148` |
| P-A | **不一致**。hash は実行時記録だけで、CCBench/third-party の消費 bytes が pin されない | `tools/pegasus/probes/t139_positive_control_probe.sh:234-252`、PBS`:108-123` |
| P-B | 合致 | `tools/pegasus/probes/t139_positive_control_probe.sh:343-357` |
| P-C | **不一致**。V-1.5 と V-2.2 の穴を継承 | patch`:68-77`、driver`:191-211` |
| P-D | **不一致** | `tools/pegasus/probes/t139_positive_control_probe.sh:366-377` |
| P-E | **未充足**。自己申告の「部分実装」は正しい | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s5-impl.md:123-125` |
| P-F | 親責務として合致。非適格ラベルあり | `tools/pegasus/probes/t139_positive_control_probe.sh:86-99`、`:235-246` |
| P-G | **未充足**。自己申告どおり部分実装 | `tools/pegasus/probes/t139_positive_control_probe.pbs:28-32` |

## 所見

[blocker] [V-1.5/P-C の二窓は「走行前半・後半」ではない。`shared_start` は runner の start barrier ではなく、全 worker 中最初の成功 commit で初期化される] [根拠 `tools/pegasus/probes/t139_positive_control.patch:68-77`、`external/ccbench/common/runner.hh:294-298`]  
[成果物影響] 真の前半に commit 0 の worker が、遅れた境界の前後で後半に2回 commitすれば 576/576 となり、不正な modeX が P-C を通る。  
[最小の直し方] runner の `storeRelease(start, true)` と同じ共有時刻を liveness buildへ渡し、固定 `[0,1500ms)` / `[1500,3000ms)` の per-worker delta を検査する。

[blocker] [P-G は統合 commit・実行中 PBS・消費した repo bytes を束縛していない。検査対象はその時点の working tree 上の3 fileだけで、読み込む `policy.json`、CCBench、事前登録文書は対象外] [根拠 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:156-158`、`tools/pegasus/probes/t139_positive_control_probe.pbs:28-46`、`tools/pegasus/probes/t139_positive_control_probe.sh:238-252`]  
[成果物影響] dirty policyで別pinを選ぶ、dirty CCBenchをbuildする、qsub後にHEADやdriverを更新する、外部コピーのPBSを投入する、のいずれでも preregistration witness と実行 bytes・TPS・verdict が分離する。  
[最小の直し方] `RUN_COMMIT` を一度だけ固定し、事前登録 blob・policy・patch・driverをその commitからjob-local bundleへ展開して使用する。実行中PBS bytesも commit blob/hash と比較し、current working treeを再参照しない。

[blocker] [P-A/V-3.2 の pin 閉包が不完全。CCBenchはHEADを記録するだけでclean/pin検査なし、third-partyは検査後にmutable working treeを `cp -a`、gflags/glogはreplace refsを拒否せず `git archive <pin>` する] [根拠 `tools/pegasus/probes/t139_positive_control_probe.sh:238-252`、`tools/pegasus/probes/t139_positive_control_probe.pbs:108-123`、`:69-83`、既存hardening `tools/pegasus/fetch_third_party.py:343-389`]  
[成果物影響] witness上のHEAD/pinを維持したまま別treeまたはignored/raced bytesをbinaryへ混ぜ、throughputと受理結果を変更できる。  
[最小の直し方] 全Git入力でreplace refs・index特殊bit等を拒否し `--no-replace-objects` を使う。CCBenchは既知のexport-ignore問題があるため、正本どおりexact commitのtracked-file tar snapshotを使う (`docs/pegasus-runbook.md:567-568`)。third-partyも同じ方式で固定する。

[blocker] [P-E の失敗閉表がrc・state artifactとして実装されていない。科学的false、row構造異常、通常のcommand failureがrc=1へ衝突し、rc=6/7も性能開始前後を区別しない] [根拠 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:141-148`、`tools/pegasus/probes/t139_positive_control_probe.sh:85-100`、`:328-336`、`:370-390`、`tools/pegasus/probes/t139_positive_control_probe.pbs:48`、`:107`]  
[成果物影響] exact falseやliveness rejectをinfra failureとして再投入したり、性能結果を含むpost-run screen failureを「開始前infra」として置換でき、採用raw集合とverdictが変わる。  
[最小の直し方] 性能開始前に永続phase markerを書き、EXIT trapで閉表のterminal stateをatomic発行する。validなtrue/false、liveness reject、pre-performance infra、post-performance failureを別stateにし、falseをscheduler上の汎用nonzero failureへ流さない。

[blocker] [P-D/V-2.8 のattempt/abort診断が「判定に使わない」契約に反して必須gateになっている] [根拠 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:138-139`、`tools/pegasus/probes/t139_positive_control_probe.sh:366-375`]  
[成果物影響] primary TPSが正常でも副次行の欠落・形式差だけでthroughput rowが捨てられ、exact verdictなしの再投入候補へ変わる。  
[最小の直し方] TPS rowをprimaryとして独立確定し、diagnostic parse失敗は `NA` とreasonを副次TSVへ残すだけにして、verdictのrcへ接続しない。

[major] [V-2.2 は恒真ではないが、「compile argv exact」の証拠面が不足する。runtime gateはCMake生成の `compile_commands.json` を読む一方、対象は `transaction.cc` 一件だけで、`ccbench_common` のargvを保存・検査しない] [根拠 `tools/pegasus/probes/t139_positive_control_probe.sh:191-211`、`:278-295`、ADD_ANALYSIS ABI契約 `external/ccbench/CMakeLists.txt:56-66`]  
[成果物影響] shared `Result` layout側だけADD_ANALYSISが食い違ってもcompile receiptが通り、ODR不整合・crash・TPS変化をP-Cが見逃す。  
[最小の直し方] `transaction.cc` に加えて `common/result.cc` と `common/util.cc` の実compile entryをexact-oneで保存・検査し、summary TSVは期待値のechoでなく検査したargvから生成する。

[major・scope外/親運用] [複数submission/file-drawerはコードで塞がれていない。ただし「全ID報告・予備1本まで」は親義務として明記済みで、未記載という疑いはrefuted] [根拠 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:144-148`、`s5-impl.md:123-125`、`tools/pegasus/probes/t139_positive_control_probe.pbs:144-148`]  
[成果物影響] ID台帳がなければ複数jobから都合のよいrawだけを選び、J=1の正例価値を失わせられる。  
[最小の直し方] 親が結果閲覧前に `(submission ID, commit, 3 hash, replacement-of, reason)` のappend-only台帳を作り、全IDを段7記録へ含める。恒久対応はsubmit/collect wrapperの裁定パッケージとする。

## Refuted・静的確認

- V-2.2の「driver自身が作った文字列との比較で恒真」はrefuted。実走経路はCMake生成のcompile databaseを読む (`tools/pegasus/probes/t139_positive_control_probe.sh:198-211`)。文字列fixtureを使うのはself-checkだけ (`:133-136`)。
- V-2.4は30行だけでなく全 `(workload, arm, rep)` exact-oneを検査する (`:79-84`)。
- V-2.5は576行と全cell exact-oneを検査する (`:45-51`)。残る欠陥は行数でなく窓の起点。
- workload argv、rep、schedule、strict inequalityをruntime env/flagで変更できる疑いはrefuted (`:311-314`、`:343-361`、`:90-98`)。
- gflags/glogの通常のworking-tree TOCTOUはarchive snapshotで閉じている (`tools/pegasus/probes/t139_positive_control_probe.pbs:69-87`)。残るのはreplace-ref等のGit identity hardening。
- 予算超過の疑いはcap算術上refuted。`10 + 20 + 2×102 + 20 + 3×72 + 420 + 2400 = 3290 < 3300 < 3600`。driver内も `2×120 + 30 + 6×(60+180+10) + 6×30 + 30×15 = 2400`。dependency build 420秒を含む (`PBS:128-148`、driver`:248-250`、`:283-286`、`:323-324`、`:361-362`)。これは実時間の緑ではない。
- self-checkとTPCC/BoMB/SBoMB smokeは1時間jobに含まれない。V-2.9はfixture保有なので違反ではないが、generic compile smokeは親が別途計算ノードで行う必要がある。
- gflags/glog archiveで `.git` や生成versionが欠ける静的疑いはrefuted。versionはCMakeListsに直接固定される (`/work/1/SFC/tanab/izanagi-thirdparty-deps/gflags/CMakeLists.txt:89-97`、`.../glog/CMakeLists.txt:1-18`)。build実走は未確認。
- 旧rawをparseする live code consumerは、`orchestrator/`・`tools/`・`hooks/` の独立検索で0件。歴史docsは明示的に旧jobを参照するだけで、旧raw bytesは不変。現決定も昇格consumer 0件とする (`docs/decisions.md:8035-8040`)。
- 新rawには `engineering_screen_J1_uncalibrated_nonqualification` が `verdict.tsv` とpreregistration witnessの双方へ出る (`tools/pegasus/probes/t139_positive_control_probe.sh:86`、`:237`)。将来consumer不在も `docs/decisions.md:8049-8055` と一致する。
- scopeは合致。`git status --ignore-submodules=none` と `git diff --stat` は指定3 fileのみ、docs・policy・output・submodule差分は0。`git diff --check`、両shellの `bash -n` はrc=0。

## 総括

- (a) **NO-GO**
- (b) blocker **5件**
- (c) refuted: compile argv恒真、30-row/576-cellのexact-one欠如、通常のgflags/glog working-tree TOCTOU、cap総和超過、runtime envによるargv/rep/schedule/閾値変更、旧rawのlive code consumer存在、gflags/glog archiveの静的source欠落
- (d) 申告と実装が食い違った項目: **V-1.5、V-2.2、V-2.8、V-3.2、P-A、P-C、P-D**。P-E/P-Gは自己申告も「部分実装」なので申告自体は正しいが、投入契約は未充足
- (e) 裁定パッケージ候補: **submission横断のappend-only ID/retry controller**、全probe共通の**commit-bound immutable source bundle**、third-party/CCBenchのhardened snapshot共通化、D162 validator/consumer機械化。