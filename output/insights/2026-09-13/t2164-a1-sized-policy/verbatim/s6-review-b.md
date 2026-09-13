## 総括

指定された必読資料はすべて読めた。**数値・hash・列挙の転記不一致は見つからなかった。**
3 つの schedule seed、順序 bit、§8 の数値を独立に再計算した。
**real の must-fix は文言 2 件**：`result_authority` の検査範囲と、感度分析の独立性仮定。
pilot の性能の優劣を主張する箇所、規律 2・7 を緩める記述は主対象に見つからなかった。
本走未投入・人間認可待ち・実行経路未完成の明示は十分。
以下の実測は読み取りと独立計算。親申告の **282 passed / rc=0 は再実行していない**。

参照略号は次の実ファイルを指す。証明書・受領証はそれぞれ全体が 1 行。

- **R**：[sized README](output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md)
- **P**：[sized policy](orchestrator/campaign/paper_story_a1_paired.v3-sized.json)
- **C**：[sizing-certificate.json](output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-certificate.json)
- **V**：[sizing-replay-receipt.json](output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-replay-receipt.json)
- **PR**：[pilot 事前登録](output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md)
- **D**：[driver](orchestrator/campaign/paper_story_a1_paired.py)

## 逐語照合の結果

以下の「一致」は、対応項目の不一致疑義を **refuted** とした結果。日本語の説明は対応値を、英語の規則列挙は文言と順序を照合した。

| 項目 | 結果 | 根拠 file:line |
|---|---|---|
| write-heavy arm 名 | 一致：`fixed10` / `no-backoff` | R:40、P:210、P:223 |
| balanced arm 名 | 一致：`fixed5` / `no-backoff` | R:41、P:251、P:264 |
| read-heavy arm 名 | 一致：`fixed2` / `no-backoff` | R:42、P:292、P:305 |
| variant の `BACK_OFF` | 一致：3 workload とも `1` | R:40、P:205、P:246、P:287 |
| variant の `BACKOFF_FIXED` | 一致：順に `10` / `5` / `2` | R:40、P:204、P:245、P:286 |
| baseline の backoff flags | 一致：全 workload で `BACK_OFF=0`, `BACKOFF_FIXED=-1` | R:40、P:217、P:258、P:299 |
| protocol | 一致：全 arm `silo` | R:44、P:211、P:224、P:252、P:265、P:293、P:306 |
| `NO_WAIT_LOCKING_IN_VALIDATION` | 一致：全 arm `1` | R:44、P:206、P:219、P:247、P:260、P:288、P:301 |
| `NO_WAIT_OF_TICTOC` | 一致：全 arm `0` | R:44、P:207、P:220、P:248、P:261、P:289、P:302 |
| `WAL` | 一致：全 arm `0` | R:44、P:208、P:221、P:249、P:262、P:290、P:303 |
| role / contrast | 一致：variant=minuend、baseline=subtrahend | R:38、P:202、P:212、P:215、P:225（他 2 workload も同じ） |
| write-heavy `ycsb_rratio` | 一致：`5` | R:40、P:238 |
| balanced `ycsb_rratio` | 一致：`50` | R:41、P:279 |
| read-heavy `ycsb_rratio` | 一致：`95` | R:42、P:320 |
| records | 一致：1,000,000 | R:49、P:114 |
| threads | 一致：48 | R:49、P:115 |
| skew | 一致：0.9 | R:49、P:118 |
| rmw | 一致：0 | R:49、P:117 |
| max_ope | 一致：10 | R:49、P:116 |
| extime | 一致：3 秒 | R:49、P:113 |
| verify 構成 | 一致：`legacy` 1 本 | R:50、P:110 |
| `mode` | 一致：`exploration` | R:51、P:32 |
| `site` | 一致：`pegasus-compute-only` | R:51、P:35 |
| `formal` | 一致：`false` | R:51、P:3 |
| `promotion_prohibited` | 一致：`true` | R:51、P:4 |
| `final_estimate_eligible` | 一致：`true` | R:61、P:37 |
| `durable_measurement_base` | 一致：README 記載の絶対パスと全文一致 | R:326、P:29 |
| `materialization_relative_path` | 一致：`output/insights/2026-09-13/paper-story-a1-balanced5-sized` | R:327、P:31 |

