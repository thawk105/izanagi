## 事前登録の全文草案

親の裁定で特に修正すべき点は、①停止は報告だけでなく入口で強制される、②重複は既存結果の再利用になる、③共通の許容集合と生成器の支持集合は異なる、の3点です。以下はこれらを反映した未発効の全文草案です。モデル等の実値が未確定であることも隠していません。

```markdown
# B-5 生成器対照 — 固定 backoff hole の条件付き優越の事前登録

本書は、固定 backoff hole について、知識付き K2 loop、
ランダム変異、機械 sweep を固定評価予算で比べる規則を定める。
2026-09-19 のユーザー決定は本書の作成を認可した。
本走、生成器の実装、D1409 の条件変更は認可していない。

## 0. 版と発効

本書は v1 である。
文書作成の commit と、本走を認可する発効 commit を区別する。
発効は、ユーザーの本走認可を伴う日付付き commit による。
発効前に本書が存在することだけでは、測定の認可にならない。

発効後は既存本文の bytes を変更しない。
訂正は末尾の Erratum 節への追記だけで行う。
訂正の理由、日付、適用する cohort、判定への影響を記す。
既存結果を有利に読み替える変更を、事前登録の訂正と呼ばない。

本書は解析器の pin を持たない。
B-5 専用の解析 consumer は未実装であり、pin は文書契約に留まる。
文書の存在、hash の記録、docs lint の成功を機械的強制と呼ばない。
本書自身の hash や自身を含む commit hash を本文へ埋め込まない。

発効時は、本書の raw bytes の SHA-256 を日付付き決定記録へ写す。
測定時点の版と、後日の解析規則の版を別々に記録する。
D1790 の区別を継承するが、対応する解析器が既にあるとは主張しない。

本書の規則に加え、§12 の実行構成の実値を発効前に固定する。
モデル、prompt、実行経路、correctness argv の未確定を既定値で埋めない。
これらが未確定の間、本書は発効可能な完成済み実験構成ではない。

## 1. 主張の形と主張しないこと

成立時に許す主張は、D1067 の次の形に限る。

「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より
高い score だった。」

比較対象は、知識と critic 還流を含む K2 loop という構成である。
LLM 単体、知識、適応、critic のそれぞれの寄与は分離しない。
workload ごとの成立条件は §7 の連言とする。

次の主張は行わない。

- この結果が LLM の必要性を示す。
- 非 LLM 生成器一般より優れる。
- 新しい CC 構造を発見した。
- 他の hole、protocol、環境でも成立する。
- 同じ金銭費用、token 数、生成時間、総 wall time で優れる。
- B-4 の還流効果または K2 知識利用の因果効果を示した。
- 本書の作成または本走の完了だけで B-5 が充足した。

`phase3-main-experiment.md` の「2026-07-10 追記」に従い、
スカラー backoff は headline 候補にしない。
本書は headline、D52 の系レベル主張、旧対照の休眠を復活させない。
失敗条件 (c) の成立を正当な結末として最初から認める。

D1409 の「非列挙」の定義は変更しない。
有限の候補集合で固定予算の生成器を比較することと、
非列挙のコード片軸が実体化したと主張することを区別する。
本書の対象は前者だけである。

## 2. 編集面と候補集合

編集面は `silo-backoff-magnitude` の既存 hole とする。
`patches/silo-backoff-fixed.patch` 適用後の
`include/backoff.hh` にある合成枝の1文だけを置換する。
stock 枝、骨格、marker、他ファイルは編集しない。

受理する意味上の候補集合を S = {1, 2, ..., 1000} µs とする。
Tier 1 文法と帰属整合検査を3 arm 共通に適用する。
実装は `double now_backoff = <literal>;` の1文である。
literal は suffix のない数値で、value と数値的に一致しなければならない。
値は有限の整数であり、bool、0、負数、1000 超を含めない。
受理済みの数値表記は既存規則で正準化する。
文法だけでなく値域と帰属整合を合わせて S を定める。

S は1000点であり、完全列挙可能である。
LLM にだけ S の外のコードを許すことはない。

ただし、共通の許容集合と各生成器の支持集合は同一語で扱わない。
random は S の全点に正の確率を持つ。
sweep は S 内の28点の格子に限定される。
LLM が S の全点へ正の確率で到達することは証明しない。
したがって「3生成器の確率的な支持集合が同一」とは書かない。
比較するのは、共通の編集面で異なる選択方策を持つ凍結生成器である。

no-op、stock 枝への切替、空実装は候補にしない。
stock は候補支持集合の外にある共通の不採用時対照である。
同じ値の再提案は許し、重複だからといって再抽選しない。
重複も新しい評価機会を使い、同じ値を fresh に測定する。
過去の性能値の再利用を新規評価として数えない。

## 3. 予算、停止、失敗の計上

各 arm × workload × 系列の探索予算を次に固定する。

- 評価数 B = 10。
- 原提案上限 A = 30。
- 系列ごとの administrative wall-clock 上限は設けない。
- 性能を理由とする早期停止は行わない。
- B 完走、または A 到達まで進める。
- certified 候補を得た時点でも停止しない。

原提案は、生成器が候補1件を提出する機会である。
空出力、schema 不合格、値域違反、文法違反も A を1消費する。
生成器の内部で候補を選び直した結果だけを提出してはならない。
API の純粋な通信障害は後述の機械故障として別記録する。

文法、帰属整合、diff 検疫、Tier0 を通過した候補を
certification pipeline へ投入した時点で B を1消費する。
Tier0 はコンパイルと固定スモークを指し、文法検査と同義ではない。
具体的なスモーク契約は発効前に実値を固定する。
現時点で B-5 共通の Tier0 が実在すると主張しない。

文法・検疫・Tier0 不通過は A を消費し、B は消費しない。
verifier の anomaly reject は B を消費する。
投入後の候補起因の失敗も、その評価機会を返却しない。
成功して certified になった候補だけを数える運用は禁止する。

A 到達時に B 未達でも系列を差し替えない。
評価済みの候補から §6 の endpoint と score を求める。
その系列は原提案予算を使い切った生成器の結果として残す。
B 未達を理由に、その系列だけを統計標本から除かない。

機械故障 retry は、同じ候補・同じ入力・同じ予定位置に限る。
上限は元の操作に対して追加2回とする。
対象は、候補処理前の通信障害、scheduler による中断、
ノード喪失、または候補と独立な依存物供給・入出力障害に限る。
単なる非ゼロ終了、signal、例外という名前だけでは認めない。

anomaly、候補起因のコンパイル失敗、遅い性能、品質判定の赤は
機械故障 retry の理由にしない。
分類不能な失敗を、無料 retry として扱わない。
retry でも同じ論理 A/B slot を使い、物理試行数と費用は全件記録する。
測定結果を得た後に、より良い値を求めて retry しない。
機械故障が上限を超えた系列は欠測とし、stock に置換しない。

D39 決定2から継承するのは「10」という数値だけである。
本規則は「10 iteration または3600秒」と同値ではない。
A/B の分離、3600秒上限の撤去、収束・逆方向枯渇停止の不適用は
探索機会を変える実質改訂であり、制約方向のみの改訂とは呼ばない。
本走認可時に、この変更を明示的に確認する。

現行 `drive_iteration` は入口で `check_stop` を実行する。
停止済みなら `ran=False` となり評価しない。
親が次の job を投入する運用だけでは B 完走を保証できない。
checkpoint の改変や初期化による迂回は、本規則への適合ではない。
B-5 の停止・計上契約に対応する実装が要る。

## 4. 生成器の操作的定義

### 4.1 LLM: 知識付き K2 手動 loop

planner、coder、critic を親が呼び出す K2 手動 loop とする。
harness 自身が LLM を spawn する構成ではない。
coder 契約は `coder-v4-autonomous-k2` とする。
reflux は on、B-4 mode は使わない。

各系列は fresh context で開始する。
他の系列、他 arm、独立再計測、floor の結果を入力へ戻さない。
系列内の過去評価と、固定した K2 知識だけを利用する。
親が性能を見て追加助言、候補修正、再抽選をしてはならない。
役割ごとの実入力と出力を全件保存する。

知識は T-2746 の `materials/knowledge-input.json` の射影を採る。
manifest digest は
`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`。
その source は commit
`2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の
`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl`。
source SHA-256 は
`2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`。
旧環境の40、30、40 µs の結果を含むことを開示する。

