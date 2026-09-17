## 前提の検算

指定された6ファイルを指定範囲で読み、一次計測資料・関連 consumer・docs の参照箇所を静的に確認した。ファイル変更、pytest、監査・性能測定は行っていない。

以下では `B`＝`s1-brief.md`、`P`＝`s2-plan.md`、`R`＝`rulings-verbatim.md`、`A`＝`tools/audit_dangling_commits.py`、`T`＝`orchestrator/tests/test_audit_dangling_commits.py` と略す。`M2`・`M3` は `output/insights/2026-09-16/t2637-offrepo-scan-yield/parent-measurements-{2,3}.md`。

- **real / must-fix：warm の費用内訳が誤っている。** B:7・49 の「455秒＋113秒」「warm約570秒」に対し、M2:8・21 は全体478.123秒、列挙455.376秒。残余は22.747秒であり、113.5秒はcold側の値（M3:73）。放置すると短縮目標・全体倍率・上限到達の見込みを誤る。
- **real / must-fix：P1はD958の受理条件を緩めている。** B:49–51 に対し、R:132–135 は独立走の最大が上限以下でなければ受理しないと明記する。項20・D2038は実装と実測の先行を求めるが、この条件を撤回していない。放置すると改善だけを根拠に未受理の変更をlandする。
- **refuted / nit：planが既存例外のrcを一律2に変更する懸念。** B:44 は不正確だが、P:131–135 は A:1808 の捕捉範囲を正しく維持している。briefをこの説明へ合わせればよい。

## 倍率の根拠

