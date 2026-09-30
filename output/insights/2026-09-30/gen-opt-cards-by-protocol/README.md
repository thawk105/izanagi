# 「Silo に入らない」文献カードを、どの CC なら入るかで分け直す (gen-opt md_9、2026-09-30)

- 目的: 文献カード (`output/insights/2026-09-29/gen-opt-literature-cards/`、本集合 295 枚) のうち「前提が合わず Silo に入らない」182 枚を中心に、
  ベースを Silo 以外の CC に広げると何枚の最適化が試せるようになるか、そのために各 CC に何の準備が要るかを数え、ベースを広げる順番を根拠つきで決められるようにする。
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_9.txt` と同 directory の `common-3.txt` (repo 外)。
- 着手: 2026-09-30 11:55 JST。入力: local main `4f412c67b`、CCBench の pin `68106660`、`cards.json` sha256 `6750adcb…a9849` (編集していない)。
- 分類の事前定義: `definition.md` (判定の子を起動する前に commit `7648ea167` で固定。登録後の改訂なし)。
- 実装・計測はしていない。計算ノードは使っていない。本文は日本語。

---

## 0. 結論

**ベースを広げても、Silo に入らない 182 枚の大半は試せるようにならない。** 8 つの CC のどれかで「前提を満たす / 小改造で満たす」(既にその CC にあるものを除く) になったのは 182 枚中 **26 枚**で、
**145 枚は 8 CC すべてで「満たさない」**だった。主な理由は事前宣言・batch・決定論実行 (57 枚)、多版が要る (単版 CC で 46 枚)、2PL の lock 表と未 commit 値の読み (45 枚)、
長い取引の専用 mode などその他 (104 枚。1 枚に複数の理由がある) で、これらは CCBench のどの CC も持たない前提である (§3)。

**CC ごとの数と準備の重さ (§4・§6):**

| CC | 182 枚のうち入る (fits+minor) | 段 A 候補 (§7 の 4 条件) | うち Silo に入らない 182 枚から | 準備の重さ (点) | 候補数 ÷ (重さ+1) | certified の証拠面 |
|---|---|---|---|---|---|---|
| mocc | 5 | **18** | 2 | **4** | **3.60** | 部分 (修理 X の pin 前進待ち) |
| cicada | 13 | 16 | 5 | 9 | 1.60 | 無 (判定器の門の拡張が要る、L) |
| ermia | 19 | 16 | **6** | 10 | 1.45 | 無 (多版 + SSN の新しい証拠面、L) |
| tictoc | 3 | 14 | **0** | 9 | 1.40 | 無 (Silo の X/P を移せる見込み、M) |
| mvto | 11 | 11 | 4 | 11 | 0.92 | 無 (L)。pin に YCSB が無い |
| oze | 3 | 10 | 1 | 10 | 0.91 | 無 (L) |
| ss2pl | 3 | 7 | 2 | 10 | 0.64 | 無 (L)。pin に YCSB が無い |
| si | 12 | 13 | 3 | — | 対象外 | **不可** (stock が write skew を出し、直列化可能性の certified は定義上出ない) |

「182 枚のうち入る」は既にその CC にある組を除いた `fits + minor`。段 A 候補は `definition.md` §7 の条件 (CCBench に無い・その CC で書ける・効果が出る workload がある・今の検査器で見られるか条件付きで見られる)。

**順番の推奨 (登録した規則 = 候補数 ÷ (重さ+1) の大きい順、`definition.md` §9):**

1. **MOCC が明確に先頭** (3.60)。候補が最も多く (18)、準備は 4 点で、欠けているのは修理 X (`f4a5169e`) を含む pin 前進 (S)、between-run floor の実測 (S)、関数方策の口 (M、並走中の md_10 の結論次第) だけ。
   ただし MOCC の候補 18 のうち 16 は Silo でも入る見込みの最適化で、**MOCC の価値は「新しいカードを試せる」より「同じ最適化を 2 つ目の単版 OCC で試せる」にある**。
2. **Cicada (1.60)・ERMIA (1.45)・TicToc (1.40) はほぼ並ぶ。** 差は判定の揺れ (§9 の留保) より小さい。何を目的にするかで選び分ける:
   - **Silo で試せない最適化を試したい** → ERMIA (182 枚から 6 枚、うち SSN の最適化 3 枚) か Cicada (5 枚)。どちらも certified の証拠面が「無」で重さ L。
     Cicada には trace の patch・証拠面の設計 (D2300)・中間案 M の採用 (D2305 項 4) が既にあり、ERMIA には trace も証拠面の設計も無く、stock の readers bitmap に 48 thread で未定義動作になる int shift がある (`cc/ermia/include/transaction.hh:123,134`)。**下地の厚さでは Cicada が先。**
   - **同じ最適化が別の CC でも効くかを見たい (転移)** → TicToc。新しいカードは 0 枚だが、単版・sort 後施錠で Silo の X/P を移せる見込みで、判定器の意味を変えずに certified まで届く唯一の候補 (M)。
3. mvto・oze・ss2pl は候補も少なく準備も重い。SI は直列化可能性の certified が出ないので対象外。

**判断の限界:** certified の証拠面が「無」の CC (MOCC 以外すべて) は、その段を済ませるまで gen-opt のベースとして「使える」とは言えない。候補の数には、試す価値の低い「設計の軸」カード (§5.3) と、CCBench の YCSB では効果が作りの産物になるカード 2 枚が混ざっている。
それらを外しても順位の先頭 (MOCC) は変わらない (§5.3、事後の感度確認)。

---

## 1. 何を確かめ、何を確かめていないか

| 確かめたこと | 確かめていないこと |
|---|---|
| 各 CC の版の持ち方・timestamp・施錠・validation・GC・workload を CCBench の pin の実ソースで読み、file:line を付けた (`cc-profiles.md`)。親は 5 点を実物で抜き取り照合し一致した | CCBench の build・実行。compile の可否 (ss2pl.cc・cicada の INLINE 系・mocc の MQLOCK) は読解だけ |
| 各 CC の準備 5 段を repo の実物 (file:line・決定番号) で確かめた (`readiness.md`)。親は 4 点を実物で照合し一致した | 準備の重さ (S/M/L) の見積りが実際の工数に合うか。見積りは定義の目安に当てた判断 |
| 295 枚 × 8 CC = 2,360 組を、結果を見る前に固定した定義で判定した (子 5 本、各 59 枚)。全組がちょうど 1 件・語彙と条件の違反 0 を機械で確かめた | カードの原典を読み直しての判定。判定はカードの欄 (前提・機構・原典の CC など) と CC 前提表だけから行った |
| 親が無作為 30 組 (seed 20260930) と各 CC の段 A 候補の上位 5 件を読み直した (§9) | 2,360 組の全件の親による読み直し |
| 「CCBench に無い」は文献カード wave が pin の中で照合した値をそのまま使った | 「世界に無い」「新しい」かどうか (本 wave の範囲外)。カードの追加・書き直し |

---

## 2. 方法

1. **定義を先に固定した** (`definition.md`)。4 値 — `fits` (前提を満たす)・`minor` (小改造で満たす)・`no` (満たさない)・`unknown` (判断不能)。
   小改造は m1 (tuple・版に field を足す)・m2 (worker ごと・全体の共有状態を足す)・m3 (既存の相に検査・分岐を足す、相の中の順序を変える)・m4 (driver が開始前に既に持つ情報を CC へ渡す) に限り、
   **骨格 (版の持ち方・serialization point と timestamp の決め方・施錠の方式・正しさの論拠) を変えるものは小改造でない**。判断不能は他の値へ寄せない。
2. **CC の前提を実ソースで確かめた** (`cc-profiles.md`)。判定の子は CC の性質をこの表だけから引いた。cc-readiness の要約 (repo 外の手がかり) は判定に使っていない。
3. **判定:** 本集合 295 枚を 59 枚ずつ 5 つに分け、Claude opus の子 5 本が共通の指示 (repo 外 `judge-prompt.md`、sha256 `e7de19cb…b3b9c`) で判定した。子は自分の出力を機械で検算した。
4. **集計:** 親の使い捨て script (repo 外 `aggregate.py`、sha256 `feffe174…5b3b0`) が全組の網羅・語彙・条件 (`already_in_cc = true` なら `fits`、`more_natural_on` の条件 (a) など) を検査してから数えた。
   script と子の生出力は repo 外 `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md9-cards-by-protocol/` にある (sha256 は §付属)。
5. **判定する CC:** 主 4 (tictoc・mocc・cicada・ermia) と参考 4 (si・mvto・ss2pl・oze)。Silo は再判定せず既存の分類を写した。d2pl は YCSB・TPC-C の driver が無い (`cc/d2pl/CMakeLists.txt:3`) ので列を作らなかった。

`verifier` 欄は「observable (注記)」の形が 22 枚あるので、observable は接頭一致で数えた (文献カード README §2 の「observable 76 枚」と同じ数え方)。

---

## 3. Silo に入らない 182 枚の行き先

- どれかの CC で入る (`fits`/`minor`、既存を除く): **26 枚** (主 4 CC に限ると 23 枚)。そのうち効果が出る workload がその CC にあるのは 22 枚 (主 4 CC で 19 枚)。
- 8 CC すべてで `no`: **145 枚**。1 枚を理由ごとに 1 回数えると、other 104・predeclared 57・mv-required 46・lock-regime 45・ts-scheme 36・partition 17・gc-structure 10・platform 8・sv-required 1。
  other の中身は、長い取引の専用 mode (Shirakami の S-LTX)、conflict graph (SGT)、commit 前の lock の受け渡し (DRP)、複数 protocol の混在 (CormCC・ACC)、TC/DC の分離 (Deuteronomy) など。
- `unknown`: 182 枚では tictoc 0・mocc 0・cicada 1・ermia 5・si 5・mvto 1・ss2pl 0・oze 5 (全 295 枚では §4)。

入るようになった 26 枚 (CC は `fits`/`minor` の CC、括弧は効果が出る workload もある CC):

| カード | 入る CC |
|---|---|
| ssn-readonly-cstamp-at-snapshot・ssn-safe-snapshot・ssn-read-mostly-cold-read-skipping・essn-exclusion-test・essn-read-from-policy | ermia (ermia) |
| essn-previous-edge-only-metadata・ssn-hierarchical-tracking | ermia (なし) |
| ermia-tid-table-generations | ermia・si (同) |
| ermia-three-epoch-manager・hana-global-sts-tracker・hana-group-gc・hyper-undo-buffer-gc・tebaldi-gc-epoch・wu-gc-granularity-tuple-vs-txn | cicada・ermia・si・mvto (同) |
| hana-table-gc | cicada・ermia・si・mvto (なし) |
| rr-o4-version-prefetching | cicada・ermia・si・mvto・oze (同) |
| abyss-ts-alloc-mutex | cicada・ermia・si・mvto (同) |
| abyss-ts-alloc-batched-atomic | cicada・mvto (同) |
| tebaldi-tso-promises | mocc・cicada (同) |
| brook2pl-read-write-constraint | mocc (mocc) |
| stov2-timestamp-splitting | tictoc・mocc (同) |
| stov2-contention-aware-index | tictoc・mocc・cicada・ermia・si (同) |
| oze-dynamic-protocol-switching | oze (oze) |
| abyss-dl-detect・abyss-lockfree-partitioned-deadlock-detector | ss2pl (ss2pl) |
| shirakami-reuse-deleted-records | 8 CC すべて (なし) |

読み方: 多版の CC (cicada・ermia・si・mvto) で入るのは主に**版の回収 (GC) の最適化**で、ERMIA だけで入るのは **SSN の最適化**である。
GC の最適化の多くは CCBench に「一部」ある (`ccbench.presence = 一部`) ので、段 A の本候補 (「無い」) ではなく副候補に数えられる (§5)。

---

## 4. CC ごとの集計

4 値の件数 (`fits / minor / no / unknown`)。列は文献カードの既存の分類ごと。

| CC | 182 枚 (Silo に入らない) | 80 枚 (CCBench にある) | 33 枚 (Silo に入る見込み) | 295 枚 | fits+minor (既存除く) 295 / 182 | 段 A 候補 (無い) | 副候補 (一部) |
|---|---|---|---|---|---|---|---|
| tictoc | 1 / 2 / 179 / 0 | 26 / 1 / 53 / 0 | 8 / 15 / 8 / 2 | 35 / 18 / 240 / 2 | 28 / 3 | 14 | 8 |
| mocc | 1 / 4 / 177 / 0 | 30 / 5 / 45 / 0 | 7 / 19 / 5 / 2 | 38 / 28 / 227 / 2 | 39 / 5 | 18 | 10 |
| cicada | 4 / 12 / 165 / 1 | 36 / 6 / 38 / 0 | 6 / 12 / 14 / 1 | 46 / 30 / 217 / 2 | 38 / 13 | 16 | 13 |
| ermia | 3 / 16 / 158 / 5 | 30 / 5 / 45 / 0 | 5 / 11 / 16 / 1 | 38 / 32 / 219 / 6 | 40 / 19 | 16 | 14 |
| si | 6 / 10 / 161 / 5 | 24 / 4 / 52 / 0 | 5 / 11 / 16 / 1 | 35 / 25 / 229 / 6 | 33 / 12 | 13 | 12 |
| mvto | 3 / 11 / 167 / 1 | 30 / 11 / 38 / 1 | 6 / 12 / 14 / 1 | 39 / 34 / 219 / 3 | 43 / 11 | 11 | 14 |
| ss2pl | 0 / 3 / 179 / 0 | 12 / 4 / 64 / 0 | 6 / 8 / 19 / 0 | 18 / 15 / 262 / 0 | 21 / 3 | 7 | 8 |
| oze | 1 / 3 / 173 / 5 | 29 / 5 / 45 / 1 | 5 / 9 / 17 / 2 | 35 / 17 / 235 / 8 | 24 / 3 | 10 | 7 |

`fits + minor` (既存除く、295 枚) の効果の 3 分類の内訳:

| CC | CPU cache | delay on conflict | version lifetime | 3 分類外 |
|---|---|---|---|---|
| tictoc | 8 | 5 | 0 | 15 |
| mocc | 8 | 12 | 0 | 19 |
| cicada | 11 | 9 | 8 | 10 |
| ermia | 10 | 7 | 8 | 15 |
| si | 10 | 5 | 8 | 10 |
| mvto | 13 | 9 | 9 | 12 |
| ss2pl | 7 | 7 | 1 | 6 |
| oze | 10 | 6 | 0 | 8 |

その他の数 (`summary.json`):

- 既にその CC にある (`already_in_cc = true`): tictoc 25・mocc 27・cicada 38・ermia 30・si 27・mvto 30・ss2pl 12・oze 28。有無を決められない (`unknown`) 組は CC ごとに 0〜4。
- `unknown` の理由: 前提表で未確認 (`cc-unverified`) は ermia 4・si 4・mvto 1・oze 5 (多版の版の回収経路の安全性、oze の旧版回収の有無など)。カードの記述不足 (`card-underspecified`) は各 CC 2〜3 (One-shot GC の要旨だけのカードなど)。
- 効果が出る workload が無い (`workload_ok = no`): 各 CC 32、mvto 41・ss2pl 40 (pin に YCSB が無いため)。
- 効果の 3 分類で version lifetime が入るのは多版の CC だけで、単版の tictoc・mocc は 0。

---

## 5. 段 A の候補

### 5.1 各 CC の上位 5 件 (登録した並べ方: fits → minor、observable → conditional、小改造の数の少ない順、同順は card_id)

| CC | 上位 5 件 |
|---|---|
| tictoc | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |
| mocc | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、healing-false-invalidation-elimination (fits)、silo-inline-record-data、tskd-tsdefer-lockfree-probing |
| cicada | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、abyss-ts-alloc-batched-atomic、abyss-ts-alloc-mutex、silo-inline-record-data |
| ermia | abyss-ts-alloc-mutex (fits)、stov2-basis-transaction-internals (fits)、ssn-readonly-cstamp-at-snapshot (fits)、abyss-lock-wait-timeout、silo-inline-record-data |
| si | abyss-ts-alloc-mutex (fits)、stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing |
| mvto | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、abyss-ts-alloc-batched-atomic、abyss-ts-alloc-mutex、silo-inline-record-data |
| ss2pl | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、silo-inline-record-data、abyss-wait-die、stov2-commit-time-updates |
| oze | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |

全件は `summary.json` の `stage_a` (本候補) と `stage_a_partial` (副候補 = CCBench に「一部」ある) にある。8 CC を合わせた本候補は 27 枚で、うち 16 枚は Silo に入る見込みの 33 枚、11 枚は Silo に入らない 182 枚から来ている。

### 5.2 CC ごとに固有のもの

- **MOCC:** 施錠待ちに上限を付ける (abyss-lock-wait-timeout) が `fits` で、Silo より自然に入る (MOCC は tuple の RW lock を blocking で待ち、未使用の `LOCK_TIMEOUT_US` も残る。`more_natural_on`)。
  182 枚から来たのは brook2pl-read-write-constraint と tebaldi-tso-promises の 2 枚。
- **ERMIA:** SSN の最適化 (ssn-readonly-cstamp-at-snapshot・ssn-safe-snapshot・ssn-read-mostly-cold-read-skipping) が ERMIA だけで入る。
- **Cicada:** 版の prefetch (rr-o4-version-prefetching)・3 epoch の回収管理 (ermia-three-epoch-manager)・tebaldi-tso-promises が 182 枚から来た。
- **TicToc:** 本候補 14 枚すべてが Silo に入る見込みの 33 枚から来た。TicToc だけで入るものは無い。

### 5.3 留保 (判定は変えず、読み手への注意)

- **設計の軸のカード (`kind = design-dimension`) が候補に入っている:** stov2-basis-transaction-internals (read/write set を hash 表にする)・abyss-ts-alloc-mutex / -batched-atomic (timestamp の割当て方)・abyss-wait-die・abyss-dl-detect。
  評価論文が比べた設計の軸で、特に timestamp の割当て 2 枚は性能の下がる基準線である。登録した並べ方は種類を見ないので上位に来るが、「文献の最適化を試す」段 A の本命ではない。
- **CCBench の YCSB で効果が作りの産物になるカード:** healing-false-invalidation-elimination (値の一致で検証を通す)・stov2-commit-time-updates (updater が恒等写像)。文献カード README §7 のとおり段 A の根拠にしない。
- **事後の感度確認 (登録した規則ではない):** 上の 7 枚を除くと本候補は tictoc 10・mocc 14・cicada 11・ermia 13・si 10・mvto 7・ss2pl 3・oze 9、候補数 ÷ (重さ+1) は mocc 2.80・ermia 1.18・cicada 1.10・tictoc 1.00・oze 0.82・mvto 0.58・ss2pl 0.27。
  先頭の MOCC は変わらず、2〜4 位の差はさらに縮む。
- abyss-ts-alloc-* を cicada・mvto で `minor` (m2) とした判定は、begin 時の timestamp の出し方を thread local clock から共有 counter に替えるもので、定義の「timestamp の決め方」(骨格) に当たると読めば `no` になる。子は「一意で thread 内単調という意味は変わらない」として `minor` にした。親は判定を変えず留保とする。

---

## 6. CCBench にある 80 枚と Silo に入る見込みの 33 枚への印

- **別の CC の方が自然に入る (`more_natural_on`、6 枚):**
  - abyss-lock-wait-timeout → mocc・ss2pl (どちらも lock を待つ経路を持つ。Silo は既定 no-wait の CAS 施錠)
  - tictoc-preemptive-abort → tictoc (近似 commit ts に使う wts/rts が TicToc にだけある)
  - cicada-write-set-sort-by-contention → cicada・mvto、cicada-early-version-consistency-check → mvto、cicada-clock-boost-on-abort → mvto (Cicada と同じ版と timestamp を持つ mvto に入る)
  - plor-read-only-dynamic-validation → mocc (OCC と read lock の両方を持つ hybrid)
- **移植の出所 (`natural_home`、既にその CC にある):** 80 枚のうち 72 枚に 1 つ以上ある (`card-level.jsonl`)。Silo に無い 58 枚の移植元の確認に使える。
- **既存の分類との食い違い (再分類はしない):** Silo に入る見込みの 33 枚のうち **DRP の 4 枚 (drp-core・drp-wild-rp・drp-intentions・drp-nullify-intentions) は 8 CC すべてで `no`** だった。
  commit 前に lock を緩めて後続へ渡し、先行者の順に commit させる機構で、本 wave の定義では施錠と serialization point の骨格の変更に当たる。文献カード wave は Silo で「入る見込み」(迷ったらこちら) としていた。段 A に DRP を選ぶなら、この骨格の変更を前提に正しさ関門を設計する必要がある。
  残る 29 枚のうち 27 枚は、どれかの CC で `fits`/`minor` (既存除く) になった。

---

## 7. 準備の表 (正本は `readiness.md` §4)

| CC | trace 計装 | certified の証拠面 | 性能計測 | LLM が書く口 | 比較基盤 | 合計 |
|---|---|---|---|---|---|---|
| silo | 0 | S | 0 | 0 | 0 | 1 |
| mocc | 0 | S | S | M | 0 | 4 |
| cicada | S | L | S | L (backoff だけなら S) | S | 9 |
| tictoc | M | M | S | L (S) | S | 9 |
| ermia | M | L | S | L (S) | S | 10 |
| mvto | L | L | S | L | S | 11 |
| ss2pl | M | L | S | L | S | 10 |
| oze | M | L | S | L | S | 10 |
| si | S | 不可 | S | — | 部分 | 対象外 |

点: 0 = 有る、S = 1、M = 2、L = 3 (`definition.md` §9)。表の点に入れていない全 CC 共通の準備が 2 つある: D2289 決定 4 の 2 関門 (検査用記録の差し込み点を LLM の編集範囲外に固定、仕組みごとの小モデル全場面検査) と、
取引内の値の照合 (正しさ関門の設計の D2b) の前提になる「自分の書きを読む」修正 (Silo 以外の CC も read を read set → write set の順に探す、`cc-profiles.md` の各 CC の 7 項)。

実物で確かめた要点:

- certified の条件は X/P の証拠面がそろうことで、対象の protocol は `{"silo","si","mocc"}` だけ (`orchestrator/verifier/model.py:37,77-82`)。他の CC は判定の上限が indeterminate になる。
- LLM が書ける EVOLVE-BLOCK の対象は `include/backoff.hh`・`cc/silo/transaction.cc`・`cc/mocc/transaction.cc` の 3 つだけ (`orchestrator/campaign/source_digest.py:85-86`)。
- 比較 harness・探索 loop は silo と mocc 以外を拒否する (`orchestrator/campaign/p3_s4_loop.py:122-127` ほか、`readiness.md` §0)。
- MOCC の stock は read-heavy で G2 を出す (pin C で 5/112 走)。修理 X で 0/112 になったが branch のみで pin は進んでいない (`output/insights/2026-09-29/mocc-validation-fix/README.md` §0、D2304)。

---

## 8. 次の wave への申し送り

- **MOCC を gen-opt の 2 つ目のベースにする準備 (推奨):** (1) 修理 X を含む CCBench の pin 前進 (push と D297 の扱いの裁定は人間の手番、D2304 項 3)、(2) MOCC の between-run floor の実測 (計算あり、見積りは起票時)、
  (3) 関数方策の口は md_10 (MOCC 版の関数方策の軸の設計) の結論を入力にする。段 A の最初の試しを人が書く名前つきの対照にするなら (3) は後でよい。
- **2 つ目の選択 (Cicada か TicToc) は目的を先に決める:** Silo で試せない最適化 → Cicada (D2305 項 4 (3) の案 A = 判定器の protocol 別の門が要る、L)。転移の確認 → TicToc (X/P の移植、M)。
- **ERMIA** は 182 枚のうち SSN 系の 7 枚が ERMIA だけで入る (効果が出る workload があるのは 5 枚) が、stock の readers bitmap の int shift (48 thread で未定義動作) を先に確かめる必要がある。
- **DRP 4 枚**を段 A に選ぶなら、骨格の変更 (commit 前の lock の受け渡し) を前提に正しさ関門を設計し直す (§6)。
- CCBench の実物で見つけた注意 (上流への還元は人間の判断): mocc の `read_internal` の abort 経路で ReadElement の一部が未初期化になると読める、ss2pl の `delete_record` が lock を取らず abort が insert を index から外さない、
  oze の leader (thid 1) と epoch 初期化 (thid 0) のずれ、mvto の版を wts 順に積まない設置、cicada の precheck のコメント (競合度順) と実装 ((storage, key) 順) の食い違い。いずれも読解だけで実行は未確認 (`cc-profiles.md` の各 11 項)。

---

## 9. 親の抜き取りと、子が迷った組

- **無作為 30 組** (`summary.json` の `spotcheck_sample`、seed 20260930): 親がカードと CC 前提表から読み直し、30 組とも判定に同意した。直した組は 0。
- **各 CC の上位 5 件** (11 枚・40 組): 判定を変えた組は 0。§5.3 の留保 3 点 (設計の軸、YCSB の作りの産物、abyss-ts-alloc-* の `minor`) を付けた。
- **子が報告した迷い (主なもの、判定はそのまま):**
  - 2PL の lock を持たない多版 CC で、pending 版・inflight 版の spin 待ちを「lock 待ち」とみなして施錠待ちの上限を `minor` にした (abyss-lock-wait-timeout ほか)。厳しく読めば `no`。
  - 部品カード (Healing・BCC・AOCC の部品) は親の機構の前提ごと判定した。
  - bcc-essential-pattern-validation × mocc、essn-exclusion-test × ermia、ermia-ssn-read-mostly-cold-read-skipping × ermia は、正しさの論拠が広がる変更で、骨格の変更 (`no`) との境目。
  - cormcc-mediated-switching × oze は、切替の判定が常に false で経路が動いたことが無いが「既にある」とした。
  - tcm-read-only-transaction-optimization・msgt-epoch-readonly-versions・shirakami-safe-snapshot × si を「既にある」としたのは、SI が検証せずに snapshot を読むからで、SI は直列化可能でない。
    分離水準を下げるカード (tictoc-lower-isolation-levels) は規律 2 に当たるので段 A の候補にしない (本 wave の候補にも入っていない)。
  - mvto・ss2pl で「TPC-C の query から予定 key 集合を近似して渡す」を m4 と読んだ組がある (ding-thread-aware-reordering・tskd-tsdefer)。CC 前提表は TPC-C では事前の key 集合を CC に渡せないとしており、これらは `workload_ok = unknown` で候補に入っていない。

---

## 付属ファイル

| file | 中身 |
|---|---|
| `definition.md` | 分類の事前定義 (commit `7648ea167`、判定前に固定) |
| `cc-profiles.md` | CC ごとの前提 (CCBench の実ソース、file:line つき) |
| `readiness.md` | CC × 準備 5 段の原票 (§0〜§3) と親の裁定 (§4) |
| `judgments.jsonl` | 判定の正本。カード × CC ごとに 1 行 (2,360 行)。欄: `card_id`・`cc`・`value`・`already_in_cc`・`workload_ok`・`reasons`・`minor_parts`・`basis_fields`・`note` |
| `card-level.jsonl` | カードごとに 1 行 (295 行)。Silo 列 (`present`/`port-candidate`/`feasible`/`mismatch`)・`more_natural_on`・`natural_home` |
| `summary.json` | 集計 (件数・効果の内訳・段 A 候補の全件・副候補・理由コード・抜き取りの標本) |

repo 外の資材 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md9-cards-by-protocol/`、sha256 の先頭 8 桁): `make_chunks.py` 629229e2、`judge-prompt.md` e7de19cb、`aggregate.py` feffe174、`inspect.py` 4049330e、`spot.py` 0627cf39、
子の生出力 `judge-1〜5.jsonl` 2686bd7d・58108f30・fa2e888c・ff547b6b・66727497、`cardlevel-1〜5.jsonl` 818d3d0a・dfdc9f9c・2ae84741・a2a1b6ad・0b892b0d、原票 `cc-profiles-raw.md`・`readiness-raw.md`。
