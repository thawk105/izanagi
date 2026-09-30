# 勝負する条件の候補と SOTA 集合・余地の定義の事前登録 (md_23)

- 登録: 2026-09-30 JST、本 wave の性能測定 (smoke を含む) を 1 本も投入する前。登録者: md_23 wave の親 (manager)。
- この file は commit 後に内容を変えない。変更は末尾の「改訂」節に追記し、理由と時刻 (date / mtime で採る) を残す。
- 根拠に使った既存記録 (すべて本 wave の前に main にあるもの):
  - 文献カード `output/insights/2026-09-29/gen-opt-literature-cards/cards.json` (md_2、295 枚 / 49 本) の `workloads_effective`。
  - CCBench の既存測定: Silo の静的 backoff (Pegasus、skew 0.9・48 thread・write-heavy で素 2.29M → 固定 10 µs 3.91M tps、abort 率 79.9% → 38.9%、
    `output/insights/2026-09-02_backoff-thread-scaling.md`)、認定較正の silo / mocc / tictoc (skew 0.9・48 thread、
    `output/env/pegasus/calibration/registered/`)、Cicada の最良設定 (`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md`)。
  - 既存記録に無いもの: theta 0.99 の多プロトコル並置、TPC-C の多プロトコル tps、長い取引の混在の多プロトコル並置 (本 wave の探索子の報告、確かめた範囲)。

## 1. 条件の候補 (5 個) と SOTA 集合

「既存の最良手法でも大きな無駄が残る」と見込む根拠は、文献がその条件で基準手法に対し大きな倍率を報告していること
(= 基準手法に大きな無駄があった) と、CCBench の既存記録の abort 率である。**倍率は各原典の基盤・thread 数での値で、CCBench の値ではない。**

| ID | 条件 | 見込みの根拠 (カードの記載、原典の図表) | SOTA 集合: CCBench にあるもの | SOTA 集合: 文献の手法 (CCBench に無い) |
|---|---|---|---|---|
| R1 | YCSB 高競合の hotspot: zipf 0.99、read 50%、10 op/txn、rmw なし、1M tuple、48 thread | Plor: YCSB-A θ0.99 で 2PL 系より 25〜42% (Plor カード)。Bamboo: 単一 hotspot で Wound-Wait 比最大 19 倍 (Releasing Locks カード)。MOCC: 高 conflict YCSB で OCC を大きく上回る。izanagi の記録: skew 0.9 でも Silo の abort 率 80% | Silo (BACK_OFF 0/1、静的 backoff 固定 5・10・25 µs)、TicToc、MOCC、Cicada、ERMIA (各 BACK_OFF 0/1)。SI は直列化可能でないので参考値 | Plor、Bamboo、Polaris、BCC、Brook-2PL、TsDefer (Transaction Scheduling: From Conflicts to Runtime Conflicts)、Ding 2018 (batching + reordering)、SGT、Polyjuice |
| R2 | TPC-C の少 warehouse: 1 warehouse、48 thread、既定の取引比 | IC3: 1 warehouse・64 thread で 434K、2PL・OCC は 50K 未満 (IC3 カード)。DRP: 1 warehouse で OCC の 6.6 倍。Transaction Healing: 少 warehouse で validation 無効 OCC の上限に近い。Brook-2PL・Orthrus も同系 | Silo (BACK_OFF 0/1、静的 backoff 固定 5・10・25 µs)、TicToc、MOCC、Cicada、ERMIA、SS2PL、MVTO、Oze (各 BACK_OFF 0/1)。SI は参考値 | IC3、DRP、Transaction Healing、Polyjuice、Tebaldi、CormCC、Bamboo、Brook-2PL、STOv2 (commit-time updates)、Orthrus |
| R3 | 長い取引と短い取引の混在: CCBench の BoMB (長い更新取引 L1 と短い取引の混合) | Oze: BoMB で Oze だけが L1 を commit させつつ短い取引の throughput を保つ (Oze カード)。Shirakami: 短い取引多数 + 長い RW 取引少数で S-OCC 単独に対し改善。ERMIA: Silo で read-mostly 取引が飢える | BoMB を持つ全プロトコル: Silo、TicToc、MOCC、Cicada、ERMIA、SS2PL、MVTO、Oze (各 BACK_OFF 0/1)。SI は参考値 | Shirakami (S-LTX)、vDriver (長い取引の版管理)、ESSN、Hybrid GC (HANA) |
| R4 | YCSB 読み主体の高 skew: zipf 0.99、read 95%、10 op/txn、1M tuple、48 thread | Cicada: read-intensive θ0.99 で高 throughput (Cicada カード)。izanagi の記録: read-heavy (skew 0.9) では静的 backoff が全点で素の Silo に負け、Silo は 10M tps 級 | R1 と同じ | Cicada 系の最適化 |
| R5 | YCSB の大きい取引・中競合: zipf 0.8、read 50%、32 op/txn、1M tuple、48 thread | Rethinking serializable MVCC: 2RMW-8R θ0.9 で SI・Hekaton を大きく上回る。取引が長いほど validation 失敗の損が大きい | R1 と同じ | 同上 + Rebirth-Retire |