**refuted / nit：`DirEntry.is_dir()` の追加statはすべてGILを解放する、という前提。** 対象CPython 3.10.12では、`readdir` と `os.lstat` のsyscall部分はGILを解放する一方、`DirEntry` のstat fallbackは保持したまま呼ぶ。P:141–147の区別は正しい。Lustreで `DT_UNKNOWN` が多ければ、I/O待ちであってもthread間で直列化しうる。[CPython 3.10.12実装](https://github.com/python/cpython/blob/v3.10.12/Modules/posixmodule.c)

**unknown / nit：warm 258µs/fileの主因が、重ね合わせ可能なsyscall待ちであること。** A:911–936にはsort、fileごとのheartbeat・dict照合、basename一致後のPath生成・lstatが混在する。455.376秒をfile数で割った値はdirectory処理も含む平均であり、待ち時間の内訳ではない。M3:29–33のC版user/sys値もPython側の内訳を証明しない。P:149の追加stat数確認は有用だが、支配率や倍率はPython prototypeの所要で判断する必要がある。

**real / must-fix：prototype先行の位置が計画上不明確。** R:18–20・122およびD2038は小さいprototypeの先行実測を要求するが、Pは完全な実装・テスト計画から本計測へ進む構成になっている。最小の是正は、全面的なテスト・変異作業へ進む前にPython並列経路の倍率を測る地点を明記すること。放置すると既知の20%改善を再現する機構へ先に実装費用を払う。

**refuted / nit：倍率不足時に既定1へ戻して完了扱いする懸念。** P:289は改善なし・悪化ならこのPython実装を不採用とし、既定1の休眠機構をlandしない。これは妥当。ただし「この実装の不採用」は「並列化一般の不採用」ではなく、R:124–126の現状維持却下も消えない。

列挙倍率と全体倍率は分ける。参考計算として、同じwarm残余が続くと仮定した場合、上限到達に必要な列挙倍率は `455.376 / (300 − 22.747) ≈ 1.64倍`。これは実測の受理判定を代替しない。

## thread 安全と F627 / F628 型

- **refuted / nit：3値monotonic fixtureの必然的な破壊。** P:81・94–106はflat treeでpoolを作らず、初期化と2回のpulseだけを残すため、T:1043–1055の3値を使い切る現行順を維持できる。一般の並列treeでpulse回数まで逐次版と同一にはならないが、B:I1は進捗行を除外している。
- **refuted / nit：共有`nonlocal failures`の競合。** 現行A:901–903を複数workerで共有すれば危険だが、P:129はworker専用closureと主threadでの合算を明記している。実装時にこの所有関係を維持すれば失敗数を落とさない。
- **refuted / nit：間隔0によるF627型の無限busy-spin。** P:92は正のtimeoutと完了futureのpending除去を指定する。完了futureがあれば待ちは即時に返るため「常に1秒待つ」わけではないが、無進捗の無限反復にはならない。P:165の検査はtimeout正値に加え、完了futureを再待機しないことも確認するとよい。
- **refuted / nit：候補mergeが必然的に二次化する。** P:77のdict lookupと既存setへの`update`なら、処理量は局所group・owner・aliasの総入力量に比例する。累積setを毎回作り直さないことが条件。A:1002–1003のowner×alias配布は既存仕様であり、本waveで拡張しない。
- **unknown / nit：future管理・計数集約の費用。** P:87・92で全slot・pendingを毎回走査するとtask数について二次項が残りうる。ただし1,188直下taskなら約70.6万の累積pending要素走査であり、176万fileのlist重複除去なら約1.55兆比較になるF628とは規模が違う。現時点で有意な退行とは示せない。

なお1,188は「候補dir数」ではなく探索根直下のjob dir数（R:201）。計数slotもfile数ではなくtask数に対応させるべきである。

## 資源と例外

**refuted / nit：走査fdが深さ×16に増える懸念。** CPythonのtopdown `os.walk` はscandirを閉じてからyield・再帰する。P:139の概ね16本という評価は妥当で、祖先のdirectory一覧等はメモリに残るがfdは残らない。[CPython os.walk実装](https://github.com/python/cpython/blob/v3.10.12/Lib/os.py)

**real / must-fix：「別環境では遅くなるだけで壊れない」は保証できない。** P:139・293が認めるとおり、`ulimit -n=262144`はthread作成余力の証明ではない。Linuxの`ulimit -u`、他process/thread、cgroupのPID上限、stack・候補保持メモリも関係する。thread作成失敗が`RuntimeError`ならA:1808経由でrc=2となり、逐次版なら完走する環境で掃除判断を止めうる。既定16の主張は「観測した環境・資源余力の範囲」に限定する。

**real / nit：例外・SIGINT後の待機は無上限になりうる。** P:137の制約説明は正しい。未開始futureをcancelしても実行中threadは止まらず、終了待ちには最遅部分木とI/O停止時間が残る。cancelは`with`を抜ける前に実施する必要がある。放置すると異常を検出してからrcを返すまで長時間止まるが、この制約はplanですでに開示されている。[Python公式資料](https://docs.python.org/3.10/library/concurrent.futures.html)

**unknown / nit：import追加の起動費用。** import位置は未確定。top-levelで追加すると空候補・走査なしでも費用が発生し、A:1793より前のimport時間は最終`elapsed_seconds`に入らない。影響量は未測定なので重大回帰とは判定できない。外側wall timeとtool内部所要を区別すればよい。

## 計測計画の妥当性

- **real / must-fix：login nodeでの性能測定計画は通常規律と矛盾する。** B:64–68に対し、`docs/pegasus-runbook.md:345–354`は性能測定を計算nodeへ限定する。P:254–255の指摘は正しい。本依頼は計画の点検であり、login測定の例外許可とは読めない。同じ割当nodeで旧版・workers=1・16を比較する。
- **real / must-fix：倍率の定義を固定する必要がある。** P:249は両方の所要を示すが倍率の算式が未指定。走査改善は「逐次列挙時間÷並列列挙時間」、利用者向け改善は「逐次全体時間÷並列全体時間」、D958は並列全体の最大で判定する。混ぜると走査倍率を監査全体の利得として報告してしまう。
- **unknown / nit：交互配置だけでcache交絡を排除できること。** P:229・252の配置と外乱記録は妥当だが、ABABには順序・持越し効果が残る。旧版対照も同時並走ではなく同じ時間帯へ順次挿入する。順序・開始終了時刻・node・負荷と、既知のworktree add／land／受入を記録し、交絡が消えたとは断定しない。
- **real / must-fix：`--ref`固定だけでは入力同一を保証しない。** P:232の固定OIDに加えて、A:1372のcore監査は到達不能集合・local branch状態を読み、探索根自体も変動する。P:252の記録は必要だが不一致の解決方法までは決めていない。不一致が出た場合は等価性確認済みとせず、入力が安定した比較を取り直す。性能系列の遅い走を「外乱」として捨てることとは分ける。
- **refuted / nit：P5がcold性能を確定する計画である懸念。** P:257は補助観測に限定している。別node初回でも共有MDS cacheは残り、client側も未使用とは限らない。別nodeのworkers=1と16を1走ずつ測ってcold倍率とは呼べない。
- **refuted / nit：逐語比較から失敗数やpath順が抜ける懸念。** P:240–246は残りをソートせず比較する。`scan_failures`はA:1714–1715、未参照copyのpathはA:1833–1843に出るため比較対象に残る。P:160・183の`AuditReport`全体比較も補完になる。

D958の各条件warm-up＋3走、比率超過時の追加3走というP:248–249は妥当。旧版1走は機能対照には使えるが、旧版に対する性能改善の再現性まで証明しない。

## scope と編集面

**refuted / nit：第2段・CLI・gate変更の混入。** B:23–26、P:110・295–298は境界helper、用途分離、alias修正を明示的に分離している。今回の局所的なhelper抽出は走査規則の共有に必要な範囲である。

**real / nit：workers envはrescueの子processへ継承されない。** `tools/check_branch_rescue.py:218–223`のallowlistに新envはなく、同:1791–1798でその環境を使用する。P:274の判定は正しい。直接監査の計測用overrideとしては支障がなく、本waveでconsumerを変更する必要はない。ただしworkers=1を掃除全体の退避設定として案内してはならない。二重走査・継承の整理はT-2663側に残る。

**real / nit：T-2664との編集面は重なる。** A:948–960のgroup集約とA:1002–1003のalias配布が接するため、意味上独立でもmerge競合はありうる。P:297の既存fan-out維持で範囲は明確。T-2662も同じtool/testファイルだが別関数である。現在の他waveの稼働・編集状態は本調査では確認しておらず、同時編集なしとは言えない。

**refuted / nit：今回の実装だけでcleanup commandとdocs pin変更が必要になる懸念。** 指定範囲の検索では本件の主な記述はD2038等の判断記録。`.claude/commands/cleanup-branches.md:37–40`の起動契約は変わらず、`tools/check_docs.py:752・6571–6579`はcommand本文のpinである。tool内並列化のためにpinを更新する必要はない。

## 親 brief の実測値と一般化

**real / must-fix：最大job dir 59,723 fileという引用は根拠の射程を越える。** B:54の根拠に相当する `parent-measurements.md:74–82` は「被覆path」の上位表で、探索根全体の全job dirランキングではない。M3:40もその単一dirの測定しか示さない。探索根全体の最大値と確認できるまで、P2のskew許容をこの値から確定しない。file数だけでもmetadata待ち・directory数のskewは評価できない。

**real / must-fix：3.8〜4.4倍は引用として一致するが、同一実装3走という説明は不正確。** M3:29–33の単一threadはGNU findが1走、bfsが2走で、242.2秒の平均は両実装を混ぜたもの。file数も各走で増えている。探索的なC版比較として明示し、Pythonの受理根拠に流用しない。

**unknown / nit：既定16が最適であること。** B:55の根拠はbfsと同じ値という比較条件であり、96 coreだから16が適切という根拠でも、Lustre一般の最適値でもない。別filesystem・nodeでの倍率と資源余力は未確認。固定値を試すこと自体は妥当だが、安全性・最適性の一般化は避ける。

**real / must-fix：P1の「D2038が上限超過を予期したから受理可能」は成立しない。** R:116–122が予期する超過はcoldへの外挿であり、D958のwarm受理条件とは条件が違う。測定して第2段へ進む根拠と、第1段の変更を受理する根拠を分ける必要がある。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定 | 根拠と放置時の影響 |
|---|---|---|
| B1 | real / must-fix | B:7・49、M2:8・21、M3:73：warm/cold混算により全体所要・短縮目標を誤る。 |
| B2 | real / must-fix | B:49–51、R:132–135、P:290：改善だけでD958未達の変更を受理しうる。 |
| B3 | real / must-fix | R:18–20・122、P:227：prototype先行の地点がなく、倍率未確認の実装費用を先払いする。 |
| B4 | real / must-fix | B:64、runbook:345：login測定計画が実行場所の規律に反する。 |
| B5 | real / must-fix | P:249、A:1561・1849：列挙倍率・全体倍率・受理所要を混同しうる。 |
| B6 | real / must-fix | P:232・252、A:1372：固定refだけでは変動入力による差を実装差から分離できない。 |
| B7 | real / must-fix | B:54、一次資料parent-measurements:74–82：全体最大の裏付けなしに部分木skewを許容している。 |
| B8 | real / must-fix | M3:29–39：混合実装の探索的倍率を同一実装の再現性として扱いうる。 |
| B9 | real / must-fix | P:139・293、A:1808：資源不足では遅延だけでなくrc=2へ変わりうるため一般化を限定する。 |
| B10 | refuted / nit | P:81–106・129：monotonic fixture破壊、共有失敗数競合、F627再発は設計上対策済み。 |
| B11 | refuted / nit | P:77、A:1002：候補mergeのF628型二次化は回避可能。 |
| B12 | unknown / nit | P:87・92・147：GIL支配率、future管理費用、Python倍率は未実測。 |
| B13 | real / nit | P:137：異常・SIGINT後の無上限待機は既知の残存制約。 |
| B14 | unknown / nit | A:1793、P:110：import起動費用は内部elapsed外となりうるが影響量未確認。 |
| B15 | refuted / nit | P:240–246、A:1714・1833：失敗数・path順は逐語比較に含まれる。 |
| B16 | real / nit | rescue:218・1791、P:274：env overrideは直接監査だけに効き、掃除全体には伝わらない。 |
| B17 | refuted / nit | cleanup:37、check_docs:752・6571：今回の変更にcommand/pin更新は不要。 |

## 総括

planのthread所有関係、順序付きmerge、heartbeat、例外伝播は概ね整合している。F627/F628の再発が必然となる設計上の欠陥は確認しなかった。

修正すべき中心は、**briefの実測値とskew根拠、D958の受理解釈、prototype先行と計測条件**である。Pythonで速くなること、既定16で資源問題が起きないこと、上限へ収まることはいずれも未実証。これらを修正して実装・実測へ進む根拠はあるが、現状のbriefのまま受理条件を確定することは支持しない。
