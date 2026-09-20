## 計画

以下の行番号は現行ファイルに対する変更アンカーである。`parse.py` 等は `orchestrator/verifier/` 配下、`test_verifier.py` は `orchestrator/tests/` 配下を指す。brief・facts・裁定抜粋は指定された job dir の資料を指す。

指定資料の読取りと署名・field・pin の静的照合のみ実施した。profile、probe、pytest は未実施。以下の数値閾値は**段 4 で事前登録する採否案**であり、実測結果ではない。

1. **現行の記憶量会計と原因の分岐**

   根拠は [facts.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/refs/facts.md:9)、[dsg.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-capacity/orchestrator/verifier/dsg.py:253)、`parse.py:547`。

   `N=winner txn 数、W=write 数、K=writer を持つ鍵数、E=重複除去後の辺数、C=辺候補数、R=source run 数、S=source 数` とする。以下は 64-bit CPython の概算であり、allocator の余白・共有・再利用を含む実測とは分ける。

   | 構造 | 現行の会計 |
   |---|---|
   | `producer` | write ごとの key 文字列約 `49+文字数` B、外側 tuple 約56 B、dict 表領域約30〜60 B/entry。16文字 key なら約150〜190 B/write。 |
   | commit・txid | `dsg.py:258–263` で **txn ごとに一度**生成し、同じ txn の writes 間で共有する。版 tuple・整数を write ごとに全額計上しない。概ね100〜150 B/txn。 |
   | `per_key` と `versions` | `:285–288`。前者の list と後者の sorted list の参照列が約16〜18 B/write。`per_key` は edge 構築呼出し中も生存する。`sorted(set(...))` の一時領域は最大の一鍵分。 |
   | parse 列 | `parse.py:573–598`。概ね `48N + 20 reads + 8W` B、別途 token blob・offsets・winner 参照列約20N B。 |
   | 辺候補 | `dsg.py:170–183`。概ね `8C+16R` B。worker は `destinations_by_source` と返却 `run_dst` を同時に持つ。pickle の転送中コピーも別途ある。 |
   | 隣接構築 | `:370–382`。set slot 約27〜64 B/edge、配列から生成する int 約28 B/edge、tuple 参照8 B/edge。さらに set・dict・tuple の source ごとの固定費。set→tuple の変換中は両容器が生存する。 |
   | Tarjan | `:432–478`。三つの dict、index 整数、stack、DFS の tuple・iterator。概ね150〜300 B/訪問頂点を初期見積りに置く。辺単価ではなく `N/E` で寄与が変わる。 |

   write-heavy 6 s の `18.8 GiB / 47,250,018 ≈ 427 B/write` は**主 process 全体**の比率である。producer/versions が write 比例の大項だが、50.8M edges の隣接・候補・parse 列も含む。producer 単体を400 B/writeと断定しない。

   read-heavy 6 s の `85.6 GiB / 594,786,279 ≈ 155 B/edge` も全体比率である。隣接の概算63〜100 B/edgeに source 固定費、候補、parse 列、producer、Tarjan、allocator の残留が加わる。こちらは **E 比例の隣接構築が支配候補**である。各 phase の最大値を足して peak と呼ばず、同時生存量で照合する。

   balanced 10 s の主 process 21.2 GiB・SIGKILLだけでは、親の構造、CoW、worker 自身の配列増大を区別できない。

   **parse worker peak。** `parse.py:549–553,585–606` は全ファイル分の `Txn/Read/Write`、`local_txns`、`occurrences`、token intern 表、列を重ねて保持する。初期モデルを次とする。

   ```
   400〜650 B/txn + 250〜350 B/read + 180〜260 B/write
   + 列の容量 + token intern 表 + 転送中コピー
   ```

   48ファイル均等なら write-heavy 6 s は一 worker 約0.25〜0.4 GiB、read-heavy 6 s は約2〜3 GiBが目安。ただし偏りと既存列の受領量を含めて測る。read-heavy の16 worker同時生存は無視できない。P5外の scanner 全面書換えを自動追加せず、parseだけで容量目標を破る場合は段4へ戻す。

   **edge worker の CoW 対象。**

   | 読取り位置 | 触る親側 object と区別 |
   |---|---|
   | `dsg.py:116–119,133` | state、trace、files tuple、columns、dict/array の header。取得した参照の refcount 更新はありうる。 |
   | `:134–145` | array payload は読取り。取り出した整数と decode 後の key は原則 worker 側の新 object。親の整数配列全体を refcount で複製する操作ではない。 |
   | `:146` | producer lookup の比較で格納済み key tuple・key str・version tupleを読む。返却する writer int の refcount は更新されうる。すべての格納 key str が単なる lookup だけで必ず dirty になるとは断定しない。 |
   | `:151–155` | versions dict から取得した list、bisect が取得・比較する version tuple、その内部整数、successor lookup が返す writer int。 |
   | `:160–164` | `keys` tupleから取得する親の key str、versions list、その版 tuple、producer の writer int。ww走査は広い範囲を触る。 |
   | worker内のGC | tracked containerのGC header。参照カウント更新とは別経路。`freeze` はこちらを抑えるが refcount CoW は止めない。 |

   **P3を判別する観測を固定する。** `phase.wall_s`、`tree.pss_peak_gib`、`edge.private_dirty_sum_peak_gib`、`edge.parent_rss_at_fork_gib`、`node.memavailable_min_gib`、`vmstat.*_delta`、`edge.pool_failure_count`、`edge.fallback_count`、worker exit/signalを記録する。

   - (a) producer phase の増分、隣接 replay phase の増分をそれぞれW・Eで割り、項目2の(i)/(iii)へ進む。
   - (b) worker出力配列の容量を差し引いても Private_Dirty の増大が残り、node MemAvailable低下と一致する場合をCoW支持とする。RSS和だけの増大は支持に数えない。
   - (c) `pswpin/pswpout`増大はswap支持、`pgmajfault`単独は補助証拠。worker終了→pool失敗→fallbackの連続記録があればfallback型。`oom_kill`はnode全体の値なので、worker PID/終了時刻との対応なしに当該workerのOOMとは断定しない。
   - どちらも出なければ原因未同定とする。未登録の高速化や並列度変更へ逃げず、目標達成の主張を留保する。

