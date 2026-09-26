# B-5 生成器対照 — 固定 backoff hole で LLM (K2 loop)・ランダム変異・機械 sweep を同一評価数で比べる事前登録

本書は、既に許可された編集面である固定 backoff hole (`silo-backoff-magnitude`) の内で、
知識付き K2 手動 loop (LLM)・ランダム変異・機械 sweep の 3 生成器を、同じ評価数の予算で比べる
規則を、結果を見る前に固定する。

2026-09-19 のユーザー決定は **本書の作成だけ**を認可した。**本走、生成器の実装、追加 gate、
D1409 の「非列挙」条件の変更は認可していない。** 本書が存在することは、測定の認可にならない。

論文素材 §8 の B-5 は「LLM 固有性の条件付き対照」であり、主張の形は D1067 (2026-08-27、ユーザー裁定) で
「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score だった」という条件付き優越へ
狭められている。本書はその形を超えない。設計の一次資料は
`output/insights/2026-08-26_b5-llm-necessity-contrast-design.md` (3 アーム設計メモ、D1012) と
`output/insights/2026-08-26/b5-contrast-review-verbatim/` (前回の草案と敵対相談 2 本)、
本書の起草経緯は `output/insights/2026-09-19/b5-generator-contrast-prereg/` にある。

## 0. 版と発効

**本書は v1 であり、これが初版である。** 改訂履歴はまだ無い。

文書を作った commit と、本走を認可する**発効 commit** を区別する。発効は、ユーザーの本走認可を伴う
日付付き commit と、その認可を記録した決定 (D 番号) による。発効前の本書は未発効の登録であり、
本書だけを根拠に測定を始めてはならない。

**発効後は既存本文の bytes を書き換えない。** 訂正は末尾へ `## N. Erratum` として追記する形でだけ行い、
訂正の理由・日付・適用する cohort・判定への影響を書く。**結果を見た後の判定規則の変更は、有利・不利の
向きを問わず事後改訂である。** 当初の規則で得た結果を本書の結果として報告し、事後改訂の下で得た結果は
別欄に分けて報告する。Erratum を追記すると file 全体の SHA-256 は変わるので、発効時に記録した
測定版の SHA-256 を保存し、追記後の版と cohort の対応を Erratum に書く。

**本書は解析器の pin を持たない。** B-5 専用の解析 consumer は未実装であり、凍結は文書契約に留まる。
文書の存在、hash の記録、docs lint の成功を「機械的強制」と呼ばない。本書自身の hash や本書を含む
commit hash を本文へ埋め込まない (hash の自己参照は禁止)。発効時には本書の raw bytes の SHA-256 を
決定記録へ写し、測定時点の版と後日の解析規則の版を別々に記録する (D1790 の区別を継承する。ただし
対応する解析器が既にあるとは主張しない)。

本書の規則に加え、§12 の「発効束」に列挙した実値 (モデル、prompt、実行経路、correctness の引数など) を
発効前に固定する。これらが未確定の間、本書は発効可能な実験構成ではない。

## 1. 主張の形と、主張しないこと

### 主張しうること

成立時に許す主張は、D1067 の形に限る。

> 固定予算 (評価数 B)・固定編集面 (固定 backoff hole) の下で、事前登録した非 LLM 生成器
> (ランダム変異、機械 sweep) より高い score だった。

比較の対象は「知識射影と critic 還流を含む K2 手動 loop」という**構成**である。LLM 単体、知識入力、
適応 (閉ループ)、critic のそれぞれの寄与は分離しない。workload ごとの成立条件は §7 の連言とする。

### 主張しないこと

- この結果が LLM の**必要性**を示す。「LLM でなければ到達できない」とは書かない。
- 非 LLM 生成器一般より優れる。登録した 2 つの対照に対する結果である。
- 新しい CC 構造を発見した。候補は固定 backoff の初期値 (スカラー) であって CC 構造ではない。
- 他の hole・protocol・環境でも成立する。
- 同じ金銭費用・token 数・生成時間・総 wall time で優れる。予算は評価数であって費用ではない。
- B-4 の還流効果、または K2 の知識利用の因果効果を示した。
- 本書の作成や本走の完了だけで、論文素材 §8 の B-5 が充足した。
- headline の復活。`docs/phase3-main-experiment.md` の「2026-07-10 追記」1 に従い、スカラー 1 個の探索に
  還元できる backoff 軸は headline 候補にしない。本書は D52 の系レベル主張、旧対照 3/4 の休眠を変えない。

**失敗条件 (c) (機械 sweep / ランダム変異で同等に再現) の成立を、正当な結末の 1 つとして最初から認める。**
P2-5 / D21 / D29 は「スカラー空間では LLM は機械探索から分離できない」ことを既に実証しており、本書の
比較でも (c) が出ることは十分ありうる。本書はそれを隠さず、優越が出た場合と同じ強さで報告する。

**D1409 の「非列挙」の条件は変更しない。** D1409 がユーザー裁定へ返した定義は D1441 (2026-09-02) で
「固定予算の下で操作的に列挙し尽くせない」へ改められている。本書はこの定義を変えず、**本書の候補集合
(1000 点、B = 10) がその定義を満たすかどうかの判定も行わない。** 有限の候補集合で固定予算の生成器を比べる
ことと、非列挙のコード片軸が実体化して旧 headline の復活条件 (D52) が満たされたと主張することは別である。
本書の対象は前者だけであり、後者は本書の主張に含めない。候補集合が完全列挙可能であること (§2) は、
D1409 の二重の壁が解けたことを意味しない。

## 2. 編集面と候補集合

編集面は `silo-backoff-magnitude` の既存 hole とする。`patches/silo-backoff-fixed.patch` を当てた後の
`include/backoff.hh` にある合成枝の 1 文だけを置き換える。stock 枝・骨格・marker・他 file は編集しない。

受理する候補集合を **S = {1, 2, …, 1000} (単位 µs、整数)** とする。これは Tier 1 文法
(`orchestrator/campaign/backoff_hole_grammar.py`、D875 / D901) と、`coder.value` の値域 (整数 1..1000)、
および value と literal の帰属整合 (D39 決定 7) を合わせた受理域である。実装は
`double now_backoff = <literal>;` の 1 文で、literal は接尾辞の無い数値、value と数値的に一致する。
bool、0、負数、1000 超は含めない。数値表記は既存規則で正準化する。

**S は 1000 点であり、完全列挙可能である。** 3 arm に同じ文法・値域・帰属整合を適用し、LLM にだけ
S の外を許すことはない。

