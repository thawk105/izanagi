結論は **NO-GO**。F-9 が M1 を既に反証しているだけでなく、P2 の group-atomic、P3 の gate/rc 定義、段 2 の snapshot・帰属・併合要件にも、受理集合を証明できない穴が残る。

## Critical 1 — I1 は親案では不足、段 2 案では循環定義

- **(a) 主張:** 親 P3(a)〜(d) は collection 被覆しか証明せず、順序、import、session fixture、process-global state、共有 filesystem を保存しない。P3(e) と段 2 の `∀X,p,h: AM=A0` は数学的には十分だが、守りたい結論そのものであり、機械的 witness がない。真に全称成立するなら反例は論理的に作れないが、提示された観測項目だけを満たす走行には反例を作れる。

- **(b) 根拠:** P3 は集合一致・nodeid 一意・gate・`max(rc)` を条件にする [brief.md:49–54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/brief.md:49)。現実には同じ nodeid が full では緑、分割では import error になった [facts.md:80–91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:80)。段 2 も collection 被覆では session/import 副作用を証明できないと認める [s2-plan.md:47–64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:47)。

- **(c) 失敗シナリオ:** 既存の `test_reflux_ir.py` と同型の collection-time producer A が validator/module global を厳格化し、consumer B が不正 main を拒否するとする。canonical full collection は A→B で B が赤、file shard では B の process に A がなく既定の緩い状態で緑になる。collection の集合、割付け一意性、gate、全 rc=0 は満たす。P3(e) は破れているが、これを判定する機構がないため「成立」と誤認できる。F-9 は逆向きの canonical-green/shard-red を実証済みであり、false-green 方向も同じ未隔離 state channel から作れる。

- **(d) 自己判定:** collection/session 非同値は **real**。false-green の具体的方向は **speculative だが実行可能**。段 2 の全称式そのものは正しく、問題は operationalization 不在。

- **(e) 是正案:** I1 の証拠を boolean equality でなく、固定 snapshot に対する `(ordinal, nodeid, report phase, exact outcome, skip/xfail種別・理由, side-effect digest)` の観測 trace refinement とする。有限 probe は「I1 証明」でなく、反例探索と明記する。partition 非依存性を静的に証明できない suite は canonical 全走へ fail-closed fallback する。

## Critical 2 — 段 2 の「同一 X」は今回の干渉状態を識別できない

- **(a) 主張:** 段 2 が挙げる tree/submodule fingerprint では、テストが実際に読む ignored output や既存 untracked file の内容を束縛できない。したがって `A0(X)` は同じ宣言上の `X` に対して複数の結果を持ち、関数として未定義になる。

- **(b) 根拠:** 段 2 の X は SHA、Git 状態、config、version、selection 関連 env を挙げる [s2-plan.md:23–30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:23)。現行 fingerprint は `git status`、tracked diff、submodule status/diffだけ [run_tests.py:1537–1609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:1537)。一方、dispatch receipt の書き先は Git ignore 対象 [\.gitignore:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/.gitignore:25) で、dispatcher は既定でそこへ書く [dispatch_compute.py:1313–1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:1313)。`_real_output_snapshot()` は ignored を含む `output/` 全体を hash する [test_s8b_floor_campaign.py:432–446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8b_floor_campaign.py:432)。今回、この差が base と shard を実際に赤くした [measurements.md:86–95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:86)。

- **(c) 失敗シナリオ:** 全 shard が同じ Git fingerprint を receipt に記録した後、ignored `output/pegasus-dispatch/` が shard ごとに異なる時刻で変化する。各 shard は別の物理状態を見ているのに coordinator は同一 X と判定する。不正 main が残す side effect を別 shard が before/after 間に消す、または authority tree と shard copy が違う場合、side-effect guard まで緑になり得る。

- **(d) 自己判定:** 状態同一性の欠落と false-red は **real**。side effect が相殺される false-accept は **speculative**。

- **(e) 是正案:** 受入 lease の取得から集約完了まで、単一の snapshot ID と fencing を維持する。各 execution root の全 read-setを content hash で束縛し、ignored/untracked bytes、submodule HEAD・dirty bytes、pytest/plugin/env、HOME/PATH/TMPDIR/locale/timezone を含める。完全な read-set を宣言できなければ shard ごとの隔離 checkoutを使い、共有 root 方式を採らない。

## Critical 3 — 4 gate は「発火回数」では意味を保存しない

- **(a) 主張:** 親 I2 の「全体として一回以上」と P3(c) の「各 shard」が矛盾している。必要なのは回数でなく、どの snapshot・execution root・invocation classification に対する証明かである。