2. **P5各案の実装設計・採否**

   **共通条件。** `core.py:53–190` の完全性検査、判定、結果組立てと、`core.py:248–338,373–386` のcapability発行・消費は親に残す。`report.py:96–136`、`model.py`、CLI schemaは変更しない。判定一致にはanomalies・notes・配列順も含む。

   採否probeは旧版と候補版を別processで同一入力に適用する。`estimate.<案>.wall_ratio` は同じ処理境界の旧比、`saved_*` は旧から候補を引いた値。**同一性検査の不一致は、性能にかかわらず不採用**とする。以下の条件を満たす案だけを指定順に積み上げ、組合せも測る。条件未達時の代替設計をauthorが追加しない。

   **(i) write単位dictを鍵単位の版・producer配列へ。**

   - **変更位置:** `dsg.py:253–288`、lookup側`:146–164`、理由再構成`:525–545`。
   - writer鍵だけに初出順IDを振る。各鍵にpacked versionの`array("Q")`とproducer txidの`array("q")`を並走させる。親はread全行を走査しない。
   - 収集中はwriteの論理ordinalも保持し、鍵単位で版順に安定整列する。重複版のwriterは現行どおり最初を保持し、それと異なるtxidによる**各write occurrence**を違反に数える。異なる鍵のduplicate notesとgenesis notesは元のordinal順へ戻す。同じwriterの重複writeを違反へ変えない。
   - fast encodingは `0≤epoch,tid<2**32` に限定して `(epoch<<32)|tid`。対象writeが範囲外なら、部分状態を破棄して従来compact builderを使う。範囲外readはtuple版比較のlookupへ退避し、切捨て・wrapしない。parseの任意精度→legacy経路も保持する。
   - `graph.producer[(key, version)]`、`graph.versions.get(key)`、`tuple(graph.versions)`を保つ薄い内部viewを`dsg.py`内に置く。内部edge処理はpacked配列を直接使い、view経由のtuple再生成を通常経路へ戻さない。
   - **効果見積り:** 最終版payloadは16 B/unique write、鍵ごとの容器・key・dict固定費が概ね200〜350 B/K。収集中ordinalでさらに8 B/write、整列中は最大一鍵分の一時objectを会計する。wallは全体sortでなく `Σ Wk log Wk` の整列＋lookup。高速化は保証しない。
   - **採用条件:** 両6 s入力で `estimate.i.saved_bytes_per_write ≥64`、builder peak旧比`≤0.75`、builder wall旧比`≤1.5`。
   - **pin:** `test_version_dup_keeps_first_writer_note_and_edge:2704`のnote、producer lookup、`adj == {0:(2,)}`を維持。`test_epoch_version_order_g2:2062`、`test_epoch_rw_successor_order_g2:2073`、`test_multi_ww_reason_report_is_hash_seed_deterministic:1592`の版順・WW理由順も維持する。

   **(ii) fork時の共有入力を配列主体にし、freezeを限定適用。**

   - **変更位置:** `dsg.py:53–59,94–96,110–164,312–345`。`_EdgeWorkerState(trace, producer, versions, keys)`の既存引数を維持する。
   - (i)採用を前提とする。鍵ごとの配列をflatなversion/txid配列とkey offsetsへまとめる。writer鍵検索はkey blob・offsets・辞書順ID配列を使い、workerはtokenから検索する。writer不在はsentinel。親の巨大なstr/tuple/int graphの反復lookupを外す。
   - first-seen key順は別に保持してww順を守る。fileローカルtoken番号は変更しない。`_EdgeWorkerState`やarray headerまで「触れない」とは主張せず、**write数に比例するPython object参照を除く**。
   - freezeはpool生成前、解除はshutdown後の`finally`。既存freeze領域が非空、非main thread、複数threadが存在する入口ではfreezeを省略して配列経路だけ使う。開始時のGC enabled状態を保存し、例外・daemon fallbackでも復元する。poolのsubmitを囲む大域lockは置かない。
   - **効果見積り:** fork共有payload自体のB/writeは(i)相当。削減対象はworkerごとのCoWと鍵ごとのPython容器。wallはblob検索の追加費とpage fault削減の差を実測する。
   - **採用条件:** 段1で `edge.private_dirty_sum_peak_gib / edge.parent_rss_at_fork_gib >1`、かつ両6 s入力で `estimate.ii.array_only.private_dirty_ratio ≤0.5`、edge phase wall旧比`≤1.5`なら配列化を採る。freeze追加はarray-only比でPrivate_Dirtyをさらに10%以上減らし、wall比`≤1.1`、GC状態復元test一致の場合だけ採る。比率5超は強いCoW支持だが、採否閾値そのものにはしない。
   - **pin:** `test_concurrent_verifications_keep_edge_worker_inputs_isolated:2246`の二つのpoolがともにforkできること、`:2211`の実worker結果採用、`:2384`のdaemon fallbackを維持。stateを親のmodule globalへ書かない。

   **(iii) source単位のset再生＋CSR。**

   - **変更位置:** `dsg.py:290–382,423–425,439–456,481–502`。
   - readの`_weighted_ranges`は**読み手rankの分割**であり、wrのsourceはwriterなのでsource範囲とは一致しない。`:307–310`の原task境界・番号・kindを維持し、全task受領検査後の親replayをsource範囲で分割する。全readをsource shardごとに再走査しない。
   - `:99–107`で全taskの件数・番号集合を検証してから、task順・run順にsource初出列を保存する。
   - runをsource別に連結する。受領済み`run_src`の各slotはsourceを読み取った後にnext-run番号へ再利用する。task別run総数のprefixでglobal run番号と元の`run_offsets/run_dst`を対応付ける。source別head/tailは配列とし、index完成後tailを解放する。これにより候補destination全体の追加コピーを避ける。
   - source別候補数の重みでreplay範囲を作り、各sourceにつき**空set一個**へ、リンク順に従来と同じ`set.update(array slice)`を実行する。set反復順をそのままCSR dstへappendし、そのsetを捨てる。source間の処理順とTarjan root順は分離する。
   - `offsets=array("Q")`、`dst=array("q")`、source初出順配列を保持する。dstは昇順にしない。既存の`adj[...]`比較にはtupleを返すviewを用意し、SCC/BFS内部はコピーしないrange iteratorを使う。
   - 配列indexの適用条件は(iv)と共通。巨大で疎なtxidでは従来隣接を使う。
   - **peak:** graph側は概ね

     ```
     8C + 16R                         受領候補（既存run_srcを再利用）
     + 8E + 8(U+1) + 8S             CSRとroot順
     + O(U)                          head・一時tail/weight
     + 最大一sourceのsetとarray slice
     ```

     `U=max(txid)+1`。parse/index、pool転送buffer、allocator余白は別途加算する。「候補＋CSRだけ」には厳密にはならないが、全sourceのsetとtupleの同時保持を除ける。巨大な一sourceの次数もprobe対象とする。
   - **採用条件:** 両6 s入力で `estimate.iii.saved_bytes_per_edge ≥32`、replay peak旧比`≤0.60`、replay wall旧比`≤2.0`、全sourceの隣接tupleとroot列が一致。
   - **pin:** `:2506`の`[1,8]`、`:2576`の`adj[0]`、run destination、run source初出列、SCC順、report上限をすべて維持する。直接呼ばれる`_edge_candidates_for_task(task, state=None)`の戻りfieldは変えず、runの再利用は親の内部処理に限定する。

   **(iv) txid直接indexのTarjan。**

   - **変更位置:** `dsg.py:429–479`。`parse.py:728–743`の昇順`winner_txid`を根拠に `U=last+1` を定数時間で得る。
   - compactで `U≤2N` のときだけ、index/lowを`array("q")`、on_stackをbytearray、node stack・DFS node/cursorを固定幅配列にする。index初期値は−1、txid=0を未訪問sentinelに使わない。rankへの変換やO(E)の登録passは置かない。
   - missing_txidsがあっても上の密度条件なら使える。穴は訪問せず、integrity値をそのまま残す。巨大疎空間・legacy・`DSG.__new__`でadjだけを持つtest objectには従来dict Tarjanを使う。
   - rootsは(iii)のsource初出列、隣接はset由来順、DFS終了時のpop・low伝播は現行と同じ。`_shortest_cycle:481`の最小txid開始・BFS順も保持する。
   - **効果見積り:** index/low/on_stackで17U B、stackとDFS状態で最大約24N B。dict版の概算150〜300 B/頂点を削る。Python arrayアクセスのboxingは残る。
   - **採用条件:** `estimate.iv.saved_bytes_per_vertex ≥64`、SCC peak旧比`≤0.60`、全Tarjan wall旧比`≤1.5`、SCCの**内部pop順と外側列順**が一致。両6 s入力では(v)を強制無効にして測る。
   - **pin:** `test_scc_dense_arrays_keep_root_emission_order_for_both_adjacency_types:2679`は名前に反して現行実装の配列使用を要求していない。adjだけのobjectで`[[10,9],[5,4]]`を返す経路を残す。`:2821`のtxid=`10**12`もboundedのままにする。

   **(v) txid前向き判定。**

   - **変更位置:** `dsg.py:569–575`の直前判定。辺候補の完全性検査、全edge構築、orphan集計後に親で行う。最初の逆向き辺で判定を打切り、その場合は必ず従来の全Tarjanへ進む。
   - 健全性は次の3行で固定する。

     > 任意の全順序 `<` について、全辺 `u→v` が `u<v` を満たすとする。  
     > cycleがあれば推移律により `v0<v1<…<vk<v0` となり、全順序の非反射性に反する。  
     > よって非巡回であり、条件を満たさない場合については何も結論しない。

   - 真なら`anomalies`は`([],0)`を返すだけとし、`core.py:60–171`と`model.py`のcertified条件を迂回しない。edge worker自体を省略してPID pinを壊さない。
   - **効果見積り:** 保存量はほぼ0、発火時はTarjan作業配列・dictを不要にする。最悪追加費O(E)、非発火時は先頭逆向き辺まで。
   - **採用条件:** `estimate.v.backward_edges`と`forward_fire`を両6 s・3 s全workloadで記録。校正緑traceの少なくとも1件で発火し、その入力で `SCC判定wall比≤0.8`、非発火入力で総wall比`≤1.05`なら採る。全部非発火なら不採用。
   - **pin:** `r1`〜`r9`全件、とくに`r8_silo_broken_norw`で、親の全Tarjan入口が実際に呼ばれ、旧reportと一致するtestを追加する。`max_report=0`でも全cycle数を保持する既存`:213`を維持する。