初回の現在性能には、同じ条件の fresh stock 観測を用いる。
以後は既存の構造化 digest と役割入力への射影を利用する。
whiteboard の5 field と `delta_pct=None` は維持する。
生 trace を役割入力として渡さない。
既存の正しさ信号を自由文の独自 schema に置換しない。

critic 診断は D2155 の明示逐語からの射影を用いる。
`k2_critic_diagnosis` の field は次の6個に限る。
`data_boundary`、`source_sha256`、`attribution`、
`recommend`、`avoid`、`uncertainty`。
同じ診断を次の planner と coder へ渡す。
初回は key を置かない。
報告用 AO から自動的に診断を拾う経路にはしない。

モデルの exact ID、推論設定、生成設定、役割本文、prompt、
入力 schema、初回入力、欠測時表現は発効束へ実値を固定する。
本書作成時にはこれらの全実値は未確定である。
可変 alias や「既定モデル」のまま発効させない。
入力保存は実送達や採用の独立証明ではないことも明記する。

### 4.2 random: 離散 log-uniform

候補は S 全体から復元抽出する。
過去の成功、失敗、anomaly、性能値によって分布を変更しない。
ここでの log-uniform は次の整数重みで厳密に定義する。

v = 1..1000 について、
`m_v = floor(2^128 × ln((v+1)/v))`、
`M = Σ m_v`、`P(v) = m_v/M` とする。
これは連続 log-uniform を整数区間 [v,v+1) に分けた分布の
固定精度による離散化であり、単なる整数一様分布ではない。
重みは全て正であり、発効前に1000個の整数配列と hash を保存する。
床関数の値が確定する精度で算出し、浮動小数点の実装差に委ねない。

乱数 preimage は UTF-8 の ASCII 文字列とし、改行なしで
`b5-generator-contrast-v1|random|w|r|a|c` とする。
w は workload 名、r は1..12、a は1..30、c は0開始の counter。
整数は先頭ゼロのない十進表記とする。
SHA-256 を unsigned big-endian の256 bit整数 U と読む。

`L = floor(2^256/M) × M` とし、U >= L なら c を増やして再度読む。
U < L なら `U mod M` を累積重み区間へ写して v を得る。
この拒否は乱数の偏りを除く処理であり、原提案の再抽選ではない。
候補生成後の重複や不成績を理由とする再抽選は禁止する。
commit hash を seed に使わず、commit の作り直しによる順序変更を避ける。

分布の選択は、B-10 の既知の性能地形を見た後の判断である。
「結果を知らずに選んだ中立な分布」とは書かない。
一様分布等を事後に追加し、良い対照だけを主比較へ採らない。

### 4.3 sweep-matched

格子は `EXTENDED_SWEEP_US` と S の共通部分とする。
具体的な28点は次のとおりである。

1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50,
75, 100, 150, 200, 250, 300, 400, 500, 560, 600, 700,
800, 900, 1000

