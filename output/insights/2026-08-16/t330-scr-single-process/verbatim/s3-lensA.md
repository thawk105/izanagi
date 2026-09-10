静的検査の結論は **X を退け、Y を再設計する** である。テスト、書き込み、Web 検索は行っていない。

### [real] 実在する T-1097 PBS から `loop.run_campaign` への間接経路があり、「caller は 1 本もない」は偽である
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs:145-154` が計算ノードで `p3_autonomous_workload_trial` を live build 指定付きで起動する。既定 drive は `orchestrator/campaign/p3_autonomous_workload_trial.py:2768-2769` の `trigger.drive_iteration`、generation は同ファイル `:2629-2645` から drive を呼び、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:595-603` が `loop.run_campaign` を呼ぶ。repo 内の実測記録もこの経路を「唯一の sanctioned 経路」としている (`output/insights/2026-08-15_t1097-s8c-live-abc/README.md:13-19,24-31`)。D122 は production CLI 配線を明記済み (`docs/decisions.md:5915-5920`)。
- 成果物影響: request 911106 自体は先行 transport gate で停止し、数値は生んでいない (`output/insights/2026-08-15_t1097-s8c-live-abc/verbatim/attempts.jsonl:1-3`)。しかし transport 欠陥の別裁定後は、同じ実在経路が claim／reservation 無しで exploratory throughput、WAL、binary SHA、report を受理できる。X はその受理集合を無防備のまま残す。
- 反証条件: transport admission と正常な role 出力を通した同 CLI が、それでも `p3_s4_loop_trigger_gating.py:595` に到達しないという観測。または、repo が sanctioned と記録した既存 PBS artifact は DW-G04 の artifact path に数えない、という明示裁定。

### [real] 段 2 は DW-G04 に「成功 measurement ID」という余分な条件を加えて X を選んでいる
- 根拠: DW-G04 は「既存 artifact path **か**計測 ID」と規定する (`docs/dev-wave/core.md:60-63`)。一方、段 2 は実在 PBS 経路を自ら認定しながら (`/home/SFC/tanab/.claude/jobs/98dc5397/tmp/t330/s2-plan.md:24`)、911106 が完走しなかったことから artifact path まで不存在と扱う (`s2-plan.md:59`)。さらに D125 の旧 D108 前提 (`docs/decisions.md:6136-6139`) は D122 の compute opt-in (`docs/decisions.md:5878-5898,5915-5920`) と実在 PBS により現状説明として失効している。
- 成果物影響: T-330 の実装発火 gate を誤って閉じ、Pegasus exploratory report／台帳の受理条件に単独性証明を追加する機会を失う。transport gateを緩めず、T-330 の sink gateだけ先に fail-closedで置くことは可能である。
- 反証条件: DW-G04 の「artifact path」が「現行全 gate を通過した成功測定 artifact」に限る、という正本上の定義が示されること。

### [real] 現存する 8c PBS 経路には `/scr` fresh namespace も durable claim／reservation もない
- 根拠: live wrapper は `T1097_OUT` 配下へ依存を作る (`live.pbs:26-28,92-126`)。実 artifact の prefix も `/work/.../live/out/.../deps` である (`/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/out/0_911106.nqsv/cmake-prefix-path.txt:1`)。`TMPDIR` 未設定時の checkout は `/tmp` を使う (`orchestrator/campaign/patchharness.py:345-364`)、build cache は共有 checkout の `external/ccbench/build-variants` である (`orchestrator/campaign/p3_autonomous_workload_trial.py:3277-3278`)。wrapper の単独性検査は `pgrep ycsb` だけである (`live.pbs:46-58`)。
- 成果物影響: 911106 は計測前停止なので現値への汚染はない。ただし先行 gate が直ると、exploratory binary／throughput の build 起源と所有 job を report から証明できず、競合 build も `pgrep ycsb` では検知できない。
- 反証条件: この CLI が sink で `/scr`、scheduler reservation、stable claim を必須検査している観測、または実際の sanctioned wrapper がそれらを供給している artifact。

### [refuted] tracked `tools/pegasus/*.sh`／`tools/*.py` に、別の隠れた `loop.run_campaign` 起動経路がある
- 根拠: production AST inventory は 12 file、15 call で閉じている (`orchestrator/tests/test_campaign.py:4720-4740`)。`dispatch_compute.py` の task は tests／provenance のみ (`tools/pegasus/dispatch_compute.py:54-79`)。`floor_campaign.sh` は別実装の `s8b_floor_campaign.py` を起動する (`tools/pegasus/floor_campaign.sh:962-965`、`orchestrator/campaign/s8b_floor_campaign.py:4052,5114`)。限定検索では tracked shell、`python -c`、subprocess からの追加経路は出なかった。
- 成果物影響: 書けない (nit)。反証されたのは tracked tree 内の追加経路であり、上記の repo 外実在 PBS 経路は残る。
- 反証条件: tracked script から15 callのいずれかへ至る import、module起動、subprocessの具体的な call chain。