3. **P2のwitness同一性**

   根拠は [dsg.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-capacity/orchestrator/verifier/dsg.py:367)、`:439,489,575`。

   | 案 | 記憶量・所要 | 同一性と裁定 |
   |---|---|---|
   | **A: set順をCSRへ保存** | CSR本体8 B/edge。再生時だけ一sourceのsetとsliceが必要。dstのsort費用なし。 | 同じ整数挿入列・array slice投入・source初出列を保存する。親の既定とD1664に従う。 |
   | B: dst昇順canonical | CSR本体はAと同じ。集合処理またはsort/uniqueが必要で、構築peakが自動的にAより小さくなるわけではない。 | BFS選択が変わりうる。P2と「既存期待値変更なし」に反するため段4裁定が必要。 |

   **推奨はA。** `set`の事前容量確保、set/dictを引数にしたupdate、worker側の先行dedupは行わない。

   pinの射程は区別する。

   - `test_broken_silo_norw_structured_report_is_exact:1837`はanomalyの`edges`列をliteralで固定する。ただし外側はfrozensetをkeyにしたdictへ変換しており、**anomaly列順そのもののpinではない**。
   - `test_broken_silo_norw_fixture_contract:1738`も辺・理由を固定するが、集合化を含む。
   - `test_multi_ww_reason_report_is_hash_seed_deterministic:1592`は全JSONのseed間一致とWW理由のkey昇順を固定する。全anomalyのliteral goldenではない。
   - `test_serial_parent_optimizations_match_workers_and_pin_witness_order:2576`はSCC順、`[[17,24],[0,8]]`、理由列を固定する。
   - `test_parallel_edge_replay_uses_global_logical_ordinal:2506`は異なる到着順で`[1,8]`を固定する。
   - `test_real_silo_fixture_bytes_are_exact:2053`が固定するのは**入力trace bytes**であり、anomalyのedgesではない。

   静的な危険候補は、複数cycleを持つr8と、衝突する宛先を持つ`:2533`の合成traceである。後者は順序保存の強い回帰対象。ただしr8がdst sortで実際に変わるとは、fixtureの実走なしに断定しない。r9は4辺の単純cycleであり、隣接tie-break変更の検出力は小さい。追加testには同じ最短長のcycleを二つ持ち、set順とdst昇順が異なるsourceを明示的に用意する。

