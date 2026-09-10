### 1. 現状の実行構造

静的確認のみを行った。pytest、性能測定、投入は実行していない。凍結済み 2 ファイルの SHA-256 は現在の定数と一致している。

- `orchestrator/campaign/loop.py:354-381` は WAL を variant 単位で replay し、terminal variant を個別に除外する。対を一単位として扱う状態はない。
- `orchestrator/campaign/loop.py:383-507` は genome を順に処理し、各 genome について `pipeline.evaluate()` を完了まで呼ぶ。したがって arm A の build、verify、全 reps、commit の後に arm B へ進む。
- `orchestrator/campaign/pipeline.py:1027-1086` は各 `evaluate()` 内で trace build と性能 build を別々に作る。これは変更後も維持すべき境界である。
- `orchestrator/campaign/pipeline.py:1288-1347` は trace を検証し、全 verify pass が成功した後だけ `certified=True` にする。`pipeline.py:1322-1333` の anomaly 即 abort も変更対象外である。
- `orchestrator/campaign/pipeline.py:1502-1525` は verify 後に `_run_bench()` を呼び、`pipeline.py:1530-1561` で bench 結果を commit する。この一体化が「両 arm を先に verify し、その後に交互測定する」ことを阻んでいる。
- `_run_bench()` は `pipeline.py:565-580` で `measure_point(..., reps=perf.reps)` を一度呼び、`pipeline.py:592-621` の一つの `bench_lock()` 内で最大 `bench_max_rounds` 回の全反復を行う。
- `orchestrator/calibrator/runner.py:1117-1158` では `measure_point` 自身が `range(reps)` を連続実行するため、外側から arm を差し込めない。
- `paper_story_a1_paired.py:3572-3608` は workload ごとに reps=N の `PerfConfig` と二つの genome を一度だけ `run_campaign()` へ渡す。balanced の N=205 は policy の `:143-153`、extime=3 は `:80-89` にある。
- 配置は既に `paper_story_a1_paired.py:808-822` の `search_config["pairing_design"]` に入り、`campaign_lock.py:19-21` の `search_config` 全体が identity key である。新しい「混在防止 gate」は不要である。
- 通常 WAL stage は `model.py:23-36` の exact 集合で、既存テスト `test_campaign.py:2620-2628` もその 8 値を固定している。stage を増やすと既存期待値変更が必要になるため採らない。
- 現行 recovery は build/verify/bench signal 後の active attempt を `wal.py:1847-1866` で拒否する。さらに verifier capability は process-bound である (`verifier/core.py:168-216,224-258`)。commit receipt はその live capability を要求して消費する (`verifier/commit_receipt.py:296-340`)。したがって、プロセス終了後に同じ attempt を成功扱いで継続することは、防壁を緩めない限りできない。

### 2. 変更面の実アンカー表

