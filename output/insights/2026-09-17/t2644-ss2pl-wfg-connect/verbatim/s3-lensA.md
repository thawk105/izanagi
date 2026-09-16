## 前提の検算 (brief・plan の記述と現物のずれ)

指定資料はすべて指定範囲を読めた。以下は静的点検であり、変更・pytest・build・実走は行っていない。略記は次のとおり。

- `brief`：指定の `s1-brief.md`
- `plan`：指定の `s2-plan.md`
- `D791`：指定の `verbatim-d790-d791.md`
- `patch`：[ss2pl-lock-protocol-study.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/patches/ss2pl-lock-protocol-study.patch)
- `runner`：[run_ss2pl_lock_study.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/tools/pegasus/run_ss2pl_lock_study.py)
- `test`：[test_ss2pl_lock_study.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/orchestrator/tests/test_ss2pl_lock_study.py)

**所見**
plan の接続修正は概ね妥当。ただし「P1〜P7 を採用できる」は条件付きに直すべきである。特に、独立検証の意味、counter の鮮度、逐語 fixture の取得手順が不足している。P3 の欠番については、今回の phase1 で誤受理経路が成立するとは判断しない。

**現物の根拠 (file:line)**
`brief:49` は `held_locks` を「実証枝」と呼ぶが、その出所は `patch:2313` の registry コピーである。`brief:52` の既存 test は新 schema と同じではなく、`test:1420` は boolean 証拠を使う。`plan:64` が追加した排他 mode 正規化は、`patch:525` の実所有表現と `runner:2365` の判定の差を正しく補う。

**成立条件**
対象を `IMPL=1 KIND=0 DLR=0 WFG=1` の YCSB とし、実装構造からの論証と、実データによる確認を区別すること。

**影響**
無条件に採用すると、接続成功を「実状態を独立観測した証明」や「逐語一致確認済み」と過大評価する。

**是正案**
plan に以下の条件付き論証を組み込み、I1・I4 の「緑」は実装後の既存受入結果へ置き換える。

## 判定材料の出所 (条件 1)

**所見**
`held_locks` は boolean より検算可能性が高いが、独立した観測源ではない。`compatible:false` だけを信用する設計にもなっていない。検証器は mode から非両立性を再導出する。

**現物の根拠 (file:line)**
`runner:2446` で waiter の待機 lock、`:2452` で要求 mode、`:2455` で holder の保持情報を照合し、`:2458` で `_edge_is_incompatible()` を呼ぶ。`held_locks` 枝は `runner:2375`、boolean の即時受理枝は `:2373`。一方、辺も保持一覧も `patch:2316` の同じ registry コピーから生成される。

**成立条件**
計器が取得・解放を正しく反映しているという信頼境界が必要である。その上で、検証器は辺の端点・lock ID・mode・非両立性を再計算できる。排他 mode の `"write"` 正規化は `patch:525` と対応する場合に限って正しい。

**影響**
registry 自体や mode 正規化が誤れば、辺と保持一覧が同じ誤りを共有し、検証器の照合を通過し得る。

**是正案**
I2 の「実証枝」を「同一 snapshot の保持一覧との照合枝」と記述する。`compatible:false` は残し、再導出も維持する。`held_locks` の採用だけで実 holder の正しさを証明したとはせず、次節の更新順序をその根拠にする。

## 連続性 (条件 2)

**所見**
今回の phase1 では、閉路なし tick を挟んで同じ signature の閉路が再出現する経路は構成できない。単に「registry と実 lock は別更新だから過渡的な偽閉路がある」とするのも不十分である。更新順序が重要になる。

**現物の根拠 (file:line)**
取得は実 lock 成功後に `publish_acquired` を行う (`patch:1569`、`:1572`、`:1785`、`:1795`)。解放は逆に、registry から削除した後で実 lock を解放する (`patch:2124`、`:2127`、`:2136`、`:2139`)。snapshot は registry mutex 下でコピーする (`patch:2313`)。DLR=0 の取得は blocker が存在する間ループし、No-Wait の失敗や wound による脱出を使わない (`patch:582`、`:657`、`:676`)。

**成立条件**
phase1 の通常 YCSB 経路、所有者以外による解放なし、hook の省略なしを前提とすると、次が成立する。

1. registry に残る排他 holder は、snapshot コピー中にも実 lock を保持する。実解放には先に同じ registry mutex で削除する必要がある。
2. 閉路の各 waiter は、別の閉路 node が実際に保持する排他 lock を要求している。その取得が既に成功した状態とは両立しない。
3. 各 worker は取得待ちを抜けないと解放へ進めないため、閉路内で最初に解放できる worker が存在しない。
4. よって閉路成立後に registry 閉路が消えることも、同一 attempt のまま作り直されることもない。

**影響**
この限定下では P3 による受理集合の拡大は示されないが、emit 列の隣接だけを根拠にすると連続性の説明が欠ける。