4. **段4→5間の見積りprobe**

   入力・復元条件は [facts.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-capacity/refs/facts.md:25)。親が計算ノードへ投入し、authorはjob dir `probe/`だけへ使い捨て実装を書く。

   - baselineと候補を別processで動かす。balanced 6 s、read-heavy 6 sを必須とし、(v)だけ3 s全3workloadも追加する。trace path、expected_commits、source context、`max_report`を統一する。
   - (i)は全writeのindex構築・lookup、(ii)は実forkと同じ全task、(iii)は全候補からのsource再生、(iv)は全Tarjan、(v)は全辺の逆向き件数を測る。小標本外挿だけで採用しない。
   - 各variantについて`payload_bytes`、`phase_peak_pss_bytes`、phase開始時からの増分、`bytes_per_write`、`bytes_per_edge`、`wall_s`を分けて出す。W/Eが0なら単価はnull。②で使う`estimate.*`の派生値も同じJSONへ記録する。
   - (ii)は旧object版、配列のみ、配列＋freezeの三条件を比較する。workerの出力生成量も測り、Private_Dirty減をすべてCoW削減と呼ばない。
   - (iii)はC/E、R/E、最大source次数、最大slice、pickle payloadと送受信peakを記録する。raw runの順序、完成隣接tuple、root列の一致を検査する。
   - (v)は `backward_edges = count(src >= dst)`をdedup後の辺で数え、`forward_fire = (backward_edges == 0)`を記録する。実装の早期打切り測定と、probeの全件計数は別計時にする。
   - 同じnodeで旧→候補→旧の順に測り、旧2走のwallが10%以上ずれる場合は採否を保留する。段1で発見した停止phaseを含む組合せprobeも実施する。

   各測定は復元後sha256照合、`_assert_single_tenant()`、開始時MemAvailable≥100 GiBを満たしてから開始する。Pss・Private_Dirty・MemAvailable・vmstatを時系列で採る。計測probe自身の出力にreportのfieldを追加しない。

   組合せの10 s見積りは、実入力のN/W/K/C/Eと6 sの単価・処理速度を使い、peakとwallに25%余裕を付ける。それでも115 GiB/3600 sを超える場合は実装着手条件未達とし、authorの設計変更で解決しない。最終的な達成判定は実測で行う。

