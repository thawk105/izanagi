## 総括

親の probe は、pegasus02 で特定の合成 fsync 負荷が `/tmp` より Lustre で速かった事実までは支えるが、受入全走の短縮は支えない。  
現行受入は 549/549 session が dispatch 形で、plan の変更は compute pytest には届かず、login の collect-only にだけ限定的に発火する。  
さらに plan の K=1 login local 測定は、通常 runner では再び compute へ dispatch されうるため、測定形自体が保証されていない。  
実 workload の容量、file 数、directory 操作、frontier への分布は probe と大きく異なり、短縮量は未推定で、悪化方向も残る。  
BLOCKER は 3 件。現状の plan v1 を受入全走高速化として実装、paired full へ進めるべきではない。

## 所見

### [BLOCKER] A1/A2: 変更対象と paired 測定が実受入 regime に一致しない

- 根拠:
  - `brief.md:290-295`
  - `plan-v1.md:5,343,368-376,395-402,512`
  - `tools/run_tests.py:1402-1457,1460-1533,2472-2533,2620-2637`
  - `orchestrator/tests/conftest.py:805-813,862-870`
  - `tools/acceptance_shards.py:1243-1248,1306-1335,1353-1453`
  - `rulings-verbatim.md:91-100`、D620
- 内容:
  - policy は LOGIN 判定なので、実受入では login の `--collect-only` subprocessには発火する。一方、compute shard の pytest は COMPUTE 判定となり変更されない。
  - collect-only では二つの memo prewarm が明示的に抑止され、`tmp_path` fixture を使うテスト本体も実行されない。したがって、probe が想定した 32 worker の一時 file workload は login collection には存在しない。
  - plan の `K=1 login local` は `IZANAGI_ACCEPTANCE_SHARDS=1` だけでは成立しない。これは shard を止めるだけで、login admission が dispatch を選べば単一 compute job へ送られる。D620 と 549/549 の実績から、この分岐が通常形である。
  - その場合、TMPDIR は dispatcher allowlist 外で、compute 側 policy も発火しないため、A/B は実質どちらも compute `/tmp` になる。直接 `python -m pytest` で login local を強制すれば、今度は受入 runner 形でなくなる。
- 結論のずれ:
  - compute pytest に対する直接短縮は設計上 0 秒である。
  - 実受入に残る可能性は login collection の branch だけで、既測値なら冷 42.78 秒、温 11.37 秒が粗い絶対上限である。しかも dispatch と併走するため、全体中央値への短縮は 0 秒でも矛盾しない。
  - K=1 local で10%以上の差が出ても、K=3 dispatch の改善根拠には使えない。
- 提案:
  - K=1 login local の full 6走は行わない。
  - まず実際の login collect-only を `/tmp` と Lustre で各3回 paired 測定し、既存 session の collection終了時刻と最遅 shard終了時刻を比較する。
  - collection が全体の max branch になっていなければ、受入全走施策として負で閉じる。

### [BLOCKER] probe は実 workload を代表せず、効果の向きも確定していない

- 根拠:
  - `io_conc_probe.py:18-36,39-44`
  - `orchestrator/tests/conftest.py:12-22`
  - `output/insights/2026-08-01_t229-devshm-removal.md:17-27,116-121`
  - `orchestrator/tests/test_s8b_oracle_driver.py:879-926`
  - `orchestrator/tests/test_s8c_preregistration_invariant.py:191-215,362-385`
  - `plan-v1.md:21-22,248-258,507`
- 内容:
  - probe は worker ごとに1 fileを一度 openし、同じ fileへ4 KiB write、flush、fsyncを100回繰り返す。timed region に rename、directory fsync、unlink、rmdir、cleanupは含まれない。
  - 実 suite の既測例は `test_campaign.py` 168 nodeで620 fsyncであり、1 nodeあたりの呼出し数も対象 fileも異なる。
  - 過去の全走は一時領域 peak 7.39 GiB、終了後4.91 GiB、top-level 174 entryだった。200個の数 byte fileとは桁も size 分布も違う。
  - frontier の T-080 は1 baseだけで36 MB、2300 fileのcopytreeとGit操作を持つ。s8c invariantはGit index、tree、commit生成であり、単一fileへの連続fsyncではない。
  - plan の211 file、6507 sinkは静的到達数であって、実行時のfile数、size、fsync回数、directory操作数ではない。
- 結論のずれ:
  - login `/tmp` で得た約29秒の差を suiteへ転写する根拠はない。短縮はほぼ0秒にも、metadata負荷による悪化にもなりうる。
  - probe自身でも6400 small fileの wall は `/tmp` 0.022秒、Lustre 0.930秒で、Lustreが0.908秒遅い。実 workloadの数万file規模へ線形外挿はできないが、少なくとも利益の向きは単一fsync形だけでは決まらない。
  - compute n=1では `/tmp` 0.026秒、Lustre 0.42秒で、同じmicrobenchmarkでも約16倍逆方向である。