各 workload・系列について、各 v の文字列
`b5-generator-contrast-v1|sweep|w|r|v` の SHA-256 昇順で並べる。
同 hash の場合は v の数値昇順とする。
最初の10点を順に評価する。
候補に依存する事前不通過があれば次点へ進む。
格子を使い切った場合は候補枯渇と記録し、差し替えない。

軸と格子の由来は既存 backoff 研究であり、新たな軸発見ではない。
格子の元定義が K2 の20/25 µs の結果より前にあることと、
今回の格子採用判断が既知結果を見た後であることを分けて記す。
既存の `MEASUREMENT_SEEDS` の shuffle は本書の hash 順ではない。
既存 sweep の template 式経路は評価経路として利用しない。

### 4.4 sweep-ceiling

同じ28点の全走を、族外の副次記述として区別する。
1000点の完全列挙や、連続空間の真の天井とは呼ばない。
その結果を主比較の格子、順序、n、endpoint 選択へ戻さない。
本 v1 の主 cohort の予算には含めず、実走は別途認可とする。
未取得なら未取得と記し、過去の B-10 を代入しない。

## 5. 共通の評価経路

3 arm とも、同じ hole literal を同じ検疫経路で評価する。
目標経路は `p3_s4_loop` の proposal 読込みから
hole 挿入、検疫、`run_campaign`、verify、bench までである。
生成器の由来は記録するが、受理文法と正しさ基準を変えない。
機械生成候補を LLM が生成したものと偽って記録しない。

性能 workload は以下の3つとする。

| workload | rratio | skew | rmw |
|---|---:|---:|---:|
| write-heavy | 5 | 0.9 | 0 |
| balanced | 50 | 0.9 | 0 |
| read-heavy | 95 | 0.9 | 0 |

性能動作点は records=1,000,000、threads=48、
extime=3秒、reps=5 とする。
1 session の観測値は5 rep の median throughput とする。
較正を満たす環境で直列実測し、勝手に records を減らさない。

候補の共通 genome は silo、BACK_OFF=1、
NO_WAIT_LOCKING_IN_VALIDATION=1、NO_WAIT_OF_TICTOC=0、WAL=0。
BACKOFF_FIXED と hole literal は候補 v と一致させる。
stock は同じ共通フラグで BACK_OFF=1、BACKOFF_FIXED=-1 とする。
これは適応 backoff の stock であり、BACK_OFF=0 の無 backoff ではない。

correctness は性能 workload と同じ tuple 数、thread 数、
rratio、skew、rmw を明示し、trace extime=3秒とする。
残りの argv、seed の扱い、verifier の mode と版を発効束で固定する。
legacy の小構成を既定値として黙って利用しない。
この exact な経路が現在の CLI で成立するとは主張しない。

各性能 session の前に、別 build・別 run の correctness を通す。
anomaly が1件でもあれば当該候補を即 reject する。
拒否候補の bench 値は取得・採用しない。
性能値には trace-disabled build の値だけを用いる。
screening の bench-first 経路を用いない。

WAL の verify、bench、commit と候補 source の対応を残す。
source、binary、環境、toolchain、argv、文法版の出所を記録する。
hash 一致だけで実翻訳単位の意味一致や compile-out を証明したとしない。
certified の射程は観測した point read/write trace に限る。

探索候補の評価 job には同機体・同 job の stock 対照を置く。
初回は stock を先に測り、その値を初期入力へ渡す。
以後の stock/candidate 順は事前 schedule で均衡化する。
stock は探索 B に含めないが、測定数と総費用には含める。
現行 job body にこの対測定が実装済みとは主張しない。

## 6. endpoint と score

探索終了時に、各系列の endpoint を1個だけ固定する。
対象はその系列内で certified となった候補である。
探索時の session median throughput が最大の候補を選ぶ。
同値は v の数値昇順、さらに評価 slot 昇順で決める。
同じ v が複数回出ても探索履歴を削除しない。

endpoint の値、source、出所 slot を独立再計測前に固定する。
探索時の最大値を score へ流用しない。
他系列の候補や過去の既知勝者を補充しない。

endpoint を N_eval=5 の fresh session で再計測する。
score はその5 session の median throughput、単位は絶対 tps とする。
各 session 内の5 rep と、系列数 n=12 を混同しない。
選択した候補が stock より遅くても、事後に stock へ取り替えない。

探索で certified 候補が1個もなければ「何も採用しない」とする。
score は同 workload・同 block の fresh stock score とする。
stock score は block 内に配置した別の5 session の median とする。
この5件は全 arm の不採用系列に共通に使い、共有を明記する。
anomaly を0 tps や −100% へ変換しない。

endpoint の再検証で anomaly が出た場合も、その候補は採用しない。
次点への選び直しはせず、stock fallback と失敗条件 (a) を記録する。
同じ source・workload の他 endpoint にも発見を適用する。
過去の certification 記録自体を書き換えることはしない。

通信障害、欠落、identity 不一致、不安定性で再計測が成立しない場合は
候補の不採用と区別し、score を欠測とする。
機械故障による欠測を stock fallback で埋めない。
stock 自身の正しさまたは測定が成立しなければ当該比較は判定不能とする。

探索、score、floor の session は互いに再利用しない。
score 確定後に候補選択へ戻らない。

## 7. 母集団、反復、floor、判定

### 7.1 母集団と配置

母集団は、この凍結した環境・workload・生成器構成での探索系列とする。
別モデル、別知識、別 hole、別 protocol へ一般化しない。
主セルは3 arm ×3 workload の9セル。
各セル n=12 系列、計108系列とする。
3つの時間分離 block に各4系列を割り当てる。

