## 分散単位の判定

結論は、**(e)「workload 単位の 3 job を同時投入し、各 job 内で verifier だけを多重化する」**を第一候補とする。(a) の統計・binary 境界を維持しつつ、実測上の律速を直接除く設計である。

| 候補 | §7 binary SHA | R2 `blocks.run_order` | §7.5 の対比較 | claim・lock・WAL | 判定 |
|---|---|---|---|---|---|
| (a) workload、3 job | **満たせる。** 各 job を `verify-perf` とし、同じ checkout 内で verify、job-local WAL の認証 attempt、perf build、SHA 照合を完結させる。[run_formal:2875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2875)、[SHA 照合:2988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2988) | 3 block 全部を登録順で走査するため維持。[block loop:2978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2978) | 各 workload の 18 対は一つの job・node 内で閉じる。workload 間で結合するのは raw throughput ではなく family の Holm 手続きである。 | workload は `search_config` と `spec_slug` に入り、campaign identity は異なる。[config_for:1460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:1460) ただし出力 root と報告処理は現状のままでは共有競合する。 | **採用候補。** job 内 verifier 多重化と、job-local root・後段 fan-in を組み合わせる。 |
| (b) `(workload, block)`、9 job | 各 block job が15変種を全部ローカル認証するなら満たせる。認証を別 block job から借りてはならない。 | 各 job が対応 block の既登録15点をそのまま走れば `blocks.run_order.<block>` は維持できる。[登録順:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/b10-backoff-shape-preregistration.md:339) block 間の開始時刻だけが変わる。 | 一つの block job に全15処置が入るため、一処置一ノードではない。比 `shape/constant-1` は共通乗数に不変である。[効果量:1672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:1672) 3 node に全処置が反復されるので完全交絡を避けられる。ただし node=block の割付けと ratio 集約を protocol に明記する必要がある。 | 現行 identity は block を区別しないため、同 workload の3 jobは同じ claim・lock・WALへ向かう。G12 claim は campaign ID 名で作られる。[loop.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/loop.py:209) block と fresh group ID を identity に入れ、9 campaign に分ける必要がある。 | **適合可能だが不採用。** 律速である15変種の認証を workload ごとに3回払い、壁時計をほぼ縮めず node-hour を約3倍にする。 |
| (c) `(workload, variant)`、45 job | 各 job 内 `verify-perf` ならセル単独では満たせる。 | **破る。** 3 block の15点 interleave を variant ごとの3反復へ組み替えるため、登録された各 block の順序を再現できない。 | **破る。** constant と対象 shape が別 job・別 nodeになり、一処置一ノードの完全交絡になる。[runbook:1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/pegasus-runbook.md:1336) | 45 identity と外側 exact conjunction が必要になる。 | **却下。** |
| (d) verify / perf 別 job | rebuild する現行形は**構造的に不成立**。job path が binary bytes に入り、[verify_performance_binary:2480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2480)で落ちる。binary bytes を輸送すれば SHA 条項だけは満たせる。 | workload 単位 perf jobなら維持可能。 | workload の全処置を同じ perf jobに置けば閉じる。 | 同一 identity の verify job後に perf jobを出すと、残存するG12 claimと競合する。fresh identityにすると verify WALとの結合が切れる。 | **却下。** byte輸送は後述の未裁定面も持ち、第一候補にする理由がない。 |
| (e) workload fan-out + job 内 verifier pool | (a) と同じ。 | (a) と同じ。 | (a) と同じ。 | 3 job-local campaignと外側 fan-in。 | **推奨。** |

D1169 は文言上 **A-2 専用**であり、B-10 の9 campaign化を自動的に許可しない。[D1169:62](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-decisions.md:62) A-2 では composition が `_protocol_preimage` に入り、`protocol_sha256`へ反映される。[paper_story_a2_certification.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/paper_story_a2_certification.py:279) B-10で3または9 campaignの論理積を正式受理するには、**B-10固有の裁定**と、exact member集合・composition規則をB-10の protocol preimageへ入れる実装が必要である。A-2の関数をB-10へ無断で一般化してはならない。

## ノード内多重化の設計

現在は二重に直列である。

- campaign は genome を一つずつ `evaluate()` に送り、完了するまで次へ進まない。[loop.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/loop.py:466)
- 各変種の正しさ検証は5反復を逐次実行する。[pipeline.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/pipeline.py:1521)
- 各反復は trace生成、直列化可能性検査、WAL書込み、tmpdir削除までを一体で行う。[pipeline.py:1365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/pipeline.py:1365)