- **(b) 根拠:** 594/632 は acceptance shape でなければ無音 pass [run_tests.py:591–666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:591)。705 は targeted run なら未初期化でも警告だけで続ける [run_tests.py:698–763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:698)。1677 は rc を変えない警告であり、valid bounded marker があれば出ない [run_tests.py:1667–1682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:1667)。

- **(c) 失敗シナリオ:**

| gate | 全 shard で発火 | 1 shard だけ | どこでも発火しない |
|---|---|---|---|
| 594 未 stage 削除 | 全 preflight 後に別 shard/fixture が tracked file を削除すれば postcheck がなく通る。別 root を検査して authority tree を land する場合も通る。 | 検査 shard の clean copy だけ緑、land root または他 root に削除がある main を受理できる。単一回が安全なのは exact frozen authority X を検査し、その後を fence した場合だけ。 | pre-existing deletion があり、それを読む test がなくても全 rc=0。canonical gateなら rc13。 |
| 632 RuleOps | 各検査対象が別 copy、または全検査後に ledger が変われば、不正 authority ledgerを通せる。 | clean coordinator copyだけを検査し、実行/land rootの壊れた ledgerを未検査にできる。逆に exact immutable X への coordinator 1 回なら十分。 | `ruleops.py check` だけが検出する production ledger破損が無音で通り、canonicalなら rc15。 |
| 705 submodule | 現 predicate は `CMakeLists.txt` と `.git` の存在だけで、wrong HEAD、dirty bytes、main gitlinkとの不一致を証明しない。全 rootで「発火」しても不正 rootが通る。 | coordinator rootだけ初期化し、remote rootでは slow real test が skip。例えば `test_s8b_floor_campaign.py:2551–2609` の canary が走らず、当該経路を壊した main が全 rc=0になり得る。 | 全 remote rootで同じ skipが起きる。collection nodeidは存在するため、集合一致だけでは検出不能。 |
| 1677 warning | 全 shardが「受入でない」と警告しても coordinator が rc0を集約すれば不正な受入になる。 | 一本の警告にも enforcement はない。 | bounded marker、M5単一 invocation、または警告抑止退行を区別できず、欠落 shardを受入扱いできる。 |

- **(d) 自己判定:** gate の実挙動は **real**。594/632 の false-accept race の一部は **speculative**。705 の skip経路と1677の非強制性は **real**。

- **(e) 是正案:** 594/632 は fan-out 前に exact immutable authority snapshotへ exactly once。705 は distinct execution root ごとに、初期化だけでなく gitlink pin・HEAD・dirty stateを attest。1677 は警告回数を捨て、各 targeted childを `non-standalone` とする構造化 receiptと、唯一 acceptanceを名乗れる coordinator tokenに置換する。

## Critical 4 — group-atomic は D63 の競合閉包を作らない

- **(a) 主張:** 同名 group を一 shardへ束ねても、未登録 node、別名 group、runner 自身の writerは直列化されない。同じ shardに置いても、unmarked nodeは `real-repo` workerと別 workerで同時実行できる。

- **(b) 根拠:** D63 の保証は単一 runner invocation内だけ [decisions.md:2406–2418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/decisions.md:2406)。hook は正本リストと完全一致した nodeだけを markする [conftest.py:238–248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/conftest.py:238)。確認できた未閉包は次のとおり。

| surface | group外 reader/writer |
|---|---|
| ignored `output/` 全木 | `_real_output_snapshot()` を使う9 node: `test_s8b_floor_campaign.py` の 4138, 4227, 4248, 4371, 4768, 4856, 4881, 4925, 4960。`real-repo` 13 fileにも入っていない [facts.md:44–50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/facts.md:44)。 |
| T-080実 repo payer | `_run()` は `root=ROOT` と memo resolverを使う [test_s8b_oracle_driver.py:1682–1717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8b_oracle_driver.py:1682)。default callerは少なくとも定義行 2534, 2633, 2653, 2686, 2703, 2743, 2793, 2836, 3031, 3076, 3412, 3475, 3540, 3594, 3620, 3650, 3700, 3755, 4055。cache miss/lock失敗時は実解決へ fail-open [real_repo_receipt_memo.py:145–163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/real_repo_receipt_memo.py:145)。既知の T-715 hole として記録済み [worklog:534–540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/archive/worklog-phase3-0810-354.md:534)。 |
| 別名 group の実 Git writer | s8c session fixture は real rootに対し alternate indexで `write-tree` / `commit-tree` を行い、共有 object databaseへ書く [test_s8c_preregistration_invariant.py:76–100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8c_preregistration_invariant.py:76)。3 nodeは `s8c-preregistration-candidate` という別 group [同:124–207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8c_preregistration_invariant.py:124)。T-716も未裁定 [worklog:542–545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/archive/worklog-phase3-0810-354.md:542)。 |
| 直接 real repo reader | `test_s8b_approved.py` の gitlink/freeze readers 58, 73, 110、`test_s8b_floor_campaign.py` の real canary/e2e 2556, 2598, 3226、`test_artifact_admission.py` の output corpus readers 681–871、`test_layer3_report.py` の real campaign readers 441, 448, 1302。immutable blob readerも含むため、全件を同じ mutexへ入れるべきとは限らないが、現正本が「全 real repo access」を表してはいない。 |
| runner writer | 各 dispatch は既定で `output/pegasus-dispatch/` を作る [dispatch_compute.py:1313–1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:1313)。pytest markerでは直列化不能。 |

