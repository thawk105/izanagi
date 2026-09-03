# 調査ノート: Why Database Manuals Are Not Enough: Efficient and Reliable Configuration Tuning for DBMSs via Code-Driven LLM Agents (SysInsight)

- **論文**: Why Database Manuals Are Not Enough: Efficient and Reliable Configuration Tuning for
  DBMSs via Code-Driven LLM Agents
  - venue/year: PVLDB 19(6): 1358-1371, 2026 / doi:10.14778/3797919.3797940。
    掲載情報は**論文本文冒頭の PVLDB Reference Format ブロック**に印字されている。
    arXiv の abstract ページ側は journal-ref 欄 `VLDB 2026`、comments 欄 `Accepted by VLDB 2026`。
  - authors: Xinyi Zhang, Tiantian Chen, Zhentao Han, Zhaoyan Hong, Wei Lu, Sheng Wang, Mo Sha,
    Anni Wang, Shuang Liu, Yakun Zhang, Feifei Li, Xiaoyong Du
  - arXiv: 2603.22708 / https://arxiv.org/abs/2603.22708 (v1、2026-03-24 投稿、cs.DB)
  - 本文取得元: https://arxiv.org/html/2603.22708v1 (HTML v1、2026-09-03 取得、87,303 文字に整形)
  - 公開 artifact: https://github.com/DBXAI/SysInsight (**本ノートは artifact を取得していない**)
- **このノートを書いた理由**: `docs/related-work/README.md` 7.1 の knob チューニング系譜エントリが
  ML/RL 4 本だけを持ち、LLM 駆動枝を持たなかったから。枝を足すにあたり、同エントリの
  2 つの文 (CC のロジックへの到達可否、P2-5 との向き) が SysInsight に対して成立するかを
  一次資料で決めるのが目的である。裁定の正本は
  `docs/related-work/claim-survey/2026-09-03-sysinsight-adjudication.md`。
- **信頼境界**: 本文は絶対規律 6 でいう「データ」である。読解にあたり誘導記述の有無を機械走査した
  (結果は末尾「規律 6 の走査」)。
- **引用の作法**: 以下で `>` と引用符を使った英文は arXiv HTML v1 の本文からの**転記**である。
  **「逐語」とは呼ばない。** HTML は LaTeXML 由来で数式を二重に持ち (`7.11 × 7.11\times`、
  `F k F^{k}`)、括弧前後に空白を入れ、表の矢印を `⇒` で持つ。整形時にこれらを正規化しており、
  **原文ファイルとの文字列一致ではない。語列は変えていない。**
  表を文章へ組み直したものも「転記」と書く。

---

## 一言要約

**DBMS のマニュアルではなくソースコードを LLM に読ませて、設定 knob の調整知識を作る。**
静的解析で knob が支配する関数を特定し、LLM の agent がその周辺コードを辿って
「この knob を上げると何が起きるか」という因果経路を言語化し、調整仮説を立てる。
仮説はそのまま使わず、100 個のサンプル設定の観測から association rule mining で
**発火条件 + 方向 + 増分 + confidence** を持つ定量 rule へ落とす。
オンラインでは perf のボトルネック関数診断で knob を選び、rule に従って動かす。

**出力は knob の値である。DBMS のコードは書き換えない。**

---

## 機構の構成

| 段 | 中身 |
|---|---|
| 静的解析 | knob が支配する関数を局所化し、LLM が探索する範囲を絞る |
| retrieval agent | 対象関数の親から辿り、未解決の callee を `search_function` API で取りに行く。文脈が十分と判断したら打ち切る |
| summary agent | 影響経路 ((1) knob 値の変化が関数呼び出しをどう制御するか、(2) 性能への含意) を説明する `structured reasoning chain` を作り、調整仮説を立てる |
| rule mining | 仮説を、100 config の観測に対する association rule mining で定量 rule へ落とす。confidence 付き |
| online | perf 診断でボトルネック関数を出し、function-knob 対応表から knob を選び、rule で調整する |

