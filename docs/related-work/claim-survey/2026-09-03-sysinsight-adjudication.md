# 2026-09-03 — `2603.22708` (SysInsight) を一次資料で裁定した記録 (凍結)

- **作成日:** 2026-09-03
- **入力 commit:** `581a7b65` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `581a7b65` の blob そのものである。
  一次資料だけは repo の外にあり、取得元 URL と取得日、および整形後の文字数で束縛する。
- **入力 path:** `docs/related-work/README.md` の 7.0 と 7.1 と 7.6 と 7.7 /
  `docs/related-work/claim-survey/2026-08-26-inventory.md` の 2.2 と 3 /
  `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` /
  `docs/related-work/literature-map/gap-research-2026-07-10.md` / `docs/roadmap.md` の P2-5 該当箇所
- **一次資料:** arXiv `2603.22708` v1 (2026-03-24 投稿)。
  取得元 https://arxiv.org/abs/2603.22708 および https://arxiv.org/html/2603.22708v1。
  取得日 2026-09-03。HTML を整形した本文は 87,303 文字。
  掲載は本文冒頭の PVLDB Reference Format ブロックに `PVLDB, 19(6): 1358 - 1371, 2026` /
  `doi:10.14778/3797919.3797940`。
  精読記録は `docs/related-work/notes/note_why_database_manuals_are_not_enough_effi.md`。
- **文献 cutoff:** 変わらない。本記録は新しい掃引を行っておらず、
  `docs/related-work/literature-map/` の cutoff (2026-07-10) を動かさない。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 何を決めたか、何を決めていないか

**決めたこと:** `docs/related-work/README.md` 7.1 の knob チューニング系譜エントリが持つ
2 つの文について、一次資料を読んで成否を決めた。あわせて同エントリへ LLM 駆動枝
(DB-BERT / GPTuner / SysInsight) を足し、判定タグを `引用元` から `引用元`+`外部補強` へ変えた。

**決めていないこと:**

- **軸 1 の検索記録の成熟度は `RW1` のまま動かない。** 本記録は 1 件の一次資料を読んだだけで、
  索引・検索式・母集合の登録 (7.7.4) を一切行っていない。**これは新しい検索ではない。**
- **本記録は新しい世界の不在を一切作らない。** 本記録が自分で測って書く「無い」は、すべて
  この 1 論文という列挙可能な母集合の中の不在 (7.7.2 でいう内部の不在) である。
- **`2026-08-26-inventory.md` の軸 1 分類 pilot の 29 行を変えない。**
  SysInsight はその凍結された母集合に含まれていないため、件数保存則にも触れない。
  本記録が下す軸判定は、pilot の表の外にある 1 件についての新しい判定である。
- **`docs/paper-story/` の版は書き換えていない。** 凍結物なので、
  確定したことは `docs/paper-story/README.md` の
  「最新スナップショット以後に確定したこと」から指す。
- **`docs/related-work/README.md` 7.6 の空白域は動かしていない。** 現行の文言のままなら
  SysInsight は反例にならない (§4.3)。破れるのは短縮した場合だけである。
- **実装面の差分はゼロである。** コード・テスト・script・機械設定を一切変えていない。

## 1. 判定に使った規則

- 争点の成否は、一次資料に**正の記述があるか**で決める。語の不在だけを根拠にしない。
- 内部の不在を書くときは母集合と走査語を同じ場所に置く (7.7.2)。
- 軸判定は `2026-08-26-inventory.md` の pilot が定めた包含条件 A〜D と判定規則をそのまま使う
  (規則を後から変えると同じ表の他の行と比べられなくなる)。

**引用の性質について。** 本記録と精読ノートで `>` を使った英文は arXiv HTML v1 からの**転記**であり、
**「逐語」ではない。** HTML は LaTeXML 由来で数式を二重に持ち (`7.11 × 7.11\times`、`F k F^{k}`)、
括弧前後に空白を入れ、表の矢印を `⇒` で持つ。整形時にこれらを正規化した。
**原文ファイルとの文字列一致ではない。語列は変えていない。**