- **(c) 失敗シナリオ:** 今回、runner receipt writerと9 nodeの snapshot readerが並走して実際に赤になった。false-green方向では、unmarked T-080 payerが grouped submodule writerの一時 patch窓を読み、壊れた verifierが期待する一時 bytesと偶然一致すれば canonicalでは赤の mainを緑にできる。

- **(d) 自己判定:** 未登録 reader/writerと false-redは **real**。一時 bytesが false-greenを作る具体的値は **speculative**。immutable readerの一部は競合対象外になり得る。

- **(e) 是正案:** marker名ではなく resource conflict graphを正本にする。各 node/harnessが `read-set` / `write-set` を宣言し、同じ mutable resourceへ触る全 producer/consumerをprocess・node横断の同一排他域へ閉じる。分類漏れを安全側に倒せないなら、共有 checkoutをやめて shardごとに隔離する。

## Major 1 — 赤の帰属は receipt ID だけでは機械化できない

- **(a) 主張:** manifest ID、shard、PBS、hostname、gw、digestは「どこで起きたか」を示すが、「なぜ起きたか」を示さない。段 2 の attribution completeness は causal classification ではない。

- **(b) 根拠:** 同じ probeで、partition由来 ImportErrorと、別 job receipt由来の snapshot failureが同時に観測された [measurements.md:86–97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:86)。段 2 の帰属測定はID列と orphan/ambiguityを数えるだけ [s2-plan.md:214–220](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:214)。

- **(c) 失敗シナリオ:** 1 shardで `_real_output_snapshot` が赤。実装回帰と誤判定して mainを拒否すれば false-red、既知の干渉だと決め打ちして無視すれば、実際に campaign codeが real outputを書いた不正 mainを受理する。単一ログから二者を区別できない。

- **(d) 自己判定:** **real**。

- **(e) 是正案:** 赤は原因にかかわらず land不可。帰属には同一 immutable snapshotで、(1) isolated canonical、(2) isolated failing shard、(3) concurrent shard＋resource mutation ledger の差分再走を要求する。解消不能なら sharded acceptanceを証拠にせず、canonical全走を唯一のfallback evidenceにする。

## Major 2 — `max(rc)` と JUnit の単純併合は不可

- **(a) 主張:** `max(rc)` は完全な固定長 vectorがあり、signalも正数へ正規化済みという条件下で「全0か」だけを見る用途なら安全だが、規範的な結果集約・帰属には使えない。

- **(b) 根拠:** pytest rcは 0=pass、1=failure、2=interrupt、3=internal、4=usage、5=no testsで順序尺度ではなく、現版には6もある [_pytest/config:101–122](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:101)。runner独自 rcは13–16 [run_tests.py:111–116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:111)。xdist worker crashはfailed report化され、workerを再生成する [xdist/dsession.py:238–267](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:238)。JUnitでは通常skipとxfailがどちらも `<skipped>` だがtypeが異なる [junitxml.py:229–248](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/junitxml.py:229)。collection errorは多数の消えたnodeを一つのerror testcaseに縮約した実例がある [measurements.md:73–84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:73)。

- **(c) 失敗シナリオ:**

  - Python `subprocess.returncode` の `[-9, 0, 0]` に `max` を取ると0となり、SIGKILL shardを受理する。
  - 期待4 shardのうち3本しか receiptがなく、その3本が0なら、観測済み集合のmaxは0。
  - 空 shardのrc5を「no-op」と0へ丸めると、割付け漏れを受理する。
  - JUnit testcase数だけを足すと、collection error 1件が消えた10 nodeを隠し、duplicateとmissingが相殺する。
  - skip/xfailのtype・理由を捨てると、環境不足による新規skipを既存許容skipとして受理する。

- **(d) 自己判定:** 欠落 shard、rc5、JUnit縮約は **real**。負signalの false-acceptは coordinator実装方式に依存するが **具体的な設計罠**。

