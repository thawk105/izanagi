# 2026-08-26 — `2604.09318` (CIR+CVN) の `要裁定` を一次資料で解いた記録 (凍結)

- **作成日:** 2026-08-26
- **入力 commit:** `b0c1a8bd` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `b0c1a8bd` の blob そのものである。
  一次資料だけは repo の外にあり、取得元 URL と取得日、および整形後の文字数で束縛する。
- **入力 path:** `docs/related-work/claim-survey/2026-08-26-inventory.md` の
  「3. 軸 1 の分類 pilot」 / `docs/related-work/README.md` の 7.0 と 7.6 と 7.7 /
  `docs/related-work/literature-map/izanagi_literature_map.md` /
  `docs/related-work/literature-map/izanagi_literature_map.csv` /
  `docs/paper-story/2026-08-26.md` の §3 と §8
- **一次資料:** arXiv `2604.09318` v1 (2026-04-10 投稿)。
  取得元 https://arxiv.org/abs/2604.09318 および https://arxiv.org/html/2604.09318v1。
  取得日 2026-08-26。HTML を整形した本文は 101,515 文字。
  精読記録は `docs/related-work/notes/note_cir_cvn_bridging_llm_semantic_understand.md`。
- **文献 cutoff:** 変わらない。本記録は新しい掃引を行っておらず、
  `docs/related-work/literature-map/` の cutoff (2026-07-10) を動かさない。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 何を決めたか、何を決めていないか

**決めたこと:** `2026-08-26-inventory.md` の軸 1 分類 pilot が `要裁定` に残した 4 件のうち
1 件 (`2604.09318` CIR+CVN) について、一次資料を読んで包含条件 A を決めた。
判定は `部分接地` / 極性 `方法論的祖先` である。

**決めていないこと:**

- **軸 1 の検索記録の成熟度は `RW1` のまま動かない。** 本記録は 1 件の一次資料を読んだだけで、
  索引・検索式・母集合の登録 (7.7.4) を一切行っていない。
- **世界の不在は一切主張しない。** 本記録に現れる「無い」は、すべてこの 1 論文という
  列挙可能な母集合の中の不在 (7.7.2 でいう内部の不在) である。
- **`docs/paper-story/2026-08-26.md` §8 の C-4 (体系的な先行研究調査) は、これで閉じない。**
  C-4 が求めるのは 7.7.4 の母集合を登録して全件を処理することであり、
  本記録が消したのは pilot が残した 4 件の `要裁定` のうち 1 件だけである。
  残り 3 件 (`2404.13359` / `2512.18746` / `2605.22721`) は `要裁定` のまま残っている。
- **`docs/paper-story/` の版は書き換えていない。** 凍結物なので、
  確定したことは `docs/paper-story/README.md` の
  「最新スナップショット以後に確定したこと」から指す。

## 1. 判定に使った規則

`2026-08-26-inventory.md` の pilot が定めた包含条件と判定規則をそのまま使う
(規則を後から変えると、同じ表の他の 28 行と比べられなくなる)。

- **包含条件:** (A) 論文の対象が並行性制御である / (B) 設計・アクション空間そのものをコードで
  生成または拡張する / (C) ワークロード条件づけがある / (D) 正しさ検証器をループ内に持つ。
- **判定規則:** A を満たせば `直接接地`。A✗ かつ B✓ なら `部分接地`。A✗ かつ B✗ なら `除外`。
  C と D は gate ではなく記録する属性である。

pilot が使えた資料は題名と監査前の 1 行要約だけで、一次資料は読んでいなかった。
**本記録は同じ規則を、一次資料を資料として当て直したものである。**

## 2. 各条件の判定

| 条件 | pilot (要約のみ) | 本記録 (一次資料) | 根拠 |
|---|---|---|---|
| A | `?` | **✗** | 対象はスレッドの同期構造。トランザクションの並行性制御ではない |
| B | ✓ | **✓ (ただし「生成」であって「拡張」ではない)** | LLM が同期構造を書くが、操作語彙は形式系が定めた固定集合 |
| C | ✗ | **✗** | 条件づけは自然言語の仕様であってワークロードではない |
| D | ✓ | **✓** | 全状態探索と静的検査を修理の輪の中で毎回回す |

### 2.1 A を ✗ とした根拠