| file:line | 現状 | 変更内容 | なぜ必要か |
|---|---|---|---|
| `orchestrator/campaign/campaign_lock.py:49-74` — closure member | enforcement closure は exact 24 path | **変更しない**。新 module/path を追加しない | 絶対条件4を守り、closure 名簿を25以上へ広げない |
| `orchestrator/campaign/loop.py:233-248,354-507` — closure member | variant ごとの逐次 `evaluate()` | identity 内の配置値を closed selector として読み、interleaved の場合だけ exact two genome を一つの pair coordinator で処理する。両 arm の source identity を先に確定し、共通 `pair_attempt_id` を付けて二つを prepare した後に paired bench へ渡す | 両 arm の build/verify を bench 前に完了させるため |
| `orchestrator/campaign/loop.py:360-381,432-437` — closure member | terminal を variant ごとに skip | interleaved のときだけ二 variant の terminal 状態を組で判定する。片側 commit、片側非terminalなどの非対称状態では未完側を測定せず fail-closed に終端化する | 再起動時に既存 arm と新規 armを偽の対にしないため |
| `orchestrator/campaign/pipeline.py:284-295,707-785` — closure member | `evaluate()` は必ず benchまたはno-bench commitまで進む | 内部 token 付きの `_PreparedEvaluation` を追加し、interleaved opt-in のときだけ verify 済み状態、perf binary、abort/finalize closure、live verifier capabilityを呼出元へ返す。既定経路と既存 `_run_bench` 二呼出しは残す | 既存 AST テスト `test_campaign.py:8010-8063` の期待を変えずに二段化するため |
| `orchestrator/campaign/pipeline.py:512-704` — closure member | N reps を一つの測定点として処理 | `_run_interleaved_pair()` を別に追加する。各 armを `measure_point(..., reps=1)` で一回ずつ測り、N 個を arm別に集約して既存と同じ中央値、CV、代表rep指標を算出する | rep単位で arm を切り替えつつ、最終 `bench_done.tps` の既存形を保つため |
| `orchestrator/campaign/pipeline.py:461-475,662-704` — closure member | `bench_done` payload は exact key closure | key集合を変えない。配置証跡は bench payloadへ新キーを足さず、別の pair journalへ置く | `test_layer3_report.py:769-785` の既存期待を変更せず、D1224を守るため |
| `orchestrator/campaign/pipeline.py:1411-1451` — closure member | verify完了後に一つのarmだけbench可能 | 全 member が certified である場合だけ paired benchを開始する。一方が red/anomalyなら準備済みpeerもfitnessなしでabortする | certified gateとanomaly即rejectを保つため |
| `orchestrator/campaign/pipeline.py:1453-1561` — closure member | live capabilityからarm単位commit | paired benchが全N対を完了した後にのみ、各armの `bench_done` と commitを出す。片側bench失敗では双方をabortし、commitを出さない | 不完全な対から片側だけを採用しないため |
| `orchestrator/campaign/wal.py:930-937` — closure member | 通常WALだけをfsync追記 | `runs/interleaved-pairs.jsonl` 用の厳密codec、`O_NOFOLLOW`、append、fsync、読取検証を同じmoduleへ追加する。1行は完了した一対の index、実行順、二variant、二attempt、二throughputを持つ | 通常stage集合を変えず、実際の対順序を耐久化するため |
| `orchestrator/campaign/wal.py:1430-1588` — closure member | attempt topologyはvariant単位 | 通常topologyは変更しない。pair journalと `build_start.pair_attempt_id` の整合を検査する専用関数を追加する | generic campaignの既存拒否集合を広げたり緩めたりしないため |
| `orchestrator/campaign/wal.py:1760-1908` — closure member | build_done以後のactive attempt recoveryを拒否 | exact interleaved profileに限る専用 recovery を追加する。journal prefixが正しい場合でも同じattemptは再開せず、対の全active memberへ専用abortを追記する。通常 recovery はそのまま残す | process-bound verifier capabilityを迂回せず、再起動をterminal invalidへ閉じるため |
| `orchestrator/campaign/wal.py:1950-2007,2127-2134` — closure member | commit/abortでvariant terminal | terminal定義は変更しない。loop側で二variantの対称性を追加確認する | WALの既存consumerを壊さずpair単位の再開判定を足すため |
| `orchestrator/campaign/ident.py:40-54,445-476` — closure member | A-1 markerは旧study/designだけ | 許可する `(study_id, pairing_design)` を閉じたtuple対応にする。旧studyと新designのcross-productは拒否する。専用pair recoveryへdispatchする | 新studyをnon-certifying laneへ配線しつつ、凍結studyの意味を変えないため |
| `orchestrator/verifier/core.py:168-258`、`verifier/commit_receipt.py:296-340` — closure members | capabilityはprocess/operation bound | **変更しない** | crash後resumeのために認証防壁を弱める案を排除する |
| `orchestrator/campaign/paper_story_a1_paired.py:76-139` — non-member | v2 path、旧study、旧hash定数を固定 | 既存定数と既存pathは変更しない。新study用定数、policy path、prereg path、result schemaを別名で追加する | D1027とbytes不変条件を守るため |
| `paper_story_a1_paired.py:661-763,801-843` — non-member | v2だけをexact検証し、grouped designをidentityへ入れる | v2 validatorを一切緩めず、別のv3 exact validator/profileを追加する。新profileだけ interleaved selector、`bench_max_rounds=1`、pair scheduleを返す | 旧studyを再解釈せず、実consumerを作るため |
| `paper_story_a1_paired.py:2150-2436,2586-2809` — non-member | armごとの標準stageとtpsを検査 | v3 collectorだけpair journalをsnapshotし、index連続性、物理順、variant/attempt binding、journal値と二armの `bench_done.tps[i]` の一致を検査する | 宣言だけのinterleavingでなく実行証跡をconsumerまで通すため |
| `paper_story_a1_paired.py:3440-3608,4530-4568` — non-member | `--study-id` は旧IDだけを受理 | `--study-id` をversioned profile selectorにし、v3 IDが新policyと新実行経路を実際に選ぶようにする。旧IDの挙動は不変 | 休眠 capabilityにしないため |
| `orchestrator/campaign/paper_story_a1_paired.v3.json` — NEW、non-member。anchor `paper_story_a1_paired.py:76,661-763` | 存在しない | 新study、interleaved schedule、rounds=1、journalと中断時invalid規則を凍結する | 実装とconsumerを同じ変更単位にするため |
| 新事前登録 README — NEW、non-member。anchor `paper_story_a1_paired.py:116-139` | 存在しない | ユーザーが発行した新studyの事前登録を新path/hashで束縛する。旧READMEと旧定数は不変 | D1027に従い別studyとして扱うため |
| `orchestrator/tests/test_campaign.py:1666-1682,7386-7502,8010-8063,9311-9360` — non-member | recovery、bench、loopの既存テスト | pair prepare、順序、lock、abort、recoveryの正負例を隣接追加する。既存assertは変更しない | 機構層の検出力を持たせるため |
| `orchestrator/tests/test_paper_story_a1_paired.py:768-830,2615-2694` — non-member | v2 bytesと旧markerを固定 | v3 policy/profile、pair journal consumer、旧studyと新designのcross-product拒否を追加する | 凍結物不変と新studyの分離を同時に検査するため |