- 提案:
  - 実 workloadから、filesystem別のfile数、size histogram、write bytes、file/dir fsync、rename、link、unlink、mkdir、rmdirを取得する。
  - frontierの3機構を実データ形のまま、同一compute allocation内で `/tmp` と候補rootをpaired比較する。
  - 合成probeを残すなら、実測したoperation mixとsize分布を再生する形へ変更する。

### [BLOCKER] wall因果とD1298 frontierの証明が欠落している

- 根拠:
  - `brief.md:79-81`
  - `plan-v1.md:378-408,505-512`
  - `rulings-verbatim.md:663-688`、D1298
  - `tools/run_tests.py:1177-1185`
  - `orchestrator/tests/conftest.py:918-924`
- 内容:
  - plan は焦点走でfsync回数を測るが、fullの全fsync数、待ち時間、critical worker上の回数を要求していない。
  - paired fullも全体wallと結果集合を見るだけで、97秒以上の10〜11 unitが全件短くなったかを測らない。
  - TMPDIR非consumerも存在する。runner sidecarとreal-repo lockは明示 `/tmp` に残るため、「全unitが一様に払う」は静的にも成立しない。
  - frontierはT-080 copytree/Git、s8c module fixture、C06探索という異なる機構であり、同じfsync費用を共有している証拠がない。
- 結論のずれ:
  - 非critical workerだけが短くなれば、work総量が下がってもwall短縮は0秒になる。
  - 10〜11 unitの一部だけなら、D1298どおり次のunitがpoleを占め、29秒のmicrobenchmark差が完全に隠れうる。
- 提案:
  - A/Bごとにfrontier unitの開始、終了、worker、loadgroup、fsync待ち、file/metadata操作を記録する。
  - 10〜11 unit全体へ効くことと、A/B後の最長unitまたはmakespan下界が10%以上下がることをfull前gateにする。
  - このgateを通らなければfull A/Bは0走で停止する。

### [MAJOR] 共有login node上のprobeは交絡を除いていない

- 根拠:
  - `brief.md:19-35,166-178`
  - `io_conc_probe.py:39-55`
- 内容:
  - probeはroot順、n=1,8,32順が固定で、rootごとに別Poolを作る。順序randomize、同時刻paired、quiescence gateがない。
  - loadavgは7.4から19.1へ動き、`/tmp` とLustreは異なる共有範囲、利用者集合、queueを持つ。
  - probe自身のI/O待ちが後続測定のloadavgへ残る。3走中央値との記載はあるが、projected artifactにはraw 3走と分散がない。
- 結論のずれ:
  - exactなlogin microprobeでも比率がどれだけ外部利用者由来か不明である。computeでは順位が既に逆転しており、regimeを跨げば向きが変わることは実証済みである。
  - 29秒対0.081秒という大差は単純なcache温度だけでは説明しにくいが、受入への転写量は依然0から負まで未確定である。
- 提案:
  - 各regimeを別々に、root順をrandomizeした短いAB/BA blockで3組以上測る。
  - 各blockでloadavg、他pytest/変異process、filesystem使用量を記録し、単独性がなければ破棄する。
  - n=1/8/32/48、cold/warmを分け、全raw値、中央値、p25/p75を保存する。

### [MAJOR] A3: pytest内側の上限とsession残差の読み方が粗い

- 根拠:
  - `brief.md:234-265`
  - `rulings-verbatim.md:190-203`、D667
  - `rulings-verbatim.md:630-642`、D1260
- 内容:
  - 338秒に対してpytest 168.57秒なら、pytestを完全にゼロにしても169.43秒が残り、最大短縮は49.9%である。
  - pytest 244.8秒なら残差93.2秒、最大短縮は72.4%である。
  - ただし両pytest値は別tip、別走、別条件なので、この範囲は説明用上限であって厳密な相分解ではない。
  - `brief.md:264` の「差の大部分はpytest外」は、244.8秒基準では外側27.6%なので断定できない。
  - planはcompute pytestを変更しないため、この49.9〜72.4%の内側上限さえ利用できない。
- 結論のずれ:
  - planの実効対象であるlogin collectionは11.37〜42.78秒かつdispatchとの並行branchであり、中央値338秒に対する実効上限はこれよりさらに小さい。
  - planより大きい候補は、queue待ち、job開始、結果回収、handled認識を含むdispatch側の93.2〜169.4秒の残差である。ただし現資料だけでは、それがcurrent K=3のcompute pytest 244.8秒より大きいとは確定できない。