---

## 2. 争点 1 — 「CC のロジック (競合検出・待機・abort の判断構造) には手が届かない」

### 2.1 判定

**現行文は無限定では成立しない。** ただし壊れ方は 1 箇所ではなく、
「待機」の扱いを二層に割らなければ正しく書けない。

| CC ロジックの三要素 | 読解 (論文が報告する範囲) | 介入 (論文が報告する範囲) |
|---|---|---|
| 競合検出 | **正の記述なし** | **正の記述なし** (44 knob の全リストが論文に無いので `なし` とは断定できない) |
| 待機 | **届いている** (`rw_lock_x_lock_wait_func` → `sync_array_wait_event` / `ut_delay`) | **既存 knob の値だけ** |
| abort | **正の記述なし** | **正の記述なし** (同上) |

**確実に言える介入の境界は「対象実装の action vocabulary とコードを拡張せず、既存 knob へ
介入する」までである。** 個々の CC 要素への介入の有無は、44 knob が列挙されていない以上、
この論文からは決まらない。

### 2.2 届いている根拠 (正の証拠)

> To understand how innodb_spin_wait_delay affects F^k, the retrieval agent first receives the code
> snippet of the parent function rw_lock_x_lock_wait_func() and is prompted to assess whether the
> context is sufficient. In the first stratum, it invokes the search_function API to retrieve the
> implementations of unresolved functions within rw_lock_x_lock_wait_func(), which are crucial for
> understanding the knob's influence, such as sync_array_wait_event().

> As shown in Figure 2(b), when srv_spin_wait_delay is non-zero, ut_delay() injects a random delay
> (from 0 to srv_spin_wait_delay) before rechecking the lock condition.

**したがって「knob 系譜は対象実装の待機挙動を見ない」とは書けない。**

### 2.3 届いていない根拠 (論文自身の限定)

> configuration knobs fundamentally influence performance by controlling predefined execution paths

介入の実体は Table 1 の 3 列目である。転記:

> Tuning Rule: r(sync_array_wait_event) > 3% => increase innodb_spin_wait_delay by (0,10]
> Confidence: 0.74

`predefined` である。spin と待ち合わせのどちらへ倒すかの分岐そのもの、その条件式、
新しい待機戦略の追加は起きない。動くのは既存のスカラの大きさだけである。

### 2.4 「値」と呼び切れない点

rule は `発火条件 => 方向 + 増分` の述語であり、単一の定数ではない。
意味論としては既存 knob の上に載る条件付き controller である。
**したがって境界線を「コードか値か」で引くと脆い。**

**引き直した境界線:**
`対象実装の action vocabulary と分岐構造を変更・拡張するか、既存 knob の上に条件付き
controller を合成するか`。

### 2.5 競合検出と abort について言えることの上限

**母集合 = 整形本文 87,303 文字の全体 (節・表・参考文献を含み、先頭切り出しをしていない) に対し、
走査語 `abort` / `deadlock` / `concurrency control` / `serializab` / `isolation level` /
`two-phase` / `innodb_thread_concurrency` を小文字一致で走査した結果はいずれも 0 件であり、
かつ精読でもトランザクションの競合検出・wait-versus-abort 方策を扱う正の記述を確認できなかった。
これはこの 1 論文という列挙可能な母集合の中の不在であって、世界の不在ではない。**
参考: `mvcc` 4 件 (undo log 鎖と `row_search_mvcc()` の文脈) / `lock_wait` 2 件。

**この不在から「agent が該当コードを読まなかった」は導けない。**
論文は `extracts hypotheses for all 44 knobs directly from the source code` と書く一方、
44 knob それぞれで取得した関数を列挙していない。
**言えるのは「トランザクションの競合検出および wait-versus-abort 方策を扱った正の記述が
一次資料に無い」までである。** これはこの 1 論文の中の不在であり、世界の不在ではない。

### 2.6 一次資料だけでは決められなかったこと