**`要裁定` の原因は日本語要約の語だった。** `docs/related-work/literature-map/` の要約は
「並行制御構造を合成」と書いており、これはトランザクションの並行性制御 (concurrency control) とも、
並行プログラムの同期構造 (concurrency structure) とも読める。**原文は後者である。**

一次資料の逐語:

> "Instead of verifying arbitrary source code, a large language model first synthesizes a
> verification-oriented concurrency artifact from a natural-language requirement or system specification."

> "Concurrency bugs such as deadlocks, signal losses, starvation, and blocking protocol errors remain
> difficult to detect and repair because they arise from interactions among threads rather than from a
> single local control path."

Table 3 が定める操作語彙は Mutex / RwLock / Condvar / Semaphore / Channel / Var / Atomic /
OS thread / async task に対する `lock` `drop` `read_lock` `write_lock` `wait` `notify_one`
`notify_all` `acquire` `release` `send` `recv` `read` `write` `load` `store` `cas` `spawn` `join`
`spawn_async` `await` `call` であり、**トランザクションの開始・コミット・中断・検証に相当する
操作は 1 つも無い。**

**語の全件走査 (母集合を併記した内部の不在):** 上記 HTML v1 を整形した本文 101,515 文字の全体
(節・表・参考文献・付録を含み、先頭切り出しをしていない) に対する小文字一致の件数は、
`serializab` 0 / `database` 0 / `concurrency control` 0 / `isolation level` 0 /
`two-phase lock` 0 / `2pl` 0 / `mvcc` 0 / `snapshot isolation` 0 / `commit` 0 / `abort` 0 /
`throughput` 0 / `many-core` 0 / `manycore` 0 / `workload` 0 / `silo` 0 / `tictoc` 0。
`transaction` の 1 件は参考文献の venue 名 `IEEE Transactions on Software Engineering`、
`occ` の 4 件はすべて `occupies` / `occasional` / `occur` の一部、
`atomicity` の 2 件は関連研究節の atomicity violation 検出である。

**この不在は、この 1 論文の中の不在である。世界の不在ではない。**

### 2.2 B を ✓ としたうえで、下位の区別を記録する理由

pilot の B は「生成または拡張」であり、どちらか一方で ✓ になる。
CIR+CVN は **生成する。** LLM が自然言語の仕様から同期構造を書き、反例を見て直す。

しかし**拡張はしない。** 書ける操作は Table 3 の閉じた集合であり、
LLM がその語彙に新しい操作を足すことはない。翻訳先の Petri ネットの意味論が語彙に束縛されているので、
語彙を足せば翻訳の正しさの証明が壊れる。**この論文は語彙を固定することで検証可能性を得ている。**

**この区別は軸 1 の主張にとって本質である** (§4 参照)。
B を ✓ の一語で潰すと、この違いが表から消える。

### 2.3 D を ✓ とした根拠

修理の輪の中で全状態探索を毎回行い、反例を文の識別子へ差し戻す。
さらに、**バグ検出器を通ったものに対して別の検査を当てている**:

> "To reduce the risk of bug-free but behavior-dropping repairs, acceptance additionally applies a
> lightweight goal-reachability check over designated critical outcomes."

§6.5 (RQ4) はこの二段目が実際に発火した例を報告している
(DeepSeek-V3 が pattern 3 で、デッドロックは消したが両スレッドが止まる修理を出した)。

## 3. pilot 表の該当行の後継値

**`2026-08-26-inventory.md` は凍結物なので書き換えない。** 同表 3.1 の第 6 行の後継値は次である。

| # | arXiv ID | A | B | C | D | 判定 | 極性 / 除外理由 |
|---|---|---|---|---|---|---|---|
| 6 | `2604.09318` CIR+CVN | ✗ | ✓ | ✗ | ✓ | 部分接地 | 方法論的祖先 |

置き換え後の件数は 直接接地 4 + 要裁定 **3** + 部分接地 **17** + 除外 5 = **29**。件数保存則は保たれる。

**この行は、9 番から 24 番までの `部分接地` / `方法論的祖先` の群と同じ区分に入る** —
すなわち Bounded Synthesis (`2502.13955`)、AtomiS (`2309.05483`)、Fence Synthesis (`2208.00285`)、
Event-B Agent (`2605.17475`)、VeriAct (`2604.00280`)、AutoICE (`2512.07501`) などの
検証付き合成の群である。CIR+CVN はその中で **対象が並行プログラムである点**が目を引くが、
**対象が並行であることは A を満たすことを意味しない** — A が問うのは
トランザクションの並行性制御かどうかである。

