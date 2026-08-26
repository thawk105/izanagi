# 調査ノート: CIR+CVN: Bridging LLM Semantic Understanding and Petri-Net Verification for Concurrent Programs

- **論文**: CIR+CVN: Bridging LLM Semantic Understanding and Petri-Net Verification for Concurrent Programs
  - venue/year: arXiv preprint 2026、cs.PL (cross-list cs.FL)、v1 (2026-04-10 13:40:58 UTC, 34 KB)、License CC BY 4.0
  - authors: Kaiwen Zhang, Guanjun Liu (いずれも Tongji University, Shanghai, China)
  - arXiv: 2604.09318 / https://arxiv.org/abs/2604.09318
  - 本文取得元: https://arxiv.org/html/2604.09318v1 (HTML v1、2026-08-26 取得、101,515 文字に整形)
  - 本文中の会議情報は `Conference: Conference; June 2026; City, Country` の雛形のままで、投稿先は特定できない
- **このノートを書いた理由**: `docs/related-work/claim-survey/2026-08-26-inventory.md` の軸 1 分類 pilot が、
  監査前の 1 行要約からは包含条件 A を決められず `要裁定` に残した 1 件だから。
  一次資料を読んで A を決めるのが目的である。
- **信頼境界**: 本文は絶対規律 6 でいう「データ」である。読解にあたり誘導記述の有無を機械走査した
  (結果は末尾「規律 6 の走査」)。
- **引用の作法**: 以下で `>` と引用符を使った英文は arXiv HTML v1 の本文からの逐語である。
  ただし **HTML 整形由来の空白と数式マークアップだけは正規化した** — 原文の HTML は
  数式を `≤ 20 \leq 20` のように二重に持ち、括弧の前後へ空白を入れる。**語列は変えていない。**
  表を文章へ組み直したものは逐語と呼ばず「転記」と書く。

---

## 一言要約

**LLM に自然言語の仕様から「検証しやすい形の同期構造」を書かせ、それを Petri ネットへ機械翻訳して
全状態を数え上げ、反例を文ごとの識別子へ差し戻して直させる**、というパイプラインの提案。
対象はスレッドの相互排他と待ち合わせ (mutex / rwlock / condvar / semaphore / channel / atomic) であり、
**デッドロックとシグナル消失を消すことが目的**である。

---

## 対象の確定 (包含条件 A の根拠)

**結論: この論文の対象はトランザクションの並行性制御ではない。**

`docs/related-work/literature-map/` の日本語要約は「LLM が自然言語仕様から Petri ネット検証可能な
**並行制御構造を合成**し、正確性を保証する検証駆動型アーキテクチャを実現」と書いている。
原文の該当語は concurrency structure (同期構造) であり、トランザクションの並行性制御 (concurrency
control) ではない。**要約の日本語が両方に読める形になっていたことが `要裁定` の原因だった。**

一次資料の逐語 (abstract):

> "Recovering concurrency structure directly from source code is difficult because shared-resource
> identity and protection relations are often obscured by aliasing, ownership, and API-specific idioms."

> "Instead of verifying arbitrary source code, a large language model first synthesizes a
> verification-oriented concurrency artifact from a natural-language requirement or system specification."

> "The trust boundary of the present work is the generated Cir artifact rather than arbitrary source code."

本文 §1 の逐語:

> "Concurrency bugs such as deadlocks, signal losses, starvation, and blocking protocol errors remain
> difficult to detect and repair because they arise from interactions among threads rather than from a
> single local control path."

Table 3 (Cir operations) が定める操作語彙 — **これが閉じた集合である点が後で効く**。
以下は**逐語引用ではなく、表を文章へ整形して転記したもの**である:

- Lock: `lock`, `drop` (Mutex, RwLock) / `read_lock`, `write_lock` (RwLock)
- Synchronization: `wait`, `notify_one`, `notify_all` (Condvar) / `acquire`, `release` (Semaphore) /
  `send`, `recv` (Channel)
- Data: `read`, `write` (Var) / `load`, `store` (Atomic) / `cas(expected, new)` (Atomic)
- Control: `spawn`, `join` (OS thread) / `spawn_async`, `await` (async task) / `call` (function)

**この集合が閉じていることは、表の存在ではなく §4.1 の形式定義が言っている。** 逐語:

> "op is an operation from Table 3 or the distinguished no-operation nop"

すなわち Cir の文が持てる操作は Table 3 と `nop` だけであり、**そこに新しい操作を足す経路は無い。**

キーワード欄も同じ方向を指す:

> "Keywords: concurrency verification, Petri nets, large language models, alias analysis,
> intermediate representation, deadlock detection"

### 語の全件走査 (母集合と走査語を併記)

**母集合**: 上記 HTML v1 を整形した本文 101,515 文字の全体 (節・表・参考文献・付録を含む。
先頭切り出しをしていない)。走査は文字列の小文字一致で行った。

