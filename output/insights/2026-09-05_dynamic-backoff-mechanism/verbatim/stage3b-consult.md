## 判定

**現状のままの投入は拒否**する。実装可能性は高いが、事前仮説、対内 CI、等価域、欠測規則、腕順序、診断指標の意味が凍結されておらず、結果を見た後に成功条件を選べる状態である。

判定は **must-fix 12 件、nit 2 件**。静的レビューのみを行い、指定どおり pytest は実行していない。

## 共通の判定式

throughput の主推定量は、生の腕別平均ではなく同一 node/job 内の対比にする。

各 workload \(w\)、thread \(t\)、node block \(i\) について、

\[
d_i(a,b;w,t)=\log \frac{TPS_{i,a,w,t}}{TPS_{i,b,w,t}}
\]

\[
CI_{95}=\bar d \pm t_{0.975,n-1}\frac{s_d}{\sqrt n}
\]

とし、百分率へは端点を \(100(\exp(x)-1)\) で戻す。n=7 なら \(t_{0.975,6}=2.4469\)、n=6 なら \(t_{0.975,5}=2.5706\) である。

実用等価域は、提案値として throughput 比 **[0.97, 1.03]**、すなわち ±3% とする。ただし B-10 の ±3% を無条件に流用せず、この機構での実用差・既存 CI・noise floorから根拠を明記して凍結する必要がある。

判定は次で固定する。

- 実用優越: CI 下端 \(>1.03\)
- 非劣性: CI 下端 \(>0.97\)
- 等価: CI 全体が \([0.97,1.03]\) 内
- 実用劣化: CI 上端 \(<0.97\)
- それ以外: inconclusive。非有意を等価と呼ばない

abort rate は副次指標として同一 node 内の percentage-point 差を示す。等価判定に使うなら throughput とは別の等価域を事前登録する。

## 提案する仮説 H1〜H6

「robust benefit」は、全24セルで非劣性、かつ `(write-heavy,48)` と `(balanced,48)` の両方で実用優越、と定義する。両 endpoint を同時に要求する intersection-union 判定なので、「都合のよいどちらか一方」を結果後に選ばない。

| 仮説 | 対比と受理条件 | 答えられる問い | 答えられない問い |
|---|---|---|---|
| H1 全動的機構 | `cw+as+dyn / tuned` が robust benefit | 全機構を積んだ実装が調整済み adaptive に追加価値を持つか | どの部分が効いたか、未測 workload・別機体でも効くか |
| H2 no-backoff safety | read-heavy 8 thread 全点で `cw+as+dyn / none` が非劣性 | backoff 不要域で実用的な損を避けたか | 機構が自動的に backoff を無効化したか |
| H3 count-window 増分 | `cw / tuned` が robust benefit | count-window package が tuned より有効か | 計数そのもの、長い実効間隔、atomic scan 費用のどれが原因か |
| H4 adaptive-step 増分 | `cw+as / cw` が robust benefit | 適応刻みを加えた増分効果 | 勾配推定が真に正しいか、step 境界の最適性 |
| H5 dynamic-ceiling 増分 | 全24セルで `cw+as+dyn / cw+as` が等価 | 「動的上限はこの範囲で実用差を生まない」という P3 の予測 | 固定上限一般が効かないこと、未測の低い ceiling |
| H6 陽性対照 | 48 thread の3 workloadすべてで `stock / tuned` の CI 上端 `<0.97` | 既知の stock 劣化が今回も再現するか | 動的腕が優れていること |

H1〜H5以外の各セルも95% CI付きで全件報告してよいが、「24点のどれかで勝った」という選択的主張はしない。そうした family-wise claim が必要なら、対比ごとに24検定を Holm 補正する。

## 結果表の形

主表では none と tuned を明示的な二基準線にし、stock は分離する。

| workload | threads | none mean | tuned mean | full/none 対内95% CI・判定 | full/tuned 対内95% CI・判定 | cw/tuned | cw+as/cw | full/cw+as |
|---|---:|---:|---:|---|---|---|---|---|