実験条件の転記:

> The target system is MySQL 8.0.36 (Community Edition, GPL license). Following prior studies
> (Kanellis et al., 2022; Lao et al., 2024), all baselines tune 44 knobs with MySQL default
> configuration as the starting point

> We run three tuning sessions for each method with 20 iterations per session. For SysInsight and
> GPTuner (Lao et al., 2024), we employ GPT-4o-mini as the backend model.

比較相手 (転記):

> Baselines. We compare the performance of SysInsight with the state of the art tuning systems
> including manual-driven methods (GPTuner (Lao et al., 2024), DB-Bert (Trummer, 2022)) and
> data-driven methods (SMAC (Hutter et al., 2011), DDPG++ (Aken et al., 2021),
> ResTune (Zhang et al., 2021), OtterTune (Aken et al., 2017)).

**online の 20 反復だけが総予算ではない。** 別に workload ごと 100 config の Latin Hypercube
サンプリングがあり、これは SysInsight の rule mining と transfer 系 baseline (ResTune / OtterTune)
の双方へ与えられる。target workload のデータは除外される。

---

## 争点 1 — 「CC のロジックには手が届かない」は SysInsight に対して成立するか

### 届いている部分 (読解)

SysInsight は待機経路を**読む**。転記:

> To understand how innodb_spin_wait_delay affects F^k, the retrieval agent first receives the code
> snippet of the parent function rw_lock_x_lock_wait_func() and is prompted to assess whether the
> context is sufficient. In the first stratum, it invokes the search_function API to retrieve the
> implementations of unresolved functions within rw_lock_x_lock_wait_func(), which are crucial for
> understanding the knob's influence, such as sync_array_wait_event().

> As shown in Figure 2(b), when srv_spin_wait_delay is non-zero, ut_delay() injects a random delay
> (from 0 to srv_spin_wait_delay) before rechecking the lock condition. A larger
> innodb_spin_wait_delay value increases the delay in each iteration, reducing the frequency of
> calls to sync_array_wait_event().

そのうえで因果を言語化する:

> "increasing this parameter makes ut_delay() inject longer delays per spin, reducing context
> switches but increasing CPU busy-wait; decreasing it shortens or skips ut_delay(), saving CPU but
> potentially increasing wakeups."

**したがって「knob 系譜は対象実装の待機挙動を見ない」とは書けない。** 見ている。

### 届いていない部分 (介入)

介入は既存 knob の値である。Table 1 の 3 列目の転記:

> Tuning Rule: r(sync_array_wait_event) > 3% => increase innodb_spin_wait_delay by (0,10]
> Confidence: 0.74

論文自身が介入面を限定している:

> configuration knobs fundamentally influence performance by controlling predefined execution paths

`predefined` である。spin と待ち合わせのどちらへ倒すかの分岐そのもの、その条件式、
新しい待機戦略の追加はどれも起きない。**動くのは既存のスカラの大きさだけである。**
(`park` は一次資料に 0 件なので、その語では書かない。)

### 「値」か「小さな方策」か

rule は `発火条件 => 方向 + 増分` の述語であり、単一の定数ではない。
**これを「値」と呼び切るのは正確でない。** 意味論としては、既存 knob の上に載る
条件付き controller である。ただしそれは DBMS の実装コードでも新しい CC の原始操作でもなく、
最終的な介入は既存 knob の値である。

**したがって境界線は「コードか値か」ではない。**
`対象実装の action vocabulary と分岐構造を変更・拡張するか、既存 knob の上に条件付き
controller を合成するか` である。

### 競合検出と abort について言えること