### 3. 設計択一と推奨

#### (P1-a) 親の案を採る

単一campaign内で二armをprepareし、rep単位で交互測定する。

「reps=1 campaignをN本」は採らない。`loop.py:383-474` では各campaignの各genomeが `evaluate()` を通り、`pipeline.py:1027-1086` で二build、`pipeline.py:1341-1347` でverifyを実行する。A-1はlegacy一passなので、balancedでは205 campaign × 2 arm = **410 verify実行**になる。

build cacheでcompileを省ける場合はあるが、verifyは再利用されない。capabilityはPID、variant、operation identityへ束縛され (`verifier/core.py:196-215,224-258`)、commit時に一度だけ消費される (`commit_receipt.py:309-333`)。別campaignへ証明書を流用する案は成立しない。

#### (P1-b) 親の案を採らない

機構とselectorだけを先にlandし、v3 artifactを次waveへ送ると休眠 capabilityになる。現行 `validate_policy()` はtracked v2との全field一致を要求し (`paper_story_a1_paired.py:745-758`)、実在するpolicyも grouped designしか選ばない (`v2.json:60-65`)。既存artifact pathまたはstudy IDで新分岐を発火できない。

代案は、実装、`--study-id` consumer、新v3 policy、ユーザー発行の新事前登録を同じland単位にすること。新事前登録が未発行なら、機構をmergeせず待つ。旧v2 JSON、旧README、`POLICY_SHA256`、`PREREGISTRATION_SHA256` は変更しない。

#### (P1-c) 親の案を採らない

「標準stageを各variant一回ずつ」は維持できるが、それだけでは実行順序も成功resumeも成立しない。

- 実順序は別の `interleaved-pairs.jsonl` に、一対完了ごとにfsyncして残す。
- 通常WAL stage集合は変更しない。これは `test_campaign.py:2620-2628` と `test_layer3_report.py:769-785` の既存期待を守るためでもある。
- crash後に同じattemptを成功継続することは、process-bound verifier capabilityのため不可である。
- 専用recoveryはpair journal prefixを検証後、未完のpair membersを双方abortする。`wal.replay()` はcommit/abortを通常どおりterminalと判定する。
- 再測する場合は同一campaignの途中継続ではなく、新しいfresh campaignとして行う。片側commit済みなら残りだけを測らない。

#### (P1-d) 親の案を採る

interleaved profileでは `bench_max_rounds == 1` をbuild/WAL前に強制する。

現行再測はarm単位で全N repsを再実行する (`pipeline.py:617-619`, `stability.py:58-90`)。これを交互配置へそのまま持ち込むと、一方だけround 2へ進む、またはpair全体を再実行する新しい未登録規則が生じる。新v3は一回のN対だけを論理round 1とし、arm別N標本からCVを計算する。高CVなら `unstable=True` とし、consumerがinvalidにする。現行consumerもrounds=1とunstable=falseを要求している (`paper_story_a1_paired.py:2257-2272`)。