stock は次の陽性対照表だけに置く。

| workload | threads=48 stock mean | tuned mean | stock/tuned 対内95% CI | H6 |
|---|---:|---:|---|---|

これなら「dynamic は stock より速い」を headline にせず、D1506 の none/tuned 二基準線を守れる。

## P9 の K と cap の再計算

T-2187 の `s1-u2560` 生値集約から、tuned の平均 throughput、2560 µs 内の期待 commit 数、K=10,000 到達時間を計算すると次になる。

| threads | write-heavy | balanced | read-heavy |
|---:|---|---|---|
| 6 | 1.430 M / 3,662 commit / 6.99 ms | 1.320 M / 3,378 / 7.58 ms | 1.567 M / 4,013 / 6.38 ms |
| 12 | 2.644 M / 6,768 / 3.78 ms | 2.384 M / 6,102 / 4.20 ms | 3.088 M / 7,906 / 3.24 ms |
| 18 | 3.512 M / 8,990 / 2.85 ms | 3.256 M / 8,337 / 3.07 ms | 4.568 M / 11,695 / 2.19 ms |
| 24 | 3.942 M / 10,091 / 2.54 ms | 3.902 M / 9,988 / 2.56 ms | 6.000 M / 15,360 / 1.67 ms |

各セルは「M tps / 2560 µs の commit / K 到達時間」。

48 thread では write-heavy が `3.946 M / 10,102 / 2.53 ms`、balanced が `4.324 M / 11,068 / 2.31 ms`、read-heavy が `10.170 M / 26,034 / 0.98 ms` である。したがって「48 thread、4 M tps、約10,000 commit」は write-heavyには合うが、read-heavyへは一般化できない。

cap=40.960 ms がKより先に発火する平均 throughput の境界は、

\[
10,000 / 0.040960 = 244,141\ TPS
\]

である。T-2187 の最小平均は1.320 M tpsなので、**観測された全 thread/workloadでKが先**であり、capが常時先行して tuned と区別不能になる領域はない。ただし平均値から個々の窓での発火順を保証することはできない。

逆に6〜12 threadでは実効窓が3.24〜7.58 msとなり、tuned の2.56 msより明確に長い。cw/tuned の差は「固定commit数」だけでなく、ほぼそのまま「更新間隔を長くした差」でもある。

## MF-01 — 仮説・等価域・多重性が未登録

**位置:** brief「成果物の形」「P6/P9」、plan「図生成器」「briefへの指摘」。  
**指摘:** 現在は腕と生値CIしか決まっておらず、どの対比を成功とするか、±何%を等価とするか、24セルから勝った点を選んでよいかが未定義である。  
**受理の含意:** 上記H1〜H6、対内log比、±3%、inconclusive規則を凍結すれば、結果を見る前の問いに答えられる。  
**拒否の含意:** 現状のままでは結果後に「優越」「同等」「どこかで改善」を選べるため、事前登録実験とは扱えない。  
**成果物への影響:** insight の主表、結論、図 caption、provenance に同じ対比と判定を載せる。  
**修正案:** prereg 文書へ式、endpoint、等価域、多重性、H1〜H6の受理条件を逐語で追加する。

## MF-02 — K は維持可能だが cap=40960 µs の根拠が逆向き

**位置:** brief P9、plan「P9」「投入設計の検算」。  
**指摘:** 40960 µs はT-2187で悪化した点であり、その値まで更新を待たせる安全上限の根拠にはならないうえ、244 kTPSまで落ちないと発火しない。  
**受理の含意:** K=10000を「一定の計数精度を狙う値」と限定し、capを10240 µsへ下げれば、既知平均ではKを邪魔せず崩壊時だけ早く救済できる。  
**拒否の含意:** 40960を維持するなら「悪化点をcapにしたから安全」という説明を捨て、未検証の非常停止値と明記しなければならない。  
**成果物への影響:** 腕表、prereg の予想実効窓、trace のcount/cap発火率が変わる。  
**修正案:** `cap=10240` を推奨し、上表と発火境界を prereg に固定する。