ただし、**共通なのは受理可能な候補集合であって、各生成器の支持集合は同じではない。** random は S の
全点に正の確率を持つ。sweep は S の内の 28 点の格子に限る。LLM が S の全点へ正の確率で到達することは
証明しない。本書が比べるのは「共通の編集面で、異なる選択方策を持つ、凍結した 3 つの生成器」である。

no-op、stock 枝への切替、空実装は候補にしない。stock は候補集合の外にある共通の対照 (§6 の不採用時の値)
である。同じ値の再提案は許す。重複だからといって再抽選しない。**重複も新しい評価機会を使い、同じ値を
fresh に測る。** 過去の性能値の再利用を新規評価として数えない。

## 3. 予算、停止、失敗の計上

各 arm × workload × 系列の探索予算を次に固定する。

- **評価数 B = 10。**
- **原提案上限 A = 30。**
- 系列ごとの administrative wall-clock 上限は設けない (job ごとの walltime は別に掛かる、§3.3)。
- 性能を理由とする早期停止はしない。certified 候補を得た時点でも、floor 超えが出ても止めない。
- B 完走、または A 到達まで進める。

### 3.1 原提案 (A) と評価 (B)

原提案は、生成器が候補 1 件を提出する機会である。空出力、schema 不合格、値域違反、文法違反も A を
1 消費する。生成器の内部で候補を選び直した結果だけを提出してはならない (提出前の選び直しは、それ自体を
A の消費として記録する)。

文法・帰属整合・diff 検疫・Tier0 (コンパイル + 固定スモーク) を通過した候補を certification pipeline へ
投入した時点で **B を 1 消費**する。**verifier が anomaly を返して reject した候補も B を 1 消費する。**
投入後の候補起因の失敗も、その評価機会を返さない。成功して certified になった候補だけを数える運用は
禁止する (Tier0 不合格と anomaly を無料で捨てられる予算は、正しさゲートの迂回を予算上の利益にする)。

文法・検疫・Tier0 不通過は A を消費し、B は消費しない。Tier0 は文法検査と同義ではない。B-5 共通の
Tier0 契約 (スモークの内容) は §12 の発効束で実値を固定する。現時点で B-5 共通の Tier0 が実在するとは
主張しない。

### 3.2 予算未消化の系列

A 到達時に B 未達でも系列を差し替えない。評価済みの候補から §6 の endpoint と score を求める。その系列は
「原提案予算を使い切った生成器の結果」として残す。B 未達を理由に、その系列だけを統計標本から除かない。
この扱いは arm の不利として残す (判定不能へは倒さない)。

### 3.3 機械故障の retry と、候補起因の失敗

機械故障の retry は、同じ候補・同じ入力・同じ予定位置に限り、元の操作に対して追加 2 回までとする。
機械故障とは次に限る。

- 候補の処理を始める前の中断 (通信障害、job 起動前の拒否)。
- scheduler の記録で裏付けられる node 喪失・preemption。
- 候補と独立な依存物の供給障害・入出力障害。

**候補の実行中に job walltime を超えた打切りは候補起因**とする。certification pipeline へ投入する前
(文法・検疫・Tier0 のコンパイルとスモークの間) の時間切れは Tier0 不通過と同じく **A だけ**を消費し、
投入後 (correctness の build・verify・性能の build・bench) の時間切れは **B を消費**して score なしとする。
walltime は本走前の試走で測った最大所要への倍率で決め、全 arm 同一にする。
anomaly、候補起因のコンパイル失敗、遅い性能、品質判定の赤は機械故障の理由にしない。分類不能な失敗を
無料 retry として扱わない。retry でも同じ論理 A/B slot を使い、物理試行数と費用は全件記録する。
測定結果を得た後に、より良い値を求めて retry しない。機械故障が上限を超えた系列は欠測とし、stock で
置き換えない。

### 3.4 D39 決定 2 との関係

D39 決定 2 から継承するのは「10」という数値だけである。本規則は「10 iteration または 3600 秒」と
同値ではない。A/B の分離、3600 秒上限の撤去、収束・逆方向枯渇による停止の不適用は探索機会を変える
実質改訂であり、「制約方向のみの改訂」とは呼ばない。**本走認可時にこの改訂を明示的に確認する。**

現行 harness の `drive_iteration` は入口で停止判定を実行し、停止済みなら評価せずに返す (単一の
campaign layout で回す場合)。§4.1 の運用契約 (評価ごとに fresh layout) ではこの停止は発火しないが、
その代わり系列内の状態継承を harness が担わない。どちらの形でも、B 完走を機械で保証する部品は無い (§10)。
checkpoint の改変や初期化による迂回は本規則への適合ではない。

## 4. 生成器の操作的定義

### 4.1 LLM: 知識付き K2 手動 loop

planner・coder・critic を親 (人間の session を運ぶ AI) が呼び出す K2 手動 loop とする。harness 自身が
LLM を spawn する構成ではない。coder 契約は `coder-v4-autonomous-k2`、reflux は on、B-4 mode は使わない。

**運用契約 (T-2746 の実運用と同じ形):** 各評価は `p3_s4_loop` の単回評価 (proposal file を渡す) を
fresh layout で 1 回呼び出す。系列内の状態 (whiteboard、直前までの構造化された正しさ・性能結果) は
harness ではなく親の射影で次の planner / coder へ渡す。**評価 k の planner 入力に写す whiteboard は、
その系列の評価 1〜k−1 のちょうど k−1 件**でなければならず、各役割の実入力と出力を全件保存する。
この継承を機械で検査する部品は無い (§10)。

各系列は fresh context で始める。他の系列、他 arm、独立再計測、floor の結果を入力へ戻さない。系列内の
過去評価と、固定した K2 知識だけを使う。**親が性能を見て追加の助言、候補の修正、再抽選をしてはならない。**