| workload | 対数 | df | `pair_indices` | `k` | `planned_sigma_tps` | 根拠 |
|---|---|---|---|---|---|---|
| write-heavy | 一致：30 | 一致：29 | 一致：`[0,30)` | 一致：`2.8315526875186725` | 一致：`66403.452108019716` | R:82、R:195、R:268、P:228、C:1 |
| balanced | 一致：30 | 一致：29 | 一致：`[0,30)` | 一致：`2.8315526875186725` | 一致：`56697.435713574683` | R:82、R:196、R:269、P:269、C:1 |
| read-heavy | 一致：30 | 一致：29 | 一致：`[0,30)` | 一致：`2.8315526875186725` | 一致：`74668.489566274948` | R:82、R:197、R:270、P:310、C:1 |

§4 は C:1 の `inputs.pilot.planning` と各桁を照合した。

| 統計量 | write-heavy | balanced | read-heavy |
|---|---|---|---|
| `sd(60 差)` | 一致：42812.622815101997 | 一致：42359.021243474039 | 一致：63253.307101347236 |
| `sd(12 ブロック平均)` | 一致：19151.199917680609 | 一致：16351.919843025382 | 一致：19561.43852591965 |
| `sigma_pair` | 一致：50538.920832270931 | 一致：50003.458802371359 | 一致：74668.489566274948 |
| `sigma_block` | 一致：66403.452108019716 | 一致：56697.435713574683 | 一致：67825.883072771554 |
| `planned_sigma` | 一致：66403.452108019716 | 一致：56697.435713574683 | 一致：74668.489566274948 |
| 採った側 | 一致：block | 一致：block | 一致：pair |
| baseline 水準 | 一致：2396610.9666666668 | 一致：3785897.2166666668 | 一致：10162917.35 |
| README 行 | R:195 | R:196 | R:197 |

| §5.6 の項目 | 結果 | 根拠 |
|---|---|---|
| write-heavy 最小下限 | 一致：`0.99592040309507701`、条件 `zero` | R:268、C:1 |
| balanced 最小下限 | 一致：`0.99995212622855378`、3 条件とも 100000/100000 | R:269、C:1 |
| read-heavy 最小下限 | 一致：`0.99995212622855378`、3 条件とも 100000/100000 | R:270、C:1 |
| write-heavy 認証試行・候補数 | 一致：1 回目・1 件、selected order_index=0 | R:263、C:1 |
| balanced 認証試行・候補数 | 一致：1 回目・1 件、selected order_index=0 | R:263、C:1 |
| read-heavy 認証試行・候補数 | 一致：1 回目・1 件、selected order_index=0 | R:263、C:1 |

hash は表示を省略しているが、実ファイルから再計算した **64 桁全部**を照合した。

| §5.7 の対象 | 結果 | 根拠 |
|---|---|---|
| pilot 入力 | 一致：`b4201083…7451ed`、path も一致 | R:279、C:1、V:1 |
| 証明書 | 一致：`41d04196…fc8299`、path も一致 | R:280、P:193、V:1 |
| 受領証 | 一致：`5027d9e7…bad540` | R:281、V:1 |
| generator | 一致：`4fa604a1…315e13` | R:287、V:1 |
| verifier | 一致：`8c3c2066…957607` | R:288、V:1 |
| README の policy/driver pin | 一致：`266c2ca4…a0303a` | P:89、D:220 |
| policy の driver pin | 一致：`4a1ff569…d720be` | D:203 |