## MF-03 — step_min=0.25 と step_max=8 は実測に支えられていない

**位置:** brief P2/P9、plan「適応刻み」「briefへの指摘 P2/P9」。  
**指摘:** 0.25 µs は `last_backoff_` の `uint64_t` 切捨てによる偽ゼロ勾配の既知領域であり、8 µs はT-2187で直接測っていない。  
**受理の含意:** `step_min=1`, `step_max=5` とすれば既知の切れ目を避け、T-2187が広い窓で平坦とした測定範囲内に収まる。  
**拒否の含意:** 0.25/8を残すなら、これは実測由来でなく倍加列の実装都合であると開示し、切捨て挙動を仮説の一部に含める必要がある。  
**成果物への影響:** 腕 identity、patch、診断軌跡、認証 exact cell がすべて変わる。  
**修正案:** 1/5へ変更するか、STEP_ADAPT時だけ過去backoffをdoubleで保持する別設計と、その増分対照を登録する。

## MF-04 — P3 の「効果なし」は既存上限実測から導けない

**位置:** brief P3、plan「動的上限」「H5相当の図」。  
**指摘:** 既存実測は固定 ceiling 50/200/1000 µs の比較であり、経路依存で半減するceilingや、step×4=32 µsまで下がる現設計を覆わない。  
**受理の含意:** H5を厳しい全24点等価仮説として置けば、「効果なし」は新実測で初めて判定される。  
**拒否の含意:** D1505を根拠に事前から無効果と記述すると、固定上限の限定結果を別機構へ外挿することになる。  
**成果物への影響:** insight ではH5を独立の増分対比として報告し、D1505の再確認と呼ばない。  
**修正案:** ceiling下限を少なくとも既測の50 µsへ束縛するか、未測領域を含む新仮説として扱う。

## MF-05 — count-window と長い更新間隔、scan overheadを識別できない

**位置:** brief P1/P6、plan「計数窓」「briefへの指摘 P1」。  
**指摘:** cwは低threadで実効窓が最大7.58 msへ伸び、さらにleaderの毎試行で全threadのatomic counterを読むため、cw/tuned差を計数窓の効果へ帰属できない。  
**受理の含意:** 七つ目の `cw-cap2560` 対照を加えれば、低throughput域で `cw-cap2560/tuned` がscan費用、`cw/cw-cap2560` が長い実効間隔の差を近似する。  
**拒否の含意:** 六腕を固定するなら、H3は「count-window実装packageの効果」に限定し、計数と時間の因果分離はscope外と明記する必要がある。  
**成果物への影響:** 対照を足す場合は性能runが1 jobあたり24件増えるが、認証22 node-hourに比べ小さい。  
**修正案:** `K=10000, cap=2560, adapt=0` の対照を追加するか、識別不能をprereg・caption・総括へ明記する。

## MF-06 — 「勾配符号的中率」は現在のtraceでは真の的中率ではない

**位置:** brief P8、plan「診断」「performanceと診断mode」。  
**指摘:** planのhitは連続する内部 `gradient_sign` の一致率であり、同じノイズを次窓で再利用した自己相関で、真の勾配や反実仮想の正解を測っていない。  
**受理の含意:** 「one-step directional success」または「successive-sign agreement」へ改名し、生の行動方向と次窓throughput差から独立再計算すれば限定的な予測精度を測れる。  
**拒否の含意:** 現定義をaccuracyと呼ぶと、内部推定器が自分自身と一致した割合を機序の直接証拠へ循環利用する。  
**成果物への影響:** 診断JSON、下段図、機序に関する本文の用語と主張範囲が変わる。  
**修正案:** 各更新に `time_diff`, `committed_diff`, throughput, pre/post backoff, actual action, step, ceiling, count/cap trigger, parity branchを保存し、行動ゼロはunscoredとする。