5. **段5の実装単位と順序**

   一authorが以下を順に実施する。変更ファイルは既存`parse.py / dsg.py / core.py / test_verifier.py`に限定し、`core.py`は原則変更不要。新moduleは作らない。closure根拠は [campaign_lock.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-capacity/orchestrator/campaign/campaign_lock.py:58)、`:127,155`。

   1. 旧版のfixture全件reportと、3 s全3workloadのreportを固定する。**同じ絶対trace_dir**を使い、`json.dumps(result_to_dict(...), sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()`のsha256を保存する。field削除による正規化はしない。
   2. 採用された(i)を入れ、fixture全件のsha256、duplicate・epoch・理由順を確認する。
   3. 採用された(ii)を入れ、同じsha256、concurrent・daemon・実worker使用・GC復元を確認する。
   4. 採用された(iii)を入れ、同じsha256に加え隣接・root順を比較する。
   5. 採用された(iv)、続いて(v)を入れる。各段で同じsha256を再確認し、(iv)は前判定無効状態でも検査する。
   6. 最終組合せで`workers=1`と`16`、既定、既存の明示48上限testを確認する。

   **fallbackの生存量も修正する。** `parse.py:793–798`と`dsg.py:318–359`は、失敗後の`received`やfutureが部分配列を保持したまま再計算へ進みうる。pool停止後に部分結果・future参照を解放してから**全件**を再計算する。成功時のPID集合は採用outcomeだけ、fallback時は親PID。観測したが不採用のworker PIDを混ぜない。

   parse側は`_ParsedFileColumns`のfieldとtoken順、`_merge_issues_and_winners:695`のsorted-file/line順・last-wins・欠番計算を維持する。全Txnを保持するscannerのstream化は本計画に追加しない。

   追加testは既存末尾`:2867`のrunnerより前に置く。

   - `test_capacity_all_fixture_reports_match_baseline_sha256`
   - `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`
   - `test_capacity_csr_preserves_set_collision_and_source_order`
   - `test_capacity_txid_arrays_preserve_gaps_and_destination_only_nodes`
   - `test_capacity_sparse_txids_avoid_dense_allocation`
   - `test_capacity_positive_fixtures_always_run_full_tarjan`
   - `test_capacity_backward_acyclic_graph_runs_full_tarjan`
   - `test_capacity_forward_shortcut_preserves_unclean_and_empty_results`
   - `test_capacity_gc_state_restored_on_success_and_failure`
   - `test_capacity_partial_outcomes_are_released_before_full_fallback`
   - `test_capacity_workers_1_and_16_match`

   `test_verifier.py:2211,2642,2754`はPID診断の消費者である。一方、receipt側が`_LAST_*`を認証に使うとは射影から確認できない。確認できる契約は`test_parallel_capability_remains_bound_to_parent_pid:2838`と`core.py:266,311–316`の**発行親PIDへの束縛**であり、これを維持する。