block 間は前 block の最終測定から次 block の初回測定まで
少なくとも1時間空け、別プロセス群として実行する。
これは cold-boot や独立性の証明ではない。
各 workload の同じ系列番号で3 arm を対にする。
arm の6通りの実行順を12組に各2回割り当てる。
順序、workload 配置、score/floor session の配置を発効前に保存する。
結果を見て block、対、順序を変更しない。

系列間で LLM context と探索状態を引き継がない。
random と sweep の順序は §4 の系列番号から導く。
測定プログラムの seed 制御の有無は別に開示する。
生成器 seed があることを、bench RNG の制御と呼ばない。

### 7.2 対象別 floor

各 endpoint に score 用とは別の N_floor=5 session を取る。
不採用系列には専用 endpoint floor を作らず、stock floor を用いる。
stock floor は workload × block ごとに5 session とする。
stock score の5 session とも分離する。

CV は session median の標本標準偏差を算術平均で割る。
標準偏差の分母は n−1 とする。
異なる endpoint の値を pool して CV を作らない。
workload ごとの stock CV は同一 stock の15件から求め、
block 内 CV も算出して両者の大きい方を採る。

比較相手 b、workload w の相対 floor f は、
0.03、stock CV、LLM と b の各 endpoint CV の最大値とする。
対数尺度の等価域は δ=ln(1+f) とする。
3% は保守下限であり、今回測った noise の値とは呼ばない。
stock だけから異なる endpoint の floor を代用しない。
5 session の CV は不確実であり、精密な noise 推定とは主張しない。

必要な floor が欠測・非有限なら比較は判定不能とする。
floor の大きさを理由に追加測定や都合のよい標本除去をしない。

### 7.3 優越の検定

検定単位は探索系列であり、候補 slot や within-run rep ではない。
系列 r の対差を `d_r=ln(score_LLM,r/score_b,r)` とする。
統計量は12個の d_r の算術平均とする。
符号を全2^12通り反転する片側 exact permutation を行う。
観測統計量以上を tail に含める。

この exact 性は、帰無下の対内交換可能性または符号対称性を前提とする。
モデルを用いない任意の平均差帰無仮説へ exact と主張しない。
時間ドリフト、共有 stock、系列相関が消えたとは主張しない。
前提を損なう配置逸脱がある場合は推測的判定を行わない。

比較族は3 workload ×2 baseline の6個に固定する。
Holm 法、family-wise α=0.05 とする。
欠測や規約不適合で判定不能な比較も族から除かず、計算上 p=1 とする。
その p=1 は観測された検定結果ではなく、判定不能の処理である。

workload ごとの条件付き優越は、2 baseline のそれぞれについて、
Holm 補正後有意、median(d)>δ、各 block の median(d)>0 を満たす連言とする。
片方への勝利だけでは workload の主張を成立させない。
全3 workload での成立を述べるには6比較すべてを満たすことを要する。

### 7.4 同等、negative、判定不能

全12系列と独立再計測・floor が揃い、
`|median(d)| <= δ` なら、登録した操作的定義で (c) 成立とする。
これは「観測差が比較 floor 内だった」という判定である。
母集団の等価性を信頼区間で証明したとは書かない。
優越性検定が非有意だったことを、その根拠にしない。

どちらか一方の非 LLM 対照が (c) を満たせば、その workload の
LLM 固有の利得は示せなかったと記す。
baseline が floor 超で上回る場合は、より強い negative として別記する。
LLM 側の差が floor 超でも補正後有意または block 再現を欠けば、
条件付き優越は示せず、優越・同等の結論は判定不能とする。

n=12 の最小片側 p は1/4096で、Holm 初段0.05/6を下回る。
これは p 値解像度の根拠であって80% power の保証ではない。
差の絶対値が等しい例では、正が11/12なら p=13/4096、
10/12なら p=79/4096となり、後者は Holm 初段を通らない。
実際の power は未知の効果と分散に依存する。
結果を見て n を増減しない。

全9セル、全6比較、全未完走、anomaly、fallback、欠測、
floor、raw p、補正 p、block 別効果を報告する。
本 v1 の主 cohort は1回だけとする。
失敗後の再発火を独立の成功機会として隠さない。
後続 cohort は別の位置づけと登録を必要とし、初回結果を置換しない。

## 8. 既知結果台帳と HARKing 境界

本書は backoff 研究全体の結果を見る前に作られた登録ではない。
前向きに固定するのは、将来の新 cohort の生成・測定・判定規則である。
以下を知った後に、分布、格子採用、n、score、判定規則を選んだ。

| 既知材料 | 内容と本書での扱い |
|---|---|
| B-10 拡張格子、fig2c | 0〜1000 µs の性能地形を既知とする。主標本へ転用しない |
| B-10 右 tail | 1000 µs 超から9999 µsまでの既知結果。S の拡張根拠にしない |
| K2 第1巡 | 20 µs、719324.5 tps。配線規模の過去観測 |
| K2 第2巡 T-2746 | 25 µs、687508.5 tps。第1巡との非同時刻比較 |
| T-2581 | 20 µs が既評価値であることを既知とする |
| proposal-3 | 20 µs の再提案。T-2746 では未評価 |
| K2 knowledge | 旧環境の40/30/40 µs、491796.5/525721.5/487088.5 tps |
| A-2/A-6 | fixed 5 µs の正負を含む別 protocol の既知結果 |
| T-1998 | balanced の別登録による対測定。B-5 の標本ではない |
| P2-4 | 旧測定契約の利得。現行 comparator にしない |
| P2-5、D52、前回設計 | スカラー探索の非分離と、前回の設計上の欠陥 |

主な所在は次のとおりである。