- 提案:
  - parent開始、各qsub、confirm、job開始、pytest開始/終了、handled、login collection開始/終了、merge終了を同一sessionで時刻化する。
  - K、worker数を再提案せず、まずdispatch/queue/handled残差の内訳を測定対象として名指しする。

### [OK] D357、D1260、D1299の形式とfull回数の最小化は、対象regime内では概ね満たす

- 根拠:
  - `plan-v1.md:380-408`
  - `docs/decisions.md:15594-15607`、D357
  - `rulings-verbatim.md:630-642,693-707`
- 内容:
  - 各arm 3走、中央値、pairwise delta、10%未満を変化なしとする点はD357/D1260に整合する。
  - tested tip、K、worker、collection digest、growth hold opt-in状態を記録するのでD1299も満たす。
  - 静的、fstype、flock、焦点、collection gateでfullを0走へ落とす設計も妥当である。
- 結論のずれ:
  - 正しいregimeであれば形式上のずれはない。各arm 3走を要求する限り、6 fullは最小である。
  - ただし現在のK=1 local計画は対象regimeが誤っているため、この6走は受入全走の結論には寄与せず、実質6走すべてが無駄になる。
- 提案:
  - 同じ枠組みをcurrent K=3、compute 48 workerへ移す場合だけ使用する。
  - login-only案は安価なcollect-only測定だけで先に裁定する。

### [MAJOR] D1035との非抵触は証明されていない

- 根拠:
  - `brief.md:54-58`
  - `plan-v1.md:3-7,416-472`
  - `rulings-verbatim.md:549-561`、D1035
  - `rulings-verbatim.md:663-688`、D1298
- 内容:
  - D1035は床を排他閉包の細分化で下げ、個々のテストの短縮を採らないと明記する。
  - planは排他閉包を細分化せず、各テストの一時I/O費用を下げる案である。「全unit共通の固定費」と名前を付けても、その共通性が未測定であり、明示 `/tmp` consumerも残る。
  - D1298に適合する余地は、frontier 10〜11 unit全体への同時効果を示した場合に限られる。planはそこを測らない。
- 結論のずれ:
  - このままでは、閉じた「個々のテストの短縮」を全体施策へ改名して実装する結果になりうる。
- 提案:
  - frontier全件への効果を示せない限りD1035抵触として不採用にする。
  - それでも採る場合は、D1035の例外としてユーザー再裁定を得る。

### [MAJOR] P5の「nodeを増やしてもmax(shard)は動かない」はD1103に反証されている

- 根拠:
  - `brief.md:95-96`
  - `rulings-verbatim.md:423-460`、D820
  - `rulings-verbatim.md:565-625`、D1103
- 内容:
  - D820は当時の単一real-repo poleを前提にした決定である。
  - D1103は排他鎖細分化後にその前提が失効したと明記し、K=2からK=3でpytest wall 285.52秒から160.92秒、差124.60秒を実測した。
  - node数増加は容量だけでなくnode内競合を減らし、直列総仕事量も1.53倍縮めた。したがって「直列unitがあればnode数でその所要もmaxも動かない」という推論は一般には偽である。
- 結論のずれ:
  - 分散案を理論上無効として早期除外すると、過去に実測された124.60秒級の競合効果を見落とす。
  - ただしK=3はD1103で確定済みなので、これはK増加の再提案を意味しない。multi-node shardも未測定であり、効くとは断定できない。
- 提案:
  - P5は「現scopeでは実装しない。current K=3は既裁定で、multi-node shardの効果は未測定」と書き直す。
  - D820を不可能性の根拠に使わない。

### [OK] D1035以外の列挙された閉鎖軸は再提案していない

- 根拠:
  - `plan-v1.md:474-503`
  - `brief.md:62-75`
- 内容:
  - worker数、shard数、collection manifest共有、hardlink、外部cache、テスト削除、real-repo group分割、T-080 groupingを実装対象にしていない。
  - LOGIN限定とcompute非変更も明記されており、regime記載自体は存在する。
- 結論のずれ:
  - これら8軸については名前変更による再提案は見つからない。
  - 問題はregimeが不明なことではなく、明記されたLOGIN限定が依頼の実regimeと一致しないことである。
- 提案:
  - 非変更表は維持する。D1035とP5だけを別途修正する。

### [MAJOR] 実測していない断定と数値不整合が残る

- 根拠:
  - `brief.md:17,24-36,40-44,50-52,79-96,140-155,180-232,263-265`
  - `plan-v1.md:5,21-22,351,370-376,505-512`