6. **段4で事前登録する変異matrix候補**

   追加testの配置アンカーは`test_verifier.py:2867`。

   | 殺す変異 | 殺すtest |
   |---|---|
   | (v)を常に発火させる | `test_capacity_positive_fixtures_always_run_full_tarjan`、既存`:213` |
   | 逆向き辺一つでnon-serializableとする | `test_capacity_backward_acyclic_graph_runs_full_tarjan` |
   | 前判定成功でintegrityをcleanにする | `test_capacity_forward_shortcut_preserves_unclean_and_empty_results` |
   | CSRのdedupを外す | `test_capacity_csr_preserves_set_collision_and_source_order`で反復辺と正確なn_edgesを固定 |
   | source内runを完了順・逆順へ変える | 同test、既存`:2506,2576` |
   | dstをsortする／rootをtxid順にする | 同test、既存`:2576,2679` |
   | txid indexを±1ずらす／0を未訪問とする | `test_capacity_txid_arrays_preserve_gaps_and_destination_only_nodes` |
   | 密度guardを外す | `test_capacity_sparse_txids_avoid_dense_allocation`。割当て入口にspyを置き、実巨大割当てに依存せず殺す |
   | packed versionをwrap／tid優先で整列 | `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`、既存`:2062,2073` |
   | duplicateの最後writerを採る／notesをkey順にする | 同test、既存`:2704` |
   | 欠落task/fileの部分結果を採用する | 既存`:2418,2734` |
   | 解放せずfallbackへ進む | `test_capacity_partial_outcomes_are_released_before_full_fallback` |
   | failed worker PIDを採用PID集合へ混ぜる | 既存`:2754`と追加fallback test |
   | freeze解除・GC状態復元を省く | `test_capacity_gc_state_restored_on_success_and_failure` |
   | 親globalへworker入力を置く | 既存`:2246` |

   変異は対応する採用分岐だけに適用する。不採用案の変異をKILLEDに数えない。

