# 2026-08-27 — 軸 1 分類 pilot に残る `要裁定` 3 件を一次資料で解いた記録 (凍結)

- **作成日:** 2026-08-27
- **入力 commit:** `9ebd340b` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `9ebd340b` の blob そのものである
  (`docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` だけは本 wave が
  同 base の上に作った先行 commit の blob である)。
  一次資料は repo の外にあり、取得元 URL・取得日・整形後の文字数と SHA-256 で束縛する。
- **入力 path:** `docs/related-work/claim-survey/2026-08-26-inventory.md` の「3. 軸 1 の分類 pilot」 /
  `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` /
  `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` /
  `docs/related-work/README.md` の 7.0 と 7.1 と 7.3 と 7.6 と 7.7 /
  `docs/paper-story/2026-08-26.md` の §3 と §8 / `docs/paper-story/README.md`
- **一次資料:**

| arXiv ID | 版 | 取得元 | 整形後 | SHA-256 |
|---|---|---|---|---|
| `2404.13359` | v1 | `https://arxiv.org/abs/2404.13359` と `https://arxiv.org/html/2404.13359v1` | 80,867 文字 | `2c2ff59178a083fd38f0295a5852635a1c860df6f968ef55941acd38a7216e68` |
| `2512.18746` | v1 | `https://arxiv.org/abs/2512.18746` と `https://arxiv.org/html/2512.18746v1` | 78,687 文字 | `bd4461490e007c3138b751f9e9e961bab047cf404b139c7b8e0ac802b85533bf` |
| `2605.22721` | v1 | `https://arxiv.org/abs/2605.22721` と `https://arxiv.org/html/2605.22721v1` | 92,322 文字 | `80271cf7d871a5bc3c344b5c85c41333b94bc102170d1ab9ff5ed5f227891522` |

  取得日はいずれも 2026-08-27。**3 件とも v1 しか存在しない** (abs ページの版一覧で確認)。
  整形規則は「`<script>` と `<style>` の中身を除去 → 残りのタグを除去 → HTML 実体参照を
  unescape → 各行の前後空白を落とし空行を 1 本に畳む」であり、**先頭切り出しをしていない。**
  したがって arXiv の site 告知文のような本文以外の行も母集合に含まれる。

- **文献 cutoff:** 変わらない。本記録は新しい掃引を行っておらず、
  `docs/related-work/literature-map/` の cutoff (2026-07-10) を動かさない。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。書いた後は上書きしない。**
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 何を決めたか、何を決めていないか

**決めたこと:** `2026-08-26-inventory.md` の軸 1 分類 pilot が `要裁定` に残した 4 件のうち、
2026-08-26 に解けた `2604.09318` を除く残り 3 件について、一次資料を読んで包含条件を決めた。

| arXiv ID | pilot | 本記録 |
|---|---|---|
| `2404.13359` Declarative Concurrent Data Structures | `要裁定` (A が決められない) | **`直接接地` / 極性 `競合`** |
| `2512.18746` MemEvolve | `要裁定` (B が決められない) | **`部分接地` / 極性 `方法論的祖先`** |
| `2605.22721` DecentMem | `要裁定` (B が決められない) | **`除外`** |

**決めていないこと:**

- **軸 1 の検索記録の成熟度は `RW1` のまま動かない。** 本記録は 3 件の一次資料を読んだだけで、
  7.7.4 の母集合を全件処理していない。同 wave が
  `2026-08-27-axis1-search-preregistration.md` で契約を凍結したが、**検索は 1 本も実行していない。**
- **`要裁定` が 0 になったのは pilot 29 行の A/B についてだけである。**
  29 行全体を一次資料で再監査したことも、7.7.4 の検索母集合を処理したことも意味しない。