### [refuted] 凍結済み Pegasus 床値経路には、reservation／claim 前の early return や無 export 迂回がある
- 根拠: committed protocol は `env_tag="pegasus"` (`output/s8b-freeze/floor_protocol.json:1`)、その契約は `single_process=True` (`orchestrator/campaign/env_contract.py:245-253`)。driver は reservation を読み検査して失敗を再送出する (`orchestrator/campaign/s8b_floor_campaign.py:4205-4221`)、続いて claim を取得し (`:4235-4273`)、その後に初めて run directory へ進む (`:4275-4279`)。必須環境変数の欠落も拒否される (`orchestrator/campaign/reservation.py:120-175`)。official は core と CLI の双方で無条件拒否される (`orchestrator/campaign/s8b_floor_campaign.py:314-324,5099-5106`)。
- 成果物影響: `IZANAGI_RESERVATION_*` を全く持たない起動が Pegasus floor の受理値へ抜けるとは書けない。別 `linux-baremetal` protocol なら reservation 不要だが (`orchestrator/campaign/env_contract.py:284-303`)、別 namespace の pilot で `eligible_for_refreeze=false` となる (`orchestrator/campaign/s8b_floor_campaign.py:3707-3722,3809-3817`)。
- 反証条件: `env_tag=pegasus`、reservation env 欠落、claim 不在のまま publish された `result.json`、または official artifact。

### [real] 床値 claim は protocol 単位の排他でなく秒単位 run ID なので、二重投入を閉じていない
- 根拠: claim identity は fresh run ID から作られる (`orchestrator/campaign/s8b_floor_campaign.py:4235-4239`)、その ID は秒時刻と protocol hash prefix である (`:4618-4619`)。`O_EXCL` が排他するのは同じ identity のファイルだけ (`orchestrator/campaign/campaign_claim.py:98-103,167-202`)。異なる `out_root` 同士も排他しないことが明記されている (`:170-174`)。
- 成果物影響: 同一 protocol を異なる秒に開始した2 jobは別 claimを取得し、別ノードなら同時に pilot resultを作れる。同一ノードで一方が build中、他方が計測中でも probe は `ycsb_.*.exe` しか見ない (`orchestrator/campaign/s8b_floor_campaign.py:976-985,3410-3435`)ため、負荷で throughput、session median、floorが変わっても `competing_process` にならない。
- 反証条件: `single_process` が「各 fresh run ID 内だけ」の意味であり、同一 protocol の同時 campaign を許すという明示契約。または異なる秒の二重投入が同一 claim pathへ衝突する観測。

### [real] R3 は文字どおり恒真ではないが、reservation は caller 自己申告なので別 wrapperが合成できる
- 根拠: bindingの8値はすべて環境変数から作られる (`orchestrator/campaign/reservation.py:120-175`)。検査するのは現在の `PBS_JOBID`、boot ID、時刻、残容量だけで (`:218-270`)、現在 hostname、実行 script SHA、submission nonce は照合しない。claimには未検証の `binding.host` が転記される (`orchestrator/campaign/s8b_floor_campaign.py:4253-4262`)一方、journalの実ホストは別に記録される (`:3591-3607`)。
- 成果物影響: 別 PBS wrapper が自分の job ID／boot IDと整合する時刻を設定し、host、script SHA、nonceを任意値で合成して pilot数値まで進める。claimのhostとjournalのhostが不一致でもreservation gateは拒否しない。なお、bindingを無変更で別ノードへコピーするだけならboot ID検査で落ちるため、host未照合だけで全入力が恒真になるわけではない。
- 反証条件: driverがscheduler所有のcreate-only receiptを読み、qstat由来host、job ID、boot ID、script hash、nonceを現在値と照合している観測。