**母集合 = 上記整形本文 87,303 文字の全体 (節・表・参考文献を含み、先頭切り出しをしていない) に対し、
走査語 `abort` / `deadlock` / `concurrency control` / `serializab` / `isolation level` /
`two-phase` / `innodb_thread_concurrency` を小文字一致で走査した結果はいずれも 0 件であり、
かつ精読でもトランザクションの競合検出・wait-versus-abort 方策を扱う正の記述を確認できなかった。
これはこの 1 論文という列挙可能な母集合の中の不在であって、世界の不在ではない。**
参考: `mvcc` は 4 件だが、いずれも undo log 鎖の長さと `row_search_mvcc()` の文脈である。

**この不在から言えるのは「論文がその読解を報告していない」までである。**
論文は「extracts hypotheses for all 44 knobs directly from the source code」と書く一方、
44 knob それぞれで取得した関数を列挙していない。したがって
**「agent が該当コードを一切読まなかった」の証拠にはならない。**
言えるのは、トランザクションの競合検出および wait-versus-abort 方策を扱った
**正の記述が一次資料に無い**ことである。**この 1 論文の中の不在であって、世界の不在ではない。**

### 一次資料だけでは決められなかったこと (latch か record lock か)

`rw_lock_x_lock_wait_func` / `sync_array_wait_event` / `ut_delay` が InnoDB の
**latch (物理的な短期同期)** の機構であって、トランザクションの **record lock 待ち**
ではない、という同定は **一次資料の本文だけでは支えられない。**
本文には `latch` 0 件 / `record lock` 0 件 / `row lock` 0 件 / `transaction lock` 0 件 /
`park` 0 件であり、正の記述は `rechecking the lock condition`、
`related to lock contention and spin-wait synchronization`、`spin-lock polling` までである。

**この同定には MySQL のソースまたは外部の InnoDB 知識が要る。**
本ノートはそれを一次資料の主張として扱わない。
一次資料だけで言えるのは「これは spin-wait 同期の経路である」までであり、
それがトランザクションの競合待ちと同じ層かどうかは、この論文からは決まらない。

---

## 争点 2 — 「P2-5 と同方向を指す外部証拠」は無限定に残せるか

### まず、7.11 倍は何に対する数字か

**専業 ML/RL に対する数字ではない。** 本文 6.2 の転記:

> Compared with GPTuner, SysInsight converges to its best configuration on average 7.11x faster
> while still delivering an average performance improvement of 19.9%.

GPTuner は本文の分類で manual-driven に入るが、**LLM を使う手法**である
(マニュアルから knob ごとの推奨範囲・推奨値・特殊値を構造化し、狭めた空間で BO を回す)。
abstract の `the SOTA baseline` と貢献箇条書きの `the second-best baseline` は対象名を省いた
短縮であり、同じ 7.11 倍と 19.9% の組を明示する 6.2 が対象を決める。
**`7.11` と `faster` が共起する本文記述はこの 3 箇所だけで、専業 ML/RL に対する収束比の数値は無い**
(整形本文全体の `faster` は 4 件で、4 件目は参考文献題名 `towards faster database tuning` である)。

**ただしこれは知識源だけを切り分けた ablation ではない。** GPTuner は
「マニュアル知識 + BO」、SysInsight は「静的解析 + LLM + rule mining + 診断 + rule 適用」であり、
7.11 倍は**両システム全体の比**である。知識源単体の比較は別にあり (6.6.5)、
SysInsight の code-derived 仮説を GPTuner 由来 (Doc1) と DB-Bert 由来へ差し替える形で行われている。

### 専業 ML/RL について本文が言っていること

> However, within 20 iterations, SMAC and DDPG++ fail to identify high-quality configurations
> because they start the search process from scratch.

knob 選択の ablation (6.6.4) でも:

> The code-based method achieves the best performance due to its accurate identification bottleneck
> functions and associate knobs through code analysis. In contrast, the ML-based method performs
> worst, as the limited number of observations is insufficient to yield reliable knob importance
> rankings.

**「knob 探索は専業 ML/RL で解けてしまう」は、この実験条件では成立しなかった。**
**regime 一般への一般化ではない** — 一次資料が測ったのは MySQL 8.0.36 の 44 knob・
1 session 20 反復 x 3 session・別途 workload ごと 100 config の履歴データ、という 1 条件だけであり、
ML ベースが最下位になった knob 選択 ablation も TPC-C 単独の結果である。