rounds=1はsettleの撤去を意味しない。最初の対の前のsettleを維持し、`require_settled=True` のconsumerでは falseを即rejectする。CV再測だけを無効にする。

#### (P1-e) 親の案を採らない

repごとのlock取得・解放は、相互排他自体は保つが、AとBの間に別campaignが入れる。これでは「隣接した一対」という配置が壊れる。

代案は **pair単位のlock** とする。各 pair index について一回 `bench_lock()` を取り、その中で二armを順に測ってから解放する。`bench_lock` はmachine-wide flockである (`lock.py:41-64`)。各arm起動直前にも `competing_bench_pids()` を呼び、advisory lockを使わない孤児や手起動processをfail-closedに検出する (`runner.py:382-414`)。別campaignの挿入はpair間だけに限定される。

### 4. テスト計画

すべてmockによる静的・単体テストとし、性能測定は行わない。

#### 正例

- `orchestrator/tests/test_campaign.py:7386-7502,9311-9360` に  
  `test_interleaved_pair_runs_one_rep_per_arm_in_exact_pair_order` を追加する。N=3で二armをprepareし、`measure_point` 呼出しが各回 `reps=1`、順序がpolicyで凍結した6呼出し、verifyがarmごと一回、pair lockが3回であることを検査する。
- 同fileに  
  `test_interleaved_pair_keeps_standard_variant_stage_projection` を追加し、variant別に `build_start, build_done, verify_done, bench_done, commit` が一回ずつであること、pair journalが3行、journal値と `bench_done.tps` が一致することを検査する。
- `orchestrator/tests/test_paper_story_a1_paired.py:768-830` に  
  `test_v2_bytes_and_hash_constants_remain_exact_when_v3_profile_is_added` と  
  `test_v3_profile_selects_interleaved_pairing_and_rounds_one` を追加する。前者は既存期待を変更せず再利用する。
- legacy grouped経路は既存 `test_pipeline_fullscale_verify_and_bench_share_immutable_numactl` (`test_campaign.py:8066-8103`) などをそのまま通し、期待値は変更しない。

#### 負例: 発火自体が目的

- `test_campaign.py:9311-9360` に  
  `test_unknown_pairing_design_refuses_before_authorization_or_wal`。
- 同fileに  
  `test_interleaved_pair_requires_exact_two_unique_genomes_before_build`。
- 同fileに  
  `test_interleaved_pair_requires_bench_max_rounds_one_before_build`。
- `test_paper_story_a1_paired.py:2615-2694` に  
  `test_a1_marker_rejects_old_study_with_interleaved_design`。旧study IDと新designのcross-productを拒否し、D1027違反の迂回を防ぐ。

#### 負例: 特定の時点で発火させたいもの

- `test_campaign.py:6968-6978` の近傍に  
  `test_interleaved_second_arm_verify_red_aborts_pair_before_first_rep`。一方のanomaly時にmeasure call、bench_done、commitが0であることを検査する。
- `test_campaign.py:7474-7487` の近傍に  
  `test_interleaved_competitor_before_second_arm_of_pair_aborts_both`。pair kの二arm目直前だけ競合を返し、それ以後の測定と双方commitを止める。
- `test_campaign.py:1666-1682` の近傍に  
  `test_interleaved_recovery_terminalizes_verified_pair_without_resuming`。build/verifyとjournal prefix後のprocess deathを模し、再起動が双方abortを追記し、測定を再開しないことを検査する。
- 同fileに  
  `test_interleaved_asymmetric_commit_never_benches_remaining_arm_on_resume`。
- `test_paper_story_a1_paired.py:2355-2436` 相当のfixture群へ  
  `test_interleaved_collector_rejects_swapped_pair_journal_order`、  
  `test_interleaved_collector_rejects_journal_tps_mismatch`、  
  `test_interleaved_collector_rejects_missing_pair_index` を追加する。

新test fileは不要である。既存 `test_campaign.py:12905-12929`、`test_paper_story_a1_paired.py:3030-3036` は自走harnessを既に持つ。分離して新設する場合は同じ `pytest.main([__file__, "-q"])` harnessが必要である。