- `output/insights/2026-09-18/t2746-k2-loop-round2/README.md`
- 同 `materials/knowledge-input.json`
- `output/insights/2026-08-26_b5-llm-necessity-contrast-design.md`
- `output/insights/2026-08-26/b5-contrast-review-verbatim/`
- `docs/b10-backoff-static-tail-preregistration.md` の開示節
- `docs/t1998-balanced-stock-inline-preregistration.md` の既知材料節
- `docs/paper-story/2026-09-17.md` の過大主張チェックリスト

一次成果物を直接読んだ項と、brief・既存記録から知った項を区別する。
特に T-2581、A-2/A-6、fig2c の全 raw 値を今回再監査したとは書かない。
発効時は、それらの exact artifact と閲覧者・閲覧時点を台帳へ追記する。
その間に得た追加の知見も差分台帳へ残す。
既知候補と同じ値が fresh に生成されることは許す。
過去の性能観測、certification、floor を新 cohort へ移植しない。

## 9. 失敗条件 (a)〜(e)

(a) anomaly が出た候補は即 reject する。
探索 B を消費し、採用候補から外す。
後段の anomaly は §6 に従い endpoint の不採用として残す。
正しさの失敗を性能観測に変換しない。

(b) 比較差が対象別 floor 以下なら、有意性だけで優越と書かない。
stock に対する利得と、生成器間の利得を区別する。
独立 floor が無ければ判定不能とする。

(c) 同じ評価予算の random または sweep-matched が、
§7 の操作的等価域内で再現すれば成立とする。
成立を失敗した実験として隠さず、正当な negative の結末として報告する。
sweep-ceiling のみで再現した場合は、予算が異なる副次記述に留める。

(d) クロスプロトコル stock 最良への優越は本書では測らない。
したがって本書から (d) の不成立を主張できない。
silo 内の生成器比較の成立を、ベース protocol 選定の妥当性へ広げない。
この点は未検証として残す。

(e) workload ごとに別々に探索した endpoint の結果を、
同一 variant の workload 横断再現と呼ばない。
同一 endpoint の他 workload 再計測は本 v1 の主予算に含まれない。
したがって workload 特化と退行の不在は示せない。
全 workload の生成器比較結果は必ず併記し、
横断評価で floor 超の退行が既知なら、それも併記する。
本書だけで B-7 や失敗条件 (e) の確認が閉じたとは書かない。

## 10. 実行可能性

| arm/共通部 | 実在するもの | 限界・欠けるもの |
|---|---|---|
| LLM | proposal 読込み、K2 manifest、検疫、単回評価、digest | 較正動作点、B/A、停止契約、独立系列の運用に実装が要る |
| random | 受理文法と単回評価部品 | 凍結分布から proposal を作る生成器に実装が要る |
| sweep-matched | 28点の元となる格子、既存 sweep | hash 順10評価と共通 literal 経路への接続に実装が要る |
| stock | BACKOFF_FIXED=-1 の既存構成 | 同 job 対測定と block stock 配置に実装が要る |
| 重複 | 過去 WAL を復元する既存処理 | fresh 評価を B と数える契約に実装が要る |
| 正しさ | 検疫と certified pipeline への委譲 | exact correctness workload と Tier0 の共通契約が未成立 |
| score/floor | 過去実験に独立再計測の先例 | B-5 の系列 endpoint、fallback、対象別 floor に実装が要る |
| 解析 | 他実験の統計・束縛の先例 | 本書を消費する B-5 解析 consumer に実装が要る |

現行 `default_perf()` は100k records、4 threads、1秒、2 repsである。
CLI はこの設定を使い、較正値への上書き口を持たない。
`default_cfg()` の identity にも配線規模が書かれている。
性能引数だけを外から読み替えて整合したとしない。

現行 loop は重複候補の既存 terminal 結果を復元する。
それは今回要求する fresh 評価と異なる。
現行 sweep の run_kind に B-5 の B 点 mode はない。
既存の31 genome 全走を10評価と同一予算扱いしない。
これらの欠ける部品を、本 docs-only 作業で実装しない。

## 11. 費用見積りと総量

最大探索量は108系列×10評価=1080評価。
原提案は最大108×30=3240件。
探索中の同 job stock は最大1080 session。
endpoint score は最大108×5=540 session。
endpoint floor は最大108×5=540 session。
block stock は score/floor 各45、計90 session。
合計は最大3330 correctness/performance session である。
fallback があっても節約分を追加探索へ振り替えない。

5 reps×3秒の設定時間だけなら、
3330×15秒=49,950秒、約13.875時間である。
これは bench の設定時間の算術であり、実 wall の予測ではない。
build、DB準備、verify、settle、再測、LLM、待ち時間を含まない。

T-2746 は配線規模の1評価で Elapse 432秒だった。
この値を3330 sessionへ機械的に掛けると399.6時間になるが、
較正動作点や共有準備費用が異なり、本走所要の推定値として採用しない。

指定範囲の資料検索では、B-10 拡張格子の
1 workload 31 genome の Elapse は見つからなかった。
8点の別 sweep には629〜632秒の完走記録がある。
単純除算は約78.6〜79.0秒/点だが、共有 build を含む別経路の平均である。
これを本 hole の1評価時間として固定しない。

前回設計に引用された旧環境の verifier 所要は140.66〜433.33秒/件。
3330件へ外挿すると verifier だけで約130.1〜400.8時間となる。
これは旧環境・異なる候補からの推定であり、今回の実測ではない。
bench 設定時間を加えると約144.0〜414.7時間相当となるが、
全 wall の区間推定でも上限保証でもない。

費用計画は百時間級と扱い、数時間で完走できるとは書かない。
本走前に、較正動作点・exact correctness 経路で所要を確認する。
その試走の結果を主標本へ入れず、閲覧を既知結果台帳へ残す。
試走と実装の認可は、本書作成の認可に含まれない。