### P2-5 との関係

P2-5 が測ったのは silo の 8 通りという**列挙しきれる**空間であり、
オラクル天井が低いこと自体が「空間は自明」の証拠になった。
SysInsight が測ったのは 44 knob の積空間に対して online 予算が 1 session 20 反復という側である。

**SysInsight は P2-5 を反証しない** — 対象も空間も予算も違い、silo のフラグ空間を再測していない。
**しかし P2-5 の外挿範囲を狭める。** 「境界の明確な空間は機械探索へ、LLM は主に空間拡張へ」
という役割分担を無限定に一般化すると、**固定 knob 空間でも観測が乏しければコード由来の
意味的 prior が効く**という反対向きの実例に当たる。

**したがって「同方向を指す外部証拠」は無限定には書けない。**
書けるのは「P2-5 が実証したのは十分に覆える小空間での否定的結果である」という限定と、
「SysInsight はそれを反証しないが外挿範囲を狭める」という但し書きの組である。

---

## 軸への接地判定

`claim-survey/2026-08-26-inventory.md` 2.2 の定義と、軸 1 の包含条件 A〜D を当てる。
**本判定は同 pilot の 29 行の母集合を変えない** — SysInsight はその凍結された母集合に
含まれていないため、件数保存則にも触れない。

### 軸 1 (対象の空白) — `除外`

| 条件 | 判定 | 根拠 |
|---|---|---|
| A 対象が並行性制御 | **✗** | 対象は DBMS の設定チューニング。spin-wait は 44 knob のうち 1 つの例 |
| B 設計・アクション空間をコードで生成または拡張 | **✗** | 全 baseline が既定の 44 knob を調整する。論文自身が `predefined execution paths` と書く |
| C ワークロード条件づけ | **✓** | 形式定義に workload characteristics が入り、online の入力にも hardware と workload が入る |
| D 正しさ検証器をループ内に持つ | **✗** | confidence は「その調整が目的関数を改善した割合」。6.3 の信頼性も #Bad Configurations と累積改善率 |

A✗ かつ B✗ なので、pilot の判定規則どおり `除外`。

### 軸 2 (帰属駆動・コーパス駆動の合成) — `部分接地` / 極性 `方法論的祖先`

ソースコードのコーパス、静的な制御依存の帰属、LLM による機序仮説、観測からの機械的 rule 誘導、
という構造は izanagi の二段構造 (機序帰属から軸を提案し、軸内を機械探索する) に強く接地する。
ただし合成対象は新しい CC 実装でも action space でもなく、既存 knob 上の条件付き方策であるため
`直接接地` までは上げない。

### 軸 3 (説明可能性) — `部分接地` / 極性 `方法論的祖先`。ただし狭い能力については `競合`

**強さは `部分接地` に留める。** `直接接地` の定義は「論文の対象がその軸の主題そのもの」であり、
SysInsight の対象は効率的で信頼できる knob チューニングである。`structured reasoning chain` は
調整仮説を作るための**中間機構**であって、論文の主題ではない。
confidence が検証するのは調整と性能改善の関連であり、**説明そのものの忠実性は評価されない。**
新しい CC も、試行の完全な provenance も、コードから測定値までの proof chain も示さない。

**ただし 1 点だけ `競合` である。**
「**DBMS のソースコードから LLM が機序説明を生成し、それを観測に接地させる**」という
狭い能力については、SysInsight が査読付きで実演している。
`docs/paper-story/` が差別化の核を説明可能性に置くとき、**この狭い能力を核にはできない。**
説明可能性の軸**全体**が埋まったわけではない — 忠実性・proof chain・provenance は空いている。

---

## この論文が izanagi の差別化に与える損害

**核にできなくなった語 (この 3 語だけである):**