`rw_lock_x_lock_wait_func` / `sync_array_wait_event` / `ut_delay` が InnoDB の
**latch (物理的な短期同期)** の機構であって、トランザクションの **record lock 待ち**
ではない、という同定は **一次資料だけでは支えられない。**
本文には `latch` 0 / `record lock` 0 / `row lock` 0 / `transaction lock` 0 / `park` 0 であり、
正の記述は `rechecking the lock condition` / `related to lock contention and spin-wait
synchronization` / `spin-lock polling` までである。

**この同定には外部の InnoDB 知識が要る。本記録はそれを一次資料の主張として採らない。**
一次資料だけで言えるのは「これは spin-wait 同期の経路である」までであり、
それがトランザクションの競合待ちと同じ層かどうかは、この論文からは決まらない。

### 2.7 落としてはならない限定

現行文を書き換えたあと、**次の 3 つはどれを落としても反例が立つ。**

1. **「手が届かない」の対象は介入であって読解ではない。** これを落として
   「knob 系譜は CC の内部を見ない」と書くと、SysInsight の 4.2 節が直ちに反例になる。
2. **届いている待機は spin-wait 同期の経路であり、トランザクションの競合待ちと
   同じ層だとは一次資料からは決まらない。** これを落として「knob 系譜は CC の待機に届く」と
   書くと、今度は SysInsight を過大評価する。
3. **競合検出と abort について言えるのは「正の記述が無い」までで、「読んでいない」ではない。**
   これを落として「knob 系譜は abort を読まない」と書くと、母集合の外へ出た断定になる。

**依頼が想定した「届かないのはプロトコルの書き換えだけである」という一限定は成立しない。**
一次資料が正に示すのは特定の spin-wait 経路の読解と値調整だけであり、
競合検出・abort の読解は立証されていない。限定は 1 つでなく上記 3 つである。

---

## 3. 争点 2 — 「P2-5 と同方向を指す外部証拠」

### 3.1 判定

**無限定では残せない。** ただし理由は依頼が想定したものと異なる。

### 3.2 7.11 倍は何に対する数字か

**専業 ML/RL に対する数字ではない。** 本文 6.2 の転記:

> Compared with GPTuner, SysInsight converges to its best configuration on average 7.11x faster
> while still delivering an average performance improvement of 19.9%.

GPTuner は本文の分類では manual-driven だが、**LLM を使う手法**である。
abstract の `the SOTA baseline` と貢献箇条書きの `the second-best baseline` は対象名を省いた
短縮であり、同じ 7.11 倍と 19.9% の組を明示する 6.2 が対象を決める。
**`7.11` と `faster` が共起する本文記述はこの 3 箇所だけで、専業 ML/RL に対する収束比の数値は無い**
(整形本文全体の `faster` は 4 件で、4 件目は参考文献題名 `towards faster database tuning` である)。

**ただしこれは知識源だけを切り分けた ablation ではない。** GPTuner は「マニュアル知識 + BO」、
SysInsight は「静的解析 + LLM + rule mining + 診断 + rule 適用」であり、
7.11 倍は**両システム全体の比**である。知識源単体の比較は 6.6.5 に別にある。

### 3.3 専業 ML/RL について本文が言っていること

> However, within 20 iterations, SMAC and DDPG++ fail to identify high-quality configurations
> because they start the search process from scratch.

knob 選択の ablation (6.6.4):

> The code-based method achieves the best performance ... In contrast, the ML-based method performs
> worst, as the limited number of observations is insufficient to yield reliable knob importance
> rankings.

**「knob 探索は専業 ML/RL で解けてしまう」は、この実験条件では成立しなかった。**
**regime 一般への一般化ではない** — 一次資料が測ったのは MySQL 8.0.36 の 44 knob・
1 session 20 反復 x 3 session・別途 workload ごと 100 config の履歴データ、という 1 条件だけであり、
ML ベースが最下位になった knob 選択 ablation も TPC-C 単独の結果である。

### 3.4 予算の正確な記述