- **本記録は新しい世界の不在を一切作らない。** 本記録が自分で測って書く「無い」は、すべて
  この 3 論文という列挙可能な母集合の中の不在 (7.7.2 でいう内部の不在) である。
  **既存の世界側の不在の文 (§3 の 1 の「本調査では未発見」、7.6 の空白域) には触れない** —
  引くときは 7.7.3 の `RW1` が許す逐語引用に限り、出典節・掃引日 (2026-07-10)・監査前である旨を
  同じ場所に置く。**本記録がそれらを言い直したり、支持したり、強めたりすることはない。**
- **`docs/paper-story/2026-08-26.md` §8 の C-4 は、これで閉じない。**
- **`docs/paper-story/` の版は書き換えていない。** 凍結物なので、確定したことは
  `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」から指す。

## 1. 判定に使った規則

pilot が定めた包含条件と判定規則をそのまま使う (規則を後から変えると、同じ表の他の 26 行と
比べられなくなる)。

- **包含条件:** (A) 論文の対象が並行性制御である / (B) 設計・アクション空間そのものをコードで
  生成または拡張する / (C) ワークロード条件づけがある / (D) 正しさ検証器をループ内に持つ。
- **判定規則:** A✓ → `直接接地`。A✗ かつ B✓ → `部分接地`。A✗ かつ B✗ → `除外`。
  C と D は gate ではなく記録する属性である。
- **`要裁定` を不在側へ倒さない。**

### 1.1 A の読み方 — 「主題領域」であって「成果物の種類」ではない

3 件のうち `2404.13359` の A は、**規則の文言だけでは一意に決まらない。**
「論文の対象が並行性制御である」は、(i) その論文が主張を立てている主題領域に
トランザクションの並行実行制御が含まれるか、とも、(ii) 論文が作った成果物が並行性制御機構か、
とも読める。

**本記録は (i) を採る。理由は pilot 自身の先例である。**
pilot は `1905.08406` (Checking Robustness Against Snapshot Isolation) を `直接接地` と裁定した。
同論文の成果物は判定手続きであって CC 機構ではなく、B は ✗ である。それでも A✓ としたのは、
対象がトランザクション一貫性モデルの正しさだからである。pilot の 3.2 節はこの裁定を
「規則を満たすものを規則の外の直観で除外すると、分類が再現できなくなる」と説明している。

**すなわち (i) は本記録が新たに導入した読みではなく、pilot が既に採っている読みである。**

**この読みを一様に当てると、再監査が要る行がある。** §5.2 に記す。

## 2. `2404.13359` — Declarative Concurrent Data Structures

Aunn Raza, Hamish Nicholson, Ioanna Tsakalidou, Anna Herlihy, Prathamesh Tagore,
Anastasia Ailamaki (EPFL, Lausanne)。`cs.DB; cs.DS; cs.PL`、2024-04-20。

| 条件 | pilot (要約のみ) | 本記録 (一次資料) | 根拠 |
|---|---|---|---|
| A | `?` | **✓** | 生成物へ注入するのはトランザクションの並行性制御であり、評価単位もトランザクションである |
| B | ✓ | **✓ (ただし「生成」であって「拡張」ではない)** | CC のコードは生成されるが、Rösti が注入するプロトコルは 1 種に固定 |
| C | ✓ | **✓** | 宣言仕様が全ワークロードを閉じており、それを根拠に同期を削る |
| D | ✗ | **✗** | 正しさは構成による。検証器はループのどこにも無い |

判定は **`直接接地` / 極性 `競合`**。

### 2.1 A を ✓ とした根拠

Rösti の backend は CC を注入する。逐語:

> "Rösti injects concurrency control primitives in the DCDS IR after performing the logical
> optimizations phase. Currently, Rösti injects strict two-phase locking (S2PL)
> ( Bernstein et al., 1987 ) CC with NO_WAIT deadlock avoidance protocol."

生成されたデータ構造は実行時にトランザクションマネージャを持つ。逐語:

> "Each call to a data structure method from C++ user code data structure operation is a
> transactional scope. At the start of this method call, CDS calls begin_txn on the assigned
> transaction manager and receive a transaction object."

> "In S2PL CC with NO_WAIT, the data structure operation can call end_txn to either successfully
> commit at the end of the transaction block or abort and rollback where it fails to acquire a
> lock on resource."

評価は OLTP DBMS との比較であり、単位は毎秒トランザクション数である。逐語:

> "We compare Rösti with Proteus, which is a state-of-the-art in-memory OLTP DBMS ... Proteus
> employs MV2PL concurrency control with snapshot isolation"

> "Then, we report the throughput of each system in million transactions per second (MTPS) for
> each setup."

そして**性能上の勝因を、論文自身が並行性制御の特化に帰属させている。** 逐語:

> "In summary, Rösti outperforms in-memory DBMS due to the simple fact that it specializes
> concurrency control to the target workload, avoiding unnecessary synchronization which a DBMS
> couldn't, and reduces the total amount of work given the specialized generated data structure."

**§1.1 の (i) の読みでは、この論文の主題領域はトランザクションの並行性制御を含む。A✓ である。**

### 2.2 反対の読み (採らなかったもの) — 記録

段 3 の敵対相談は A✗ を構成した。**その構成は成り立つので、逐語で残す。**

論文が自分で述べる目的は、データ構造の生成である。

> "We aim to enable developers to create scalable concurrent data structures tailored to their use
> case with the same effort as designing a non-thread-safe data structure."

> "In this paper, we make the case for Declarative Concurrent Data Structures (DCDS), a framework
> for the automatic generation of concurrent data structures from a serial specification."

**この読み ((ii)、成果物の種類で判定する) を採ると、A✗ / B✓ / `部分接地` になる。**

**本記録が (ii) を採らなかった理由は 2 つである。**

1. §1.1 のとおり (ii) は pilot の `1905.08406` の裁定と矛盾する。同論文の成果物も CC 機構ではない。
2. 7.7.5 は「`要裁定` を不在側へ倒さない」と要求する。`競合` は候補が在る側、
   `部分接地 / 方法論的祖先` は在らない側である。境界例では在る側へ倒すのが規則に合う。

**(ii) を採る場合の件数は §4 に併記する。**

### 2.3 B を ✓ としたうえで、下位の区別を記録する理由

pilot の B は「生成または拡張」であり、どちらか一方で ✓ になる。DCDS は **生成する** —
逐次仕様から thread-safe な IR を作り機械語まで下ろす。

しかし **Rösti が注入する CC プロトコルは 1 種に固定である** (§2.1 の逐語 "Currently, Rösti
injects strict two-phase locking (S2PL) ... with NO_WAIT")。走行中にプロトコル空間を広げる経路は無い。

**ただし「固定」はフレームワークの性質ではなく Rösti の性質である。** DCDS の枠組み自体は
プロトコルを規定しない。逐語:

> "The specific CC algorithm used is not prescribed by the framework and is a choice left to the
> implementation of the framework."

すなわち正確には **「フレームワークは実装者による方式選択を許すが、Rösti の生成走行は
S2PL+NO_WAIT を自動選択も拡張もしない」** である。

**さらに、DCDS は izanagi の対象そのものを将来課題として名指ししている。** 逐語:

> "The most appropriate concurrency control algorithm depends on workload, such as optimistic CC
> for low-contention while pessimistic for high-contention workloads ... The DCDS framework will
> enable dynamic tracing of workload at runtime and then adapt the optimizations and CC mechanism
> accordingly."

**これは既知アルゴリズムの適応的な選択であって、新しい CC の合成ではない。**
同じく将来課題とされている物理最適化は、施錠のグルーピングと**取得順序の並べ替え**である。

> "The physical optimizer will operate on concurrent IR and optimize the injected CC operations;
> For example, by lock grouping across attributes and reordering lock acquisition statements to
> reduce the runtime cost of aborts."

### 2.4 C を ✓ とした根拠

DSL が「ワークロード・アプリケーション固有の要求」を宣言する場所を持つ。

> "The embedded DSL includes constructs and abstractions for attribute and function declarations
> in a typed manner, statements and expressions for defining a function body, and context for
> declaring workload- and application-specific requirements."

宣言が全操作を閉じていることを根拠に同期を削る。

> "Further, in contrast to DBMS, Rösti has complete knowledge of the workload and by construction,
> ensures that no other operation will be performed on the declared data structure. This enables
> Rösti to optimize and eliminate any unused attribute or functionality."

評価は YCSB の読み書き比と分布 (一様 / Zipfian) を振っている。

### 2.5 D を ✗ とした根拠

**正しさは構成によって得られており、検証器はループのどこにも無い。** 逐語:

> "The Logical Optimizer and Physical Optimizer only improve the performance of the resulting CDS;
> they are not necessary for correctness."

同論文が定義する correctness も、直列化可能性ではない。

> "In the context of this paper, correctness entails ensuring no race conditions, live- or
> dead-locks, and that conflicting concurrent operations do not produce inconsistent results."

### 2.6 語の全件走査 (母集合を併記した内部の不在)

整形本文 80,867 文字の全体 (節・表・参考文献を含み、先頭切り出しなし) に対する小文字一致の件数:

`concurrency control` 28 / `transaction` 79 / `abort` 7 / `workload` 24 / `oltp` 7 / `2pl` 3 /
`two-phase` 2 / `isolation` 2 / `snapshot isolation` 1 / `throughput` 3 / `verif` 1 /
`serializab` **0** / `mvcc` **0** / `linearizab` **0** / `model check` **0** / `tpc` **0** /
`many-core` **0** / `latency` **0** / `machine learning` **0** / `neural` **0**。

`llm` の 1 件は参考文献の著者名 `Aaron Ballman` の一部である。
`isolation` の 2 件は、1 件が ACID の説明、1 件が比較対象 Proteus の snapshot isolation である。

**すなわち、この論文には LLM も学習も進化探索も出てこない。** 自動化は宣言仕様に対する
コンパイラ最適化である。**この不在は、この 1 論文の中の不在である。世界の不在ではない。**

## 3. `2512.18746` — MemEvolve: Meta-Evolution of Agent Memory Systems

`cs.CL; cs.MA`。

| 条件 | pilot (要約のみ) | 本記録 (一次資料) | 根拠 |
|---|---|---|---|
| A | ✗ | **✗** | 対象は LLM エージェントの記憶機構。並行性制御は主題に無い |
| B | `?` | **✓** | モジュールの**実装コード**を LLM が診断に基づいて書き換える |
| C | ✗ | **✓** | タスク族ごとに進化させ、適合度はタスク集合上の実測である |
| D | ✗ | **△** | タスク成否はループ内にあるが、生成物の正しさを検証する器ではない |

判定は **`部分接地` / 極性 `方法論的祖先`**。

### 3.1 A を ✗ とした根拠 (語の全件走査)

整形本文 78,687 文字の全体に対する小文字一致の件数は、
`concurrency control` **0** / `concurrenc` **0** / `transaction` **0** / `serializab` **0** /
`isolation level` **0** / `mvcc` **0** / `throughput` **0** / `workload` **0** / `oltp` **0**。
`database` の 4 件はベクトルデータベースなど記憶実装の話である。

**A は正の証拠の不在ではなく、正の証拠の内容から ✗ である** — 論文が扱うのは
encode / store / retrieve / manage の 4 部品からなる記憶機構である。

### 3.2 B を ✓ とした根拠

**生成されるのは記憶の内容ではなく、記憶機構の実装コードである。** 逐語:

> "MemEvolve evolves the programmatic implementations of these modules in a model-driven fashion,
> using feedback from the agent's performance in the inner loop."

> "These variants differ in encoding strategies, storage rules, retrieval constraints, or
> management policies, yet all conform to the unified memory-system interface and remain
> executable by the agent."

書き換えは指定された実装箇所に限られる。

> "Conditioned on the defect profile ... a redesigned architecture is constructed by modifying only
> the permissible implementation sites within the modular interface, thereby ensuring compatibility
> and isolating architectural changes to the designated design space."

**これは pilot が `2509.19349` (ShinkaEvolve) と `2512.13857` (EvoLattice) に B✓ を与えたのと
同じ基準である** — 指定された穴の中でコードを合成する。語の上ではむしろこちらが直接的である。

**したがって B✓ は、pilot の他の行と同じ基準の適用であって基準の緩和ではない。**

### 3.3 C を ✓ とした根拠と、その限界

`workload` の語は 0 件である。しかし機構は、適合度をタスク集合上の実測 (性能・コスト・遅延の
3 次元) から取り、非優越ソートで親を選ぶ。論文はタスク族ごとの特化を明示している。

> "Memory systems evolved on TaskCraft are unlikely to transfer effectively to fundamentally
> different task families ... Nevertheless, MemEvolve enables the discovery of broadly applicable
> memory architectures within a shared task regime, while retaining the capacity for further
> task-specific adaptation when required."

**`workload` の語彙ではなく `task family` / `benchmark` の語彙で同じことを述べている、と読んだ。**
これは本記録の解釈であり、語の一致ではない。

### 3.4 D を △ とした根拠

タスクの成否 (ベンチマーク正解率) がループ内の適合度信号であり、変異体は
"remain executable by the agent" が要求される。**しかし生成された機構そのものの正しさを
検証する器は無い。** pilot が `2509.19349` に付けた `△` と同じ位置づけとする。

### 3.5 izanagi との関係 (軸 1 ではなく軸 2・軸 5 側)

診断 → 設計の 2 相は、izanagi の critic → coder と同型である。
軌跡の証拠から欠陥プロファイルを作り、それを条件に実装を書き換える。
**軸 1 に対しては `部分接地` にとどまる** — 対象が並行性制御ではないからである。

## 4. `2605.22721` — DecentMem (Self-Evolving Multi-Agent Systems via Decentralized Memory)

`cs.MA`。

| 条件 | pilot (要約のみ) | 本記録 (一次資料) | 根拠 |
|---|---|---|---|
| A | ✗ | **✗** | 対象はマルチエージェントの記憶。並行性制御は主題に無い |
| B | `?` | **✗** | 生成物は自然言語の記憶片と行動であり、設計空間を生成しない |
| C | ✗ | **✓** | 検索と pool 選択が実行中のタスクへ条件づけられる |
| D | ✗ | **△** | LLM 評価器が段階ごとに correctness を採点し router へ戻す |

判定は **`除外`**。理由コード: **生成対象が自然言語の記憶片と行動であって設計空間の生成でない。**

### 4.1 B を ✗ とした根拠 — 正の構造証拠で示す

**「設計空間を生成する記述が見つからなかった」ではなく、閉じた構造が本文に書かれている。**

- 記憶は固定された 2 pool (E-pool と X-pool) に分割される。
- X-pool が作るのは "an exploratory memory piece z_new for the current context" である。
- それを LLM へ渡して行うのは "executable action generation" である。
- タスク終了後、X-pool の記憶片は E-pool へ統合され X-pool は空へ戻る。
- 付録の完全な prompt 集合が要求する出力は、役割名・二択の routing・直接回答・
  下位タスクの JSON・評価の JSON であり、記憶機構のコードでも行動語彙の拡張でもない。

**したがって `除外` は不在側への横倒しではなく、正の証拠に基づく判定である。**

### 4.2 訂正 — 「router の重みは固定」は誤りである

**本 wave の親 brief は当初「固定 router 重み」を B✗ の理由に挙げたが、これは一次資料と食い違う。**
固定されているのは X-pool の重み 1.0 であり、E-pool の重みと選択確率は段階評価で更新される。

> "Meanwhile, w_{m,X-pool} = 1.0 remains fixed. In this way, successful exploitation increases
> reliance on the E-pool, while successful exploration prevents the router from over-committing
> to past experience."

**B✗ の根拠は §4.1 の閉じた構造であって、重みの固定性ではない。**
この訂正は段 3 の敵対相談が一次資料から構成したものである。

### 4.3 D を △ とした根拠

> "After execution, the full solution trajectory is evaluated stage by stage by an LLM evaluator."

> "Rather than scoring only the final answer, the evaluator assesses each stage in terms of
> correctness, allocation quality, intermediate coherence, and final integration."

**correctness を採点してループへ戻している。** 健全な正しさ gate ではないので ✓ には足りないが、
✗ でもない。`2509.19349` と同じ `△` とする。

### 4.4 7.4 の既存採録は動かさない

`2605.22721` は `docs/related-work/README.md` の 7.4 に `外部補強` として既に採録されている
(whiteboard の二 pool 構造の理論裏付け)。**本記録はその採録を変更しない。**
軸 1 に対して `除外` であることと、7.4 の柱に採録されていることは矛盾しない —
軸別の判定と柱の分類は別の軸である。

## 5. pilot 表の該当行の後継値

**`2026-08-26-inventory.md` は凍結物なので書き換えない。** 同表 3.1 の第 5・7・8 行の後継値は次である。

| # | arXiv ID | A | B | C | D | 判定 | 極性 / 除外理由 |
|---|---|---|---|---|---|---|---|
| 5 | `2404.13359` Declarative Concurrent Data Structures | ✓ | ✓ | ✓ | ✗ | 直接接地 | 競合 |
| 7 | `2512.18746` MemEvolve | ✗ | ✓ | ✓ | △ | 部分接地 | 方法論的祖先 |
| 8 | `2605.22721` DecentMem | ✗ | ✗ | ✓ | △ | 除外 | 生成対象が自然言語の記憶片と行動であって設計空間の生成でない |

### 5.1 件数保存則

`2026-08-26-cir-cvn-adjudication.md` による第 6 行の後継化を織り込んだ起点は
直接接地 4 + 要裁定 3 + 部分接地 17 + 除外 5 = 29 である。本記録を適用すると:

**直接接地 5 + 要裁定 0 + 部分接地 18 + 除外 6 = 29。** 重複なし。

§2.2 の反対の読み ((ii)、成果物の種類で判定) を採る場合は
**直接接地 4 + 要裁定 0 + 部分接地 19 + 除外 6 = 29** である。どちらでも保存則は成立する。

### 5.2 この読みが作る再監査の義務 (本 wave では実施しない)

§1.1 の (i) の読みを一様に当てると、pilot が `除外` とした次の 2 行の A が疑わしくなる。

- 第 25 行 `2208.00315` (Release-Acquire Transactional Memory) — 除外理由は
  「実装の形式化と検証であって合成でない」。**これは B の理由であって A の理由ではない。**
- 第 26 行 `1710.04839` (Semantics of Transactions / Weak Memory) — 除外理由は「意味論の形式化」。
  **主題領域はトランザクションの意味論である。**

**本記録はこの 2 行を再判定しない。** 依頼の scope は `要裁定` 3 件であり、`除外` 行の
再判定は別の作業である。**この所見はユーザー裁定へ返し、worklog の次の一手へ起票する。**

### 5.3 C と D の欄について — 集計も比較もしてはならない

本記録は 3 行の C と D を一次資料で当て直した (C を 2 セル、D を 2 セル動かした)。
**その結果、29 行の C/D 欄は混合証拠になっている** — 一次資料由来は
`2604.09318` を含む 4 行だけで、残り 25 行は監査前の題名と 1 行要約に由来する。

**したがって 29 行の C/D を集計してはならず、行をまたいで比較してもならない。**
比較したいなら、他 25 行も同じ一次資料基準で当て直す必要がある。これは別の作業である。

なお **pilot の第 5 行の C は元から ✓ である。** 本記録が C を動かしたのは第 7・8 行の 2 セルだけで、
「3 件とも C を変えた」は誤りである。

## 6. 主張軸への影響

### 6.1 `docs/paper-story/2026-08-26.md` §3 の 1 — 書き換えは要らないが、3 つの限定は落とせない

§3 の 1 は「アクション空間自体をコードで拡張する既存例は本調査では未発見」と書いている
(出典: `docs/related-work/README.md` 7.6 の空白域 2 に対応する主張。掃引日 2026-07-10、
`docs/related-work/literature-map/` は監査前データである。7.7.3 の `RW1` が許す逐語引用として引く)。
**本記録はこの文を支持も強化もしない。言うのは、DCDS がこの文を覆さないということだけである。**

覆さない理由は、DCDS に LLM も進化ループも敵対 verifier も無く、CC プロトコル空間を
走行中に拡張しないことである (§2.3、§2.6)。**したがって現行の §3 の 1 は格下げも書き換えも要らない。**

**ただし、次の 3 つの限定のどれを落としても DCDS が直ちに反例になる。**

1. **「LLM が」** を落として「CC を自動生成した例は無い」と書くと、DCDS が反例になる。
   DCDS は CC のコードを機械的に生成する。
2. **「アクション空間自体を拡張する」** を落として「ワークロード特化の CC を作った例は無い」と
   書くと、DCDS が反例になる。DCDS は自分の勝因を
   "it specializes concurrency control to the target workload" と書いている。
3. **「トランザクションの並行性制御を対象とする」** を落として「並行コードを自動生成した例は
   無い」と書くと、DCDS も `2604.09318` (CIR+CVN) も反例になる。

**本記録が足すのは、その 3 語を落とすと具体的に何が反例になるかという実例である。**

### 6.2 「生成対象」は 3 段に分けて書く

DCDS を扱うときに混同が起きやすいので、生成対象を 3 つに分ける。

1. データ構造の実装の生成 — **DCDS は行う。**
2. 固定した CC プロトコルの注入コードの生成 — **DCDS は行う。**
3. CC プロトコル / アクション空間そのものの生成・拡張 — **DCDS は行わない。**

**この区別なしに「直接接地 / 競合」だけを置くと、§3 の 1 と矛盾して見える。**

### 6.3 `docs/related-work/README.md` 7.6 の空白域

- **空白域 1** (CC 合成に特化した敵対的 verifier + リーク制御を備えた進化ループ):
  DCDS はこの交点に当たらない。verifier をループ内に持たず (§2.5)、進化ループも無い。
  **本記録は空白域 1 を強化しない。言えるのは「この 1 件は空白域 1 の設定に当たらない」だけである。**
- **空白域 2** (LLM がアクション空間そのものをコードで拡張する CC 合成):
  DCDS は LLM を使わず、プロトコル空間を拡張しない。**直接覆さない。**
  ただし「CC についてコード生成そのものが未踏」という読みは、この 1 件で不可能になる。

### 6.4 採録

`2404.13359` を `docs/related-work/README.md` の **7.1** へ採録し、7.0 の逆引き索引へ 1 行足す。
判定タグは `引用元` + `外部補強` とする。

**7.3 ではなく 7.1 とした理由。** 7.3 の柱の定義は
「LLM エージェントがワークロード仕様からシステム丸ごとを bespoke 合成する系譜」である。
**DCDS に LLM は無い** (§2.6 の走査)。7.1 の柱の定義は
「ワークロードに合わせて CC を設計/学習/合成する系譜と、その素材となる古典 CC」であり、
DCDS はワークロード宣言に合わせて CC のコードを設計・合成する。**定義の文言では 7.1 が合う。**

**段 2 のプラン子と段 3 の敵対相談は、いずれも 7.3 を推した。** 理由は「生成対象が
CC プロトコルではなく対象特化データ構造だから」である。**親はこれを採らなかった** —
その理由は柱の定義が生成対象ではなく合成の主体 (LLM エージェント) で書かれているからである。
**この見解相違を未解決として記録する。**

`2512.18746` と `2605.22721` は軸 1 の理由では採録しない
(`2605.22721` は別の理由で既に 7.4 に採録済みであり、それは動かさない)。

## 7. C-4 に残っているもの

本記録の後、pilot の `要裁定` は 0 件になる。**それでも C-4 は閉じない。**

| 残件 | 状態 |
|---|---|
| 軸 1 の検索の実行 | 契約は `2026-08-27-axis1-search-preregistration.md` で凍結済み。**実行は 1 本もしていない** |
| 第 25・26 行の A の再監査 | §5.2。本 wave では実施しない |
| 29 行の C/D 欄の証拠階層 | §5.3。25 行が監査前要約由来 |
| 7.0 索引の全軸再棚卸し | 本 wave の採録で索引は 26 → 27 エントリになる。軸別の集計は再導出が要る |
| 軸 3 と軸 4 の母集合登録 | 未着手 (`RW0`) |
| 2026-07-10 掃引の `RW2` 化 | 不可能。やり直すしかない |

## 8. 規律 6 — 誘導記述の走査と、その限界

3 本の一次資料は絶対規律 6 でいう「データ」である。走査の結果を構造化して残す。

**走査は 3 本の整形本文の全体 (先頭切り出しなし) に対して行った。**走査語は
`ignore (all )?(previous|prior|above)` / `disregard` / `system.?prompt` /
`you are an? (ai|assistant|language model)` / `as an ai` / `new instruction` / `override` /
`do not follow` / `instead,? (please )?(output|write|say)` / `jailbreak` / `prompt.?inject`
で、大文字小文字を無視した。**hit は `2404.13359` が 0 件、`2512.18746` が 0 件、
`2605.22721` が 7 件** (`system prompt` 1 / `prompt_injected` 2 / `prompt_injection` 4) である。

**検出したもの (いずれも読み手への指示ではないと判定した)。**

1. `2605.22721` の実験設定節が、自分たちの AutoGen solver へ与えた system prompt
   (`"You are a smart agent designed to solve problems."`) を引用している。
2. `2605.22721` の付録の事例研究に、`prompt_injected_to_solver` と `prompt_injection_text` という
   **field 名そのもの**があり、その値として `"Use only the stated premises."` のような
   命令文が並ぶ。**同論文が自分の solver へ注入した記憶片の記録である。**
3. `2605.22721` の付録の完全な prompt 集合に、`"Only respond with the role name, nothing else."`
   `"Respond ONLY with a valid JSON array"` などの直接命令が多数ある。
   **同論文が実験エージェントへ与える prompt テンプレートである。**
4. 3 本とも末尾に arXiv の site 告知文 (`"Report Issue"` `"Have a free development cycle?"` 等) を含む。
   **本文ではなく arXiv の UI である。**

**いずれにも従っていない。** `ignore previous` / `ignore prior` / `you are an AI` のような、
読み手の上位指示を置換しようとする記述は 3 本とも見つからなかった。

**走査自身の限界 (実測した失敗)。** 親の初回走査は正規表現に `prompt injection` (空白区切り) を
使ったため、**下線区切りの `prompt_injection_text` / `prompt_injected_to_solver` を取り逃がした。**
段 3 の敵対相談が全文の独立確認でこれを検出した。
**「hit は 1 件だけ」という親の初回報告は、狭い語形の走査結果としては再現できるが、
誘導形文字列の全件報告としては不十分だった。**

## 9. この記録の限界

- **一次資料 3 件しか読んでいない。** 網羅率について何も言わない。
- **HTML v1 だけを読んだ。** PDF 版との差分は確認していない。3 件とも v2 以降は存在しない。
- **語の走査は文字列一致である。** 同義の言い換えは拾えない。ただし本件では、
  操作の逐語・実行時構造・評価単位という**正の証拠**が判定を決めているので、
  判定は語の不在だけに依存していない。
- **§1.1 の A の読みは、pilot の先例に接地しているが、pilot の規則文そのものには書かれていない。**
  §2.2 に反対の読みと、それを採った場合の件数を併記した。
- **`2404.13359` の投稿先は特定していない。** 本文の会議情報は `Conference: ; ;` の雛形のままである。
- **本記録は独立監査を受けていない。** 段 3 の敵対相談 2 本と段 6 の敵対レビューが検査した。
  §6.4 に未解決の見解相違が 1 件残っている。