## MF-07 — node交絡は抑えられるが、固定腕順序との交絡が残る

**位置:** brief P6、plan「performance mode」「図生成器」。  
**指摘:** 各jobが全腕を含むのでarmとnodeの一対一交絡はないが、現mainは常に同じcell順で走り、armと時間順・温度・occasion driftが完全に対応する。  
**受理の含意:** 7個の腕順序を投入前に固定してcounterbalanceし、対内log比で集約すればnodeの共通乗数と順序効果を抑えられる。  
**拒否の含意:** 固定順のままでは、後段の動的腕だけに現れた差を機構効果と時間ドリフトから分離できない。  
**成果物への影響:** group manifestにrepごとの腕順序とhostnameを保存し、解析はrep identityで対にする。  
**修正案:** 6巡回順＋事前固定した第7順をcommitし、可能なら7 distinct hostを完了条件にする。

## MF-08 — P6 の15分は近そうでも、導出と引用が成立していない

**位置:** brief P6、plan「投入設計の検算」。  
**指摘:** 8.5分/120 runは4.25秒/runだが、現mainのwall計測は5 buildと120 runを既に含むため、そこへ6 buildを再加算するplanは二重計上である。  
**受理の含意:** 8.5分が真正なら6/5比例でdriver約10.2分、別計測のprologue約2分を足して約12.2分が中心見積もりになる。  
**拒否の含意:** 現在のprojected insightは8.5分自体を記録せず、記載の20.26〜20.47はCPU/elapsed比なので、一次成果物なしに15分を実測根拠とは呼べない。  
**成果物への影響:** prereg の時間表に根拠artifact、中心値、hard upper boundを分けて載せる。  
**修正案:** performance JSONへPBS prologue時間も保存し、過去7 JSONのwall値を引用してmin/median/maxから再見積もりする。

補足すると、性能jobは144 processで、extimeだけの下限は7.2分である。各processが1M recordのDBを再構築するので1 job 144回、全7 jobで1008回だが、この費用は過去の8.5分に既に含まれる。

認証についても、briefの「verifier 23分、job 52分」はprojected T-2189 insightと一致しない。同 insight が示すverify経過は87.1〜458.9秒で、52分のjob経過は記載されていないため、55分を使うなら別のreceipt/logを一次根拠として束縛すべきである。

## MF-09 — 40分超過時の損失と n=6 規則が未定義

**位置:** brief P6、plan「投入設計の検算」「performance main」。  
**指摘:** performance JSONは全build・全144 runの終了後に一括生成されるため、walltime killや途中例外ではそのnode blockの機械可読結果を丸ごと失う。  
**受理の含意:** 完了済みpointのappend-only journalと終端manifestを導入し、完全blockだけを解析すれば、障害と欠測の区別を保てる。  
**拒否の含意:** 一括JSONのまま40分を超えるとstdout以外を失い、成功したセルだけを救済するか全blockを捨てるかを結果後に選ぶことになる。  
**成果物への影響:** group manifest、欠測表、図入力validatorにcomplete-block判定が必要になる。  
**修正案:** 原則7 complete blocks、1 block欠測なら全セル共通でn=6・df=5、補完なし・外れ値除外なし、n<6はconfirmatory判定なしと登録する。

infra failureだけはmetricを見ずに同じrep indexを新nonceで再投入してよい。複数の有効結果ができた場合に採るものも「最初に完了したvalid receipt」などと事前固定する。

## MF-10 — 認証24 jobは条件付き後続waveの方が費用対効果がよい