## 4. 主張軸への影響

### 4.1 `docs/paper-story/2026-08-26.md` §3 の 1 — 行の書き換えは要らないが、限定は 2 つ要る

§3 の 1 は「アクション空間自体をコードで拡張する既存例は本調査では未発見」と書いている。
**CIR+CVN はこの文を覆さない。** 覆さない理由は 2 つあり、**どちらも文の中に残っていなければならない。**

1. **対象がトランザクションの並行性制御であること。** これを落として
   「並行制御構造を LLM が合成した例は無い」と書くと、CIR+CVN が直ちに反例になる。
2. **空間の「拡張」であって、固定語彙の中の「生成」ではないこと。** これを落として
   「LLM に並行処理のコードを書かせた例は無い」と書くと、やはり CIR+CVN が反例になる。

**したがって §3 の 1 に対する本記録の指示は「狭めよ」ではなく「この 2 語を落とすな」である。**
現行の §3 の 1 は両方を持っているので、**格下げも書き換えも要らない。**
本記録が足すのは、**その 2 語を落とすと具体的に何が反例になるかという実例**である。
限定を落とした短縮版が書かれかけたとき、この行が止める。

### 4.2 `docs/related-work/README.md` 7.6 の空白域 1 — 記述が一次資料と食い違う

7.6 の 1 は「7.3 の検証付き合成は 2025 末〜2026 に急増するが**対象は Rust/C の逐次コード・
形式仕様で**、C++ many-core CC 実装を敵対 verifier で毎反復ゲートする設定は空白」と書いている。

**「逐次コード」の部分がこの 1 件で成り立たなくなった。** CIR+CVN は同じ検証付き合成の群にいて、
対象は並行プログラムである。**空白域の主張そのものは残る** — CIR+CVN も
トランザクションの直列化可能性を扱わず、性能を評価しないからである。
**変わるのは「なぜ空白なのか」の説明であり、空白の有無ではない。**

### 4.3 採録

`docs/related-work/README.md` の 7.3 へエントリを足し、7.0 の逆引き索引へ 1 行足す。
判定タグは `外部補強` とする — 借りる機構は無く、izanagi の既存判断
(絶対規律 2 と絶対規律 3) を外から支える証拠だからである。

**借用の実体は、目標到達検査が「検証器は通るが振る舞いを落とした修理」を捕まえた実例である。**
izanagi の絶対規律 2 は、最適化圧力が正しさ検査を攻撃しに来るという前提に立っている。
CIR+CVN はスループット最適化ではなくバグ修理という別の文脈で、**同じ形の抜け道に別途の検査を
足す必要があった**と実測込みで報告している。izanagi の auditor の設計を、別ドメインから支える。

## 5. C-4 に残っているもの

本記録の後、pilot の `要裁定` は 3 件残る。

| arXiv ID | 残る理由 |
|---|---|
| `2404.13359` Declarative Concurrent Data Structures | A が決められない (対象が並行データ構造)。`literature-map/` の柱 1 にあるが 7.0 索引にも 7.1 本文にも無く、却下したのか未処理なのかの記録が無い |
| `2512.18746` MemEvolve | B が決められない (メモリ構造の進化) |
| `2605.22721` DecentMem | B が決められない |

そのうえで、**`要裁定` が 0 件になっても C-4 は閉じない。**
pilot の母集合は `literature-map/` の閉じた 29 件であり、7.7.4 が求める
索引 (arXiv / OpenAlex / DBLP の和集合)・検索式・cutoff の事前登録は行われていない。
C-4 を閉じる道は 7.7.4 の母集合登録から始まる別の作業であり、
その入口は worklog の「次の一手」にある T-1881 以降の項目である。

## 6. この記録の限界

- **一次資料 1 件しか読んでいない。** 網羅率について何も言わない。
- **HTML v1 だけを読んだ。** PDF 版との差分、および v2 以降の存在は確認していない。
- **語の走査は文字列一致である。** 同義の言い換え (例: 直列化可能性を別の語で述べる) は
  拾えない。ただし本件では、操作語彙の表と評価対象の 9 パターンという**正の証拠**が
  対象を決めているので、判定は語の不在だけに依存していない。
- **投稿先は特定していない。** 本文の会議情報は雛形のままで、査読の有無は分からない。
