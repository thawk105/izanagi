### B1 read 側 API 照合には発火の正例がない

**重大度:** must-fix
**根拠:** `plan2.md:50-58,128,172-177`、`cicada-certified-evidence-design/README.md:65-80`、`ruling-D2300.md:3`。plan は API の checked 件数が正で違反 0 を求めるが、用意する壊しは B・U と既存の巡回用三本だけで、API の登録漏れ・余分な登録・誤った body 対応を発火させない。
**放置時:** API 照合が実質動かなくても合格し、「read 側も照合した」という一次資料と性能値の条件が強く見えすぎる。
**推奨対処:** `read()` 成功と read set の対応を一箇所だけ壊す小さな正例を追加し、API 違反の帰属を要求する。費用上それが難しければ、API の発火確認は未了と一次資料に明記し、D2305 項 4 の性能値条件を満たしたとは扱わない。

### B2 inline の追加 site は必要性を分けて見積もるべき

**重大度:** should
**根拠:** `plan2.md:7-13,28,79-85`、`external/ccbench/cc/cicada/include/tuple.hh:54-108`、`external/ccbench/cc/cicada/include/transaction.hh:173-245,343-367`。実行中の inline slot の返却は `gcAfterThisVersion()` と `writeSetClean()`、再取得は `newVersionGeneration()` を通る。`Tuple::init()` は初期化であり、YCSB point read/update ではもう一方の `init()` を使う INSERT は対象外である。
**放置時:** 同じ事象を `Tuple` と `TxExecutor` の双方で数える設計になり、世代の二重増分や計装面の拡大を招く。
**推奨対処:** 世代の初期値を `Version` の constructor で定め、実行中の増分を三経路の一箇所ずつに置けるか先に検証する。`Tuple` 側への追加は、三経路を迂回する対象内の呼び出しを示せた場合に限る。親 brief (P1) の三関数説をそのまま採るという意味ではなく、初期化と権利操作を列挙した上で計装箇所を最小化する。

### B3 既存 trace patch の強化だけでは B の主張に届かない

**重大度:** should
**根拠:** `patches/instr-cicada-trace.patch:8-25,79-88`、`plan2.md:10,23-30,75-92`、`vhash-cicada-best-config-verify/README.md:37,53`。既存の `trace_read_wts_` と `READ_WTS_MISMATCH` は登録時と commit 時の wts を比べる。同じ wts での再利用、切り離し後に再取得されない版、abort した読みはこの比較だけでは覆えない。既存 patch の bytes は md_20 の検査 build にも束縛されている。
**放置時:** wts 比較を B と呼ぶ局所修正では、実物の P5 型欠陥を検出できる範囲と論文の「回収・再利用されていない」が食い違う。
**推奨対処:** B の事象記録は別 patch に置く方針を維持する。一方、既存 mismatch 行を新たな合否面として増築せず、従来の回帰指標として扱う。

### B4 B の負例 0 件は登録前の取り違えを否定しない

**重大度:** must-fix
**根拠:** `plan2.md:17,28-32,183-187`、`external/ccbench/cc/cicada/transaction.cc:102-126`。版 pointer の取得から read set 登録までに走査と pending 待機がある。plan 自身が、最初の pointer 取得より後で世代を読み始める方式には窓が残ると認めている。
**放置時:** B 違反 0 を「生存中に読んだ値の版が取り違えられていない」全体の証拠にすると、一次資料の reads-from 忠実性と性能値の説明が過大になる。
**推奨対処:** 登録後から tx 終了までを検査した、という限定を論文用の文にも明記する。選択から登録まで含む忠実性を性能値格上げの必須条件とするなら、当該窓の保護または検出を別の設計判断として段 4 に戻す。

### B5 job 表は対照を共有でき、node 時間は現時点で未確定

**重大度:** should
**根拠:** `plan2.md:130-138,172-179`、`cicada-certified-evidence-design/README.md:121-132`。plan の「少なくとも 26 run」は B・U・旧壊し三本にそれぞれ stock 対照を足した計上である。同じ genome・cell・計装 bytes・実行条件なら、同時期の stock 対照を共有できる。一方、設計の 0.22〜0.36 node 時間は 10〜16 run の算術で、plan の条件数には適用できない。
**放置時:** 台帳の費用見積りが古いまま残るか、重複対照で 2 node 時間の枠を消費する。
**推奨対処:** 壊しごとに必要な対照条件を先に固定し、同一条件の stock run を共有する。生死確認で **run 時間・build・判定時間**を別々に測ってから総 node 時間を再計算する。異なる genome や E-max の対照を便宜上共有しない。

### B6 旧壊し三本は回帰確認として必要だが、役割を限定する

**重大度:** should
**根拠:** `cicada-certified-evidence-design/README.md:175-181`、`plan2.md:128,135-136,172-177`。md_24 の完了条件には既存の巡回検出三本が残っている。一方、それらは M の B・U・API 照合の発火を示す壊しではない。
**放置時:** 三本の再走を M の新しい照合の検出力として数えれば一次資料が誤り、三本を省けば既存の巡回検出を壊していないことが未確認になる。
**推奨対処:** 三本は M を重ねた後の判定器回帰として各一本走らせる。対照の共有で run 数を削り、M の発火証拠は専用の B・U・API 正例と区別して記す。

## 総括

現状の plan はそのまま採用しない。M を判定器・campaign に入れず、CCBench の patch、repo 外起動器の合否、一次資料を成果物とする範囲設定は D2305 に合っている。BEST の性能値へ M の証拠を結ぶなら inline 対象化も必要で、範囲外案ではその性能値の地位は上がらない。ただし inline 計装箇所は初期化と実行中の事象を分けて縮められる。採用前に read 側 API の正例を用意し、B の登録前の窓を主張へ反映し、対照共有後の実測単価で node 時間を更新する。各合否 field は生死確認で実在・要求値への到達を確かめる。静的相談のため、patch 適用、build、発火、所要時間は未確認である。