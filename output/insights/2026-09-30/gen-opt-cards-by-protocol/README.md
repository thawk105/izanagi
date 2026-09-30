# 「Silo に入らない」文献カードを、どの CC なら入るかで分け直す (gen-opt md_9、2026-09-30)

- 目的: 文献カード (`output/insights/2026-09-29/gen-opt-literature-cards/`、本集合 295 枚) のうち「前提が合わず Silo に入らない」182 枚を中心に、
  ベースを Silo 以外の CC に広げると何枚の最適化が試せるようになるか、そのために各 CC に何の準備が要るかを数え、ベースを広げる順番を根拠つきで決められるようにする。
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_9.txt` と同 directory の `common-3.txt` (repo 外)。
- 着手: 2026-09-30 11:55 JST。入力: local main `4f412c67b`、CCBench の pin `68106660`、`cards.json` sha256 `6750adcb…a9849` (編集していない)。
- 分類の事前定義: `definition.md` (判定の子を起動する前に commit `7648ea167` で固定。定義の本文は登録後に改訂していない)。
- 判定の正本: `judgments.jsonl` (子の判定に、段 6 のレビュー 2 巡を受けた親の訂正 24 組を当てたもの。訂正した組は `revision` 欄に元の値と理由を持つ。§10)。
- 実装・計測はしていない。計算ノードは使っていない。本文は日本語。

---

## 0. 結論

**ベースを広げても、Silo に入らない 182 枚の大半は試せるようにならない。** 8 つの CC のどれかで「前提を満たす / 小改造で満たす」(既にその CC にあるものを除く) になったのは 182 枚中 **20 枚**で、
**151 枚は 8 CC すべてで「満たさない」**だった。主な理由は事前宣言・batch・決定論実行 (57 枚)、多版が要る (単版 CC で 51 枚)、2PL の lock 表と未 commit 値の読み (45 枚)、
timestamp の決め方が合わない (41 枚)、長い取引の専用 mode・正しさの論拠の変更などその他 (116 枚。1 枚に複数の理由がある) で、これらは CCBench のどの CC も持たない前提か、小改造の範囲を超える変更である (§3)。

**CC ごとの数と準備の重さ (§4・§7):**

| CC | 182 枚のうち入る | 段 A 候補 (定義 §7 の 4 条件) | うち Silo に入らない 182 枚から | 準備の重さ (点) | 候補数 ÷ (重さ+1) | certified の証拠面 |
|---|---|---|---|---|---|---|
| mocc | 5 | **13** | 2 | **4** | **2.60** | 部分 (修理 X の pin 前進待ち) |
| cicada | 11 | 13 | **3** | 9 | 1.30 | 無 (判定器の門の拡張が要る、L) |
| ermia | 14 | 13 | 3 | 10 | 1.18 | 無 (多版 + SSN の新しい証拠面、L) |
| tictoc | 3 | 11 | 0 | 9 | 1.10 | 無 (Silo の X/P を移せる見込み、M) |
| oze | 3 | 10 | 1 | 10 | 0.91 | 無 (L) |
| mvto | 9 | 9 | 2 | 11 | 0.75 | 無 (L)。pin に YCSB が無い |
| ss2pl | 3 | 7 | 2 | 10 | 0.64 | 無 (L)。pin に YCSB が無い |
| si | 12 | 13 | 3 | — | 対象外 | **不可** (stock が write skew を出し、直列化可能性の certified は定義上出ない) |

「182 枚のうち入る」は既にその CC にある組を除いた `fits + minor` の枚数。段 A 候補は `definition.md` §7 の条件 (CCBench に無い・その CC で書ける・効果が出る workload がある・今の検査器で見られるか条件付きで見られる) を満たすカード。

**順番の推奨 (登録した規則 = 候補数 ÷ (重さ+1) の大きい順、`definition.md` §9):**

1. **MOCC が明確に先頭** (2.60)。候補が最も多く (13)、準備は 4 点で、欠けているのは修理 X (`f4a5169e`) を含む pin 前進 (S)、between-run floor の実測 (S)、関数方策の口 (M、並走中の md_10 の結論次第) だけ。
   ただし MOCC の候補 13 のうち 11 は Silo でも入る見込みの最適化で、**MOCC の価値は「新しいカードを試せる」より「同じ最適化を 2 つ目の単版 OCC で試せる」にある**。
2. **Cicada (1.30)・ERMIA (1.18)・TicToc (1.10) が続く。** 差は判定の揺れ (§9・§10) と同じ程度に小さい。何を目的にするかで選び分ける:
   - **Silo で試せない最適化を試したい** → **Cicada**。182 枚から来た候補は Cicada 3 枚 (版の prefetch、3 epoch の回収管理、書き手の予約の先出し)、ERMIA 3 枚 (うち 1 枚は性能の下がる基準線の timestamp 割当て) で、
     ERMIA だけに入る SSN の最適化は、ほとんどが正しさの論拠を替える変更で候補に残らなかった (§10)。どちらも certified の証拠面が「無」で重さ L だが、
     Cicada には trace の patch・証拠面の設計 (D2300)・中間案 M の採用 (D2305 項 4) が既にある。ERMIA には trace も証拠面の設計も無く、stock の readers bitmap に 48 thread で未定義動作になる int shift がある (`cc/ermia/include/transaction.hh:123,134`)。
   - **同じ最適化が別の CC でも効くかを見たい (転移)** → **TicToc**。新しいカードは 0 枚だが、単版・sort 後施錠で Silo の X/P を移せる見込みで、判定器の意味を変えずに certified まで届く見込みがあるのは TicToc だけ (M)。
3. oze・mvto・ss2pl は候補も少なく準備も重い。SI は直列化可能性の certified が出ないので対象外。

**判断の限界:** certified の証拠面が「無」の CC (MOCC 以外すべて) は、その段を済ませるまで gen-opt のベースとして「使える」とは言えない。候補の数には、試す価値の低い「設計の軸」カードと、
CCBench の YCSB では効果が作りの産物になるカードが混ざっている。それらを外しても順位の先頭 (MOCC) は変わらない (§5.3、事後の感度確認)。
**「満たさない」は「試せない」と同じではない。** 定義は骨格 (版の持ち方・timestamp の決め方・施錠の方式・正しさの論拠) を変えるものを小改造から外したので、BCC や DRP のように原典が Silo 上で論拠を示した機構も
「満たさない」に入る (§6)。それらは、新しい論拠に合わせた正しさ関門を設計すれば試せる別枠である。

---

## 1. 何を確かめ、何を確かめていないか

| 確かめたこと | 確かめていないこと |
|---|---|
| 各 CC の版の持ち方・timestamp・施錠・validation・GC・workload を CCBench の pin の実ソースで読み、file:line を付けた (`cc-profiles.md`)。親は 5 点を実物で抜き取り照合し一致した | CCBench の build・実行。compile の可否 (ss2pl.cc・cicada の INLINE 系・mocc の MQLOCK) は読解だけ |
| 各 CC の準備 5 段を repo の実物 (file:line・決定番号) で確かめた (`readiness.md`)。親は 4 点を実物で照合し一致した | 準備の重さ (S/M/L) の見積りが実際の工数に合うか。見積りは定義の目安に当てた判断 |
| 295 枚 × 8 CC = 2,360 組を、結果を見る前に固定した定義で判定した (子 5 本、各 59 枚)。全組がちょうど 1 件・語彙と条件の違反 0 を機械で確かめた | カードの原典を読み直しての判定。判定はカードの欄 (前提・機構・原典の CC など) と CC 前提表だけから行った |
| 親が無作為 30 組 (seed 20260930) と各 CC の段 A 候補の上位 5 件を読み直した (§9)。段 6 の独立レビューと焦点再レビュー (どちらも Codex、read-only) が件数を正本から数え直して一致を確かめ、定義からの逸脱を計 5 件指摘した。親は同じ型の組を洗い出して 24 組を直した (§10) | 2,360 組の全件の親による読み直し。§10 の洗い出しは判定の note とカードの機構・正しさの欄の語での検索と、同じ機構のカード群の一覧で行った。語に掛からない同型の組が残っている可能性はある |
| 「CCBench に無い」は文献カード wave が pin の中で照合した値をそのまま使った | 「世界に無い」「新しい」かどうか (本 wave の範囲外)。カードの追加・書き直し |

---

## 2. 方法

1. **定義を先に固定した** (`definition.md`)。4 値 — `fits` (前提を満たす)・`minor` (小改造で満たす)・`no` (満たさない)・`unknown` (判断不能)。
   小改造は m1 (tuple・版に field を足す)・m2 (worker ごと・全体の共有状態を足す)・m3 (既存の相に検査・分岐を足す、相の中の順序を変える)・m4 (driver が開始前に既に持つ情報を CC へ渡す) に限り、
   **骨格 (版の持ち方・serialization point と timestamp の決め方・施錠の方式・正しさの論拠) を変えるものは小改造でない**。判断不能は他の値へ寄せない。
2. **CC の前提を実ソースで確かめた** (`cc-profiles.md`)。判定の子は CC の性質をこの表だけから引いた。cc-readiness の要約 (repo 外の手がかり) は判定に使っていない。
3. **判定:** 本集合 295 枚を 59 枚ずつ 5 つに分け、Claude opus の子 5 本が共通の指示 (repo 外 `judge-prompt.md`) で判定した。子は自分の出力を機械で検算した。
4. **集計:** 親の使い捨て script (repo 外 `aggregate.py`) が全組の網羅・語彙・条件 (`already_in_cc = true` なら `fits`、`more_natural_on` の条件 (a) など) を検査し、親の訂正 (`corrections-parent.jsonl`) を当ててから数えた。
   script と子の生出力は repo 外 `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md9-cards-by-protocol/` にある (sha256 は §付属)。
5. **判定する CC:** 主 4 (tictoc・mocc・cicada・ermia) と参考 4 (si・mvto・ss2pl・oze)。Silo は再判定せず既存の分類を写した。d2pl は YCSB・TPC-C の driver が無い (`cc/d2pl/CMakeLists.txt:3`) ので列を作らなかった。

`verifier` 欄は「observable (注記)」の形が 22 枚あるので、observable は接頭一致で数えた (文献カード README §2 の「observable 76 枚」と同じ数え方)。

---

## 3. Silo に入らない 182 枚の行き先

- どれかの CC で入る (`fits`/`minor`、既存を除く): **20 枚** (主 4 CC に限ると 17 枚)。そのうち効果が出る workload がその CC にあるのは 17 枚 (主 4 CC で 14 枚)。
- 8 CC すべてで `no`: **151 枚**。1 枚を理由ごとに 1 回数えると、other 116・predeclared 57・mv-required 51・lock-regime 45・ts-scheme 41・partition 17・gc-structure 10・platform 8・sv-required 1。
  other の中身は、長い取引の専用 mode (Shirakami の S-LTX)、conflict graph (SGT)、commit 前の lock の受け渡し (DRP)、複数 protocol の混在 (CormCC・ACC)、TC/DC の分離 (Deuteronomy)、正しさの論拠の変更 (§10 の規則 A) など。
- `unknown`: 182 枚では tictoc 0・mocc 0・cicada 1・ermia 5・si 5・mvto 1・ss2pl 0・oze 5 (全 295 枚は §4)。

入るようになった 20 枚 (括弧は効果が出る workload もある CC):

| カード | 入る CC |
|---|---|
| ermia-three-epoch-manager・hana-global-sts-tracker・hana-group-gc・hyper-undo-buffer-gc・tebaldi-gc-epoch・wu-gc-granularity-tuple-vs-txn | cicada・ermia・si・mvto (同) |
| hana-table-gc | cicada・ermia・si・mvto (なし) |
| rr-o4-version-prefetching | cicada・ermia・si・mvto・oze (同) |
| ermia-tid-table-generations | ermia・si (同) |
| abyss-ts-alloc-mutex | ermia・si (同) |
| essn-read-from-policy | ermia (ermia) |
| ssn-hierarchical-tracking | ermia (なし) |
| tebaldi-tso-promises | mocc・cicada (同) |
| brook2pl-read-write-constraint | mocc (mocc) |
| stov2-timestamp-splitting | tictoc・mocc (同) |
| stov2-contention-aware-index | tictoc・mocc・cicada・ermia・si (同) |
| oze-dynamic-protocol-switching | oze (oze) |
| abyss-dl-detect・abyss-lockfree-partitioned-deadlock-detector | ss2pl (ss2pl) |
| shirakami-reuse-deleted-records | 8 CC すべて (なし) |

読み方: 多版の CC (cicada・ermia・si・mvto) で入るのは主に**版の回収 (GC) の最適化**である。GC の最適化の多くは CCBench に「一部」ある (`ccbench.presence = 一部`) ので、
段 A の本候補 (「無い」) ではなく副候補に数えられる (§5)。

---

## 4. CC ごとの集計

4 値の件数 (`fits / minor / no / unknown`)。列は文献カードの既存の分類ごと。

| CC | 182 枚 (Silo に入らない) | 80 枚 (CCBench にある) | 33 枚 (Silo に入る見込み) | 295 枚 | fits+minor (既存除く) 295 / 182 | 段 A 候補 (無い) | 副候補 (一部) |
|---|---|---|---|---|---|---|---|
| tictoc | 1 / 2 / 179 / 0 | 26 / 1 / 53 / 0 | 8 / 12 / 11 / 2 | 35 / 15 / 243 / 2 | 25 / 3 | 11 | 8 |
| mocc | 1 / 4 / 177 / 0 | 30 / 5 / 45 / 0 | 6 / 13 / 12 / 2 | 37 / 22 / 234 / 2 | 32 / 5 | 13 | 8 |
| cicada | 4 / 10 / 167 / 1 | 36 / 5 / 39 / 0 | 6 / 11 / 15 / 1 | 46 / 26 / 221 / 2 | 34 / 11 | 13 | 13 |
| ermia | 2 / 12 / 163 / 5 | 30 / 5 / 45 / 0 | 5 / 11 / 16 / 1 | 37 / 28 / 224 / 6 | 35 / 14 | 13 | 13 |
| si | 6 / 10 / 161 / 5 | 24 / 4 / 52 / 0 | 5 / 11 / 16 / 1 | 35 / 25 / 229 / 6 | 33 / 12 | 13 | 12 |
| mvto | 3 / 9 / 169 / 1 | 29 / 10 / 40 / 1 | 6 / 11 / 15 / 1 | 38 / 30 / 224 / 3 | 38 / 9 | 9 | 14 |
| ss2pl | 0 / 3 / 179 / 0 | 12 / 4 / 64 / 0 | 6 / 8 / 19 / 0 | 18 / 15 / 262 / 0 | 21 / 3 | 7 | 8 |
| oze | 1 / 3 / 173 / 5 | 29 / 5 / 45 / 1 | 5 / 9 / 17 / 2 | 35 / 17 / 235 / 8 | 24 / 3 | 10 | 7 |

`fits + minor` (既存除く、295 枚) の効果の 3 分類の内訳:

| CC | CPU cache | delay on conflict | version lifetime | 3 分類外 |
|---|---|---|---|---|
| tictoc | 8 | 5 | 0 | 12 |
| mocc | 7 | 12 | 0 | 13 |
| cicada | 8 | 9 | 8 | 9 |
| ermia | 9 | 6 | 8 | 12 |
| si | 10 | 5 | 8 | 10 |
| mvto | 10 | 8 | 9 | 11 |
| ss2pl | 7 | 7 | 1 | 6 |
| oze | 10 | 6 | 0 | 8 |

その他の数 (`summary.json`):

- 既にその CC にある (`already_in_cc = true`): tictoc 25・mocc 27・cicada 38・ermia 30・si 27・mvto 30・ss2pl 12・oze 28。有無を決められない (`unknown`) 組は CC ごとに 0〜4。
- `unknown` の理由: 前提表で未確認 (`cc-unverified`) は ermia 4・si 4・mvto 1・oze 5 (多版の版の回収経路の安全性、oze の旧版回収の有無など)。カードの記述不足 (`card-underspecified`) は各 CC 2〜3 (One-shot GC の要旨だけのカードなど)。
- 効果が出る workload が無い (`workload_ok = no`): 各 CC 32、mvto 41・ss2pl 40 (pin に YCSB が無いため)。
- 効果の 3 分類で version lifetime が入るのは多版の CC と ss2pl (1) で、単版の tictoc・mocc は 0。

---

## 5. 段 A の候補

### 5.1 各 CC の上位 5 件 (登録した並べ方: fits → minor、observable → conditional、小改造の数の少ない順、同順は card_id)

| CC | 上位 5 件 |
|---|---|
| tictoc | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |
| mocc | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |
| cicada | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |
| ermia | abyss-ts-alloc-mutex (fits)、stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing |
| si | abyss-ts-alloc-mutex (fits)、stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing |
| mvto | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、ermia-three-epoch-manager、rr-o4-version-prefetching |
| ss2pl | abyss-lock-wait-timeout (fits)、stov2-basis-transaction-internals (fits)、silo-inline-record-data、abyss-wait-die、stov2-commit-time-updates |
| oze | stov2-basis-transaction-internals (fits)、abyss-lock-wait-timeout、silo-inline-record-data、tskd-tsdefer-lockfree-probing、tskd-tsdefer-proactive-deferment |

全件は `summary.json` の `stage_a` (本候補) と `stage_a_partial` (副候補 = CCBench に「一部」ある) にある。8 CC を合わせた本候補は 18 枚で、うち 11 枚は Silo に入る見込みの 33 枚、7 枚は Silo に入らない 182 枚から来ている。

### 5.2 CC ごとに固有のもの

- **MOCC:** 施錠待ちに上限を付ける (abyss-lock-wait-timeout) が `fits` で、Silo より自然に入る (MOCC は tuple の RW lock を blocking で待ち、未使用の `LOCK_TIMEOUT_US` も残る。`more_natural_on`)。
  182 枚から来たのは brook2pl-read-write-constraint と tebaldi-tso-promises の 2 枚。
- **Cicada:** 版の prefetch (rr-o4-version-prefetching)・3 epoch の回収管理 (ermia-three-epoch-manager)・tebaldi-tso-promises の 3 枚が 182 枚から来た。
- **ERMIA:** 182 枚から来たのは rr-o4-version-prefetching・ermia-three-epoch-manager と、基準線の abyss-ts-alloc-mutex の 3 枚。SSN の最適化 (ESSN の除外条件、read-only の commit 時刻、safe snapshot、cold read の省略) は §10 で「満たさない」に直した。
- **TicToc:** 本候補 11 枚すべてが Silo に入る見込みの 33 枚から来た。TicToc だけで入るものは無い。

### 5.3 留保と事後の感度確認

- **設計の軸のカード (`kind = design-dimension`) が候補に入っている:** stov2-basis-transaction-internals (read/write set を hash 表にする)・abyss-ts-alloc-mutex (timestamp の割当て方)・abyss-wait-die・abyss-dl-detect。
  評価論文が比べた設計の軸で、特に abyss-ts-alloc-mutex は性能の下がる基準線である。登録した並べ方は種類を見ないので上位に来るが、「文献の最適化を試す」段 A の本命ではない。
- **CCBench の YCSB で効果が作りの産物になるカード:** stov2-commit-time-updates (updater が恒等写像になる)。文献カード README §7 のとおり段 A の根拠にしない (同じ注意の healing-false-invalidation-elimination は §10 で「満たさない」に直した)。
- **事後の感度確認 (登録した規則ではない):** 上の 5 枚を除くと本候補は tictoc 8・mocc 10・cicada 11・ermia 10・si 10・mvto 7・ss2pl 3・oze 9、候補数 ÷ (重さ+1) は mocc 2.00・cicada 1.10・ermia 0.91・oze 0.82・tictoc 0.80・mvto 0.58・ss2pl 0.27。
  先頭の MOCC と 2 位の Cicada は変わらない。

---

## 6. CCBench にある 80 枚と Silo に入る見込みの 33 枚への印

- **別の CC の方が自然に入る (`more_natural_on`、5 枚):**
  - abyss-lock-wait-timeout → mocc・ss2pl (どちらも lock を待つ経路を持つ。Silo は既定 no-wait の CAS 施錠)
  - tictoc-preemptive-abort → tictoc (近似 commit ts に使う wts/rts が TicToc にだけある)
  - cicada-write-set-sort-by-contention → cicada・mvto、cicada-early-version-consistency-check → mvto (Cicada と同じ版と timestamp を持つ mvto に入る)。子が付けた cicada-clock-boost-on-abort → mvto は §10 の規則 T で外した (`summary.json` の `dropped_more_natural_on`)
  - plor-read-only-dynamic-validation → mocc (OCC と read lock の両方を持つ hybrid)
- **移植の出所 (`natural_home`、既にその CC にある):** 80 枚のうち 72 枚に 1 つ以上ある (`card-level.jsonl`)。Silo に無い 58 枚の移植元の確認に使える。
- **既存の分類との食い違い (再分類はしない):** Silo に入る見込みの 33 枚のうち **11 枚は 8 CC すべてで `no`** だった。
  - DRP の 4 枚 (drp-core・drp-wild-rp・drp-intentions・drp-nullify-intentions): commit 前に lock を緩めて後続へ渡し、先行者の順に commit させる機構で、施錠と serialization point の骨格の変更に当たる。
  - BCC の 4 枚 (bcc-essential-pattern-validation と部品 3 枚) と Healing の 3 枚 (healing-transaction-healing・healing-access-cache・healing-false-invalidation-elimination): stock の validation が abort させていた取引を commit させ、正しさを原典の新しい論拠で言う機構 (§10 の規則 A)。
  - 文献カード wave は、迷ったら Silo で「入る見込み」とする規則だった。本 wave の定義ではこれらは小改造でない。**段 A でこれらを選ぶなら、その論拠に合わせた正しさ関門の設計が前提になる** (文献カード README §6.3 の別枠 2 位の BCC も同じ)。
  - 残る 22 枚のうち 20 枚は、どれかの CC で `fits`/`minor` (既存除く) になった。

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
- **ERMIA** の SSN 固有の最適化は、どれも正しさの論拠を替えるか、候補の条件を満たさなかった。ERMIA をベースにするなら、stock の readers bitmap の int shift (48 thread で未定義動作) を先に確かめる必要がある。
- **論拠を替える機構 (BCC・DRP・ESSN など) を段 A に選ぶなら、** 骨格の変更を前提に正しさ関門を設計し直す (§6、§10)。
- CCBench の実物で見つけた注意 (上流への還元は人間の判断): mocc の `read_internal` の abort 経路で ReadElement の一部が未初期化になると読める、ss2pl の `delete_record` が lock を取らず abort が insert を index から外さない、
  oze の leader (thid 1) と epoch 初期化 (thid 0) のずれ、mvto の版を wts 順に積まない設置、cicada の precheck のコメント (競合度順) と実装 ((storage, key) 順) の食い違い。いずれも読解だけで実行は未確認 (`cc-profiles.md` の各 11 項)。

---

## 9. 親の抜き取りと、子が迷った組

- **無作為 30 組** (`summary.json` の `spotcheck_sample`、seed 20260930、訂正前の集計で抽出): 親がカードと CC 前提表から読み直し、30 組とも判定に同意した。直した組は 0。
- **各 CC の上位 5 件** (訂正前の集計で 11 枚・40 組): 判定を変えた組は 0 で、留保を 3 点付けた。うち「abyss-ts-alloc-* × cicada・mvto の `minor`」は段 6 レビューが must-fix として指摘し、§10 で直した。
- **子が報告した迷い (主なもの):**
  - 2PL の lock を持たない多版 CC で、pending 版・inflight 版の spin 待ちを「lock 待ち」とみなして施錠待ちの上限を `minor` にした (abyss-lock-wait-timeout ほか)。厳しく読めば `no`。判定はそのまま。
  - 部品カード (Healing・BCC・AOCC の部品) は親の機構の前提ごと判定した。§10 の BCC の訂正もこの作法に合わせた。
  - cormcc-mediated-switching × oze は、切替の判定が常に false で経路が動いたことが無いが「既にある」とした。
  - tcm-read-only-transaction-optimization・msgt-epoch-readonly-versions・shirakami-safe-snapshot × si を「既にある」としたのは、SI が検証せずに snapshot を読むからで、SI は直列化可能でない。
    分離水準を下げるカード (tictoc-lower-isolation-levels) は規律 2 に当たるので段 A の候補にしない (本 wave の候補にも入っていない)。
  - mvto・ss2pl で「TPC-C の query から予定 key 集合を近似して渡す」を m4 と読んだ組がある (ding-thread-aware-reordering・tskd-tsdefer)。CC 前提表は TPC-C では事前の key 集合を CC に渡せないとしており、これらは `workload_ok = unknown` で候補に入っていない。

---

## 10. 段 6 の独立レビューと訂正

レビューは 2 巡行った (どちらも Codex、read-only、reasoning medium)。1 巡目のレビューは README の件数・表・比を正本 (`summary.json`・`judgments.jsonl`・`cards.json`) から数え直し、すべて一致した (転記の誤りは 0)。
候補の抽出・並べ方、CC 前提表と準備表の根拠 (proof の protocol 集合、EVOLVE-BLOCK の 3 source、各 CC の WORKLOADS、YCSB の操作列)、規律 2 の扱いにも問題は無かった。
所見は判定と定義の食い違いで、親はすべて real と判断した。2 巡目の焦点再レビューは、1 巡目の訂正の閉じ具合 (R2 closed、R1・R3 partial) と、同じ規則に当たる未訂正の組を指摘した。

| # | 所見 | 親の判断 |
|---|---|---|
| R1 (must-fix) | abyss-ts-alloc-mutex・-batched-atomic × cicada・mvto を `minor` にしたが、begin 時の timestamp の出所を替えるのは定義の「timestamp の決め方」の変更 | real。規則 T で直した |
| R2 (must-fix) | ssn-readonly-cstamp-at-snapshot × ermia を `fits` にしたが、read-only の commit 時刻を ++Lsn から snapshot 時刻に替える | real。規則 T で直した |
| R3 (should-fix) | essn-exclusion-test × ermia を `minor` にしたが、SSN の除外条件を替えて受理を広げる = 正しさの論拠の変更 | real。規則 A で直した |
| F1 (must-fix、2 巡目) | cicada-clock-boost-on-abort × mvto を `fits` にしたが、abort 後の timestamp の値を boost で変えるので規則 T に当たる | real。直し、この組に付いていた `more_natural_on` も外した |
| F2 (must-fix、2 巡目) | healing-transaction-healing・healing-access-cache × tictoc・mocc を「修復後に再検証する」として残したが、カードには stock の論拠だけで commit できる根拠が無い | real。規則 A で直した (親の除外理由はカードに根拠が無かった) |
| F3 (nit、2 巡目) | 台帳 fragment の「3 組」は所見 3 件・計 6 組の混同 | real。fragment を直した |

親は所見の組だけでなく、同じ型の組を洗い出して一貫して直した (定義の本文は変えていない。定義 §2 の「骨格」の当てはめを明文化したもの):

- **規則 T:** 取引に timestamp を割り当てる出所・値の決め方を替える組は `no` (`ts-scheme`)。同じ counter の同じ値を、排他の手段だけ替えて取るもの (abyss-ts-alloc-mutex × ermia・si。`++Lsn` を mutex で守る) は決め方を変えないので `fits` のまま。
  直した組 (8): abyss-ts-alloc-mutex・-atomic-add・-batched-atomic × cicada・mvto (6 組)、ssn-readonly-cstamp-at-snapshot × ermia、cicada-clock-boost-on-abort × mvto。
- **規則 A:** stock の validation が abort させていた取引を commit させ、その正しさを stock の CC の論拠だけでは言えない組は `no` (`other:correctness-argument`)。abort を早めるだけ・待ちを足すだけの変更は当たらない。部品カードは親の機構と同じ扱いにする。
  直した組 (16): essn-exclusion-test・essn-previous-edge-only-metadata・ssn-read-mostly-cold-read-skipping・ssn-safe-snapshot × ermia、bcc-essential-pattern-validation と部品 3 枚 × mocc、
  healing-false-invalidation-elimination × tictoc・mocc・cicada・mvto、healing-transaction-healing・healing-access-cache × tictoc・mocc。
- **洗い出しの方法:** 1 巡目は判定の note に「論拠・受理・timestamp・時刻・近似・値の一致・cstamp・clock・証明・直列化順」などの語を含む `fits`/`minor` の組と、BCC・ESSN・SSN・Healing の全カードの判定を並べて読んだ。
  2 巡目は、カードの機構・実装・正しさの欄に「abort せず・commit させ・修復・受理・clock・boost・採番・論拠・証明・serializab」などを含み、どこかの CC で `fits`/`minor` (既存除く) の 29 枚を読み直した。
- **規則に当たらないとして残した組 (理由):** essn-read-from-policy × ermia (SSN は commit 順と整合する read-from なら成り立つ、原典の SSN の論拠の範囲)、ssn-hierarchical-tracking × ermia (追跡を粗くする保守側の変更)、
  stov2-timestamp-splitting × tictoc・mocc (受理は広がるが、列の部分集合を 1 つのデータ項目と見れば stock と同じ OCC の論拠が当たる)、ccbench-read-phase-extension ほか待ち・abort の時機だけを変える組。
  2 巡目の Healing のように、親の「当たらない」判断が誤っていた例があるので、これらも攻撃の余地は残る。
- 訂正は子の生出力を変えずに `corrections-parent.jsonl` (24 行) に置き、集計が当てた。`judgments.jsonl` の該当組は `revision` 欄に元の値・理由コード・訂正の理由を持つ。訂正の向きは `fits`/`minor` → `no` だけ (正しさを弱める向きの訂正は無い)。
- **訂正の影響 (子の判定 → 訂正後):** 182 枚から入るのは 26 → 20 枚、全 CC で `no` は 145 → 151 枚。段 A 候補は mocc 18 → 13、cicada 16 → 13、ermia 16 → 13、tictoc 14 → 11、mvto 11 → 9 (si・ss2pl・oze は si 13、ss2pl 7、oze 10 で不変)。
  比は mocc 3.60 → 2.60、cicada 1.60 → 1.30、ermia 1.45 → 1.18、tictoc 1.40 → 1.10。**先頭の MOCC は変わらず、2 位以下は Cicada・ERMIA・TicToc の順になった。**

生出力は repo 外 `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md9-cards-by-protocol/codex/review-out.md` と `focus-out.md` (どちらも `tools/check_codex_output.py` rc=0)。
2 巡目の訂正後は再レビューを回していない。訂正後の件数・比は親が正本から再集計した (集計 script の検査を通過)。

---

## 付属ファイル

| file | 中身 |
|---|---|
| `definition.md` | 分類の事前定義 (commit `7648ea167`、判定前に固定) |
| `cc-profiles.md` | CC ごとの前提 (CCBench の実ソース、file:line つき) |
| `readiness.md` | CC × 準備 5 段の原票 (§0〜§3) と親の裁定 (§4) |
| `judgments.jsonl` | 判定の正本。カード × CC ごとに 1 行 (2,360 行)。欄: `card_id`・`cc`・`value`・`already_in_cc`・`workload_ok`・`reasons`・`minor_parts`・`basis_fields`・`note`・`revision` (親の訂正を当てた 24 組だけ非 null) |
| `corrections-parent.jsonl` | 段 6 の親の訂正 24 行 (組・規則 T/A・理由コード・理由) |
| `card-level.jsonl` | カードごとに 1 行 (295 行)。Silo 列 (`present`/`port-candidate`/`feasible`/`mismatch`)・`more_natural_on`・`natural_home` |
| `summary.json` | 集計 (件数・効果の内訳・段 A 候補の全件・副候補・理由コード・抜き取りの標本・訂正件数・訂正で外した `more_natural_on`) |

repo 外の資材 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md9-cards-by-protocol/`、sha256 は同 dir の `SHA256SUMS`): `make_chunks.py`・`judge-prompt.md`・`aggregate.py`・`inspect.py`・`spot.py`、
子の生出力 `judge-1〜5.jsonl`・`cardlevel-1〜5.jsonl`、原票 `cc-profiles-raw.md`・`readiness-raw.md`、レビューの prompt と出力 `codex/`。