online の探索 horizon は 1 session あたり 20 反復 × 3 session である。
**ただしそれが総予算ではない。** 別に workload ごと 100 config の Latin Hypercube サンプリングが
あり、SysInsight の rule mining と transfer 系 baseline (ResTune / OtterTune) の双方へ与えられる。
target workload のデータは除外される。
したがって「20 << 空間」だけで regime を記述するのは不正確である。

### 3.5 P2-5 との関係の確定

P2-5 が測ったのは silo の 8 通りという**列挙しきれる**空間であり、
オラクル天井が低いこと自体が「空間は自明」の証拠になった。
SysInsight が測ったのは 44 knob の積空間に対して online 予算が乏しい側である。

- **SysInsight は P2-5 を反証しない。** 対象も空間も予算も違い、silo のフラグ空間を再測していない。
  **P2-5 の小空間での否定的結果を撤回する必要はない。**
- **しかし P2-5 の外挿範囲を狭める。** 「境界の明確な空間は機械探索へ、LLM は主に空間拡張へ」
  (roadmap §126) を無限定に一般化すると、**固定 knob 空間でも観測が乏しければコード由来の
  意味的 prior が効く**という反対向きの実例に当たる。

**したがって「同方向を指す外部証拠」は無限定には書けない。**
本記録が採る書き方は「P2-5 が実証したのは十分に覆える小空間での否定的結果である」という限定と、
「SysInsight はそれを反証しないが外挿範囲を狭める」という但し書きの組である。

### 3.6 併せて限定した行

現行エントリの **「Izanagi は knob 探索をしない (P2-5 で既反証)」** も P2-5 の射程を越えている。
P2-5 が反証したのは小さい列挙可能なフラグ空間における LLM 誘導の付加価値であって、
knob tuning 一般ではない。**「研究対象として採らない」と「P2-5 が何を反証したか」を分けて書く。**

---

## 4. 主張軸への影響

### 4.1 軸判定 (pilot の表の外にある新しい 1 件)

| 軸 | 強さ | 極性 | 根拠 |
|---|---|---|---|
| 軸 1 (対象の空白) | **除外** | — | A✗ (対象は設定チューニング) かつ B✗ (`predefined execution paths`、44 knob を拡張しない)。C✓ / D✗ |
| 軸 2 (帰属駆動・コーパス駆動の合成) | **部分接地** | 方法論的祖先 | コーパス = ソースコード、静的な制御依存の帰属、LLM の機序仮説、観測からの機械的 rule 誘導。ただし合成対象は既存 knob 上の条件付き方策 |
| 軸 3 (説明可能性) | **部分接地** | 方法論的祖先 (狭い能力についてだけ **競合**) | `structured reasoning chain` / causal link / hypothesis / 定量 rule / confidence を持つが、論文の主題は knob チューニングであり説明は**中間機構**。説明の忠実性・proof chain・provenance は評価しない |

軸 1 の D を ✗ とした根拠: confidence の定義は「その調整が目的関数を改善した割合」であり、
6.3 の信頼性指標も `#Bad Configurations` と累積改善率である。
**直列化可能性・isolation・deadlock freedom を判定しない。**

### 4.2 軸 3 — 埋まったのは狭い能力だけで、軸全体ではない

`docs/paper-story/` は差別化の核を説明可能性に置いている。
**SysInsight が埋めたのは「DBMS のソースコードから LLM が機序説明を生成し、観測に接地させる」
という狭い能力であって、説明可能性の軸全体ではない。**
強さは `部分接地` であり、`競合` はこの狭い能力にだけ付く (§4.1 の表)。

**核にできなくなった語:** 「LLM に DBMS のソースコードを読ませる」/「コードから機序を取り出す」/
「観測に接地した説明を作る」。**この 3 語だけである。**
説明の忠実性、proof chain、試行 provenance は SysInsight が評価しておらず、依然として空いている。