- **(e) 是正案:** expected shard manifestとterminal receiptを1対1照合し、欠落・重複・signal・timeout・corrupt/missing JUnitはすべて拒否。raw child rcを保存し、origin付き型へ変換する。JUnitは `(manifest ordinal, occurrence, raw nodeid, report phase)` で併合し、collection error、setup/teardown error、skip/xfail/XPASS、理由を保存する。空 partitionは投入せず、予期しないrc5は拒否する。

## Major 3 — P4 の「非選択 option なら安全」と M5 の「単一 collection」は成立しない

- **(a) 主張:** selectionを変えないことは outcomeを変えないことではない。M5も「単一 controller」ではあるが「単一 collection/session hook」ではない。

- **(b) 根拠:** 現runnerは既定 `-n` で `--tx` を事実上上書きし、`--rsyncdir` は `.git` を送らないため repo意味論を変える [s2-plan.md:121–130](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:121)。M5は collection/session hooksを一つと記す [同:166–179](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:166) が、既存測定自身が「xdist各workerは全fileをcollectする」と確認している [measurements.md:99–114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:99)。

- **(c) 失敗シナリオ:** remote rootに `.git`/submodule/toolがなく、mainが壊した real-build経路のテストがskipする。nodeid collectionは一致し、全rc=0。canonical initialized checkoutなら当該canaryが走って赤になる。M5でも各workerのcollection-time side effectはworker数・host数だけ発生し、共有 filesystem副作用は一controllerでは消えない。

- **(d) 自己判定:** `--tx`の現挙動、rsync差、per-worker collectionは **real**。

- **(e) 是正案:** P4後半は撤回する。M5を候補に残すなら、controllerだけでなくworker topology、全workerのcollection/output、root pin、plugin/interpreter、session hook回数、resource排他をcanonical C48と比較する。remote transportをallowlistへ足すだけの変更は受入形に認定しない。

## Major 4 — 親の性能実測は安全性反証には使えるが、採用性能値にはできない

- **(a) 主張:** 実測は「現M1が不正」と「件数均等が悪い」を支持するが、「1.99倍・ポイント+16%」「k=4で飽和」「M0は小さく閉じる」の一般化は成立していない。

- **(b) 根拠:**

  - 全armがfile列挙の非受入形でleaseなし [measurements.md:1–5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:1)。
  - base自身が8 failedで、shardと並走したreceiptに汚染された [同:8–17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:8)、[同:94–97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:94)。
  - `k4time` は同じbase JUnitをweightにした一回のin-sample LPT [同:19–28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:19)。
  - 実際のqueue waitは約350秒で、`max(pytest wall)` はlease/end-to-end makespanではない [同:134–138](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/measurements.md:134)。
  - 段2自身の採用protocolは最低5 paired block、Latin square、semantic mismatch時中止を要求する [s2-plan.md:185–223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/s2-plan.md:185)。
  - 「receipt副作用は必ず」は過剰一般化で、dispatcherにはrepo外 `output_root` seamがある [dispatch_compute.py:1286–1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:1286)。

- **(c) 失敗シナリオ:** 1.99倍を採用値として設計を進めると、productionではqueue wait、coordinator、receipt回収、lease保持を含む占有が短縮せず、同時に未解決のpartition false-greenを導入する。「速い」という誤った一般化が正しさ変更の採用圧力になる。

- **(d) 自己判定:** **real**。ただし最長testが現条件で強い下界であること自体は支持される。

- **(e) 是正案:** 性能評価は semantic screening通過後だけ行う。repo外 receipt、isolated canonical control、同一tip、開始時刻を含むend-to-end makespan、固定総worker、複数partition、paired block、node Latin squareを必須にする。`conftest`へのpath追加だけを「suite hermeticity完了」とせず、call-time outcomeとfixture/resource状態まで再監査する。

## 総括

- この分割は実装してよいか: **No — 現行M1/P1〜P4は実装不可。完全なsnapshot/fencing、resource閉包、型付き併合、canonical fallbackを新設し、改めてユーザー裁定を得るまで進めない。**
- 親 brief の否定点: **P1の意味論的分割単位としての十分性、P2のgroup-atomic十分性、P3(a)(c)(d)と(e)を証拠扱いする部分、P4のmanifest十分性・`--tx` allowlist安全説を否定。P5は支持。**
- 段 2 プランで受理集合を壊す部分: **現時点のM4/「実装しない」結論自体は壊さないが、狭いsys.path修正後にM1を解禁する条件、M5の「単一collection/session」前提、不完全なX・resource閉包・skip/xfail/collection-error併合のまま条件付き○とする部分は壊す。**