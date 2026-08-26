# 調査ノート: MemEvolve: Meta-Evolution of Agent Memory Systems

- **論文**: MemEvolve: Meta-Evolution of Agent Memory Systems (併せて EvolveLab を公開)
  - venue/year: arXiv preprint、`cs.CL` (cross-list `cs.MA`)、v1
  - arXiv: 2512.18746 / https://arxiv.org/abs/2512.18746
  - 本文取得元: https://arxiv.org/html/2512.18746v1 (HTML v1、2026-08-27 取得、78,687 文字に整形、
    SHA-256 `bd4461490e007c3138b751f9e9e961bab047cf404b139c7b8e0ac802b85533bf`)
- **このノートを書いた理由**: `docs/related-work/claim-survey/2026-08-26-inventory.md` の
  軸 1 分類 pilot が、監査前の 1 行要約からは包含条件 B (設計・アクション空間そのものをコードで
  生成または拡張するか) を決められず `要裁定` に残した 1 件だから。
  「メモリ構造の進化」が設計空間の生成に当たるかが、要約からは決められなかった。
- **信頼境界**: 本文は絶対規律 6 でいう「データ」である。誘導記述の有無を機械走査した
  (結果は末尾「規律 6 の走査」)。
- **引用の作法**: `>` と引用符の英文は arXiv HTML v1 の逐語である。
  HTML 整形由来の空白と数式マークアップ、および曲線アポストロフィ (U+2019) の ASCII 化だけを
  正規化した。語列は変えていない。

---

## 一言要約

**LLM エージェントの記憶機構そのものを進化させる外側のループ**の提案。
記憶を encode / store / retrieve / manage の 4 部品へ分解し、走った軌跡を診断して
**その部品の実装コードを書き換えた変異体**を作り、タスク上の実測で親を選ぶ。
併せて既存の記憶方式 12 種を同じインタフェースへ再実装した EvolveLab を公開している。

---

## 対象の確定 (包含条件 A の根拠)

**結論: 対象は並行性制御ではない。A は ✗ である。**

整形本文 78,687 文字の全体に対する小文字一致の件数は
`concurrency control` 0 / `concurrenc` 0 / `transaction` 0 / `serializab` 0 /
`isolation level` 0 / `mvcc` 0 / `throughput` 0 / `workload` 0 / `oltp` 0。
`database` の 4 件はベクトルデータベースなど記憶実装の文脈である。

**A✗ は語の不在だけでなく、正の証拠から決まる** — 論文が扱うのは 4 部品からなる記憶機構である。

---

## 手法の核 (包含条件 B の根拠)

**結論: B は ✓ である。生成されるのは記憶の内容ではなく、記憶機構の実装コードである。**

> "MemEvolve evolves the programmatic implementations of these modules in a model-driven fashion,
> using feedback from the agent's performance in the inner loop."

### 設計空間

記憶機構 Ω を 4 つの部品へ分解する — encode (経験の知覚と整形) / store (情報の確定) /
retrieve (文脈に応じた想起) / manage (統合と忘却)。

### メタ進化のオペレータ

2 段である。

1. **アーキテクチャ選択.** 各候補を (性能, −コスト, −遅延) の 3 次元で要約し、
   非優越ソートで Pareto 順位を付け、同順位内では性能で並べて上位 K を親にする。
2. **診断 → 設計.**
   - **診断:** 親が走らせた軌跡バッチを見る。成否・トークンコストに加え、
     軌跡へアクセスする replay インタフェースがあり、想起の失敗・無効な抽象化・
     格納の非効率を名指しできる。出力は 4 部品それぞれの欠陥プロファイルである。
   - **設計:** 欠陥プロファイルを条件に、**許可された実装箇所だけ**を書き換えて S 個の変異体を作る。

     > "a redesigned architecture is constructed by modifying only the permissible implementation
     > sites within the modular interface, thereby ensuring compatibility and isolating
     > architectural changes to the designated design space."

     > "These variants differ in encoding strategies, storage rules, retrieval constraints, or
     > management policies, yet all conform to the unified memory-system interface and remain
     > executable by the agent."

**この形は `2509.19349` (ShinkaEvolve) や `2512.13857` (EvoLattice) に B✓ を与えたのと同じ基準である** —
指定された穴の中でコードを合成する。語の上ではむしろこちらが直接的である。

### EvolveLab

