## 所見一覧

- **BLOCKER C1** — `summary.json` は全 job の `E-C` をまとめた中央値を持たず、`Jmax` は別の量なので、D1320 の 75 秒には答えていない。放置時: 75 秒が `Rpair` 中央値 14 秒へすり替わり、受入受理集合は不変だが解析集合は n=549 から n=679 へ変わり、D1320 参照が不成立になる。
- **MAJOR C2** — 分布の中央値は加法分解できないため、各中央値を成分として足し引きできない。放置時: raw 値は不変でも 11、13、14 秒の関係が誤って原因内訳になり、受入受理集合は不変、恒等式への参照が過剰になる。
- **MAJOR C3** — 679 / 737 の complete-case と、104 checkout、2 か月、K=2/3 の混合集団は、典型的な受入への一般化を支えない。放置時: 欠測と構成比により中央値と裾が変わりうる一方、受入受理集合は不変で、成果物の参照範囲が scan 時点を越えてしまう。
- **MAJOR C4** — D1320 の中央値 338 秒は再観測されたが、件数と式の同定に失敗しており、再現成功とは書けない。放置時: 数値 338 は同じでも解析集合が 549 から559へ変わり、受入受理集合は不変、D1320 の exact reproduction という参照が誤りになる。
- **MAJOR C5** — collection の `off_path` は時系列分類であって因果的な非寄与の証明ではない。放置時: collection 寄与が誤って 0 秒とされ、受入受理集合は不変だが 75 秒の原因帰属が変わる。
- **MINOR C6** — 二つの診断差は測点の不一致を示すだけで、NQSV 内部理由や overhead を同定しない。放置時: 値と受入受理集合は不変だが、queue wait と Elapse の意味に関する参照が誤る。

## 依頼に答えているか

答えていない。D1320 の 75 秒は、

`median(session span, n=549) - median(全 job の E-C, n=1297)`

という、観測単位も母集合も異なる非対差である。一方、今回の `Jmax=328` は各 complete-case session で最長の job を一つ選んだ後の n=679 の分布であり、全 job の分布ではない。

追加すべき集計を一つだけ挙げるなら、対象 cohort を明記した全 eligible shard の `E_j-C_j` の pooled distribution、少なくとも `n` と nearest-rank median である。outcome 別の中央値を後から合成して pooled median を復元することはできない。

ただし、それを追加しても再構成できるのは「二つの中央値の差」だけで、75 秒の因果的な内訳ではない。exact な D1320 比較には、元の session ID、job ID、選択規則も必要である。

今回の値から言える範囲は次のとおりである。

- `S=339`: complete-case 679 session の login marker envelope の中央値。
- `Jmax=328`: 同じ session ごとの最長 `E-C` の中央値。全 job の中央値ではない。
- `Env=328`: session ごとの `max E-min C` の中央値。
- `Skew=1`: paired な `Env-Jmax` の中央値。median Env と median Jmax がともに328でも、Skew の中央値は0とは限らない。
- `Rout=13`: paired な `S-Env` の中央値。静的 clock offset には依存しないが、前後区間や原因には分解されていない。
- `Rpair=14`: paired な `S-Jmax` の中央値。D1320 の75秒とは別の estimand。

`median(S)-median(Jmax)=11` だが、`median(S-Jmax)=14` である。この実測自体が中央値を項別に足し引きできないことを示す。`median(Rout)=13` と `median(Skew)=1` の和が今回は14でも、行単位の恒等式から中央値の加法性は導けない。

complete-case から落ちた58 session には timeout、qdel、shared deadline、遅い accounting により長時間側が欠ける経路がある。偏りの方向や大きさは確定できないため、「短い側へ偏った」と断定せず「長い側が選択的に欠けうる」とするのが限界である。

また、既知 checkout 値は104群に分散し、390 / 679 session は checkout 値自体が欠測している。月別でも `S` 中央値は8月334秒、9月369秒、K別では K=2 が333秒、K=3 が357秒である。したがって全体339秒を単一 checkout、単一月、現在または典型的な受入の中央値とは呼べない。

## 書いてよい文と書いてはいけない文

書いてよい文:

- 「scan 時点の complete-case 679 session では、`S`、`Jmax`、`Env`、`Skew`、`Rout`、`Rpair` の中央値はそれぞれ339、328、328、1、13、14秒だった」
- 「`Rpair=Rout+Skew` は各行で成立する代数的恒等式であり、原因帰属の検証ではない」
- 「691 session では、collection subprocess 復帰後に書かれる login log の mtime が最後の handled mtime 以下だった。46 session は判定不能だった」
- 「D1320 の338秒と同じ中央値は観測されたが、cohort は再現しなかった」

書いてはいけない文:

- 「75秒は13秒の外側費用と1秒の dispatch skew に分解された」
- 「Jmax 328秒はD1320の全 job 中央値263秒を更新した値である」
- 「median S 339秒から median Jmax 328秒を引いた residual は14秒である」
- 「collection は全件 off-path なので session を遅らせていない、または寄与は0秒である」
- 「D1420 の51.7秒 collection が今回の session residual に含まれる」
- 「339秒は現在または典型的な受入の中央値である」

collection について結論できるのは marker の順序までである。親は collection 復帰後に worker 結果を読み始めるため、collection が先に終わっていても、既に ready だった worker の処理を待たせた可能性は残る。したがって「ログインノードの全件 collection は75秒の内訳ではない」とは結論できない。

## D1320 再現失敗の読み方

正式な読み方は「D1320 cohort は再現しなかった」である。

2026-08-29 cutoff では、目標 `(568, 1, 18, 549)` に対して `(586, 1, 26, 559)` だった。増分は inventory +18、marker 欠測 +8、included +10であり、現在の archive が元の記録より件数上の上位集合になった方向を示す。ただし、追加された session の同一性や理由は記録から確定できない。

両方の S 定義が338秒になったことから書けるのは、「拡大した現在 cohort でも338秒が観測され、この10件の included 増加では中央値が動かなかった」までである。これは数値の限定的な頑健性を示すが、元 cohort、parser、選択規則、集計式の再現を証明しない。

さらに両候補式が同じ338秒なので、D1320 がどちらを使ったかは同定できない。cutoff scan に完全一致もないため、cutoff を動かして件数を合わせる根拠はない。

## 診断値の意味

`receipt queue_wait_s - (Started-Created)` は、比較可能な1734 shard すべてで負だった。最も0に近い値が -1.41秒、中央値が -3.06秒、最小が -789.75秒なので、receipt 値は全比較行で accounting span より短かった。

これは二つが同じ queue wait の測定ではないことを強く示す。receipt は qsub 復帰から qstat が最初に `RUN` と解釈されるまで、accounting は Created から Started までであり、起点も終点の意味も異なる。receipt が「真の queue wait を過小評価した」、qstat が誤った、または NQSV staging が差の原因だった、とはこの資料だけでは断定できない。

`Elapse-(Ended-Started)` は n=1737、中央値 +4秒、範囲 +1〜+10秒だった。従って NQSV の `Elapse` は全比較行で表示時刻差より長く、両者を同値にはできない。時刻の1秒分解能、丸め、scheduler 内部の包含区間などのどれが差を作ったかは断定できず、この差を起動費用や終了費用と呼ぶこともできない。

## 新しい観測点

全 job の pooled median は保存済みの `C/E` から再集計可能であり、新しい計装は不要である。一方、次の区間は現在の保存記録だけでは原理的に分離できない。

- `min C-min F` と `max H-max E`: session の前後で login clock と scheduler clock を対応付ける高分解能の同時刻観測が必要。
- qsub 呼出し開始、scheduler Created、qsub 復帰、confirm 書込み: qsub 前後と confirm の同一 login monotonic clock marker、および対応する scheduler event marker が必要。
- qstat の初回 `RUN` 解釈から accounting Started、実際の job script 開始まで: request ID に束縛した raw qstat 応答と観測時刻、compute 側 job entry marker が必要。
- scheduler Ended から login 側の terminal 検知まで: 各 terminal poll の raw 応答と同一 login monotonic clock の観測時刻が必要。
- result、log、accounting の生成・可視化・検証完了: artifact ごとの ready、visible、verification-complete marker が必要。
- receipt 永続化、scheduler log relay、handled 書込み: 各処理の開始・終了を同一 login monotonic clock で刻む境界 marker が必要。
- login collection の session への因果的寄与: collection start/return、各 worker payload-ready/send、親の receive 開始時刻が同一 login clock 上で必要。
- handled 後の worker join、親集約、merge、root junit、呼出し元への復帰: session proxy より後まで含む真の wall を問う場合だけ、それぞれの境界 marker が必要。
- `Elapse` と `Ended-Started` の差: 高分解能の scheduler service 境界と、相関可能な compute process entry/exit marker が必要。

## 総括

`summary.json` が新たに測ったのは、complete-case 679 session における paired residual `Rpair=14秒` と、その行単位の `Rout+Skew` 分解である。これは有用な別 estimand だが、D1320 の非対差75秒の内訳ではない。

D1320 は「中央値338秒の限定的な再観測」と「exact cohort 再現失敗」を併記すべきである。collection、queue wait 差、Elapse 差はいずれも診断値であり、原因や短縮対象へ昇格できない。

これらは事後解析上の包含と解釈に限る。受入の判定、排他、選択、受理集合を変更する根拠にはせず、変更も提案しない。read-only review のため pytest は実走しておらず、緑は主張しない。