設計は次の形にする。

1. coordinatorだけが build、campaign WAL、`EvalResult`、capability順序を所有する。workerはWALへ書かない。
2. K変種分について、48-threadのtrace生成を一度に一つだけ実行し、各反復を固有tmpdirへ残す。trace生成中に他のtrace生成や性能測定を重ねない。
3. trace生成を止めた後、その batch の直列化可能性検査を反復間・変種間でworker poolへ送る。最大5反復だけの並列ではread-heavyを十分縮めにくいため、複数変種を一つのbatchに含める。
4. coordinatorが結果を論理的な `(variant order, repetition index)` 順へ戻し、成功時だけ既存と同じ順序で `VERIFY_DONE` とcapabilityを確定する。
5. batch検証後にtmpdirを削除し、次batchへ進む。全15変種の認証が終わるまでperf loopへ入らない。

絶対規律1は維持される。verify campaignは既に `do_bench=False` であり、trace有効binaryの検査しか行わない。[b10 sweep:2914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2914) 性能測定はその後、trace無効binaryを再hashしてから別runとして行う。[同:2988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2988) verifierのCPU利用は性能値ではない。ただしtrace生成とworker検査を重ねると48-threadの正しさrunをCPU競合させるため、採らない。

絶対規律2について、**「全worker終了後に初めてreject」は採らない。** 全5件の論理積を取る限りfalse acceptは増えず、数学的なゲートは弱くならないが、事前登録の「anomalyを返したら即reject」という時間的契約には反する。[prereg §7:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/b10-backoff-shape-preregistration.md:651) 最初のanomalyまたは検証不能結果を受けた時点でcoordinatorがrejectを確定し、未開始taskをcancelする。既に走っているworkerはcleanupのため終了してよいが、その結果を受理判断やperf解禁に使わない。

並行度 `P` は推測で固定しない。次をread-heavyの最大traceで測り、全workloadの最悪値から決める。

- verifier 1 processのpeak RSS、worker数ごとの合計cgroup memory
- trace生成process、coordinator、page cacheを含むpeak memory
- 1反復tmpdirのbytes数・inode数と、K変種×5反復のpeak容量
- worker数ごとの検査throughputとI/O wait
- tmpdir削除完了後の容量回収

ノードは48 physical core、ユーザー利用可能DRAM約115 GiB、`/scr`約5.4 TBである。[runbook §1:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/pegasus-runbook.md:35) 実効上限は `min(空きcore、memory上限、scratch bytes/inode上限、同時task数)` で決める。

現行tmpdirは反復ごとに一意な `mkdtemp` を使い、finallyで `shutil.rmtree` する。[pipeline.py:1375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/pipeline.py:1375)、[同:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/pipeline.py:1518) 多重化後も一ディレクトリ一workerとし、workerがfile descriptorを閉じた後にcoordinatorだけが削除する。

`p2_2._assert_single_tenant()` は、schedulerが専有を保証しないノードで外部tenantを拒否する入場条件である。[runbook §1:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/pegasus-runbook.md:45)、[b10 sweep:2869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2869) 同じjob内のworker数やmemory余裕を証明するものではないため、`P=47`の根拠にはしない。

## 欠陥 2 の解法

推奨設計では、**各 workload jobが同一job・同一checkout内で15変種の認証と45 performance cellを完結する。** 分散後もこの回避策は成立する。workload間でbinaryや認証を共有しない。

これは一次資料で確定した3経路、すなわち `.rodata` の `__FILE__`、RUNPATH、buildcache staging pathと、path非依存化が `149 → 56 → 45,454 bytes` へ発散した結果を回避する。[一次資料:88](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-insight-t1905.md:88)、[同:103](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-insight-t1905.md:103)

binary bytesをjob間輸送する案は、**D1220の射程には入らない。** D1220が却下したのはcache identityから絶対source rootを外してcross-job cache hitを起こす変更である。[D1220:86](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-decisions.md:86) rebuildせず認証済みbytesをcopyし、宛先で同じSHAを確認する行為は、その文言だけでは承認も禁止もされていない。

D1372もcache identityを維持し、cross-job cache entryの再束縛を主張しない決定である。[D1372:119](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-decisions.md:119) binary単体の輸送を裁定していない。ただしRUNPATHが元jobの`/scr`を指し、job終了時にはその領域が削除される。[job script:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/tools/pegasus/b10_backoff_shape_campaign.sh:277) したがってbinary単体輸送は実行closureとして未成立であり、正式案に採らない。

同一job方式が成立するため、現時点で事前登録§7を緩める改訂は不要である。

