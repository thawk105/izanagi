# 調査ノート: Self-Evolving Multi-Agent Systems via Decentralized Memory (DecentMem)

- **論文**: Self-Evolving Multi-Agent Systems via Decentralized Memory (DecentMem)
  - venue/year: arXiv preprint、`cs.MA`、v1
  - arXiv: 2605.22721 / https://arxiv.org/abs/2605.22721
  - 本文取得元: https://arxiv.org/html/2605.22721v1 (HTML v1、2026-08-27 取得、92,322 文字に整形、
    SHA-256 `80271cf7d871a5bc3c344b5c85c41333b94bc102170d1ab9ff5ed5f227891522`)
- **このノートを書いた理由**: `docs/related-work/claim-survey/2026-08-26-inventory.md` の
  軸 1 分類 pilot が、監査前の 1 行要約からは包含条件 B を決められず `要裁定` に残した 1 件だから。
  **同論文は `docs/related-work/README.md` の 7.4 に `外部補強` として既に採録されている** —
  本ノートは軸 1 に対する判定だけを扱い、7.4 の採録は動かさない。
- **信頼境界**: 本文は絶対規律 6 でいう「データ」である。誘導記述の有無を機械走査した
  (結果は末尾「規律 6 の走査」)。**3 本の一次資料のうち、hit が出たのはこの 1 本だけである。**
- **引用の作法**: `>` と引用符の英文は arXiv HTML v1 の逐語である。
  HTML 整形由来の空白と数式マークアップ、および曲線アポストロフィ (U+2019) の ASCII 化だけを
  正規化した。語列は変えていない。

---

## 一言要約

**マルチエージェントの記憶を中央集権の共有庫でなく、エージェントごとの 2 プールに分ける**提案。
過去の軌跡を固めた exploitation プール (E-pool) と、未見の文脈のために LLM が作る候補を置く
exploration プール (X-pool) を持ち、どちらから引くかの重みを段階ごとの評価で更新する。
解空間への到達可能性と `O(log T)` の累積 regret を証明したと主張する。

---

## 対象の確定 (包含条件 A の根拠)

**結論: 対象は並行性制御ではない。A は ✗ である。**

整形本文 92,322 文字の全体に対する小文字一致の件数は
`concurrency control` 0 / `concurrenc` 0 / `serializab` 0 / `isolation level` 0 / `mvcc` 0 /
`throughput` 0 / `workload` 0 / `oltp` 0 / `database` 0。`transaction` の 1 件も CC の文脈ではない。

---

## 手法の核 (包含条件 B の根拠)

**結論: B は ✗ である。生成物は自然言語の記憶片と行動であって、設計空間の生成ではない。**

**「設計空間を生成する記述が見つからなかった」ではなく、閉じた構造が本文に書かれている。**

### 固定された構造

- エージェントは Base / Role / Memory / Tool の 4 要素で定義される。
- 記憶は E-pool と X-pool の 2 つに固定される。
- E-pool の記憶片は `z = (ξ, r*)` で、`r*` は軌跡 (タスク分解・直接回答などの行動と、
  次段へ渡す協調軌跡) と、**行動選択の理由を書いた自己注釈**の対である。

  > "Unlike standard MAS memory, our memory piece z records not only what was solved, but also how
  > the task was solved and who executed each sub-task."

- X-pool が作るのは "an exploratory memory piece z_new for the current context" である。
- 検索または探索で得た記憶片を LLM へ渡して行うのは "executable action generation" である。
- タスク終了後、X-pool の記憶片は E-pool へ統合され、X-pool は空へ戻る。
- 付録の完全な prompt 集合が要求する出力は、役割名・二択の routing・直接回答・
  下位タスクの JSON・評価の JSON である。**記憶機構のコードでも行動語彙の拡張でもない。**

**したがって `除外` は不在側への横倒しではなく、正の証拠に基づく判定である。**

### 訂正 — 「router の重みは固定」は誤りである

本 wave の親 brief は当初、B✗ の理由に「固定 router 重み」を挙げた。**これは一次資料と食い違う。**
固定されているのは X-pool の重み 1.0 であり、E-pool の重みと選択確率は段階評価で更新される。

> "Meanwhile, w_{m,X-pool} = 1.0 remains fixed. In this way, successful exploitation increases
> reliance on the E-pool, while successful exploration prevents the router from over-committing to
> past experience."