| 走査語 | 件数 | 実際に現れた文脈 |
|---|---|---|
| `serializab` | 0 | — |
| `database` | 0 | — |
| `concurrency control` | 0 | — |
| `isolation level` | 0 | — |
| `two-phase lock` / `2pl` | 0 / 0 | — |
| `mvcc` | 0 | — |
| `snapshot isolation` | 0 | — |
| `commit` / `abort` | 0 / 0 | — |
| `throughput` | 0 | — |
| `many-core` / `manycore` | 0 / 0 | — |
| `workload` | 0 | — |
| `silo` / `tictoc` | 0 / 0 | — |
| `transaction` | 1 | 参考文献の venue 名 `IEEE Transactions on Software Engineering` のみ |
| `occ` | 4 | すべて `occupies` / `occasional` / `occur` の一部。並行性制御の OCC ではない |
| `latency` | 0 | — |
| `atomicity` | 2 | 1 件は関連研究節の本文 (`atomicity violations` の検出)、1 件は参考文献の題名 (`A type and effect system for atomicity`) |

**これは「世界の不在」ではなく、この 1 論文という母集合の中の不在である。**
7.7.2 の区分でいう内部の不在にあたる。

---

## 手法の核

1. **二つの形式系。** Cir (Concurrency Intermediate Representation) は文単位・別名なしの模型で、
   共有資源は大域的に一意な名前を持ち、どの資源をどのロックが守るかが明示され、各文が安定した
   識別子を持つ。Cvn (Concurrency Verification Net) は重み付き place/transition Petri ネットに、
   有限の大域変数ストアと三値ガード (真・偽・不明) を足したもの。
2. **翻訳と数え上げ。** 検査を通った Cir は機械的に Cvn へ翻訳され、状態空間を網羅探索する。
   反例は文の識別子へ差し戻され、直す場所を指す。
3. **二層の検査。** 静的規則 61 本 + 解析述語 5 本。
4. **目標到達検査 (これが izanagi にとって一番の見どころ)。** 逐語:

   > "To reduce the risk of bug-free but behavior-dropping repairs, acceptance additionally applies a
   > lightweight goal-reachability check over designated critical outcomes."

   すなわち **「バグ検出器は通るが、振る舞いを落として通しただけの修理」を別の検査で弾く**。
   §6.5 (RQ4) は、この失敗が実際に起きることを実測している:

   > "A Cir that passes the definite-bug check is not necessarily correct. Two distinct failure modes
   > remain invisible to the bug detectors: (1) repair-induced regression and (2) livelock obstruction."

   例として DeepSeek-V3 が pattern 3 で、チャネル操作の順序を入れ替えてデッドロックは消したが
   両スレッドが止まる修理を出し、目標到達検査が捕まえて次の回で直った、と報告している。

---

## 実験

- 対象は 9 個の bounded-concurrency pattern。逐語の名前:
  (1) Two-mutex deadlock (2) Condvar signal loss (3) Channel + mutex DL (4) Three-lock circular
  (5) Partial deadlock (6) Dual condvar cross (7) Semaphore throttle (BL) (8) CAS contention (BL)
  (9) FnSummary prop. (BL)。末尾 3 個は (BL) = バグ無しの対照。
- 使った LLM は 5 種。逐語: "GPT-5 and Claude 4.6 Opus ( frontier ), Qwen and Gemini 3 Pro ( strong ),
  and DeepSeek-V3 ( compact ). All models use temperature 0 with a 4 096-token output limit."
- 規模。逐語: "All patterns remain under 250 states"、"Full state-space exploration completes in
  ≤ 20 ms for all patterns"、目標到達検査の追加費用は "< 0.5 ms"。
- **アプリケーションの性能 (スループット・遅延) は評価していない。**
  この論文が測る時間は状態空間探索と検査の所要時間だけである。
  母集合 (本文 101,515 文字の全体) に対する走査で `throughput` 0 件、`latency` 0 件。
- **修理の回帰は 2 種類あり、捕まえる機構が違う。混ぜてはならない。**
  - **構造的な回帰 4 件** (25 個の model-pattern 課題の中間 4 回)。`drop` の欠落、branch 先の破れ、
    `notify` の置き場所の誤り。**第 1 層の静的検査が捕まえ**、次の回で直った。
  - **意味的な回帰 2 件** (DeepSeek-V3 の pattern 3、Qwen 3.5 の pattern 6)。
    **こちらは静的検査もバグ検出器も通り抜ける。** 逐語:

    > "Both regressions pass all 61 static-check rules and all definite-bug detectors.
    > They are bug-free and structurally valid. The goal-reachability check is the only mechanism
    > that detects them. Without it, these repairs would be accepted as verified despite silently
    > dropping essential program behavior."
- **なお、LLM は Cir だけでなくソースコードも同じ仕様から生成する** (§6.6)。逐語:
  "The LLM generates both the Cir and the source code from the same specification."
  信頼境界が Cir 側に置かれているのは、そのソースと Cir の対応を形式的に示すことが
  一般には不可能だから、と同節が述べている。

