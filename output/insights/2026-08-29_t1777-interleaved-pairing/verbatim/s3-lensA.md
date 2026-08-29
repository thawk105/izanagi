静的検査のみ。pytest、性能測定、投入は実行していない。

1. [severity: must-fix] [観点: 3]
[攻撃シナリオ] pair k の arm A の `measure_point(reps=1)` が完了した直後、arm B の完了前に process が落ちる。計画は「完了した一対」だけを journal に書くため、記録は「pair k の測定開始前に落ちた」場合と同一になる。確認済み観測、開始済みだが未確定の観測、未開始を復元できず、後続の fresh campaign が性能観測後の再走かどうかも判定できない。
[根拠 file:line] `stage2-plan.md:29,64-68`; `orchestrator/calibrator/runner.py:1117-1158`; `orchestrator/campaign/paper_story_a1_paired.v2.json:70-78`
[提案] journal を append-only の `pair_start`、arm ごとの `arm_done`、`pair_done` にする。少なくとも `pair_start` は最初の spawn 前に fsync し、未完 pair は性能観測開始済みとして fail-closed に扱う。

2. [severity: must-fix] [観点: 3]
[攻撃シナリオ] 新 v3 config を `ident.is_a1_non_certifying_config()` の許可 tuple に加えると、`run_campaign()` は A-1 専用 WAL context へ入る。しかし `wal.py` は旧 study ID と旧 grouped design を別途 hard-code しているため、`a1_non_certifying_io()` が build 前に拒否する。計画表は `ident.py` の変更だけを明記し、この第二 marker を更新対象にしていない。
[根拠 file:line] `stage2-plan.md:29-33`; `orchestrator/campaign/ident.py:36-54`; `orchestrator/campaign/wal.py:102-125`; `orchestrator/campaign/loop.py:327-335`
[提案] `wal.py` 側も同じ closed `(study_id, pairing_design)` 対を受理させ、旧 study × 新 design と新 study × 旧 design の双方を WAL context 入口で拒否するテストを足す。

3. [severity: must-fix] [観点: 5]
[攻撃シナリオ] pair 0 の後で lock を解放し、別 campaign が長い bench を実行して終了する。その後 pair 1 が lock を取ると、`competing_bench_pids()` は既に終了した process を検出しない。計画は settle を最初の pair 前だけ維持するため、pair 1 以降を再静定せず測り、最初の `settled=True` を全 N pair の証跡として残しうる。
[根拠 file:line] `stage2-plan.md:76,80-82`; `orchestrator/campaign/lock.py:41-64`; `orchestrator/campaign/pipeline.py:592-621`; `orchestrator/calibrator/runner.py:382-402`
[提案] machine-wide `bench_lock()` を N pair 全体で一度だけ保持する。各 arm 前の競合 probe は残す。これが最小で、再 settle や pair 別 settled 証跡も不要になる。

4. [severity: must-fix] [観点: 6]
[攻撃シナリオ] v3 policy、事前登録、measurement selector を追加しても、実際の submit は常に旧 policy と旧 `STUDY_ID` を読み、job body も旧 ID と v2 path しか受理しない。したがって新機構には qsub まで到達する consumer がなく、D1028 が禁じる休眠 capability のままである。
[根拠 file:line] `stage2-plan.md:35-40,54-58`; `orchestrator/campaign/paper_story_a1_paired.py:1080-1112,4530-4538`; `tools/pegasus/paper_story_a1_paired.sh:13-17,42,765-768`
[提案] `submit` にも closed study selector を追加し、qsub contract と job body を旧 v2、新 v3 の exact profile に分岐させる。旧 literal と旧経路はそのまま残し、追加テストで固定する。

5. [severity: must-fix] [観点: 2]
[攻撃シナリオ] `_PreparedEvaluation` 構築時に `pf.binary` を `tr.binary` と取り違えても、予定された順序、`reps=1`、stage 数、pair journal 件数のテストは通りうる。`measure_point()` は渡された path が trace-disabled build かを検査せず、そのまま spawn する。新 interleaved 経路用の binary 分離テストと変異が計画にない。
[根拠 file:line] `stage2-plan.md:24-25,88-97,131-140`; `orchestrator/campaign/pipeline.py:1027-1042`; `orchestrator/calibrator/runner.py:1156-1158`; `orchestrator/campaign/paper_story_a1_paired.py:2016-2043,2112-2147`
[提案] prepared object に `BuildResult` を保持して `trace is False` と build_done の perf digest/path 一致を paired bench 入口で検査する。`pf.binary` を `tr.binary` に変える一行変異と、全 measure call の exact perf path を検査する test を加える。

6. [severity: should-fix] [観点: 3]
[攻撃シナリオ] pair journal への write 中に crash して末尾が部分 JSON になる。通常 WAL は正常な改行終端なので既存 tail repair は noop だが、専用 recovery は journal prefix を検証できず、双方 abort にも進めない。計画には journal の strict codec、append、fsync はあるが、torn tail の証拠付き repair がない。
[根拠 file:line] `stage2-plan.md:29-31,64-68`; `orchestrator/campaign/wal.py:831-905`; `orchestrator/campaign/ident.py:462-468`
[提案] 通常 WAL と同じく、最後の改行境界だけを対象に removed digest と receipt を残す journal tail repair を専用 recovery の前に置く。