**位置:** brief P4/P6、plan「certificationのexact二値化」「投入設計」。  
**指摘:** 24×55分なら約22 node-hourで、本wave全体の約92%を、正しさ制御を直接変えない動的1腕へ支払う一方、性能失敗でも費用は回収できない。  
**受理の含意:** H1を満たした場合だけ認証を解禁し、未実行なら「動的腕は未認証、採用不可」と明記すれば、verifierを一切緩めず費用を節約できる。  
**拒否の含意:** 性能結果に関係なく同waveで認証するなら、期待約22 node-hourだけでなくouter walltime上限24×2.25=54 node-hourも予算として承認すべきである。  
**成果物への影響:** prereg に認証go/no-go、未認証表示、後続wave参照を追加する。  
**修正案:** 順序を「性能7 jobを並行投入 → 診断 → H1通過時のみ認証pilot 1本 → 残り23本を並行投入」とする。

認証jobはperformance artifactのpath/SHAを要求するため、現契約では性能と認証の同時投入はできない。queue混雑はnode-hourを減らさないので、24本を直列化する理由にもならない。

## MF-11 — 図は生値CIだけでは判定を表現せず、新generatorの重複も不要

**位置:** brief「成果物の形」、plan「図生成器」。  
**指摘:** 提案図の誤差棒は腕ごとの生値CIであり、仮説が使う同一node内の対比CIではないため、重なった線からH1〜H5を判定できない。  
**受理の含意:** thread図を記述用に残し、上記の対内CI表またはforest plotを同じ生値から生成すれば、図と判定式が一致する。  
**拒否の含意:** 腕別CIの重なりを有意差判定に使うとpaired designの利点を捨て、誤った結論を招く。  
**成果物への影響:** provenanceへ対内samples、CI、verdict、prereg commitを追加する。  
**修正案:** `plot_t2187_adaptive_consts.py` の `threads` modeを拡張する方を推奨する。

既存generatorは既に2×3パネル、可変cell集合、Student-t CI、実寸fixture、fail-closed bbox、PNG/PDF/provenanceを備える。dynamic fieldの厳格parse、none/tunedの強調、paired contrastを加え、診断は同scriptの新modeまたは小さい専用consumerにすれば、ほぼ同じgeneratorを複製する必要はない。

診断図の6本×最大65,536更新は密度が高いため、全点をprovenanceへ保持したうえで、図だけは事前固定したdecimationと極値保持を使う。hit率はn=1なのでCIなしというplanの扱いでよい。

## MF-12 — 事前登録のfreeze境界が不足している

**位置:** brief「docs」「段4で凍結」、plan「図生成器」「投入設計」。  
**指摘:** 文書名だけが決まり、どのcommit・patch stack・driver・解析コード・腕順序をqsub前に束縛するかが定義されていない。  
**受理の含意:** B-10と同様に文書blob、commit ancestry、patch/driver/PBS/generator SHAを全runへ束縛すれば、結果前に存在した規則を検証できる。  
**拒否の含意:** pathだけを固定すると同じpathを結果後に改訂でき、事前登録の効力を証明できない。  
**成果物への影響:** performance/diagnostic/certification JSONと図provenanceに同じfreeze identityを持たせる。  
**修正案:** 次節の最低項目を埋めたcommitを作り、そのcommitを指すrunだけをformal resultとして受理する。

## 事前登録文書に最低限必要な節

`docs/dynamic-backoff-preregistration.md` には少なくとも次が要る。

- 版、発効状態、改訂履歴、結果閲覧前後の境界
- T-2187/T-2216を既に見ていることと、今回が未見holdoutではないこと
- 書ける主張・書けない主張
- 6腕、または追加対照を含むexact macro値とarm identity
- `update_us` など条件付きinert fieldの説明
- workload、thread、records、extime、rep数
- 7 node/job block、distinct-host条件、事前固定した腕順序
- H1〜H6、primary endpoint、副次endpoint
- 対内log比CI、t値、±3%等価域、複合判定、多重性
- 欠測、timeout、partial block、retry、n=6、n<6、外れ値規則
- K/capの発火境界と予想実効窓
- perf/diagnostic/certification buildの分離とheadline eligibility
- 診断指標の非循環定義、unscored、overflow規則
- 認証の条件付きgo/no-goと、未認証腕の表示
- 凍結commit、文書blob、ccbench pin、A/B patch hash・順序付きstack digest
- probe/PBS/解析generator/verifier closureのidentity
- expected job集合、出力namespace、group manifest、成果物hash
- 「性能値は未認証」「認証は測った固定条件の正しさだけ」という主張境界