## 欠陥 1 の解法

現行 `_prepare_official_output()` は一つのofficial rootを解決し、その共通claim rootを作る。[b10 sweep:2811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2811) 並行jobへそのまま使ってはならない。

| 実体 | 現行の並行writer | 必要な設計 |
|---|---|---|
| claim root | workload identityならclaim filenameは異なるが、共通directoryを複数jobが更新する。block分割は現行identityも同じなので直接衝突する。 | 外側group rootの下に `jobs/<workload>/`、block案なら `jobs/<workload>/<block>/` を事前作成し、各jobのclaim rootをその子へ置く。A-2のjob-local root型が実証済み。[A-2:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/paper_story_a2_certification.py:733)、[同:2993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/paper_story_a2_certification.py:2993) |
| campaign lock・WAL | workload案ではidentity別、block案では同一。lockはcampaign全体を保持する。[loop.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/loop.py:394) | fresh group IDをcampaign preimageへ入れる。block案はblock IDも入れる。job-local output rootでlock・WALを完全分離する。 |
| `runs/` block record | create-only自体は安全だが、同一layoutへ書くと同じfilenameが `O_EXCL` で衝突する。[b10 sweep:2283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2283) | worker固有layoutへ書く。fan-in時に期待する3×45、または9×15のexact集合を読む。 |
| 全workload報告 | 現在は各workerが他workload rootを読み、直後にreportを書く。[b10 sweep:3047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:3047) writer進行中のrootを読むため、§7.5の独立条件を満たさない。 | workerでは集約・判定・report生成をしない。全request terminal後、単一fan-inだけがexact member集合を検証し、全workload reportを一度だけcreate-onlyで書く。 |

さらに現行 `cache_root` は全job共通の `external/ccbench/build-variants` である。[b10 sweep:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:2883) runbookはbuild-cache claim共有も非独立と明記する。[runbook:1300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/pegasus-runbook.md:1300) job-local cache rootへ分ける。これはcross-job hitを作らず、D1220と整合する。

group manifestは仮想的な新台帳ではなく、runbook §7.5がfan-out時に要求するrequest・入力hash・出力namespace・期待成果物の対応表である。[runbook:1372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/docs/pegasus-runbook.md:1372)

## 所要と資源の見積り

性能測定本体は1 workload 4.5分なので、write-heavyの3時間50分から約4.5分を除いた225.5分を認証側とみなす。read-heavyは5時間5分で15変種中3変種なので、単純線形外挿は `305 × 15 / 3 = 1,525分`、約25時間25分である。[実測:14](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-worklog-1186.md:14) balancedの14/15を6時間で打ち切った実測からは約385.7分、性能分を足して約6時間30分となる。[同:46](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-worklog-1186.md:46)

以下はjob prologueを `H` として別扱いした外挿である。

| 案 | job数・必要node | serial verifierの壁時計 | node-hour概算 |
|---|---:|---:|---:|
| workload | 3 job・3 node | 最大約25時間30分 | 約35.8時間 + `3H` |
| workload×block | 9 job・9 node | 各read jobが約25時間26分。9本同時でも最大はほぼ変わらない | 約107.0時間 + `9H` |
| workload×variant | 45 job・45 node | readの先頭3変種が代表なら約102分。ただし最大変種は不明 | 約35.8時間 + `45H` |
| verify/perf分離 | 6 job、2 wave、同時最大3 node | verify最大約25時間25分、その後perf約4.5分 | 約35.8時間 + `6H`。binary輸送時間は未算入 |
| 推奨案 | 3 job・3 node | `max_w(S_w + C_w/P_w + 4.5分)` | `Σ(S_w + C_w/P_w + 4.5分) + 3H` |

`S_w` はbuild・trace生成・直列I/O、`C_w` は並列化対象の検査時間、`P_w` は実測で決めるworker数である。全225.5分、385.7分、1,525分を47で割った値は楽観的な算術下限にすぎず、予測値にはしない。仮に `S=0` ならread-heavyは約37分になるが、実際にはtrace生成とI/Oが残る。

read-heavyの1反復がwrite-heavyの175秒頭打ち値の何倍かは、提示された実測からは算出できない。5時間5分にはtrace生成・書出し・検査が混在し、1反復単独値ではない。約25.6マイクロ秒/取引試行と175秒頭打ちも、655万件超のtrace切り捨て疑いが残る。[一次資料:142](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-insight-t1905.md:142)、[同:156](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-insight-t1905.md:156) この頭打ちを上限として資源見積りへ固定してはならない。親の実測では、workload・変種・反復別にtrace行数、commit witness、検査時間、peak RSS、trace bytesを分離して取る必要がある。