7. [severity: should-fix] [観点: 6]
[攻撃シナリオ] brief は D1139 後の記録・自己整合検査を「関門ではない」と一般化し、「着手条件は満たされた」と結論する。しかし live closure と記録 commit blob の不一致は現在も `IdentityMismatch(contract-loader-drift)` で拒否される。また land には未発行の v3 事前登録と未決の pair 順序が残る。
[根拠 file:line] `brief.md:26-30`; `D1139.md:7-9`; `orchestrator/campaign/ident.py:253-263,351-369`; `stage2-plan.md:146-148`
[提案] 「批准集合との突き合わせという着手条件だけが解消した。自己整合 gate は残り、land は v3 事前登録と順序裁定待ち」と書き換える。

8. [severity: should-fix] [観点: 6]
[攻撃シナリオ] brief の「1 arm 区間 615 s」を wall-clock 区間として費用や交絡窓に使う。`3 × 205` は ccbench に渡す nominal extime の総和にすぎず、205 回分の process 起動、perf、temporary directory、parse、cleanup を含まない。
[根拠 file:line] `brief.md:19-22`; `frozen_policy_v2.json:80-89,143-153`; `orchestrator/calibrator/runner.py:636-688,1117-1158`
[提案] 「nominal workload time 615 s、実 wall-clock arm 区間は未測定」と限定する。

9. [severity: should-fix] [観点: 6]
[攻撃シナリオ] brief の「loop.py / pipeline.py の bytes pin は 0 件」を根拠に、変更が実行時 source binding に影響しないと扱う。実際には両 path が A-1 non-certifying source closure に入り、submit intent が git blob OID と working SHA-256 を記録し、後段で exact 再照合する。
[根拠 file:line] `brief.md:45-55`; `orchestrator/campaign/paper_story_a1_paired.py:119-131,1715-1754,3682-3705`
[提案] 「凍結された固定 digest 定数はないが、各投入の source binding では bytes が pin される」と区別する。

10. [severity: survived] [観点: 1]
[攻撃シナリオ] arm A を prepare 後、arm B の verify が red/anomaly になる経路を攻撃した。計画どおり paired bench を「全 member certified」の後だけ開始し、prepared peer も abort するなら、arm A の rep、bench_done、commit は発生しない。
[根拠 file:line] `stage2-plan.md:22-28,112-117`; `orchestrator/campaign/pipeline.py:1322-1333,1410-1452,1502-1525`
[提案] この防壁は維持する。負例は anomaly だけでなく build error、trace timeout、probe errorにも展開する。

11. [severity: survived] [観点: 2]
[攻撃シナリオ] 現行 grouped 経路で trace build が perf 測定へ混入できるか攻撃した。cache key は `trace` を含み、perf build は trace symbol 不在を検査する。A-1 collector も trace0 configure、実行 path、現在の binary digest を再検査するため、混入した結果は受理されない。
[根拠 file:line] `orchestrator/campaign/buildcache.py:618-636,2992-3014,3064-3069`; `orchestrator/campaign/paper_story_a1_paired.py:2016-2043,2112-2147`
[提案] 現行防壁を v3 collector にそのまま再利用し、所見 5 の新 seam 用入口検査を追加する。

12. [severity: survived] [観点: 4]
[攻撃シナリオ] grouped と interleaved が同じ campaign identity に混ざるか攻撃した。`pairing.design` は `search_config["pairing_design"]` に入り、`search_config` 全体と `trial` が canonical preimage に含まれる。新 study ID と新 design valueを使う限り identity は分離され、別 field は不要である。
[根拠 file:line] `orchestrator/campaign/paper_story_a1_paired.py:801-843`; `orchestrator/campaign/ident.py:169-195`; `orchestrator/campaign/campaign_lock.py:19-21`
[提案] schedule を変えるたび design value を世代更新する closed mapping を validator で固定する。identity field は増やさない。

13. [severity: survived] [観点: 6]
[攻撃シナリオ] brief の exact 24 path と凍結値を独立確認した。closure tuple は実際に24要素で、射影された policy は repo の v2 と byte-for-byte 同一だった。実 SHA-256 も `POLICY_SHA256`、`PREREGISTRATION_SHA256` と一致した。
[根拠 file:line] `orchestrator/campaign/campaign_lock.py:47-74`; `orchestrator/campaign/paper_story_a1_paired.py:76,136-139`; `orchestrator/campaign/paper_story_a1_paired.v2.json:66-68`; `orchestrator/tests/test_paper_story_a1_paired.py:824-831`
[提案] 変更不要。これは静的照合であり、pytest の緑は主張しない。

14. [severity: survived] [観点: 7]
[攻撃シナリオ] v3 発行が旧 v2 policy、旧 preregistration、旧 hash 定数を上書きする経路を攻撃した。計画は新 path、新定数、別 validator を要求し、旧 validator は tracked v2 bytes と両 hash を exact 検査している。
[根拠 file:line] `stage2-plan.md:35-40,54-58,94-96`; `orchestrator/campaign/paper_story_a1_paired.py:745-758`; `orchestrator/tests/test_paper_story_a1_paired.py:815-831`
[提案] golden の再生成は行わず、旧四値の byte-for-byte 不変 test を追加のまま保つ。

## 総括

- 最重要 must-fix は所見 1、完了 pair だけの journal では片 arm 測定後 crash を復元できない点。
- `wal.py` の旧 A-1 marker が新 v3 を拒否するため、現プランのままでは実行不能。
- pair ごとの lock 解放と first-pair-only settle は、pair 間の他 campaign 挿入後に未静定測定を許す。
- submit と job body が旧 study 固定で、新 v3 consumer は end-to-end に接続されていない。
- trace/perf 分離は現行経路では生存したが、新 prepared seam の入口検査と変異 test が必要。
- D1139 は批准照合だけを撤去しており、closure 自己整合 gate まで消してはいない。
- exact 24 path、pairing identity、凍結 v2 bytes と両 hash は静的攻撃を生存した。