7. **段6後の最終実測**

   `facts.md:25–44`の復元・node投入手順を使い、項目4のprobeを改修版の`core.py:28`全経路へ適用する。fixed-5の10 s×3workloadと3 s×3workloadを、nodeごとに独立したsubmit-treeから検証する。

   | 比較対象 | 要求 |
   |---|---|
   | fixture全件 | 旧新の`result_to_dict` sha256一致。赤fixtureは全Tarjanを通って赤。 |
   | 3 s×3workload | 同一path・expected_commits・source contextで旧新sha256一致。 |
   | 10 s×3workload | 各件が115 GiB以内、3600 s以内に完走。`serializable`と`certified`を記録。旧verdict欄は「なし／比較不能」。 |
   | briefの完走済み校正12 verdict | 親が提示する既存一覧に対しverdict・certified・anomaly_count・total_cycles・integrity・statsを照合。 |

   表にはwall、主process maxrss、process tree Pss peak、Private_Dirty peak、MemAvailable最小、fallback有無も付す。RSS和をnode使用量としない。Pssはprocess記憶量の指標なので、node側の占有変化も併記する。

   10 sの結果を「旧新一致」と記載しない。600 sを超えても本waveの容量目標とは分けて記録し、校正規則や`indeterminate (operational)`の扱いを変えない。