### [real] F319 により、実在 Silo ladder report の `clean:true` と性能値の proof chain が現在疑わしい
- 根拠: F319 は共有 masstree cache に ignored 生成物71件、`config.h` と archiveを実測した (`docs/failures.md:7705-7725`)。検査はHEADと通常のporcelainだけ (`orchestrator/campaign/silo_ladder_rung1.py:930-987`)、wrapperはその永続treeを`cp -a`で `/scr` へ複製する (`tools/pegasus/silo_ladder_rung1.sh:343-383`)。build自身もsource tree内へconfig/archiveを書く (`external/ccbench/cmake/ThirdParty.cmake:57-78`)。実在 report は `all_pass=true`、`performance_direction=true`、masstree `clean=true` を主張する (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:8,124-137,4053-4063`)うえ、例えば164649 TPSと3939248 TPSを載せる (`:3054,3089`)。
- 成果物影響: この ability-probe report の `clean:true`、`all_pass`、性能方向、各 throughput は、使用した `config.h`／archiveの起源をproof chainから確定できない。分類上はresearch／recovery非適格 (`:134-137`)なので、現 certified 選択そのものは変わらない。
- 反証条件: 当該job開始時のexact persistent snapshotについてignored fileが0件だった記録、または使用した`config.h`／archive bytesをjob-local生成receiptへhash束縛した記録。

### [real] 床値の oracle dependency hash は private marker に留まり、最終 manifest／binary bindingから脱落する
- 根拠: 床値preflightは共有masstreeのHEADと`config.h` hashを取る (`orchestrator/campaign/s8b_floor_campaign.py:1537-1578`)。oracle receipt自体もdependency rootとconfig hashを持つ (`orchestrator/campaign/sort_swo_oracle.py:1368-1385`)。しかし`PreparedCell.oracle_attempt` (`orchestrator/campaign/s1_direct_comparison.py:159-165,709-722`)は`binding_from_prepared`で捨てられ (`orchestrator/campaign/s8b_materialization.py:112-122`)、最終portable recordにもoracle receiptやconfig hashがない (`orchestrator/campaign/s8b_floor_campaign.py:2318-2339`)。D413もoracle rootと実build rootが別treeだと認定している (`docs/decisions.md:17303-17321`)。
- 成果物影響: 将来の`sort_best`床値 manifest／resultは、oracleを通した共有`config.h` bytesと実測binaryをproof chain上で結べない。`s8b-build-cache`だけ `/scr` へ移してもこの欠陥は閉じず、F319対応をT-1094／T-1095から横取りするS4単独実装も誤りである。
- 反証条件: 最終manifestのhash対象にoracle receipt、dependency config hash、実buildと同一のdependency rootが入り、verifierが完全一致を要求する観測。

### [refuted] `s8b-build-cache` が永続領域にあるだけで、正規 floor wrapperは同一binaryを跨ジョブ再利用する
- 根拠: floor wrapperはjob固有`/scr/$PBS_JOBID`にgflags／glogを置き、`CMAKE_PREFIX_PATH`へ設定する (`tools/pegasus/floor_campaign.sh:97-101,810-923`)。v2 identityは正準化したdependency prefix pathを含む (`orchestrator/campaign/buildcache.py:750-770,1043-1066,1307-1347`)。cache hit時もpreimage、admission、toolchain、binary SHAを再検査する (`:918-1005,1363-1385`)。
- 成果物影響: 書けない (nit)。正規wrapperではjob IDごとにprefix pathとdigestが変わるため、`s8b_floor_campaign.py:1953`の永続rootだけを根拠に既存floor値を汚染済みとは言えない。F319のthird-party source cacheとは別問題である。
- 反証条件: 異なるPBS jobが同じdependency prefix／digestで`cached=true`を得たartifact、またはdependency pathがjob間で再利用された記録。

### [real] X の「成果物不変」は certified だけを数え、DW-G05 が要求する exploratory report／台帳を落としている
- 根拠: 段2は「certified選択等は不変」とし、exploratory WALを将来物として除外する (`/home/SFC/tanab/.claude/jobs/98dc5397/tmp/t330/s2-plan.md:59-61`)。しかしDW-G05はreportと台帳の値／受理集合も対象にする (`docs/dev-wave/core.md:65-69`)。brief自身もYの成果物影響を「Pegasus由来のexploratory値が台帳に入る」と定義している (`/home/SFC/tanab/.claude/jobs/98dc5397/tmp/t330/brief.md:64-68`)。
- 成果物影響: Yのclaim／reservation gateはcertified選択を変えなくても、8c exploratory report、WAL、binary、throughputの受理集合を変える。したがって「certified不変」を理由にXへ落とすのは成果物会計の欠落である。
- 反証条件: exploratory report／WAL／台帳をDW-G05の成果物から除外する明示規定、またはcompute上の全callerが恒久的にsink前で拒否される証明。

## 総括
- 最重は、repoがsanctionedと記録したT-1097 PBSから`loop.run_campaign`への実在経路であり、Xのcaller不存在とDW-G04判定を崩す。
- 床値側もstable claimではなく、reservationは自己申告なので、二重投入と合成bindingを単独性証明として拒否できない。
- F319は実在Silo ladder reportのproof chainを既に疑わしくしている。ただしcache rootだけのS4では閉じず、Yはsink-local claim、権威あるreservation、fresh namespaceを一体で実装すべきである。