**是正案**
P3 をこの phase1 限定の論証付きで採用する。`plan:358` の一般的な欠番懸念と、今回の実行経路で到達可能な状態を区別する。検証器単体が任意の欠番入力を拒否するという主張はしない。tick 検査の新設は不要である。

## counter 不変 (条件 3)

**所見**
計器が出す counter は毎回の現在値ではなく、attempt 開始時の写しである。したがって同じ attempt の snapshot では、計器側の構造によって不変になる。条件3は独立した進行監視としては働かない。ただし、今回の真の閉路内では実 counter も更新箇所に到達できず、不変という値そのものは正しい。

**現物の根拠 (file:line)**
transaction の登録呼出しは `TxExecutor::begin()` の `patch:1512` にあり、実 counter を渡す。registry の counter 代入は `patch:2554`・`:2555`。`before_wait`・`acquired`・`released` は counter を更新しない。実 YCSB counter は `external/ccbench/include/ycsb.hh:151`・`:163`・`:166` で更新される。検証器は `runner:2358`・`:2469` で写しの一致を比較する。

**成立条件**
同一 worker が順次実行し、閉路中に取得待ちから counter 更新箇所へ進めないこと。これにより開始時の値が閉路中の現在値と一致する。

**影響**
恒常的に古い値を出す計器の不具合を、条件3の比較だけでは検出できない。

**是正案**
段4で次のどちらかを明示する。

- 今回は開始時の写しを維持し、条件3は実装上冗長だが値は正しいと論証する。
- 独立した更新追跡まで必要なら、実 commit/abort counter 更新時に診断用の写しも同期して更新する。

後者でも counter 本体を二重加算せず、watchdog から通常の非 atomic counter を無同期に読まない。既存の abort 所有権検査は、写しの鮮度を証明するものではない。

## hard timeout (条件 4)

**所見**
3枚の後の閉路解消と、別原因による timeout は、保存された3枚と `timed_out` だけでは区別できない。しかし D791 の逐語は「kill まで閉路が持続」を条件としていない。また今回の phase1 では、前節の実装論証により成立した閉路の自然解消経路がない。

**現物の根拠 (file:line)**
`D791:33` は連続3 snapshot、`:36` は該当走行の hard timeout を要求する。watchdog は `patch:2515` で return する。`runner:2696` から timeout による TERM、必要なら KILL を行う。期限を stage deadline が制限した場合は `runner:2706` で例外になり、通常の受理結果にはしない。

**成立条件**
条件1〜3が正しいこと、および同じ走行の実 `_run_process` 結果を使うこと。`termination="term"` でも timeout による終了なら条件4の対象となる。

**影響**
「timeout まで同一閉路を観測した」「その閉路が timeout の原因だと外部検証した」と書くと、成果物の証明範囲を超える。

**是正案**
P6 は維持可能。受領証・説明は「連続3 snapshot の閉路証拠と、同一走行の hard timeout」とする。kill までの観測を要求する変更は今回不要であり、行うなら強化として別途明示する。

## 規律 1 の保持

**所見**
plan の配置なら規律1を保持できる見込みである。`util.cc` の宣言文も、診断限定の起動時呼出し追加だけでは不一致にならない。ただし、変更後の不在性・inert witness は未測定である。

**現物の根拠 (file:line)**
`patch:30` で `wfg.cc` 自体を条件付き sources にする。`plan:98` の起動時呼出しは `#if SS2PL_WFG_DIAG` 内。既存軸 literal は `patch:2223` からの `ShowOptParameters()` にある。`runner:424` は例外を同関数の1箇所に限定する。宣言の正確な位置は `runner:89`、`util.cc` の文言は `:98` である。

**成立条件**
serializer と stdout helper を診断専用 TU 内に置き、起動時呼出しだけを guarded な YCSB main に追加すること。`wfg.cc` 全体は現在、内部の `#if` ではなく CMake で除外される。

**影響**
共通 TU へ無条件の呼出しや出力を移すと性能 build の動作を変えるが、plan の配置ではその変更は発生しない。

**是正案**
配置を維持し、新 patch で既存の不在性・inert 受入を取り直す。`util.cc` の宣言文は変更不要。なお inert 検証は TU 差分集合と宣言を照合するもので、宣言文の意味を自動検算するものではない (`runner:1729`)。「性能 binary の全 bytes 同一」は前処理による除去だけからは保証しない。

## test の逐語性と既存 test

**所見**
plan は「probe で一致確認」と書くが、実 stdout を fixture に差し替える具体的手順がない。さらに掲載 fixture は既に実出力と逐語一致しない。既存 boolean fixture と新しい保持一覧 fixture は、期待値を変えずに共存できる。