## 欠陥 3・4 の扱い

欠陥3は、推奨多重化の実測後に必要walltimeを決め、その値を一つの契約から派生させることを正式投入の前提とする。現在はPBSの12時間、receipt照合、scheduler自己検査、submit receipt、driver側receipt検査に43200秒が重複する。[job script:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/tools/pegasus/b10_backoff_shape_campaign.sh:5)、[同:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/tools/pegasus/b10_backoff_shape_campaign.sh:168)、[submitter:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/tools/pegasus/submit_b10_backoff_shape.sh:199)、[driver:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:492) 現状のread-heavy線形外挿は12時間を超えるため、未測定のspeedupを前提に放置できない。

欠陥4は**正式分散投入の必須前提**に置く。signal handlerの `local name=$1 number=$2 rc=$((128 + number))` は、`set -u`により`write_failure`前に落ちる。[job script:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/tools/pegasus/b10_backoff_shape_campaign.sh:107) これは実際のread-heavy撤去とbalanced打切りで再現済みである。[一次資料:117](/home/SFC/tanab/.claude/jobs/e76b4f80/tmp/wave-t1905-b10-multinode-design/verbatim-insight-t1905.md:117) job数が増えるほど影響面が増え、D193による非再開可能WALと残存claimの操作者判断に必要な終端理由を失う。修正・signal実測・`failure.json`確認前に正式系列を投入してはならない。

## 親 brief への反証

- **P1は一部正しいが並列範囲が広すぎる。** verifierは並列化できるが、48-thread trace生成まで並行させると固定された正しさworkloadをCPU競合させる。並列化対象は保存済みtraceの検査であり、WALとtrace producerはcoordinatorに残す。
- **P2は第一候補として誤り。** block内対比較は閉じるが、各block jobが15変種の認証を全部必要とし、律速を3回複製する。さらに現行campaign identityにblockがなく、3 jobは同じG12 claim・lock・WALへ向かう。
- **P3は正しい。** variant fan-outはR2を破り、一処置一ノードの完全交絡になる。
- **P4の「D1220の射程確認」は正しい。** 結論は「byte輸送はD1220の射程外だが、承認済みでも実行可能でもない」である。
- **P5は不完全。** claim・block record・report以外に、共通build cache、固定campaign trial、共有親rootがある。特に `trial` はspec SHA固定でsubmission nonceを含まず、fresh campaign identityにならない。[config_for:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-multinode-design/orchestrator/campaign/b10_backoff_shape_sweep.py:1518)
- **P6は支持する。** 欠陥4は前提条件である。

## ユーザー裁定へ返す項目

1. **推奨分散単位:** fresh group内の3 workload job同時投入と、各node内のoffline verifier多重化を採るか。推奨は採用。
2. **B-10固有の外側composition:** exact 3 workload campaignの論理積、job-local root、単一fan-inをB-10 protocolへ追加し、その規則をprotocol hash対象へ入れるか。D1169だけでは自動承認されない。
3. **write-heavyの扱い:** 新compositionで3 workloadをfresh groupとして取り直し、旧write-heavyは解析集合から除外するか。推奨は再取得。旧write-heavyとfreshな残り2 workloadを混成受理するなら、その異種compositionを別途明示裁定する必要がある。
4. **block案を選ぶ場合のみ:** node=block、全15処置を各nodeへ置く割付け、within-block ratio、3 block集約をprotocolに固定するか。ただしnode-hour約3倍なので非推奨。
5. **binary輸送:** D1220は判断していない。将来verify/perf分割を再検討する場合だけ、binaryとruntime closureのcross-job輸送を新規裁定へ返す。今回の推奨案では不要。
6. **事前登録§7:** 同一job方式を採る限り改訂しない。SHA条項や検証反復数を緩めない。

## 総括

正式設計は、**1 fresh group = 3 workload jobを別nodeへ同時投入し、各jobは同一checkoutの`verify-perf`を完結、job内では保存済みtraceの直列化可能性検査だけを実測上限まで多重化、全job終了後に単一fan-inで135 cellを集約する**形とする。

9 block jobは統計上は成立可能だが、正しさ認証を3倍複製するため実測上の律速を解かない。45 variant jobとverify/perf分離は現行事前登録またはbinary・claim境界を破る。欠陥3・4、job-local durable/cache root、B-10固有composition hashが実装・確認されるまで投入しない。

本回答では実装、書込み、pytest、投入を行っていない。