---

## izanagi との関係

### 軸 1 (AI による並行性制御の合成) への接地

`docs/related-work/README.md` 7.7.5 の語彙で書く。判定の根拠は
`docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` に置いた。

- **強さ: 部分接地。** 対象がトランザクションの並行性制御ではないので、軸 1 の主題そのものではない。
- **極性: 方法論的祖先。** 検証器を輪の中に置いて毎回直させる形は izanagi と同じ。

### 借りるもの

1. **「検証器は通るが振る舞いを落とした修理」への備えが、外部で独立に必要とされた実例。**
   izanagi の絶対規律 2 (正しさゲートを緩める変異を許さない) と auditor は、最適化圧力が
   正しさ検査を攻撃しに来るという前提に立つ。CIR+CVN はスループット最適化ではなく
   バグ修理の文脈で、**同じ形の抜け道 (検査は満たすが中身が空になる) に別途の検査を足した**。
   しかも**その抜け道は思考実験ではなく、5 モデル中 2 つで実際に通り抜けた** —
   61 本の静的規則もバグ検出器も素通りし、目標到達検査だけが捕まえた (§6.5 の逐語は上に引いた)。
   **izanagi の auditor が「あってもなくても同じ」ではないことの、別ドメインからの外部証拠**として引ける。
2. **反例を「文の識別子」へ差し戻す形。** 単なる合否でなく構造化した診断を返す点は、
   izanagi の絶対規律 3 (正しさシグナルを後付けにしない) と同じ思想である。IDS が示した
   「合否だけに落とすと性能が激減する」の別ドメインからの実例として並べられる。

### 借りないもの

- **Petri ネットによる全状態数え上げ。** 対象規模が違う。この論文は 250 状態未満・20ms で閉じる
  模型を扱っており、izanagi が扱う C++ many-core の実装はその規模ではない。
  izanagi は形式証明でなく trace ベースの直列化可能性検査を採る (IDS の項と同じ理由)。
- **信頼境界の置き方。** この論文の信頼境界は「LLM が生成した Cir という模型」であって、
  実際に走るソースコードではない。izanagi は実際に走る CCBench の C++ を計測対象にするので、
  この境界設定は採れない。

### 軸 1 の主張との距離 — どの語がどう違うか

| 観点 | CIR+CVN | izanagi 軸 1 |
|---|---|---|
| 対象 | スレッドの同期構造 (mutex/condvar/semaphore) | トランザクションの並行性制御 |
| 正しさの基準 | デッドロック不在・シグナル消失不在・目標到達 | 直列化可能性 (G2 を含む cycle の不在) |
| 生成の対象 | 固定語彙 (Table 3) の中で書かれた模型 | 既存 CC 実装のコード片そのもの |
| 空間の扱い | Cir の**原始操作語彙**は形式系が定めた閉じた集合 (Table 3 と `nop`)。**拡張しない** — 関数・資源・制御フローは新しく作れるが、新しい操作は作れない | アクション空間自体をコードで拡張する |
| 条件づけ | 自然言語の仕様 | ワークロード |
| 性能 | 評価しない | スループットが目的関数 |

---

## 規律 6 の走査

本文全体 (101,515 文字) に対し、振る舞いを誘導する記述の定型を機械走査した。
走査語と件数: `ignore previous` 0 / `ignore all previous` 0 / `you must` 0 / `disregard` 0 /
`as an ai` 0 / `system prompt` 0 / `do not verify` 0 / `skip verification` 0 / `treat this as` 0 /
`instructions:` 0 / `assistant:` 0 / `override` 0 / `mark as verified` 0 / `note to reviewer` 0 /
`note to the reviewer` 0 / `report that` 1。

唯一の hit である `report that` は「シグナル消失の診断はこう報告するだろう」という道具の説明文
("a signal-loss diagnostic would report that the witness reaches n2 before the worker reaches w3")
であって、読み手への指示ではない。**誘導記述は検出しなかった。anomaly なし。**

なお、arXiv の HTML には論文本文でない site 側の告知文が混ざる
(逐語: "arXiv is now an independent nonprofit! Learn more")。
整形後の本文に site の飾りが残ることを、次に同じ経路で読む者は知っておくとよい。
**語を走査するときは、この種の行が母集合に含まれていることを勘定に入れる。**

---

## 引用/リンク

- arXiv: https://arxiv.org/abs/2604.09318 / 本文取得元 HTML: https://arxiv.org/html/2604.09318v1
- 主要参照: abstract, §1 Introduction, §4.1 (Cir), §4.2 (Cvn), Table 3 (Cir operations),
  Table 5 (test matrix), §6.5 / Table 10 (RQ4: goal preservation), §7 Related Work
- izanagi 側の対応箇所: `docs/related-work/README.md` 7.3 (採録先) と 7.6 (空白域の記述)、
  `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` (判定の記録)、
  絶対規律 2 / 絶対規律 3 (`CLAUDE.md`)