8. **リスク表**

   | 事象 | 検知方法 | 対処 |
   |---|---|---|
   | 巨大pickle転送・候補配列の重複保持 | `dsg.py:333–345`で転送bytes、worker返却時・親受領時peakを測る。read-heavy 10 sの16 GB超は未確認仮説 | 全task到着後のfuture参照を解放。上限未達なら採用保留。新spill機構を自動追加しない。 |
   | hottest keyのsortがpeakを支配 | `dsg.py:285–287`相当probeで最大Wkと一時領域を計測 | (i)のpeak条件を満たさなければ不採用。 |
   | packed整数の範囲逸脱 | `parse.py:575–600`と追加境界test | 範囲guardと従来比較・builderへの退避。wrap禁止。 |
   | array/bisectのboxingで遅くなる | `dsg.py:153,163`相当のwall・lookup件数 | (i)/(ii)のwall条件で不採用。 |
   | freeze解除忘れ・呼出し元のfreeze状態破壊 | pool成功・例外・daemon・既存freezeのtest | 既存freeze時は追加freezeしない。`finally`で所有した変更だけ復元。GCはprocess全体の状態という限界を明記。 |
   | set順が再現されない | `dsg.py:375–378`、隣接tuple全比較、collision test | 原task順、元array slice、空setからの再生を保持。 |
   | source連結indexの破損 | run総数・到達数・重複到達・辺候補総数のtest | 受領完全性確認後だけ再利用。失敗時は部分CSRを採用しない。 |
   | source一個の巨大次数 | 最大source次数・set peakを測る | 「一sourceなら小さい」と仮定しない。容量条件未達は段4へ戻す。 |
   | 疎なtxidで巨大配列割当て | `parse.py:728–739`、既存`:2821` | `U≤2N` guard、従来dict経路。 |
   | legacyとcompactの意味差 | `core.py:38–48`、既存`:2671`、追加overflow test | legacyを残し、同じnotes・anomaliesまで比較。 |
   | parse workerが依然支配 | `parse.py:547` phaseのtree Pss | scanner書換えへscopeを拡張せず、目標未達として親へ戻す。 |
   | campaign lock drift | `campaign_lock.py:58,127,155`の対象bytes変更 | 既存lockの再開不能を記録。lockを書き換えて継続しない。 |
   | queue滞留・node同居 | `facts.md:40–44`の投入結果と開始条件 | queue待ちとverifier wallを分離。同居時は測定不成立。loginへ測定を移さない。 |

## brief と食い違う点

- **P3(a)の単価の解釈。** 約400 B/write・150 B/edgeは全主processの経験比率。`dsg.py:261–285`ではcommit tupleとtxidがtxn単位で共有され、producer単体の単価ではない。代案は項目1の同時生存構造別会計。
- **P5(i)の整数幅。** `Version`はtuple、compact列も各要素がsigned 64-bitであり、常に一つの64-bit整数へ詰められる保証はない（`model.py:23`、`parse.py:575–600`）。代案は限定幅fast path＋従来経路。
- **P5(ii)の無条件freeze・「配列だけ」。** state/header参照は残り、GC状態はprocess全体に及ぶ。既存concurrent testは二つのpoolの同時進行を要求する（`test_verifier.py:2246–2322`）。代案は配列化を本体にし、freezeを適用条件付きの追加措置にする。
- **P5(iv)のdense前提。** 巨大で疎なtxidをboundedに扱う既存契約がある（`test_verifier.py:2821`）。代案は`U≤2N`の直接indexと従来dict経路の併存。
- **比較対象12 verdictの特定不足。** brief`:8`は12件を要求するが、facts`:9–16`に示された完走行は7件で、12件のexact一覧は射影にない。代案は親の既存一覧を段4入力として固定すること。件数を推測して補わない。

P1、P2のA案、P4、新file禁止、既存test期待値変更禁止には従う。

## 総括

write単位objectと全sourceのset同時保持を減らし、原task順・隣接順・SCC順を保存する。  
各案は事前登録したprobe閾値とreport完全一致を満たした場合だけ採る。  
最大のリスクは候補転送・parse worker・CoWを含む同時peakと、source再生の所要である。  
段3では、run_src再利用の順序証明、版重複notesの再現、freezeの適用境界を重点的に攻撃してほしい。