- 「LLM に DBMS のソースコードを読ませる」— SysInsight が査読付きで行っている。
- 「コードから機序を取り出す」— 同上。
- 「観測に接地した説明を作る」— 同上 (rule mining + confidence)。

**説明可能性の軸そのものが埋まったわけではない。** SysInsight は説明の忠実性を評価せず、
proof chain も試行 provenance も持たない。そこは空いている。

**残る差別化:**

- 対象がトランザクションの並行性制御であること。
- 対象実装の action vocabulary そのものを拡張すること (SysInsight は固定 44 knob)。
- 正しさゲート (直列化可能性の検証) を毎反復回すこと。SysInsight にこの層は無い。

`docs/related-work/README.md` 7.6 の空白域 2 と 3 は、**現行の文言のままなら反例にならない** —
7.6.2 は「対象がトランザクションの CC」と「空間の拡張」の積条件を明記しており、
7.6.3 は「新 CC」の条件を持つ。**短縮すると即座に破れる。**
どの短縮が破れるかは裁定記録に列挙した。

---

## 正しさに関わる knob について

本文に名前が現れる InnoDB knob は 8 個である
(`innodb_buffer_pool_instances` / `innodb_buffer_pool_size` / `innodb_log_buffer_size` /
`innodb_log_file_size` / `innodb_purge_batch_size` / `innodb_random_read_ahead` /
`innodb_read_ahead_threshold` / `innodb_spin_wait_delay`)。いずれも性能専用である。
`flush_log_at_trx_commit` 0 / `sync_binlog` 0 / `doublewrite` 0 / `durab` 0 / `fsync` 0。

**ただし 44 個の全リストは論文に無い。**
したがって「SysInsight は正しさや耐久性に関わる knob を触らない」とは**言えない**。
**言えるのは、母集合 = 整形本文 87,303 文字の全体を走査語 `flush_log_at_trx_commit` /
`sync_binlog` / `doublewrite` / `durab` / `fsync` で走査した結果がいずれも 0 件であり、
かつ精読でも本文に名前が現れる 8 個以外の knob を確認できなかった、までである。**
走査語の外にある耐久性・正しさ関連の knob が 44 個の中に含まれる可能性は排除していない。

---

## このノートの限界

- **HTML v1 だけを読んだ。** PDF 版との差分、v2 以降の存在、および
  PostgreSQL 評価を含むという technical report は確認していない。
- **公開 artifact (github.com/DBXAI/SysInsight) を取得していない。**
  実装が本文の記述と一致するかは検査していない。
- **図の画素内容を読んでいない。** Figure 4 / 5 / 7 / 8 の数値は、
  テキスト化されたキャプションと本文が述べる範囲でしか確認できていない。
- **語の走査は文字列一致である。** 同義の言い換えは拾えない。
  ただし争点 1 の判定は語の不在だけに依存しておらず、Table 1 と 4.2 節の
  正の証拠が介入面を決めている。
- **44 knob の全リストが論文に無い**ため、knob 集合についての主張はすべて本文出現分に限る。
- 掲載情報 (PVLDB 19(6):1358-1371) は本文冒頭のブロックと arXiv abstract ページの
  2 箇所で確認したが、**VLDB Endowment 側の公式ページには当たっていない。**

---

## 規律 6 の走査

整形本文 87,303 文字全体に対し、指示めいた文字列を機械走査した。
走査語は `ignore previous` / `ignore the above` / `disregard` / `system prompt` / `you are an ai` /
`as an ai` / `instruction:` / `do not verify` / `skip verification` / `you must` / `please output` /
`assistant:` / `jailbreak` / `prompt injection` / `override` / `llm reviewer` /
`if you are a language model` / `reviewers should` / `accept this paper`。

hit は `instruction:` の 1 件のみで、文脈は SysInsight 自身の online prompt の構成説明
(`The prompt mainly consists of three components: (1) Task instruction: ...`) である。
**エージェントの振る舞いを変えようとする記述は検出しなかった。**