**残る差別化:** 対象がトランザクションの並行性制御であること / 対象実装の action vocabulary
そのものを拡張すること / 正しさゲート (直列化可能性の検証) を毎反復回すこと。

ただし SysInsight の confidence が検証するのは調整と性能改善の関連であって、
LLM の因果説明そのものの忠実性ではない。新しい CC も、試行の完全な provenance も、
コードから測定値までの proof chain も示さない。

**この件の後続処理は本記録では閉じない。** `docs/paper-story/` は凍結物であり、
差別化の核の書き換えは本 wave の scope 外である。worklog の「次の一手」へ送る。

### 4.3 7.6 の空白域 — 現行文言は生き残る。短縮すると破れる

- **7.6.2** は「対象がトランザクションの CC であること」と「空間の拡張であること」の
  積条件を明記している。SysInsight は 44 knob を拡張せず、DBMS のコードを書き換えないので、
  **現行文言のままなら反例にならない。**
  破れる短縮: **「LLM に DBMS のコードを読ませる研究はない」「コード内部から方策を作る研究はない」。**
- **7.6.3** は「新 CC + 速さの理由 + 試行記録」の積条件を持つので、**現行文言のままなら反例にならない。**
  破れる短縮: **「速さの理由 + 試行由来の知識」だけを差別化として書くこと。**

### 4.4 採録

`docs/related-work/README.md` 7.1 の既存エントリへ LLM 駆動枝を足し、
判定タグを `引用元` から **`引用元`+`外部補強`** へ変え、7.0 の逆引き索引の該当行を更新する。

**`外部補強` の接地は「LLM 由来方策の性能観測による事前検証」である。**
SysInsight は LLM が出した調整仮説をそのまま使わず、観測から定量 rule へ落として
confidence を付けてから使う。C3 の転記:

> To ensure safety and effectiveness, tuning decisions must be grounded in real system behavior and
> verifiable prior to deployment. Yet both data-driven models and LLMs offer no intrinsic guarantees
> of correctness or generalizability

**補強するのは性能の信頼性であって直列化可能性ではない。**
この限定を接地欄から落としてはならない。落とすと、izanagi の正しさ verifier と同形の
外部証拠があるかのように読める。

---

## 5. この記録の限界

- **一次資料 1 件しか読んでいない。** 網羅率について何も言わない。
- **HTML v1 だけを読んだ。** PDF 版との差分、v2 以降の存在、PostgreSQL 評価を含むという
  technical report は確認していない。
- **公開 artifact (github.com/DBXAI/SysInsight) を取得していない。**
  実装が本文の記述と一致するかは検査していない。
- **図の画素内容を読んでいない。** Figure 4 のキャプションに比率は無かったが、
  図中に別の数値がある可能性は排除していない。
- **44 knob の全リストが論文に無い。** したがって「SysInsight は正しさ・耐久性に関わる knob を
  触らない」とは言えない。言えるのは「本文に現れる 8 個は性能専用であり、
  母集合 = 整形本文 87,303 文字の全体を走査語 `flush_log_at_trx_commit` / `sync_binlog` /
  `doublewrite` / `durab` / `fsync` で走査した結果がいずれも 0 件であり、かつ精読でも本文に
  名前が現れる 8 個以外の knob を確認できなかった」まで。走査語の外にある耐久性・正しさ関連の
  knob が 44 個の中に含まれる可能性は排除していない。
- **語の走査は文字列一致である。** 同義の言い換えは拾えない。ただし争点 1 の判定は
  語の不在だけに依存しておらず、Table 1 と 4.2 節の正の証拠が介入面を決めている。
- **掲載情報は本文冒頭のブロックと arXiv abstract ページの 2 箇所でしか確認していない。**
  VLDB Endowment 側の公式ページには当たっていない。
- **本記録の敵対検査は 2 本の独立コンテキストで行った** (一次資料忠実性レンズ / regime と
  主張接地レンズ)。両者の指摘のうち、親の当初裁定を壊したものは本文へ取り込んである。
  取り込みの判断は親が行っており、**第三者による再監査は受けていない。**