- 内容:
  - `brief.md:17` の「決定的な新事実」は、同file `:79-81` と `:180-224` がwall因果未実証、実regime不一致として自ら撤回している。
  - 表の29.06 / 0.081は約359倍であり、240倍ではない。small file差は0.908秒で、1.4秒ではない。29.06秒に対する総処理量は約110 fsync/sで、107ではない。別raw sampleを混ぜた可能性があるが、raw値が提示されていない。
  - 「全unitが一様に速くなる」は固定 `/tmp` consumerとnonconsumerに反証され、plan自身も `:507` で強すぎると認める。
  - `brief.md:153` のcluster-wide flock断定は二host probeなしでは強すぎる。plan `:508` も未確認としている。
  - `brief.md:228` のlogin collectionがcritical pathという断定は、dispatchとの併走を無視している。必須branchではあるが、wallを決めるbranchとは限らない。
  - `plan-v1.md:5` の「compute `/tmp` は十分速い」はn=1しか測っておらず、n=48は未測定である。
- 結論のずれ:
  - benefitを最大約29秒あるいは10%以上と過大評価する一方、metadata悪化、compute逆転、branch overlapを過小評価する。
- 提案:
  - 数値は「このhost、この時刻、このprobe形の観測」に限定する。
  - raw 3走を保存し、表、倍率、throughput、本文を同じraw集合から自動生成する。
  - 「速い」「critical」「一様」は実受入の相分解後だけ使用する。

## 親の実測への反証

- login n=32 probeは、実受入のlogin相にもcompute相にも一致しない。loginは単一process collect-only、computeは別nodeの48 workerである (`brief.md:194-211`)。
- login collectionはshard dispatch開始後に実行されるため、全体wallは概ね `max(login collection, slowest dispatch)` で決まる。collection短縮がそのまま加算短縮になるわけではない (`tools/acceptance_shards.py:1243-1248,1306-1357`)。
- 実frontierは単一fileへの連続fsyncではない。T-080は36 MB、2300 fileのcopytreeとGit履歴処理、s8c invariantはGit index/tree/commit、C06族はsource構造探索である。
- compute n=1ではlocal `/tmp` がLustreより速い。親の結論はfilesystem一般でなく、混雑したlogin nodeの特定probeに限られる。
- P5はD1103の実測に直接反する。D820の旧pole前提は既に失効している。

## 測り直しの設計

1. まずfullを走らせず、既存568 sessionから次を復元する。

   - dispatch開始、各confirm、login collection開始/終了、job開始、pytest開始/終了、handled、merge終了。
   - login collectionがslowest branchだったsession数。
   - queue待ち、compute pytest、handled遅延を分離した中央値とp25/p75。

2. plan v1をLOGIN限定のまま評価するなら、同一tipのcollect-onlyだけをA/B各3回測る。

   - A=`TMPDIR=/tmp`、B=unsetによるLustre policy。
   - AB/BAを事前randomizeし、loadavgと他利用者のpytest/変異processを記録。
   - nodeid digest、件数、hold stateを一致させる。
   - collectionが実sessionのmax branchにならなければ、full 0走で負として閉じる。

3. compute側へ設計を変更する場合だけ、frontierの実operationを測る。

   - current K=3、48 worker、growth hold既定、同一tip/digest。
   - frontier 10〜11 unitについて、file数、size、write bytes、file/dir fsync、rename/link/unlink、mkdir/rmdir、各syscall待ち時間を取得する。
   - focused tracingは `strace -ff -T -yy` 相当、fullでは低overheadのcgroup単位counterを使い、計測走のwall自体は効果証拠にしない。
   - 三つのfrontier機構すべてで同方向の短縮が予測されなければ停止する。

4. 上記gateを通った場合だけproduction-shaped paired fullを行う。

   - K=3、compute 48 worker、同一tip、同一digest、growth hold opt-inなし。
   - 各arm 3走、計6走が最小。
   - pytest wallと受入全体wallを分け、queue waitも別列にする。
   - D1299の5項目に加え、compute host、実効TMPDIR/fstype、frontier unit一覧と各所要を記録する。
   - median 10%以上、3 pair中2 pair以上同方向、frontier全件同方向、結果集合完全一致を採用条件にする。

## 見落としたかもしれないこと

- 本レビューは静的検査のみで、pytest、probe、受入全走は実行していない。
- compute n=48 probeの結果は射影資料に含まれておらず、compute高並列時の順位は未判定である。
- 338秒はmtime proxyで、job開始やpytest境界を直接表さない。168.57秒、244.8秒との割合は厳密な同一母集団比較ではない。
- syscall数の静的callsite数は動的回数にならず、Gitなど子process内部のfsyncも含まない。最終裁定には実行時観測が必要である。