総実行 wall の提案上限は600時間とする。
これは約400時間級の外挿に余裕を置いた管理上の提案であり実測値ではない。
本走認可時に受容可否を確認する。
計上対象は build、verify、bench、失敗、retry、floor、再計測の全実行時間。
queue 待ち、親の待機、LLM の時間・費用は別欄にも記録する。
上限不足が判明したら、観測値を理由に n や正しさ条件を下げない。
未完走比較を対称に判定不能として終了する。

## 12. 発効束、凍結、閉じないもの

発効前に、次の実値と文書契約を1つの対象 cohort へ結び付ける。

- 本走認可の日付、decision ID、承認対象 commit。
- 本書の raw-byte SHA-256 と、その保存先。
- repository、CCBench、文法、環境、toolchain の版。
- 実行 script、生成器、解析規則の bytes と hash。
- LLM のモデルと全役割 prompt、知識射影、入力 schema。
- random の整数重み表、seed preimage、sweep 全順序。
- 108系列の schedule、各評価・score・floor の識別子。
- correctness/Tier0/bench の exact argv と失敗時処理。
- D39 の予算・停止改訂、総費用上限への明示承認。
- 既知結果台帳の差分と、規約適合を確認した実装の所在。

この一覧は機械 gate の新設指示ではない。
現在ある検査と、文書上の確認と、未実装を区別する。
今回の変更面は本書と docs 地図の1 bullet だけである。

本書は、ユーザーの本走認可、実装の存在、実送達、
cold-boot、無人実行、一般的な安全性を代行しない。
D1409 の二重の壁、旧 headline の休眠、B-4 の因果分離を閉じない。
クロスプロトコル最良比較と同一 variant の横断退行検査も閉じない。
既存結果、certified 選択、材料レポート値、試行台帳は変更しない。

## 13. 過大主張チェックリストとの整合

`paper-story/2026-09-17.md` の「過大主張チェックリスト」に加え、
本書の結果を記述する際には次を守る。