- 静的 backoff の固定値 (5・10・25 µs) は izanagi の B-10 系列の genome (`orchestrator/campaign/b10_backoff_shape_sweep.py` の固定形の genome) を使う。
  指定の値の genome が無い場合は、最も近い固定形の値を使い、使った値を記録する (結果を見てから選ばない)。
- ERMIA は SSN で直列化可能を保つ設定として扱う。SI は直列化可能でないので「最良」の選定から外し、参考値としてだけ表に載せる。
- MOCC は pin C で read-heavy の G2 が記録されている (D2261)。R4 の MOCC の値は、同じ条件で直列化可能であることが確かめられていない旨を付けて載せる。
  他の条件でも、本 wave は trace 付きの検査を回さない (stock プロトコルの性能の並置であり、試作は作らない。§3)。

## 2. 測定する条件の選び方 (結果を見る前に固定)

- 測る条件: **R1、R2、R3** (上位 3)。順位の理由: 文献の倍率が大きい (R2 の IC3・DRP は 6〜8 倍級、R1 の Bamboo は最大 19 倍、R3 は Oze が「他は L1 を commit できない」)、
  かつ CCBench の既存 workload でそのまま作れる。R4 は既存記録で Silo が 10M tps 級・静的 backoff が負ける (余地が小さい見込み)、R5 は文献の根拠が 1 本だけ。
- R3 は smoke で「L1 と短い取引の commit 数を取引の種類ごとに取り出せる」ことを確かめられた場合だけ本測定する。取り出せなければ R3 は「未測定 (理由)」とし、
  **R4・R5 で置き換えない** (結果を見て条件を差し替えない)。
- thread 数は 48 (Pegasus の論理コア数、HT 無効)。実行時間 extime 3 秒、反復 3 回。値は反復の中央値。

## 3. SOTA 集合のうち何を測るか

- 測る: 上の「CCBench にあるもの」の全構成 (BACK_OFF 0/1 の両方と、Silo の静的 backoff 3 値)。「最良に調整した値」= 各プロトコルの構成の中で中央値が最大のもの。
  BACK_OFF 0/1 で binary が同一になるプロトコル (その define を読まないもの) は 1 構成として数える (binary の sha256 で判定)。
- 測らない: 文献の手法の試作。理由: (1) 余地は「上限の目安との差」で判定でき、試作は SOTA 側 (比べる相手) であって新しさに寄与しない、
  (2) 試作ごとに trace 付き build と検査器の往復が要り (規律 2)、本 wave の計算予算 (2 node 時間未満) と時間に合わない。
  文献の手法は、原典の倍率 (原典の基盤での値) を「その条件で既に取られている余地」の目安として判定に使う。
- build は trace 無効・計器無効 (`CCBENCH_TRACE=0`、`CCBENCH_ADD_ANALYSIS=0`、Release、sanitizer なし)。compile の命令の -D 値を build 後に照合する。

## 4. 上限の目安と余地の定義

条件ごとに次を出す。

- **最良 (S)**: 目標の条件での、SOTA 集合 (CCBench、SI を除く) の最良構成の中央値 throughput。
- **B1 (競合なしの目安)**:
  - R1: 同じ op 構成で zipf 0 (一様) にした YCSB での、各プロトコル既定構成 (BACK_OFF=1) の中央値の最大。
  - R2: warehouse 数を 48 (= thread 数) にした TPC-C での、各プロトコル既定構成の中央値の最大 (**データが大きくなる効果を含む緩い目安**)。
  - R3: 長い取引の thread を 0 にした BoMB (短い取引だけ、同じ短い取引の thread 数) の短い取引の throughput の最大。あわせて、短い取引の thread を 0 にした L1 単独の commit 率。