### 5. 変異事前登録の候補

closure member変異ではF357/F358の `contract-loader-drift` 共通核を必ず別記し、下記nodeが共通核控除後のdeltaに現れた場合だけKILLEDとする。ERRORだけで対象コードへ未到達なら候補から外す。

| 1行変異 | 壊す不変条件 | 落ちるべきpytest node id |
|---|---|---|
| `loop.py` の interleaved selector比較を `==` から `!=` へ | groupedとinterleavedのdispatch分離 | `orchestrator/tests/test_campaign.py::test_interleaved_pair_runs_one_rep_per_arm_in_exact_pair_order` |
| interleaved測定の `reps=1` を `reps=member.perf.reps` へ | 一呼出し一rep | 同node |
| pair内の `for member in scheduled_members` を `for member in reversed(scheduled_members)` へ | policyで凍結した物理順 | 同node |
| `if any(member.aborted for member in members)` を `if all(...)` へ | 一arm redならbench開始禁止 | `orchestrator/tests/test_campaign.py::test_interleaved_second_arm_verify_red_aborts_pair_before_first_rep` |
| journal rowの `"pair_index": pair_index` を `pair_index + 1` へ | pair indexは0始まり連続 | `orchestrator/tests/test_paper_story_a1_paired.py::test_interleaved_collector_rejects_missing_pair_index` |
| pair terminal非対称条件を常にfalseへ | resume時に未対armを測らない | `orchestrator/tests/test_campaign.py::test_interleaved_asymmetric_commit_never_benches_remaining_arm_on_resume` |
| v3 collectorの `actual_order != expected_order` を `actual_order == expected_order` へ | journal物理順のconsumer検査 | `orchestrator/tests/test_paper_story_a1_paired.py::test_interleaved_collector_rejects_swapped_pair_journal_order` |
| v3 policy検査の `bench_max_rounds != 1` を `== 1` へ | interleavedは論理round exact 1 | `orchestrator/tests/test_paper_story_a1_paired.py::test_v3_profile_selects_interleaved_pairing_and_rounds_one` |

先頭6件のclosure変異用testは、`test_paper_story_a1_paired.py:2615-2694` と同様にauthorization、identity capture、source bindingをfixtureで隔離し、意味変異の行まで到達させる。これにより共通核控除後deltaを空にしない。

### 6. 危険と未解決

- 新v3のstudy ID、policy bytes、事前登録本文とhashが未提示である。P1-bを退ける以上、ユーザー発行の新事前登録が揃うまで実装をlandできない。
- pair内の順序を常に adaptive→static10 とするか、pairごとに先頭armを反転するAB/BA方式にするかは統計設計上未決である。実装前にv3 policyで一意に凍結する必要がある。
- process death後の成功resumeは既存live verifier capabilityと両立しない。本案はterminal invalidへ閉じ、fresh campaignを要求する。
- WALはvariant単位なので、二arm commitを原子的に一括追記できない。片側commit窓はpair非対称検査でinvalidにする。
- pair journalのfsync費用とpair間lock再取得費用は未実測である。正式測定ではなく、後続waveの非採用probeで上限だけ確認すべきである。
- `measure_point(reps=1)` の複数結果を集約するとき、代表repのcounter、abort rate、latency選択を `runner.py:1035-1045` と同じ規則にしなければ既存leading indicatorの意味が変わる。
- v3 result、receipt、materialization schemaは旧v3 resultと別世代にする必要がある。旧 `PAIRING_DESIGN` や旧limitationsを上書きしてはならない。
- pytestと変異matrixは未実行であり、緑またはKILLEDとは報告しない。

## 総括

- 最重要の設計択一は「単一campaign内のexact-two-arm pair coordinator」を採ることである。
- reps=1 campaignをN本作る案はbalancedで410 verifyとなり、証明書再利用もできない。
- 両armをbuild/verify後、各pairを一つのmachine-wide lock区間として測る。
- repごとのlock解放はarm間への他campaign挿入を許すため採らない。
- 通常WAL stageは変えず、完了pairを別journalへ耐久記録する。
- crash後の同attempt成功resumeは行わず、双方abortしてfresh campaignを要求する。
- rounds=1は採るが、settleと競合probeは維持する。
- v3 policyと新事前登録なしで機構だけをlandする案は休眠 capabilityになるため採らない。