briefに既にあるのは腕、3 workload、8 thread、n=7、extime、perf/診断分離、部分的な認証範囲である。仮説、統計判定、等価域、多重性、順序、欠測、retry、freeze identity、認証go/no-goは欠けている。

## A-01 — perf buildと診断buildの分離は受理

**位置:** brief「不変条件」「P8」、plan「performanceと診断mode」「図生成器」。  
**指摘:** `BACKOFF_TRACE=0` のsymbol 0検査、別schema、`headline_eligible=false`、診断throughputを図へ混ぜない設計は規律1を満たす。  
**受理の含意:** 診断は機序資料に限定し、性能主張を7個のtrace-disabled blockだけから作ればよい。  
**拒否の含意:** 診断throughputをheadlineやH1〜H5へ混ぜるとbuild差と計装負荷が処置差へ混入する。  
**成果物への影響:** insightでは性能表と診断節を分離し、相互に数値を代用しない。  
**修正案:** 診断をperfと同じnode・時間帯へ置く必要はないが、source/toolchain identityは揃え、計装が軌跡を乱しうる限界を明記する。

同時刻へ揃えてもinstrumentation confoundは消えない。診断3腕を同一診断job内で比較することの方が重要である。

## N-01 — arm labelとinert値の表記が揺れている

**位置:** brief P9、plan「正式な6 cell」。  
**指摘:** briefの `cw+as` / `cw+as+dyn` とplanの `cw-as` / `cw-as-dyn` が一致せず、さらにcount cap非ゼロ時の `update_us=2560` はruntime上inertである。  
**受理の含意:** exact labelと条件付きinert fieldをpreregで一意化すればjoinやcaptionの曖昧さは消える。  
**拒否の含意:** 未修正でも測定自体は可能だが、成果物間のidentity比較が不要に複雑になる。  
**成果物への影響:** JSON label、表、図legendを同じ綴りへ統一する。  
**修正案:** machine labelはhyphen形、表示名はplus形など、一方向の写像を固定する。

## N-02 — 「Cicada」の表示は算法由来に限定する

**位置:** brief scope、plan「briefへの指摘」、図title案。  
**指摘:** 実測protocolはSiloであり、Cicadaはadaptive backoff算法の由来にすぎない。  
**受理の含意:** 「Silo上のCicada型adaptive backoff」と書けば対象を正確に表せる。  
**拒否の含意:** 単にCicada実験と書くと別protocolの測定に読まれうる。  
**成果物への影響:** insight title、図caption、認証要約の名称だけを修正する。  
**修正案:** protocolとalgorithm originを別fieldで保存する。

## 総括

- **must-fix: 12件**
- **nit: 2件**
- **反証したbrief前提:** P6の「8.5分から3.6秒/runを導く計算」とその計上方法、P9の「K=10000が48 thread全workloadで2560 µs相当」という一般化、および40960 µs capの安全根拠
- **未支持だが未反証:** P3の動的ceiling無効果、P8/planの「勾配符号的中率」という解釈
- **維持可能:** P1のcount-window機構、P4の全機構on一腕だけの認証、P5のpatch重ね適用、P7のledger非追記、perf/diagnostic build分離
- **提案仮説:** H1 全動的機構対tuned、H2 read-heavyでのnone非劣性、H3 count-window増分、H4 adaptive-step増分、H5 dynamic-ceiling等価、H6 stock陽性対照

最大の問題は、六腕が「実装packageとして効いたか」には答えられても、現状ではcount数、実効更新間隔、scan overheadを分離できず、診断の「的中」も真の勾配精度ではない点である。投入前に統計判定と主張境界を凍結し、可能なら短cap対照を追加し、認証24 jobはH1通過後の後続段へ送るのが最も費用対効果が高い。