- **B2 (abort に消えた仕事の目安)**: 最良構成の throughput / (1 − abort 率)。abort した試行が commit した試行と同じ費用で、すべて commit できたら、という目安。
  **待ち・backoff の休止に消えた時間は含まない** (trace・計器なし build では測れない)。
- **余地比**: r1 = B1 / S、r2 = B2 / S。

判定の閾値 (結果を見る前に固定):

| 余地 | 条件 |
|---|---|
| 大 | r1 ≥ 2.0 かつ r2 ≥ 1.5 |
| 中 | 大でなく、r1 ≥ 1.5 または r2 ≥ 1.3 |
| 小 | それ以外 |

- B1 は直列化可能性が本質的に課す待ち (同じ hot な行を書く取引は順に並ぶしかない) を無視するので、達成できる値ではない。r1 だけで大を言わない (r2 と組にする)。
- 文献の手法が同じ条件で基準に対し既に大きな倍率を出している場合、その余地の一部は「既知の SOTA が既に取っている」。判定 (§5) ではこれを併記する。

## 5. 判定の書き方 (手順 4)

条件ごとに、(a) 余地 (§4 の閾値)、(b) 文献の SOTA が既に取っている余地 (原典の倍率、基盤が違う旨つき)、
(c) 新しさの地図 (N3) で先行研究の表現範囲の外にある仕組みの型が、その条件の無駄 (abort・待ち・長い取引の干渉) に効きそうか (機構の筋道で書く)、を書く。
推す条件は「(a) が大か中、かつ (c) に筋道がある」もの 1〜2 個。無ければ「推せる条件は無い」と書く。

## 6. 計算の予算と分割

- 合計 2 node 時間未満。1 job 5 分程度に分割し、多数を同時に投げる (2026-09-30 のユーザー指示)。
  job の中で直列に回る点の数と 1 本の見積もり時間を、投入前に本 dir の測定の記録に書く。
- 処置 (プロトコル・構成) とノードを 1 対 1 に割り付けない: 1 本の job に、ある条件のある変種 (目標 / 上限) の全構成を入れ、反復で job を分ける。
  job 内の実行順は seed 固定の乱順。
- build は測定と別の job で行い、binary を repo の外 (`/work/SFC/tanab/tmp/md23-gen-opt-novelty-2026-09-30/bin/`) に sha256 つきで置く。測定 job は $TMPDIR へ写して sha256 を照合してから走らせる。
- 走らせる前に各ノードで単独性を確かめる (他の計測プロセスが無いこと)。

## 改訂

- 改訂 1 (2026-09-30 21 時台 JST、smoke を含む性能測定を 1 本も投入する前、driver の読み合わせで判明): R3 の BoMB の起動形を固定する。
  - 理由: BoMB の mixed mode (`-bomb_mixed_mode=true`) は、別の dispatcher thread が要求を一定の率 (`bomb_mixed_short_rate` 既定 500、既定は毎分) で待ち行列に入れる
    開いた系の負荷であり (`include/bomb.hh` の `request_dispatcher`・`decideType`)、最大 throughput の測定にならない。non-mixed mode は thread ごとに取引型を固定する閉じた系で、
    既定の thread 数 (L1 1・S1 1・S2 1・残りは S5 = ChangeProductQuantity) は §1 の「短い取引の種類と割合は BoMB の既定」の「割合」(`bomb_perc_s1` 50・`bomb_perc_s2` 50、S3〜S5 は 0) と一致しない。
  - 固定する形: non-mixed mode。短い取引の thread を既定の割合 50:50 で S1 (UpdateMaterialCostMaster) と S2 (IssueJournalVoucher) に分ける。
    R3-mixed = `thread_num` 48、L1 1、S1 24、S2 23、S3・S4・S5 は 0。R3-short-only = `thread_num` 47、L1 0、S1 24、S2 23。R3-long-only = `thread_num` 1、L1 1、短い取引 0。
    他の BoMB 引数は既定。S1 は L1 が読む材料原価を更新するので、L1 と短い取引の競合はこの形で生じる。
  - 変種ごとに、出力に現れるべき取引型だけを要求する (short-only に L1 は無く、long-only に短い取引は無い)。