| seed・配置 | 結果 | 根拠 |
|---|---|---|
| write-heavy root | 一致：独立 SHA-256 が README・policy の双方と一致 | R:114、R:121、P:237 |
| balanced root | 一致：独立 SHA-256 が README・policy の双方と一致 | R:114、R:122、P:278 |
| read-heavy root | 一致：独立 SHA-256 が README・policy の双方と一致 | R:114、R:123、P:319 |
| write-heavy 順序 | 一致：counter=0、`1,0,0` | R:138、D:1812 |
| balanced 順序 | 一致：counter=0、`1,1,0` | R:139、D:1812 |
| read-heavy 初回 | 一致：counter=0、`1,1,1` で引き直し | R:133、D:1828 |
| read-heavy 採用順序 | 一致：counter=1、`1,0,1` | R:140、D:1815 |
| bit 0 の物理順 | 一致：`A^5 B^5 B^5 A^5` | R:89、P:63 |
| bit 1 の物理順 | 一致：`B^5 A^5 A^5 B^5` | R:90、P:64 |
| ブロック数・先行数 | 一致：対ブロック6、armブロック12、各先行3、組3 | R:83、P:57、P:61、D:1811 |

16 規則は、それぞれ **文言・位置とも一致**。pilot 事前登録との対応も一致した。

| 規則番号・識別内容 | 結果 | 根拠 |
|---|---|---|
| 1 arm 集合 | 一致 | R:344、P:39、PR:233 |
| 2 build attempt 数 | 一致 | R:345、P:40、PR:234 |
| 3 bench 前 build/verify | 一致 | R:346、P:41、PR:235 |
| 4 certified/workload tag | 一致 | R:347、P:42、PR:236 |
| 5 competing-tenant probe | 一致 | R:348、P:43、PR:237 |
| 6 settle | 一致 | R:349、P:44、PR:238 |
| 7 throughput 不在 | 一致 | R:350、P:45、PR:239 |
| 8 aggregate CV 未定義 | 一致 | R:351、P:46、PR:240 |
| 9 aggregate CV の全 rep 使用 | 一致 | R:352、P:47、PR:241 |
| 10 integer rounds=1 | 一致 | R:353、P:48、PR:242 |
| 11 unstable=false | 一致 | R:354、P:49、PR:243 |
| 12 block の 5 正値・有限点 | 一致 | R:355、P:50、PR:244 |
| 13 schedule receipt | 一致 | R:356、P:51、PR:245 |
| 14 interruption/片側完了 | 一致 | R:357、P:52、PR:246 |
| 15 trace0 source evidence | 一致 | R:358、P:53、PR:247 |
| 16 CCBench pin/dirty | 一致 | R:359、P:54、PR:248 |

| 再走理由 | 結果 | 根拠 |
|---|---|---|
| `build-failure-before-bench` | 一致 | R:372、P:101、PR:258 |
| `verify-failure-before-bench` | 一致 | R:373、P:102、PR:259 |
| `competing-tenant-detected-before-bench` | 一致 | R:374、P:103、PR:260 |
| `scheduler-or-infrastructure-failure-before-bench` | 一致 | R:375、P:104、PR:261 |

CCBench 境界名は R:331 が参照する pilot 事前登録から照合した。

| CCBench 項目 | 結果 | 根拠 |
|---|---|---|
| canonical pin | 一致：`511c9538e4e8efa54b45cda62e72389ed3b706ec` | R:330、P:17、PR:216 |
| `login-submit-before-intent-and-qsub` | 一致 | R:331、P:10、PR:218 |
| `compute-job-body-preflight` | 一致 | R:331、P:11、PR:218 |
| `driver-measurement-start` | 一致 | R:331、P:12、PR:219 |
| `before-each-trace-and-perf-build` | 一致 | R:331、P:13、PR:219 |
| `artifact-consumer-arm-validation-and-materializer-raw-recollection` | 一致 | R:331、P:14、PR:220 |

## must-fix

1. **real — 「`result_authority` は実装のどこからも読まれない」は過大な断言。**

   根拠：R:65。個別 field の意味を解釈する production コードは検索で見つからなかったが、D:1750 は全 top-level field を比較するため、`authority` 辞書内部のこの文字列も比較対象になる。さらに D:1753 は policy 全 bytes の pin を検査する。

   **成果物影響：人間可読の正本が、説明用文字列も凍結内容として検査される事実を否定している。**

   直し方：「認可・昇格を判断する意味上の分岐には使われない。ただし policy 内容一致・bytes pin の検査対象には含まれる」と限定する。これは実装読解による所見で、変更 policy の実走結果ではない。