- B-5 の主張は、登録した2対照への固定予算下の条件付き優越に限る。
- backoff が完全列挙可能なスカラー軸であることを併記する。
- 共通の編集面と、生成器の支持集合・情報利用の違いを分ける。
- K2、適応、critic を含む構成比較であることを落とさない。
- certified の射程と、要求構成・実 build の同一性の限界を添える。
- trace-disabled 性能と別走 correctness の証拠を混同しない。
- stock 適応 backoff と、無 backoff 対照を混同しない。
- 3% の保守下限、今回の CV、他実験の floor を別々に記す。
- 非有意、floor 内の操作的同等、欠測による判定不能を分ける。
- 全 workload、anomaly、fallback、未完走を数値主張に添える。
- 過去の結果を新 cohort の標本や予測的再現へ昇格させない。
- 配線、文書、hash、lint の成功を測定結果や機械的強制と呼ばない。
- 本書や本走の完了を、headline・B-4・B-7・B-10 の充足と呼ばない。
```

## docs/README.md の bullet 草案

挿入位置は、`t1998-balanced-stock-inline-preregistration.md` の bullet の直後、`b10-multinode-formal-run-design.md` の直前です。現物は `docs/README.md:58`、`:62`。

- `b5-generator-contrast-preregistration.md` — 固定 backoff hole で知識付き K2 loop・ランダム変異・機械 sweep を同一評価予算で比較する事前登録。条件付き優越、独立再計測による score、系列単位の判定、既知結果、実装が要る部分、発効条件を定める。**本走の認可ではなく、headline と D1409 の条件を変更しない。**

## 実行可能性の照合

以下の相対 path はすべて指定 worktree 基準です。

| arm | 既存機構 | file:line | 実在する部分 | 欠ける部分 | 「実装が要る」か |
|---|---|---|---|---|---|
| 共通 | Tier 1・値域 | `orchestrator/campaign/backoff_hole_grammar.py:4`、`:719`、`:745` | 1文、正準化、整数1..1000 | B-5 の生成・反復ではない | 文法自体は不要 |
| 共通 | value/literal 整合 | `orchestrator/campaign/p3_s4_loop.py:1666` | literal と value の数値一致 | — | 不要 |
| LLM | 親主導 K2 | `orchestrator/campaign/p3_s4_loop.py:25`、`:2815`、`:2822` | proposal、role、manifest の入口 | exact model/prompt の発効束 | 文書固定が必要 |
| LLM | critic 診断 | `orchestrator/campaign/p3_s4_loop.py:1222`、`:1237`、`:1248` | exact 6 field、両役割への同一射影 | 実送達・改善効果の証明 | 射影は実在。効果は未取得 |
| LLM・共通 | 性能設定 | `orchestrator/campaign/p3_s4_loop.py:1564`、`:1631`、`:3044` | identity と perf の配線規模設定 | 1M/48/3秒/5 reps・3 workload の共通運用 | **要る** |
| LLM・共通 | 停止 | `orchestrator/campaign/p3_s4_loop.py:1319`、`:2470`、`:2559` | 入口停止で評価を拒否 | B/A 分離、収束停止不適用、3600秒撤去 | **要る。運用だけでは不足** |
| 共通 | 単回評価 | `orchestrator/campaign/p3_s4_loop.py:1980`、`:2014` | 検疫後 `run_campaign` に委譲 | exact correctness の指定・記録、共通 Tier0 | **要る／未成立** |
| 共通 | 重複 | `orchestrator/campaign/p3_s4_loop.py:1795`、`:2027` | terminal の既存 WAL 復元 | 重複も fresh に1評価する契約 | **要る** |
| LLM・共通 | 計算ノード job | `tools/pegasus/p3_s4_loop_pegasus.sh:1`、`:580` | compute-only、proposal1件の呼出し | 同 job stock 対、B-5 schedule | **要る** |
| random | 専用生成器 | `output/insights/2026-08-26_b5-llm-necessity-contrast-design.md:26`以降、親 brief「段1実測」 | 前回の意味検索では不在、親も維持 | 分布・seed から literal proposal を生成 | **要る** |
| sweep | 格子・既存 driver | `orchestrator/campaign/backoff_extended_sweep.py:55`、`:112`、`:433`、`:1331`、`:1490` | 29物理点＋2対照、固定 shuffle、較正動作点 | 0除外28点の hash 順・B点・literal共通経路 | **要る** |
| 共通 | 較正定数 | `orchestrator/campaign/p2_2.py:54` | 1M、48、3秒、5 reps | loop CLI への接続 | **要る** |
| 共通 | 統計・束縛 | `docs/phase3-main-experiment.md:258`、`docs/t1998-balanced-stock-inline-preregistration.md:20` | 他実験の先例 | B-5 の score/floor/6比較 consumer | **要る** |

**brief に対する訂正根拠：**

- 「停止は報告で、親が次巡を投げれば続く」は成立しません。`:2559` の入口停止が評価を止めます。
- 同じ値の重複を再計測する契約は、`:1795` の既存結果復元と異なります。
- 28点 sweep の支持集合は1000点ではありません。同じなのは許容される編集面です。
- script 自身の説明は「投入器ではなく job body」です。`tools/pegasus/p3_s4_loop_pegasus.sh:8`。

random の不在は今回の全コード再検索による断定ではなく、指定された前回調査と親の確認を根拠にしています。

## 既知結果台帳

| 材料・path | 既知内容 | 今回の確認範囲 |
|---|---|---|
| `output/insights/2026-09-18/t2746-k2-loop-round2/README.md:40` | 第2巡25 µs、687508.5 tps、Elapse 432秒 | 実走記録を直接読んだ |
| 同 `:56` | 第1巡20 µs、719324.5 tps。時刻・tree・集約が異なる | 第2巡記録から確認。差−4.4%を退行と読まない |
| 同 `:74`、`:78`、`:83` | proposal-3は20 µs、T-2581も既評価。proposal-3自体は未評価 | 記録を直接読んだ。T-2581 raw は未再監査 |
| 同 `materials/knowledge-input.json:4`、`:7`、`:9` | manifest、旧40/30/40のWAL、source commit/path/hash | 射影本文を直接読んだ |
| `docs/paper-story/2026-09-17.md:1748` | fig2cの性能地形、sweet-spot と機序主張の区別 | 指定§7を読んだ。fig2c raw は未再監査 |
| `docs/b10-backoff-static-tail-preregistration.md:52` | 2000/4000/9999 µs の先行探索の開示 | 指定の該当節を読んだ |
| `docs/paper-story/2026-09-17.md:1937` | 右tailの結末、legacy correctness と性能未認証の限定 | §7から確認 |
| `docs/paper-story/2026-09-17.md:1810`、`:1902` | A-2/A-6の正負、別protocol・別attempt | §7とbriefから確認。raw は未再監査 |
| `docs/t1998-balanced-stock-inline-preregistration.md:64` | 登録前の balanced 生値、旧+11.3%は既知 | 文書を直接読んだ |
| `docs/paper-story/2026-09-17.md:1745` | P2-4旧値は旧測定契約の事例 | 現行比較の基礎にしない |
| `output/insights/2026-08-26_b5-llm-necessity-contrast-design.md:145` | 前回 must-fix 11系統 | 設計メモと相談2本を読んだ |

random 分布・格子採用・n は、**これらを知った後の設計判断**です。既存格子が先に存在したことは、今回の対照選択まで結果非依存だったことを意味しません。

## 費用見積り

**31 genome の Elapse は指定された検索範囲では見つかりませんでした。**

| 根拠 | 実測・算術 | 適用限界 |
|---|---:|---|
| `output/insights/2026-09-18/t2746-k2-loop-round2/README.md:40` | 1評価432秒 | 配線規模。較正済み本走へ直接移せない |
| `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md:289` | 8点632/631/629秒 | 拡張31点ではなく別の8点走 |
| 上記8点の単純除算 | 約78.6〜79.0秒/点 | **算術値**。単独jobの評価時間ではない |
| `output/insights/2026-08-26_b5-llm-necessity-contrast-design.md:188` | 旧 verifier 140.66〜433.33秒/件 | 前回設計が引用した実測。今回は原校正ファイルを再監査していない |
| `docs/phase3-main-experiment.md:309` | rr95で433.3秒 | 旧環境・gate構成の値 |

草案の追加測定を含む最大量は次のとおりです。

| 用途 | 数 |
|---|---:|
| 主探索 | 1080評価 |
| 探索の同job stock | 1080 session |
| 独立 endpoint score | 540 session |
| 独立 endpoint floor | 540 session |
| block stock の score/floor | 90 session |
| **合計** | **3330 session** |
| 原提案上限 | 3240件 |
| retry物理試行 | 上記とは別計上、各操作追加2回まで |

- bench設定時間の算術：**13.875時間**。
- 旧 verifier 所要を3330件へ外挿した**推定**：**約130.1〜400.8時間**。
- bench設定時間を足した参考算術：**約144.0〜414.7時間**。build、Tier0、準備、再測等を含む総所要ではありません。
- K2の432秒を機械的に掛けると399.6時間ですが、条件が異なるため予測値には採用しません。
- 草案の総wall上限600時間は**親への管理予算案**です。実測から確定した必要時間ではありません。
- sweep-ceiling は別枠。1回の全格子走なら3 workload×28点＝84候補ですが、独立再計測等は別途必要です。

## 前回 must-fix 11 系統の判定

番号は設計メモ§6に対応します。

| 番号 | 解消・残存 | 理由 | 草案での扱い |
|---:|---|---|---|
| 1 | **一部解消・一部残存** | LLMの任意コードによる空間拡張は literal 制限で消える。一方、sweepの支持は28点 | §1–2で条件付き主張、許容集合と支持の区別。stock/no-op/重複を固定 |
| 2 | **残存** | 共通pipelineという名称だけでは exact correctness を束縛しない。loop呼出しに明示指定がない | §5、§10、§12。発効前に exact argv・経路固定、実装が要る |
| 3 | **設計上解消・実装残存** | A到達と機械欠測を分離すれば arm 依存の系列除外を避けられる | §3、§6–7。A到達はscore化、機械欠測はp=1を置き族維持 |
| 4 | **設計上解消** | anomalyを任意の性能数値へ変換しない | §6。実測stock fallback、正しさ失敗も別報告 |
| 5 | **交絡は残存** | K2・適応・criticを含む比較であり、同じbytesを渡しても情報利用は同じでない | §1、§4。構成比較に限定、既存schema凍結、B-4効果を主張しない |
| 6 | **設計上具体化・実装残存** | stockだけのCVでは対象別floor義務を満たさない | §6–7。stockのフラグ・測定数・共有、独立endpoint floor、CV式を固定 |
| 7 | **設計上解消** | holeとcohortを1個に固定し、欠測比較を族から除かない | §7。族6、p=1、再発火で置換禁止 |
| 8 | **残存を明示** | 文書だけでは実行拒否やconsumer束縛にならない。今回追加gateはscope外 | §0、§10、§12。文書契約と未実装を明記、休眠解除を主張しない |
| 9 | **一部解消** | 現在の具体的既知結果は列挙できた。全raw artifactの再監査は未実施 | §8。直接閲覧と伝聞を分け、発効時の差分台帳を要求 |
| 10 | **設計上解消・実装残存** | 探索の最大値を検定へ再利用しない | §6。endpoint固定後に独立5 session、floorも別標本 |
| 11 | **改訂内容は明確化、承認残存** | A/B分離・時間上限撤去・停止不適用はD39と同値でない | §3、§11–12。本走時の明示認可事項 |

「草案で閉じた」は設計上の曖昧さを閉じたという意味です。実行機構が閉じたという意味ではありません。

## 親の provisional 裁定への応答

| 裁定 | 応答 | 理由 |
|---|---|---|
| P1 | **条件付き賛成** | B=10/A=30、anomaly消費は採る。「D39継承」は訂正。入口停止の対応が必要。総量管理も別途固定する |
| P2 | **条件付き賛成** | 0除外28点とhash順は採る。「支持集合が同一」は「許容集合が共通」へ訂正。commit hashをseedにせず、系列別順序を固定 |
| P3 | **条件付き賛成** | log-uniformを具体的確率質量まで定義する。離散化、counter、符号化、rejection samplingを固定し、既知結果後の選択を開示 |
| P4 | **条件付き賛成** | 共通literal経路は妥当。ただし現CLIでは較正動作点、correctness、停止、重複、stock対が足りず、現状で実走可能とはしない |
| P5 | **条件付き賛成** | 独立5 sessionとstock fallbackを採る。stockは適応backoffと明記し、再検証anomalyと機械欠測を区別する |
| P6 | **条件付き賛成** | 系列・log比・符号反転・Holm6・連言は採る。**stock CVだけのfloorには反対**。対象endpointの独立floorを加える。等価域はlog尺度へ変換し、(c)は操作的同等と限定 |
| P7 | **条件付き賛成** | A到達を除外しない方針に賛成。機械故障の閉じた列挙は候補との独立性を必要条件にし、非ゼロ終了全般を無料retryにしない |
| P8 | **賛成** | 知識付きK2構成という限定を維持。D2155の診断射影を採る一方、実受領・改善効果は未実証と書く。K0は追加しない |
| P9 | **賛成** | 未実装consumerのpinを実在扱いしない。発効前の未確定実値を開示し、測定時点と解析時点の版を区別する |

## ユーザー裁定へ返すべき事項

本走認可時に必要な確認です。**今回の文書作成を止めるための確認ではありません。**

1. **D39の実質改訂**：B=10/A=30、3600秒の系列上限撤去、収束・逆方向枯渇停止の不適用。
2. **凍結した実験構成**：モデル、prompt、K2入力、D2155還流、random分布、28点sweep、n=12。
3. **scoreと失敗処理**：stock適応backoffのfallback、再検証anomaly、機械欠測、重複のfresh評価。
4. **追加費用**：独立endpoint floor、同job stock、最大3330 session。総wall600時間案の採否。
5. **未閉鎖の主張**：(d)クロスプロトコル最良、(e)同一variantの横断退行は今回閉じない。
6. **本走の具体的認可**：必要部品とexact構成が存在するcommitを対象にする。文書作成の認可から推定しない。
7. **D52/D1409との境界**：今回の限定比較を認可しても、headlineの復活や「非列挙」の定義変更にはしない。

実装方式や追加gateの採用案は、本成果物には含めていません。

## 総括

全文草案は作成可能ですが、現行機構だけで本走できる状態ではありません。  
停止・重複・支持集合について、briefの前提を訂正する必要があります。  
既知結果を開示し、(c)成立と判定不能を正当な結末として固定しました。  
費用は百時間級の推定で、較正済み共通経路の実測所要は未取得です。  
ファイル変更、本走、pytestは行っていません。