**現物の根拠 (file:line)**
`plan:162`・`:164` の軸行は `ADD_ANALYSIS`、`BACK_OFF`、DLR marker、後続軸を省略している。現物は `external/ccbench/cc/ss2pl/util.cc:62` と `patch:2223`。workload 行は実物がタブ (`external/ccbench/include/ycsb.hh:207`)、fixture は空白である。`runner:2885` は stdout の hash を残すが本文を残さず、`:2887` は解析済み snapshot である。既存の受理枝は `runner:2373`・`:2375` の両方が残る。

**成立条件**
合成 fixture の parser 契約確認と、実 C++ 出力由来の回帰確認を区別すること。新 fixture では `holder_holds_lock` を含めず、保持一覧の照合を通すこと。

**影響**
現案だけでは実 serializer が壊れても固定 fixture は通り続け、逐語接続の証拠にはならない。

**是正案**
段6を次の順序にする。

1. 計算ノード1走で、実 `_run_process` が収集した stdout を hash 化・解析だけで失わないよう保全する。全 bytes の保証が必要なら `text=True` による変換前の捕捉も必要となる。
2. 実際の軸行・workload 行・連続3 event を、空白や ID を再生成せず fixture へ写す。
3. 既存 parser・検証器を通す焦点テストを実走由来 fixture で再実行する。
4. 閉路が出なければ受理正例の実走 fixture は未取得と記録し、合成値で代用したと報告しない。

既存3 test の期待値は保持できる。ただし `test_deadlock_evidence_accepts_three_stable_actual_holder_snapshots` という名前でも、現内容が実 holder を観測した証拠になるわけではない。

## 段 4 へ返す択一

**所見**
P・I の多くは構造上の根拠を持つが、新しい接続の実測ではない。静的根拠があることと、親の見立てだけであることも区別すべきである。

**現物の根拠 (file:line)**

| 対象 | 現在の根拠と未実証部分 |
|---|---|
| P1 | `runner:2240`・`:2695` の経路は存在。新 emit の flush・行保全は未実測 |
| P2 | field 不一致は現物確認可能。新 serializer の接続は未実測 |
| P3 | phase1 限定の更新順序による論証あり。検証器自体は tick を見ない |
| P4 | 保持一覧照合枝は存在。出力する新計器は未実測 |
| P5 | 動作点は `runner:2857`・`:2910` と一致。過去記述は今回の再現保証ではない |
| P6 | watchdog 停止は `patch:2512` に実在。新 stdout の枚数は未実測 |
| P7 | guarded 呼出しは設計。変更後の不在性は未実測 |
| I1 | 条件除外は現物にあるが、新 patch の「引き続き緑」は予測 |
| I2 | 検証器の述語と保持一覧枝は現物にある。「独立」の範囲は要限定 |
| I3 | brief が変更前の実測 rc=0 を記載。親の読解だけとは分類しない |
| I4 | 期待値保持は可能だが「同 schema」は誤り。変更後の成功は未実測 |
| I5 | 別 thread・mutex コピーは現物で確認可能。実 holder との対応は更新順序で論証する |

過去成果物からの再検査不足は、指定一次資料 `verbatim-insight-s5.md:22` にも明記されている。

**成立条件**
段4では未測定を成功扱いせず、次の択一を解決すること。

| 論点 | 推奨 | もう一方の選択 |
|---|---|---|
| 独立性・P3 | phase1 限定の実装論証を明記し、P3を維持 | 論証を採らず、計器側で空 snapshot も既存抽出経路へ流して連続列を保つ |
| counter | 開始時の写しの正しさと冗長性を明記 | 診断限定で実更新時の counter 反映まで含める |
| P6・timeout | D791 逐語の射程でP6を維持 | kill までの持続観測へ強化する |
| fixture・完了 | 段6で実 stdout を取得し差し替える | 実走 fixture 未取得なら接続の実証完了を保留する |

**影響**
択一を未解決にすると、同じ成果物について「接続設計済み」と「独立検証を実証済み」が混同される。

**是正案**
推奨側を plan に反映する。閉路未観測は走行失敗とはせず、brief 冒頭の `accepted_cycle ≠ None` による実証は未達と区別する。新しい gate・台帳は必要ない。

## 総括

**所見**
plan は条件付きで採用可能。P3 の実装到達可能な誤受理例は今回の phase1 では成立せず、P6 も D791 逐語に反しない。主な修正点は独立性の説明、counter の意味、実 stdout 由来 fixture の取得手順である。

**現物の根拠 (file:line)**
`patch:2124` の解放順序、`:1512` の counter 登録、`runner:2458` の非両立再導出、`:2885` の stdout 保存範囲。

**成立条件**
phase1 の境界を明示し、変更後の実走・既存受入結果を取得すること。

**影響**
修正しない場合、受理集合の拡大よりも、成果物が証明した内容の過大申告が主要な問題となる。

**是正案**
段4で上記択一を確定し、段6の実データ取得・fixture 差し替えを具体化してから実証完了とする。