2. **real — §8 の確率式に note 発生の独立性仮定がない。**

   根拠：R:416。「各反復の note 発生確率が p」だけでは `1-(1-p)^(2n)` は導けない。例えば全60反復の note 発生が完全に連動していても各反復の周辺確率は p だが、少なくとも1件発生する確率は p になる。

   **成果物影響：感度分析が、反復間依存を限定せず workload 無効化確率を述べている。**

   直し方：「各反復の note 発生が独立で、共通確率 p と仮定した感度分析では、note による無効化確率は…」とする。独立計算値は `0.0582637377768318`＝約5.8%で、数値の訂正は不要。反例は数学上の構成であり、実際の note の依存を観測したという意味ではない。

## nit

1. **real — counter による実効 seed の説明が省略されている。**

   R:101 は原像書式を示すが、D:1813 の「counter=0 は root をそのまま使用」と、D:1816 の「counter>0 は原像を SHA-256 の hexdigest にする」を明記していない。表は実装と一致しているため転記不具合ではないが、この2点を添えると README 単独で再計算できる。

2. **real — §8 の「観測」の対象が曖昧。**

   R:421 は「pilot の後」と明記する一方、R:422 は単に「観測を見てから選び直さない」と書く。R:107・R:129 と合わせれば意図は追えるが、「本走の観測」と明示すると凍結時点の読み違いを減らせる。

## refuted

- **refuted — §5.8 が再計算や道具側の登録値強制まで保証している。**  
  R:293 は道具が強制しないと明記し、R:309 は申告値の一致だけと限定する。D:223 の5定数と D:1423 の型・値比較は、R:298 の各登録値と一致する。consumer が証明書の数値を再計算するという記述はない。

- **refuted — §6.3 が16規則の完全な enforcement を保証している。**  
  R:365 が明示的に否定する。別途実装で拒否すると書いた `rep_notes` は D:5261 で実際に拒否条件になっている。静的に確認した範囲で文書と整合する。

- **refuted — sized README が pilot の性能の優劣を述べている。**  
  R:195 の表は散らばり・baseline 水準のみ。R:220 の improvement/regression は判定規則、R:232 の ±6% は模型の条件であり、pilot の観測結果への評価ではない。pilot 結果 README の差の列を、本走 README は転載していない。

- **refuted — schedule seed を pilot 前からの凍結と偽っている。**  
  R:107 が pilot 後の新規凍結と明記し、R:129 が別原像への引き直しを禁止する。R:206 の凍結済み seed の定義域は、同節の sizing 数値実験に対応し、PR:184 と一致する。  
  **成立するのは本走の観測に対する前向き性**である。初回原像の選択が pilot 情報から独立だったことや、過去に候補を試していないことまで、この文書・hashだけで証明できるわけではない。それらを偽った証拠は今回見つからなかった。

- **refuted — driver 更新を理由に過去の pilot を無効化・昇格している。**  
  R:180 は登録済みの集計手順の適用を述べ、R:283 と V:1 が束縛する source は generator/verifier の2本。現行 driver との差による過去測定の再判定を指示する記述はない。

- **refuted — 規律2を緩める文書になっている。**  
  R:320 は bench 前の build/verify、R:347 は certified true を要求する。D:5237 の certified 検査、D:5239 の anomaly 検査とも矛盾しない。R:365 の実装完全性の留保は、判定規則を免除する文章ではない。

- **refuted — 「本走が起動可能になった」と読ませている。**  
  冒頭 R:9 に未投入・人間認可、R:401 に結果不在、R:402 に実行可能を意味しないと明記する。D:7127 と `orchestrator/campaign/paper_story_a1_source.v1.json:3` も pilot 専用契約の残存を裏付ける。

## 親裁定へ返す項目

- **must-fix 2件を文言修正として採用するか。** 証明書・受領証の変更は不要。
- seed の前向き性は「本走観測前に固定」の範囲で受理可能。pilot 前からの独立な無作為化まで拡張しない。
- 今回の照合は本走投入の認可・実行面の完成判定にはならない。既記載の人間認可待ちを維持する。