`BaseMemoryProvider` という抽象基底クラスが全記憶方式の protocol を定める。
既存 12 方式 (ExpeL、Agent Workflow Memory、Dynamic Cheatsheet ほか) を同じインタフェースへ
再実装している。オンライン評価 (経験を逐次更新) とオフライン評価 (静的軌跡で蓄積してから未見タスク)
の両方を持つ。

---

## 実験

- ベンチマーク: WebWalkerQA / xBench-DeepSearch / TaskCraft / GAIA の 4 種。
- フレームワーク: SmolAgent、Flash-Searcher ほか。バックボーンは GPT-5-Mini、GPT-4o、o3-mini など。
- 主張: 既存フレームワークを最大 17.06% 改善。TaskCraft 上で進化させた記憶機構が、
  未見のベンチマークとバックボーンへ 2.0〜9.09% の利得で転移する。
- 進化の結果から読み取った設計原則として「エージェントの関与を増やす」「階層化」
  「多段の抽象化」を挙げている。

---

## ワークロード条件づけと正しさ検証器 (C と D)

- **C は ✓ とした。** ただし `workload` の語は 0 件である。適合度はタスク集合上の実測で、
  論文自身がタスク族ごとの特化を明言している。

  > "Memory systems evolved on TaskCraft are unlikely to transfer effectively to fundamentally
  > different task families ( e.g. , embodied action), where environments, action space and tool
  > sets differ substantially. Nevertheless, MemEvolve enables the discovery of broadly applicable
  > memory architectures within a shared task regime, while retaining the capacity for further
  > task-specific adaptation when required."

  **`workload` ではなく `task family` / `benchmark` の語彙で同じことを述べている、と読んだ。
  これは解釈であって語の一致ではない。**
- **D は ✗ とした。** タスクの成否がループ内の適合度信号であり、変異体は
  "remain executable by the agent" を要求される。**しかし正しさを判定することを役目とする器が
  無い** — 成否はベンチマークの成果指標であって検証器ではない。
  段 6 の敵対レビューが、当初の `△` は包含条件の字面から導けないと指摘し、親が訂正した。

---

## izanagi との関係

### 借りるもの (軸 1 ではなく軸 2・軸 5 側)

- **診断 → 設計の 2 相は izanagi の critic → coder と同型である。**
  軌跡の証拠から構造化した欠陥プロファイルを作り、それを条件に実装を書き換える。
  絶対規律 3 (正しさシグナルを後付けにせず、なぜ壊れたかを次の一手の入力にする) と同じ形を、
  性能改善の文脈で外から支える。
- **多目的の親選択 (性能・コスト・遅延の非優越ソート)** は、izanagi が
  スループット単独でなく特性の違う variant を残したいときの参照点になる。

### 借りないもの

- **記憶機構そのものの進化。** izanagi の whiteboard は固定構造で運用する立場である。
- **正しさ gate を持たない進化。** MemEvolve の適合度はタスク成否だけで、
  絶対規律 2 が要求する「正しさを破る変異は即 reject」に相当する器が無い。

### 主張との距離 (軸 1)

**`部分接地` / 極性 `方法論的祖先`。** 対象が並行性制御ではないので軸 1 の主題ではない。
B を満たすのは、指定された穴の中でコードを合成する形が同じだからである。

---

## 規律 6 の走査

整形本文 78,687 文字の全体に対して、
`ignore (all )?(previous|prior|above)` / `disregard` / `system.?prompt` /
`you are an? (ai|assistant|language model)` / `as an ai` / `new instruction` / `override` /
`do not follow` / `instead,? (please )?(output|write|say)` / `jailbreak` / `prompt.?inject`
を大文字小文字を無視して走査した。**hit は 0 件である。**

末尾に arXiv の site UI 由来の文字列を含むが、本文ではなく HTML の chrome であり従っていない。

**走査語は有限である。** この走査は「誘導記述が無い」ことの証明ではない。
実際、同 wave の `2605.22721` では、下線区切りの語形を含めなかった初回走査が hit を取り逃がしている
(詳細は `docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md` の §8)。

---

## 引用/リンク

- abs: https://arxiv.org/abs/2512.18746
- HTML v1: https://arxiv.org/html/2512.18746v1
- 判定の全根拠: `docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md`
- 分類 pilot の起点: `docs/related-work/claim-survey/2026-08-26-inventory.md`