知識は T-2746 の `materials/knowledge-input.json` の射影を採る。manifest digest は
`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`、その source は commit
`2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の
`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl`、source の SHA-256 は
`2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611` である。この射影は旧環境の
40 / 30 / 40 µs の結果 (性能、正しさ、leading indicators、旧実行条件を含む WAL の射影) を含む。
**LLM arm は結果既知の知識を持ち、random / sweep は持たない。** この非対称は本書の限界であり、
K0 (知識なし) arm は足さない (scope 外)。

系列の初回の現在性能には、§5.4 の系列開始 stock (同機体・同 job) を用いる。以後は既存の構造化 digest と
役割入力への射影を使う。whiteboard の 5 field と `delta_pct=None` は維持する。生 trace を役割入力として
渡さない。既存の正しさ信号を自由文の独自 schema に置き換えない。

critic 診断は D2155 の明示逐語からの射影を用いる。`k2_critic_diagnosis` の field は `data_boundary`、
`source_sha256`、`attribution`、`recommend`、`avoid`、`uncertainty` の 6 個に限り、同じ診断を次の planner と
coder へ渡す。初回は key を置かない。報告用の agent 出力から自動的に診断を拾う経路にはしない。

モデルの exact ID、推論設定、生成設定、役割本文、prompt、入力 schema、初回入力、欠測時の表現は
§12 の発効束へ実値を固定する。**本書作成時にはこれらの実値は未確定である。** 可変 alias や「既定モデル」の
まま発効させない。入力の保存は、実送達や採用の独立証明ではない。

### 4.2 random: 離散 log-uniform

候補は S 全体から復元抽出する。過去の成功・失敗・anomaly・性能値によって分布を変えない。

log-uniform は次の整数重みで厳密に定める。v = 1..1000 について
`m_v = floor(2^128 × ln((v+1)/v))`、`M = Σ m_v`、`P(v) = m_v / M`。これは連続 log-uniform を整数区間
[v, v+1) に分けた分布の固定精度による離散化であり、整数一様分布ではない。重みは全て正である。
発効前に 1000 個の整数配列とその hash を保存し、床関数の値が確定する精度で算出する (浮動小数点の
実装差に委ねない)。

乱数の preimage は改行の無い ASCII 文字列 `b5-generator-contrast-v1|random|w|r|a|c` とする。w は workload 名
(`write-heavy` / `balanced` / `read-heavy`)、r は系列番号 1..12、a は原提案番号 1..30、c は 0 始まりの counter、
整数は先頭ゼロの無い十進表記。SHA-256 を unsigned big-endian の 256 bit 整数 U と読み、
`L = floor(2^256 / M) × M` として U ≥ L なら c を増やして引き直し、U < L なら `U mod M` を累積重みの区間へ
写して v を得る。この引き直しは乱数の偏りを除く処理であり、原提案の再抽選ではない。候補生成後の重複や
不成績を理由とする再抽選は禁止する。commit hash を seed に使わない (commit の作り直しで順序が変わる)。

**分布の選択は、B-10 の既知の性能地形 (sweet-spot が 0〜10 µs にあること) を見た後の判断である。**
「結果を知らずに選んだ中立な分布」とは書かない。一様分布などを事後に追加し、都合のよい対照だけを
主比較へ採ることはしない。

### 4.3 sweep-matched

格子は `orchestrator/campaign/backoff_extended_sweep.py` の `EXTENDED_SWEEP_US` と S の共通部分とする。
具体的な 28 点は次のとおり (0 は S の外なので除く)。

```
1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50,
75, 100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000
```

各 workload・系列について、各 v の文字列 `b5-generator-contrast-v1|sweep|w|r|v` の SHA-256 の昇順に並べ、
同 hash は v の数値昇順とする。**最初の 10 点を順に評価する。** 候補に依存しない事前不通過 (機械故障) なら
同じ点を retry し、候補起因の不通過なら次点へ進む。格子を使い切ったら候補枯渇と記録し、差し替えない。

軸と格子の由来は既存の backoff 研究であり、新たな軸発見ではない。格子の元定義が K2 の 20 / 25 µs の
結果より前にあることと、**今回の格子採用の判断が既知結果を見た後であること**を分けて記す。既存の
`MEASUREMENT_SEEDS` による順序は本書の hash 順ではない。既存 sweep の template 式経路は評価経路として
使わない (§5.1)。

### 4.4 sweep-ceiling

同じ 28 点の全走は、比較族の外の副次記述として `sweep-ceiling` と呼び分ける。1000 点の完全列挙や
連続空間の真の天井とは呼ばない。その結果を主比較の格子・順序・n・endpoint 選択へ戻さない。本 v1 の
主 cohort の予算に含めず、実走は別途認可とする。未取得なら未取得と記し、過去の B-10 の値を代入しない。

## 5. 共通の評価経路

### 5.1 経路

3 arm とも、同じ hole literal を同じ検疫経路で評価する。目標経路は `p3_s4_loop` の proposal 読込みから
hole 挿入・検疫・`run_campaign` (build × 2 / verify / bench) までである。生成器の由来は記録するが、受理文法と
正しさ基準を変えない。機械生成の候補を LLM が生成したものと偽って記録しない。

### 5.2 動作点

性能 workload は次の 3 つとする。

| workload | rratio | skew | rmw |
|---|---:|---:|---:|
| write-heavy | 5 | 0.9 | 0 |
| balanced | 50 | 0.9 | 0 |
| read-heavy | 95 | 0.9 | 0 |

性能の動作点は records = 1,000,000、threads = 48、extime = 3 秒、reps = 5 (較正済みの値、
`orchestrator/campaign/p2_2.py` の定数) とする。較正を満たす環境で直列に実測し、勝手に records を減らさない
(発火環境の較正がより小さい値を選んだ場合だけ変更する)。

候補の共通 genome は silo、`BACK_OFF=1`、`NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0`。
`BACKOFF_FIXED` と hole literal は候補 v と一致させる。stock は同じ共通フラグで `BACK_OFF=1`、
`BACKOFF_FIXED=-1` とする。**これは適応 backoff の stock であり、`BACK_OFF=0` の無 backoff ではない。**

### 5.3 session の定義

1 session = 既存の bench 経路 1 回。5 rep を測り、rep 内の変動係数が閾値を超えれば静定して測り直す
(最大 3 round)。5 rep の完走と settle の成立を要求し、rep 欠落の median を採らない。3 round で不安定なら
その session は**品質欠測**とする — 機械故障でも候補起因でもない第 3 の分類であり、B も A も返さず、
fallback に置き換えない。1 session の観測値は採用 round の 5 rep の median throughput とする。
物理測定回数は論理 session 数の最大 3 倍まであり、台帳に別記する。現行 loop がこの契約に相当する
flag を渡すかは束縛されていない (§10)。

### 5.4 stock の測定

- **系列開始 stock:** 各系列の最初の評価と同機体・同 job で stock を 1 session 測り、LLM arm の初期
  `current_perf` に渡す (random / sweep にも渡すが、分岐に使わない)。探索 B には含めない。
- **block stock:** workload × block ごとに stock を 5 session 測る。§6 の不採用時の値と §7.2 の CV に使う。
- 探索 job ごとの stock 対測定は行わない。

### 5.5 正しさ

各性能 session の前に、別 build・別 run の correctness を通す。correctness は性能 workload と同じ tuple 数・
thread 数・rratio・skew・rmw を明示し、trace extime = 3 秒とする。残りの引数、seed の扱い、verifier の
mode と版は §12 の発効束で固定する。**legacy の小構成 (tuple = 200 / thread = 4 / rr50) を既定値として黙って
使わない。** この exact な経路が現在の CLI で成立するとは主張しない (§10)。

anomaly が 1 件でもあれば当該候補を即 reject する。拒否候補の bench 値は取得・採用しない。性能値には
trace-disabled build の値だけを用いる。screening の bench-first 経路を用いない。WAL の verify・bench・commit と
候補 source の対応を残し、source・binary・環境・toolchain・引数・文法版の出所を記録する。hash の一致だけで
実翻訳単位の意味一致や compile-out を証明したとしない。certified の射程は観測した point read / write の
trace に限る。

## 6. endpoint と score

探索終了時に、各系列の endpoint を 1 個だけ固定する。対象はその系列内で certified となった候補で、探索時の
session median throughput が最大のもの。同値は v の数値昇順、さらに評価 slot 昇順で決める。同じ v が
複数回出ても探索履歴を削除しない。endpoint の値・source・出所 slot を独立再計測の前に固定し、探索時の
最大値を score へ流用しない。他系列の候補や既知の勝者を補充しない。

**anomaly の波及:** 値 v について workload w で anomaly が 1 件でも観測されたら (探索・再計測のいずれで、
どの順序でも)、v は w の全 arm・全系列で endpoint の資格を失う。先行する certified 記録は歴史事実として
残す (規律 7) が、資格には使わない。既に score が確定した系列に後から発見が及んだ場合は、その系列を
不採用 (下記 fallback) と失敗条件 (a) の記録へ改め、日付付きの「結果の訂正」として報告する (Erratum では
ない)。

endpoint を **N_eval = 5 の fresh session** で再計測する。score はその 5 session の median throughput
(絶対 tps) とする。同じ 5 session から endpoint の CV (§7.2) も求める。各 session 内の 5 rep と系列数 n = 12 を
混同しない。選んだ候補が stock より遅くても、事後に stock へ取り替えない。

探索で certified 候補が 1 個も無ければ「何も採用しない」とし、score は同 workload・同 block の block stock
5 session の median とする (**fallback**)。この 5 件は全 arm の不採用系列に共通に使い、共有を明記する。
anomaly を 0 tps や −100 % へ変換しない。

endpoint の再計測で anomaly が出た場合も、その候補は採用しない。次点への選び直しはせず、fallback と
失敗条件 (a) を記録する。通信障害・欠落・identity 不一致で再計測が成立しない場合は、候補の不採用と区別して
score を欠測とする。品質欠測 (§5.3) も同じ。機械故障による欠測を fallback で埋めない。stock 自身の
正しさまたは測定が成立しなければ、当該比較は判定不能とする。探索・score・block stock の session は互いに
再利用しない。score 確定後に候補選択へ戻らない。

**この score の意味:** 「生成された certified 候補の性能」だけでなく「候補を採用できなければ stock を使う」
という運用の性能である。各 arm の certified endpoint 数 (12 中) を必ず併記する (§7.4)。

## 7. 母集団、反復、floor、判定

### 7.1 母集団と配置

母集団は、凍結した環境・workload・生成器構成での探索系列とする。別モデル・別知識・別 hole・別 protocol へ
一般化しない。主セルは 3 arm × 3 workload の 9 セル、各セル **n = 12 系列**、計 108 系列。3 つの時間分離
block に各 4 系列を割り当てる。

block 間は、前 block の最終測定から次 block の初回測定まで少なくとも 1 時間空け、別プロセス群として
実行する。これは cold-boot や独立性の証明ではない。各 workload の同じ系列番号で 3 arm を対にし、
arm の 6 通りの実行順を 12 組に各 2 回割り当てる。順序、workload 配置、score / stock session の配置を
発効前に保存し、結果を見て変えない。系列間で LLM context と探索状態を引き継がない。random と sweep の
順序は §4 の系列番号から導く。測定プログラムの seed 制御の有無は別に開示し、生成器の seed があることを
bench の乱数の制御とは呼ばない。

### 7.2 floor と等価域

- **stock CV:** workload w ごとに次の 4 つの CV を出し、その**最大値**を `CV_stock(w)` とする。
  (1) block stock 15 session (5 × 3 block) の median の CV、(2)(3)(4) 各 block 内 5 session の median の CV。
  CV は標本標準偏差 (分母 n−1) を算術平均で割った値。
- **等価域:** `f(w) = max(0.03, CV_stock(w))`、対数尺度で `δ(w) = ln(1 + f(w))`。3 % は保守下限であり、
  今回測った noise の値とは呼ばない。異なる endpoint の値を pool して CV を作らない。
- **精度 gate:** endpoint の 5 session の CV が `2 × f(w)` を超えるなら、その endpoint を含む対は
  **精度不足**とする。endpoint CV を等価域には入れない。
- 必要な floor が欠測・非有限なら比較は判定不能とする。floor の大きさを理由に追加測定や都合のよい
  標本除去をしない。

### 7.3 優越の検定

検定単位は探索系列であり、候補 slot や rep ではない。系列 r の対差を `d_r = ln(score_LLM,r / score_b,r)`
(b = random または sweep-matched) とする。統計量は対差の算術平均。符号を全 2^n 通り反転する片側 exact
permutation を行い、観測統計量以上を tail に含める。

**前提 (登録する仮定):** 帰無の下で、対差 d_1 … d_n は**互いに独立で、各々の符号が対称**である。これを
支えるのは、系列が fresh context・別 seed で始まること、対の 3 arm が同じ block で均衡順に走ること、
block が時間分離されていることである。**支えないもの**も明記する — 同じ block 内の対に共通に入る時間ドリフト
(機体の温度・負荷) は対差の相関を生みうる。この検定はその相関が無視できるという仮定の下での exact p であり、
仮定の成立を本書は証明しない。**仮定が崩れた場合の扱い:** 本書は依存を検出する検定を置かず、依存に対する
防壁も持たない。連言の (iii) (3 つの時間分離 block のそれぞれで median(d) > 0) は 3 block での再現を
要求する条件であって、対へ同時に入る共通ショック (全体でも block ごとでも) による偽陽性を排除するものではない
(例: 全対差が同じ確率変数に等しければ、各対差の符号が対称でも誤判定の確率は 1/2 になりうる)。独立性が
崩れた場面の偽陽性率は名目より高い。したがって条件付き優越の主張には**必ず「登録した独立性の仮定の下で」を
添え**、block 別の median(d) と対差の一覧を併記する。仮定の成立を事後に主張したり、崩れを理由に規則を
変えたりしない。

**fallback 対と副解析:** 共有 stock (§6 の fallback) による依存は fallback を含む対にだけ入る。そこで
**副解析 = fallback (どちらか一方でも) を含む対を除いた同じ手続き**を登録し、次のとおり使う。

- 同一比較で fallback 対が **1 以下**なら、主解析 (全 12 対) で (i)〜(iii) を判定し、副解析は併記する。
- fallback 対が **2 以上**なら、主解析は記述として併記し、**副解析を判定に使う**。副解析では Holm へ入れる p、
  median(d)、block 別 median(d) の**すべて**を残った対だけから計算する。残った対が **6 未満**、または
  いずれかの block で **1 未満**なら、その比較は**対不足で判定不能**とする。
- 「主解析と副解析の向きが違う」ことを判定に使わない (どちらを使うかは上の規則で一意に決まる)。
- 副解析で判定した比較の結論は、**「候補を採用できた系列の対に限った」条件付き優越 / 同等**として書き、
  除いた対の数と除いた側の arm を必ず添える。fallback 込みの運用 score (§6) に基づく主解析の値は記述として併記し、
  両者を混ぜない。

比較族は 3 workload × 2 baseline の **6 個**に固定し、Holm 法、family-wise α = 0.05 とする。判定不能・規約不適合の
比較も族から除かず、計算上 p = 1 とする (これは観測された検定結果ではなく判定不能の処理である)。

workload ごとの**条件付き優越**は、2 baseline のそれぞれについて、(i) Holm 補正後に有意、(ii) median(d) > δ、
(iii) 各 block の median(d) > 0、を満たす連言とする (判定に使う解析は上の規則で決めたもの)。片方への勝利
だけでは workload の主張を成立させない。3 workload 全体での成立を述べるには 6 比較すべてを満たすことを要する。

### 7.4 判定順と結末の集合

比較 (workload w、baseline b) ごとに、次の順で判定し、**先に該当した結末で止める**。判定に使う解析
(主 / 副) は §7.3 の規則で先に決める。

1. **規約不適合** — 配置逸脱、発効束との不一致 → 当該比較は無効 (報告はする)。
2. **判定不能 (欠測・不成立)** — 12 系列のいずれかが機械故障・品質欠測、stock の測定または正しさが不成立、
   floor が欠測・非有限。
3. **生成不成立** — LLM と b の certified endpoint 数 (12 中) を数え、**両方が 6 未満**なら「双方生成不成立」、
   **片方だけが 6 未満**なら「(その arm の) 生成不成立」。いずれも優越・同等の判定は行わず、記述統計
   (両 arm の score、fallback 数、主・副解析の値) だけを報告する。
4. **判定不能 (対不足・精度不足)** — 判定に使う解析の対が 6 未満または block に 1 未満、または判定に使う対に
   精度不足の endpoint が含まれる。
5. **条件付き優越** — §7.3 の連言 (i)〜(iii)。
6. **同等 = 失敗条件 (c) の成立** — 判定に使う対で `|median(d)| ≤ δ`。「観測差が比較 floor 内だった」という
   判定であり、母集団の等価性を区間で証明したとは書かない。優越性検定が非有意だったことをその根拠にしない。
7. **逆向きの記述的差** — b が LLM を `median(d) < −δ` で上回る。有意な逆向き優越とは書かない (検定は片側)。
8. **判定不能 (残り)** — LLM 側の差が δ 超でも補正後有意または block 再現を欠く場合。優越・同等の結論を出さない。

どちらか一方の非 LLM 対照が (c) を満たせば、その workload の LLM 固有の利得は示せなかったと記す。

全 12 対を使う場合の最小片側 p は 1/4096 で、Holm の初段の閾値 0.05/6 を下回る。副解析で対が n 個に減れば
最小 p は 1/2^n に落ちる (6 対なら 1/64 ≈ 0.0156)。Holm は段階的 (閾値は小さい p から順に 0.05/6、0.05/5、…、
0.05/1) なので、その比較が有意になるかどうかは族内の他の比較の p にも依存する。これは p 値解像度の根拠であって
80 % 検出力の保証ではない。差の絶対値が等しい例では、正が 11/12 なら p = 13/4096、10/12 なら p = 79/4096 となり、
後者は初段の閾値を通らない。実際の検出力は未知の効果と分散に依存する。結果を見て n を増減しない。

全 9 セル、全 6 比較、全未完走、anomaly、fallback、欠測、floor、raw p、補正 p、block 別の効果、各 arm の
certified endpoint 数を報告する。本 v1 の主 cohort は 1 回だけとする。失敗後の再発火を独立の成功機会として
隠さない。後続 cohort は別の位置づけと登録を要し、初回の結果を置き換えない。

## 8. 既知結果台帳と HARKing 境界

**本書は backoff 研究の結果を見る前に作られた登録ではない。** 前向きに固定するのは、将来の新 cohort の
生成・測定・判定規則である。設計選択と、その時点で見えていた既知結果の対応は次のとおり。

| 設計選択 | 見ていた既知結果 |
|---|---|
| random の分布を log-uniform にした | B-10 拡張格子の性能地形 (sweet-spot が 0〜10 µs)、右 tail の結果 |
| sweep 格子を `EXTENDED_SWEEP_US` ∩ S (0 除外) にした | 同上。格子自体は B-10 で先に凍結されていたが、採用の判断は結果を見た後 |
| B = 10、A = 30、n = 12 | D39 決定 2 の予算、P2-5 の系列数、前回設計の費用見積り |
| 等価域を stock CV と 3 % の大きい方にした | 旧環境の between-run floor 3.0 %、S-1 の floor campaign、official 床値案 |
| K2 knowledge を凍結射影で使う | K2 1・2 巡の結果、knowledge manifest の 40 / 30 / 40 µs |

既知の材料の所在と扱い:

| 既知材料 | 内容と本書での扱い |
|---|---|
| B-10 拡張格子 (fig2c) | 0〜1000 µs の性能地形を既知とする。主標本へ転用しない |
| B-10 右 tail | 1000 µs 超〜9999 µs の既知結果。S の拡張根拠にしない |
| K2 第 1 巡 | 20 µs、719324.5 tps。配線規模の過去観測 |
| K2 第 2 巡 (T-2746) | 25 µs、687508.5 tps。第 1 巡との非同時刻比較であり退行とも改善とも読まない |
| T-2581 | 20 µs が既評価値であること |
| K2 の proposal-3 | 20 µs の再提案 (T-2746 では未評価) |
| K2 knowledge | 旧環境の 40 / 30 / 40 µs (491796.5 / 525721.5 / 487088.5 tps) と WAL の射影 |
| A-2 / A-6 | fixed 5 µs の正負を含む、別 protocol の既知結果 |
| T-1998 | balanced の別登録による対測定。B-5 の標本ではない |
| P2-4 | 旧測定契約の利得 (+38 % / +11 %)。現行の比較の基礎にしない |
| P2-5、D52、前回設計 | スカラー探索での非分離、前回設計の欠陥 (§5 の三すくみ) |

主な所在: `output/insights/2026-09-18/t2746-k2-loop-round2/README.md` と同 `materials/knowledge-input.json`、
`output/insights/2026-08-26_b5-llm-necessity-contrast-design.md`、`output/insights/2026-08-26/b5-contrast-review-verbatim/`、
`docs/b10-backoff-static-tail-preregistration.md` の開示節、`docs/t1998-balanced-stock-inline-preregistration.md`、
`docs/paper-story/2026-09-17.md` の過大主張チェックリスト。

一次成果物を直接読んだ項と、brief・既存記録から知った項を区別する。T-2581、A-2 / A-6、fig2c の raw 値は
本書の起草で再監査していない。発効時は exact な artifact と閲覧者・閲覧時点を台帳へ追記し、その間に得た
追加の知見も差分台帳へ残す。既知候補と同じ値が fresh に生成されることは許す。過去の性能観測・certification・
floor を新 cohort へ移植しない。「random / sweep は open-loop」は実行中の性質であり、分布・格子を選んだ
設計者は既知結果を見ている。

## 9. 失敗条件 (a)〜(e) の本書版

- **(a)** anomaly が出た候補は即 reject し、探索 B を消費し、採用候補から外す。後段の anomaly は §6 に従い
  endpoint の不採用として残す。正しさの失敗を性能観測に変換しない。
- **(b)** 比較差が等価域以下なら、有意性だけで優越と書かない。stock に対する利得と、生成器間の利得を区別する。
  独立 floor が無ければ判定不能とする。
- **(c)** 同じ評価予算の random または sweep-matched が §7 の等価域内で再現すれば成立とする。成立を失敗した
  実験として隠さず、正当な negative の結末として報告する。sweep-ceiling だけで再現した場合は、予算が異なる
  副次記述に留める。
- **(d)** クロスプロトコル stock 最良への優越は本書では測らない。したがって本書から (d) の不成立を主張できない。
  silo 内の生成器比較の成立を、ベース protocol 選定の妥当性へ広げない。
- **(e)** workload ごとに別々に探索した endpoint の結果を、同一 variant の workload 横断再現と呼ばない。同一
  endpoint の他 workload 再計測は本 v1 の主予算に含まれない。したがって workload 特化と退行の不在は示せない。
  全 workload の生成器比較結果は必ず併記し、横断評価で floor 超の退行が既知ならそれも併記する。本書だけで
  B-7 や (e) の確認が閉じたとは書かない。

## 10. 既存機構での実行可能性の照合

2026-09-19 時点の repo (local main `a99425b66`) で、親と段 2・段 3 の子が実コードを読んで照合した結果である。
「実在」は部品の存在であって、B-5 の契約に接続済みという意味ではない。

| arm / 共通部 | 既存機構 (所在) | 実在する部分 | 欠ける部分 | 判定 |
|---|---|---|---|---|
| 共通: 文法・値域 | `orchestrator/campaign/backoff_hole_grammar.py` (Tier 1 文法、`validate_backoff_value`) | 1 文、正準化、整数 1..1000 | — | 実装不要 |
| 共通: 帰属整合 | `orchestrator/campaign/p3_s4_loop.py` (value == literal の検査) | 数値一致の強制 | — | 実装不要 |
| LLM: 入口 | `p3_s4_loop` の proposal 読込み (`--run-iteration`)、`--coder-role coder-v4-autonomous-k2`、`--knowledge-manifest`、`tools/pegasus/p3_s4_loop_pegasus.sh` (job body) | 単回評価、K2 manifest の束縛、検疫、digest | exact model / prompt の発効束、系列状態 (whiteboard k−1 件) の継承検査、系列開始 stock → planner 入力の順序 | **実装が要る** (状態継承の検査と初回 stock の順序)。model / prompt は文書固定 |
| LLM: critic 診断 | `p3_s4_loop` の `k2_critic_diagnosis` (D2155) | exact 6 field、planner / coder への同一射影 | 実送達・改善効果の証明 | 射影は実在。効果は未取得 |
| 共通: 性能構成 | `p3_s4_loop.default_perf()` = records 100k / threads 4 / extime 1 / reps 2 (配線規模)。CLI に上書き口なし。identity にも配線規模が入る | 配線規模の評価 | 較正済み動作点 (1M / 48 / 3 s / 5 reps、`p2_2.py`) と 3 workload での運用 | **実装が要る** |
| 共通: session 契約 | `orchestrator/campaign/pipeline.py` の bench (5 rep、CV 閾値超で静定再測、最大 3 round、`require_all_reps` 等の flag) | 品質再測定と rep 完走要求の部品 | loop からの flag 束縛、品質欠測の分類と台帳 | **実装が要る** |
| 共通: 停止・予算 | `p3_s4_loop.drive_iteration` (入口で停止判定)、D39 決定 2 の予算 | 単一 layout での停止判定 | B / A の分離台帳、収束停止の不適用、fresh layout 運用での B 完走の検査 | **実装が要る** (運用だけでは不足) |
| 共通: 重複 | `p3_s4_loop` の `_resolve_duplicate` (単一 layout で terminal 結果を WAL から復元) | 復元 | 重複も fresh に 1 評価する契約 (fresh layout 運用では発火しないが、機械の保証は無い) | **実装が要る** |
| 共通: correctness | `pipeline.evaluate` (既定 correctness は tuple 200 / thread 4 / rr50 / rmw の小構成)、`performance_correctness_workload()` は実在するが loop から未接続 | 部品 | exact correctness 引数の指定・記録、共通 Tier0 | **実装が要る / 未成立** |
| LLM・共通: 計算ノード job | `tools/pegasus/p3_s4_loop_pegasus.sh` | 保存済み proposal 1 件の呼出し | 同 job の系列開始 stock、B-5 の schedule | **実装が要る** |
| random | 不在 (2026-08-26 の意味検索と親の確認。`search_baselines.py` の random 順 replay は別物) | 受理文法と単回評価の部品 | 凍結分布・seed から literal proposal を作る生成器 | **実装が要る** |
| sweep-matched | `backoff_extended_sweep.py` (`EXTENDED_SWEEP_US` 29 点、`MEASUREMENT_SEEDS` の固定順、較正動作点、`run_campaign` 経由、run_kind に B 点 mode なし) | 格子の元定義、較正動作点の全走 driver | 0 除外 28 点の hash 順・B 点・literal 共通経路への接続 | **実装が要る** |
| stock | `BACKOFF_FIXED=-1` の既存構成 | genome | 系列開始 stock と block stock の配置 | **実装が要る** |
| 解析 | 他実験の統計・束縛の先例 (S-1、T-1998、B-10 待ち方) | 先例 | 本書を消費する B-5 解析 consumer (score / floor / 6 比較 / 判定順) | **実装が要る** |

**本 docs-only の変更単位では、これらを実装しない。** 実装の認可は本書の作成の認可に含まれない。

## 11. 費用の見積り

論理 session 数 (retry・品質再測定の物理回数を除く):

| 用途 | 数 |
|---|---:|
| 主探索 (108 系列 × B = 10) | 1080 |
| 系列開始 stock (108 系列 × 1) | 108 |
| endpoint の再計測 (108 × N_eval = 5) | 540 |
| block stock (5 × 3 block × 3 workload) | 45 |
| **合計** | **1773** |
| 原提案上限 (108 × 30) | 3240 件 |

物理測定は品質再測定で最大 3 倍、retry で各操作 +2 回まで増えうる (別計上)。

根拠と限界:

- bench の設定時間だけなら `1773 × 5 rep × 3 秒 ≈ 7.4 時間`。これは算術であり実 wall の予測ではない
  (build・DB 準備・verify・settle・再測・LLM・queue 待ちを含まない)。
- T-2746 の配線規模の単回評価は job Elapse 432 秒だった。較正動作点の 1 評価時間はこれから導けない。
- B-10 拡張格子の 1 workload 31 genome の Elapse は、起草時の資料検索では見つからなかった。8 点の別 sweep
  (`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/`) に 629〜632 秒の完走記録があり単純除算で
  約 79 秒 / 点だが、共有 build を含む別経路の平均であり、本 hole の 1 評価時間として固定しない。
- 前回設計が引用した旧環境の verifier 所要は 3 秒 trace 1 件あたり 140.66〜433.33 秒。1773 件へ外挿すると
  verifier だけで約 69〜213 時間 (推定。旧環境・異なる候補からの外挿であり今回の実測ではない)。

**費用計画は百時間級と扱い、数時間で完走できるとは書かない。** 本走前に、較正動作点・exact correctness 経路で
所要を試走で確認する。その試走の結果は主標本へ入れず、閲覧を既知結果台帳へ残す。試走と実装の認可は本書の
作成の認可に含まれない。「総実行 wall」の管理上限は本走認可時に、試走の実測所要への倍率で決める (本書では
固定しない)。計上対象は Tier0・stock・verify・bench・失敗・retry・再測の全実行時間 (job Elapse の総和)。
queue 待ち、親の待機、LLM の時間・費用は別欄に記録する。上限不足が判明しても、観測値を理由に n や正しさ
条件を下げず、未完走の比較を対称に判定不能として終了する。n = 9 (3 block × 3 系列) などの縮小案は本 v1 に
無い。採るなら主 cohort の結果を見る前に別仕様として固定する。

## 12. 発効束、凍結、本書が閉じないもの

発効前に、次の実値と本書の契約を 1 つの対象 cohort へ結び付ける。

- 本走認可の日付、決定 (D) 番号、承認対象の commit。
- 本書の raw bytes の SHA-256 と、その保存先。
- repository、CCBench、文法、環境 (較正 record)、toolchain の版。
- 実行 script、生成器、解析規則の bytes と hash。
- LLM のモデル exact ID と推論・生成設定、全役割の prompt、知識射影、入力 schema、初回入力、欠測時の表現。
- random の整数重み表とその hash、seed preimage、sweep の系列別全順序。
- 108 系列の schedule (block、arm 順、系列番号)、各評価・score・stock session の識別子。
- correctness / Tier0 / bench の exact 引数と失敗時処理、job walltime とその根拠 (試走の最大所要 × 倍率)。
- D39 決定 2 の予算・停止改訂 (§3.4) と、総実行 wall 上限への明示承認。
- 既知結果台帳の差分と、§10 の欠ける部品を満たす実装の所在 (commit)。

この一覧は機械 gate の新設指示ではない。現在ある検査と、文書上の確認と、未実装を区別する。**本 v1 の
変更面は本書と `docs/README.md` の 1 bullet だけである。**

本走認可時にユーザーへ確認する事項 (本書の作成を止める事項ではない):

1. D39 決定 2 の実質改訂 — B = 10 / A = 30、3600 秒の系列上限の撤去、収束・逆方向枯渇停止の不適用。
2. 凍結する実験構成 — モデル、prompt、K2 知識射影、D2155 の還流、random 分布、28 点 sweep、n = 12。
3. score と失敗処理 — 適応 backoff stock への fallback、再計測 anomaly、機械欠測、品質欠測、重複の fresh 評価。
4. 費用 — 1773 論理 session、試走で決める総実行 wall 上限の受容。縮小案があればその最終仕様 (結果を見る前)。
5. 未閉鎖の主張 — (d) クロスプロトコル最良、(e) 同一 variant の横断退行は本書で閉じない。
6. 本走の具体的認可 — §10 の部品と exact 構成が存在する commit を対象にする。文書作成の認可から推定しない。
7. D52 / D1409 との境界 — 本比較を認可しても headline の復活や「非列挙」の定義変更にしない。

本書は、ユーザーの本走認可、実装の存在、実送達、cold-boot、無人実行、一般的な安全性を代行しない。
D1409 の二重の壁、旧 headline の休眠、B-4 の因果分離を閉じない。クロスプロトコル最良比較と同一 variant の
横断退行検査も閉じない。既存の結果、certified 選択、材料レポートの値、試行台帳は変更しない。

## 13. 過大主張チェックリストとの整合

`docs/paper-story/2026-09-17.md` の「過大主張チェックリスト」の既存項目 (certified の保証範囲、backoff の機序を
帯の外へ広げない、無 backoff 対照と stock を混同しない、K2 の巡を一般化しない、「非列挙」の壁を解決済みと
書かない、成果物を「新しい CC」と書かない、など) に加え、本書の結果を書くときは次を守る。

- B-5 の主張は、登録した 2 対照に対する固定予算下の条件付き優越に限る。「必要性」「発見」を書かない。
- backoff が完全列挙可能なスカラー軸であること、その上での比較であることを併記する。
- 共通の受理候補集合と、生成器ごとの支持集合・情報利用の違いを分けて書く。
- 比較対象が「知識射影と critic 還流を含む K2 loop の構成」であることを落とさない。
- certified の射程と、要求構成・実 build の同一性の限界 (`src_token` の限定) を添える。
- trace-disabled の性能と、別走の correctness の証拠を混同しない。
- 適応 backoff の stock と、無 backoff 対照 (`BACK_OFF=0`) を混同しない。
- 3 % の保守下限、今回測った stock CV、他実験の floor を別々に記す。
- 非有意、等価域内の操作的同等、欠測・精度不足による判定不能、生成不成立を分ける。
- 全 workload、anomaly、fallback、未完走、certified endpoint 数を数値主張に添える。
- 過去の結果 (K2 の 20 / 25 µs、B-10、A-2 / A-6) を新 cohort の標本や予測的再現へ昇格させない。
- 配線・文書・hash・lint の成功を、測定結果や機械的強制と呼ばない。
- 本書や本走の完了を、headline・B-4・B-7・B-10 の充足と呼ばない。
- fallback を含む score の意味 (§6) を結論の文まで通す。「双方が不採用だった」を「同等に再現した」と書かない。
- 副解析で判定した比較は「候補を採用できた系列の対に限った」結論として書き、除いた対の数を添える (§7.3)。
- 条件付き優越には「登録した独立性の仮定の下で」を添える (§7.3)。

## 14. 本書が閉じないもの (まとめ)

- 本走の認可と実施。§10 の実装。§11 の試走。
- D1409 の「非列挙」の定義。D52 の休眠。旧 headline。
- LLM 単体・知識・適応・critic の寄与の分離 (K0 arm は無い)。
- クロスプロトコル最良 (d)、同一 variant の横断退行 (e)、B-7。
- 統計の前提 (対差の独立性と符号対称性、時間ドリフト、系列相関) の成立の証明と、崩れの検出。本書は前提を
  明示し、崩れうることと、その場合に主張へ添える限定 (§7.3) を固定するだけである。

## 15. Erratum — v1 cohort を block 1 stage 1 で閉じ、判定不能と既知結果の閲覧を開示する (2026-09-26)

**種類:** 本書の判定規則の変更ではない。cohort `b5-registered-v1` の実行を打ち切った事実と、その帰結・閲覧の開示である。§0 に従い、既存本文の bytes は変えずに追記した。
**適用する cohort:** `b5-registered-v1` (D2227 項 2 で発効)。測定時点の本書の raw bytes の SHA-256 は発効束が記録した
`66cc3911e0e4026de7ff6d33d419c362d40130944ec1f30be1ec2f2ac9afd669` であり、v1 cohort の実行はすべてこの版の下で行われた。本節の追記後の版は v1 cohort のどの測定にも使っていない。
**決定:** D2249 項 1 (ユーザー裁定、2026-09-26) により v1 を閉じ、write-heavy・balanced の 2 workload の v2 として登録し直す (`docs/b5-generator-contrast-preregistration-v2.md`)。

**実行した範囲:** block 1 stage 1 の 12 job だけ (2026-09-23 21:53 JST 投入、job Elapse の和 126,426 s = 35.1 node 時間)。残り 8 stage は投入していない。v1 を再開しない。

**判定 (§7.4 の手順 2 で止まる):** 6 比較すべてが**判定不能 (欠測)**。生成器の比較の結果ではない。優越・同等・逆向きのいずれも主張しない。
- LLM の 4 系列 (3 workload) は、親 session が 2026-09-23 23:50〜23:52 JST に利用の週上限 (429) で止まり、series job が提案を 2,700 s 待って `proposal-wait-timeout` で終わった。
  score が無いので分類不能欠測である (failures F1050)。本書 §3.3 は 429 を機械故障として retry する経路を持たず、実装にも無かった。
- write-heavy の random 2 系列は、系列開始 stock の品質欠測 (静定待ちの時間切れ、`stock-unestablished`) で終わった。§5.3 は品質欠測を retry しないので、
  write-heavy の LLM 対 random は LLM 系列を再開しても判定不能のままである。
- write-heavy の LLM 系列は 14 機会のうち採用 1 (評価 1 回)、coder の検疫による却下 11、planner の出力書式 (JSON をコードフェンスで囲んだ) による却下 1、429 による時間切れ 1 だった。
  検疫の却下 11 件はすべて、評価 1 の critic 診断の `recommend` に「次の critic 評価への指示」と名乗る採否の読み方の記述があり、coder がそれを指示めいた内容として申告したことによる。
  評価 2 が起きないため同じ診断が 11 回入力された。検疫は設計どおり働いた。v2 はこれを受けて critic への入力を改めた (v2 §4.1)。

**既知結果の閲覧 (§8 の差分台帳):** v1 の結果は v2 の主標本に入れない。v2 の設計選択は次の閲覧の後に行った。
- 本走 wave (dev-wave `t2797-b5-main-run`、2026-09-23〜24): 実行者として全 12 系列の台帳・LLM 親の入出力を見た。
- 費用見直し wave (2026-09-26 14:07 JST 前後、Claude): 全 12 系列の台帳 event の所要・品質・終了理由と候補値 (探索中の v と endpoint の v) を集計で見た。
  throughput は balanced の LLM 系列の評価 1 件を 1 回見た (`output/insights/2026-09-26/t2797-b5-cost-options/README.md` §8)。
- v2 準備 wave (dev-wave `t2797-b5-v2-prep`、2026-09-26 22:03〜22:45 JST の間、Claude): write-heavy の LLM 系列の critic 診断 1 件 (系列開始 stock と値 80 の throughput・その比を含む)、
  critic への入力 (値 80 の fitness_tps と abort_rate を含む)、planner・coder の出力 13 件 (提案値を含む)、台帳の却下 event を読んだ。balanced・read-heavy の LLM 系列の critic 診断は
  「指示」の語を含む行だけを見た。score の集計、系列間・arm 間の比較はしていない。
- v2 の規模 (2 workload・n = 12) は所要時間と費用から決めた (D2249 項 1)。所要は候補値と相関する (backoff の小さい候補ほど検証が長い) ので、結果から完全に独立だとは言わない。

**判定への影響:** v1 の 6 比較は判定不能で確定し、後の cohort の結果で置き換えない (§7.4)。v2 は v1 の失敗後の再発火であり、独立の成功機会として隠さない。