**B✗ の根拠は上の閉じた構造であって、重みの固定性ではない。**
この訂正は段 3 の敵対相談が一次資料から構成した。

---

## ワークロード条件づけと正しさ検証器 (C と D)

- **C は ✓ とした。** ただし条件づけられるのは**検索とプール選択**であって、生成された設計ではない。
  検索は現タスクの類似度と閾値で行い、閾値を下回れば X-pool へ落ちる。
- **D は △ とした。** LLM 評価器が段階ごとに correctness を採点し、router へ戻している。

  > "After execution, the full solution trajectory is evaluated stage by stage by an LLM evaluator."

  > "Rather than scoring only the final answer, the evaluator assesses each stage in terms of
  > correctness, allocation quality, intermediate coherence, and final integration."

  健全な正しさ gate ではないので ✓ には足りないが、✗ でもない。
  **`△` は「正しさの採点がループ内にあるが、生成物を検証する器ではない」場合に使う。**
  同じ wave で `2512.18746` は当初 `△` としたが、正しさを判定する役目の器が無いため ✗ へ訂正した。

---

## 実験

3 つの MAS フレームワーク (AutoGen、DyLAN、AgentNet)、5 つのバックボーン
(Qwen3-4B/8B/14B、Gemma4-E2B/E4B)、5 つのベンチマーク
(AIME25&24、MBPP-Plus、BBH、ALFWorld)。中央集権の最強 baseline (G-Memory) に対して
平均正解率で最大 23.8%、記憶なしに対して最大 52.5% の改善、トークン使用量は最大 49% 削減と主張する。

---

## izanagi との関係

7.4 の既存エントリが記録するとおり、**whiteboard の二プール構造の理論裏付け**が借用点である。
本ノートはそれを動かさない。

**軸 1 に対しては `除外` である。** 対象が並行性制御でなく (A✗)、
設計空間をコードで生成も拡張もしない (B✗) からである。

---

## 規律 6 の走査

整形本文 92,322 文字の全体に対して、
`ignore (all )?(previous|prior|above)` / `disregard` / `system.?prompt` /
`you are an? (ai|assistant|language model)` / `as an ai` / `new instruction` / `override` /
`do not follow` / `instead,? (please )?(output|write|say)` / `jailbreak` / `prompt.?inject`
を大文字小文字を無視して走査した。**hit は 7 件である**
(`system prompt` 1 / `prompt_injected` 2 / `prompt_injection` 4)。

**いずれも読み手への指示ではないと判定した。従っていない。**

1. **実験設定節の system prompt.** 自分たちの AutoGen solver を初期化する文字列
   (`"You are a smart agent designed to solve problems."`) の引用である。
2. **付録の事例研究の `prompt_injected_to_solver` / `prompt_injection_text`.**
   **field 名そのもの**であり、値は `"Use only the stated premises."` のような命令文である。
   **同論文が自分の solver へ注入した記憶片の記録である。**
3. **付録の完全な prompt 集合.** `"Only respond with the role name, nothing else."`
   `"Respond ONLY with a valid JSON array"` などの直接命令が多数ある。
   **同論文が実験エージェントへ与える prompt テンプレートである。**

末尾に arXiv の site UI 由来の文字列を含むが、本文ではなく HTML の chrome である。

`ignore previous` / `ignore prior` / `you are an AI` のような、読み手の上位指示を置換しようと
する記述は見つからなかった。

### 走査自身の限界 (実測した失敗)

**親の初回走査は正規表現に `prompt injection` (空白区切り) を使ったため、
下線区切りの `prompt_injection_text` / `prompt_injected_to_solver` を取り逃がした。**
段 3 の敵対相談が全文の独立確認で検出し、親が現物で裏取りしてから走査語を `prompt.?inject` へ
広げ直した。**「hit は 1 件だけ」という初回報告は、狭い語形の走査結果としては再現できるが、
誘導形文字列の全件報告としては不十分だった。**

**走査語は今も有限である。** この走査は「誘導記述が無い」ことの証明ではない。

---

## 引用/リンク

- abs: https://arxiv.org/abs/2605.22721
- HTML v1: https://arxiv.org/html/2605.22721v1
- 判定の全根拠: `docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md`
- 分類 pilot の起点: `docs/related-work/claim-survey/2026-08-26-inventory.md`
- 7.4 の既存採録: `docs/related-work/README.md`
