# 調査ノート: Learning Deliberately, Acting Intuitively: Unlocking Test-Time Reasoning in Multimodal LLMs

- **論文**: CoRR 2025 (arXiv:2507.06999v1). 著者: Yahan Yu (京都大学 / インターン時 NEC), Yuyang Dong (NEC), Masafumi Oyamada (NEC)。
  - URL: https://arxiv.org/abs/2507.06999 / DOI 表記 10.48550/arXiv.2507.06999
  - **本文取得経路**: `fetch_article_fulltext(doi=...)` は CrossRef 404 で失敗（DOI 未登録）。→ arXiv abstract ページ (`arxiv.org/abs/2507.06999`) と arXiv HTML 版 (`arxiv.org/html/2507.06999v1`) を直接取得して全文精読。図は本文テキストからは取得せず（図の視覚内容は本ノートの根拠にしていない）。

---

## 問題設定 / 一言要約

マルチモーダル LLM (MLLM) の推論を強化したいが、既存手法は追加アノテーションや複雑なルールベース報酬に依存し、学習コストとスケーラビリティが問題。本論文は **D2I (Deliberate-to-Intuitive)** を提案: **学習時**は「熟慮的 (deliberate)」な構造化推論戦略を **ルールベースの format reward だけ**で誘導してモダリティ整合を鍛え、**推論時**にはその明示的戦略を外して「直感的 (intuitive)」に自由生成させる。つまり **「学習時の推論の深さ」と「テスト時の応答の柔軟さ」を分離** する。追加アノテーション・複雑報酬なしで in-domain / out-of-domain 双方でベースラインを上回る。

一言: **「学習では型を厳しく強制し、本番では型を外して能力だけ発現させる」ことで、reward を軽く保ったまま転移可能な推論力が育つ**、を実証した論文。

---

## 手法の核（具体的に）

1. **D2I パラダイム vs D2D**: 既存手法（学習も推論も熟慮的＝D2D, Deliberate-to-Deliberate）に対し、D2I は学習=deliberate / 推論=intuitive に非対称化。図1がこの対比を主題にしている。
2. **報酬は GRPO の accuracy reward を維持しつつ format reward だけを差し替える**。追加の人手アノテーションや複雑な rule-based reward を **足さない**のが売り。学習コスト削減とスケーラビリティが動機。
3. **3種の deliberate reasoning 戦略**（いずれも format reward で強制、正解教師は最終回答のみ）:
   - **LOC (Region Localization)**: 画像中の関連領域の座標を `<box>…</box>` で明示させ、「見てから考える」を誘導。出力形式 `<think>…<box>…</box>…</think><answer>…</answer>`。
   - **JUS (Region Justification)**: 解答に重要な視覚手がかりを `<crucial>…</crucial>` に自然言語で言語化させる。解釈可能性と視覚-意味整合を狙う。
   - **PAR (Parsing Consistency)**: 応答冒頭で画像を構造化言語/記号表現に `<parse>…</parse>` パースさせ、全体理解を先に固める。
4. **推論時はこれら明示タグ/戦略を除去**し、intuitive スタイルのプロンプトで自由生成。学習で獲得した能力が暗黙に発現する（＝「テスト時に能力がアンロックされる」）。
5. **なぜ D2I > D2D か（本論文の因果仮説）**: 最終回答しか教師がないため box 座標や parse の**中間出力の質は保証されない**。D2D は推論時に低品質な視覚グラウンディングを出すと推論トレースを汚染して誤答を招く。D2I は推論時に出力制約を緩めるので低品質中間物に邪魔されない。ただし **general（非数学）ベンチでは逆に D2D 有利**（易しく多様なタスクでは構造化中間出力が十分高品質で推論に寄与するため）。
6. **Case study の含意**: GRPO/LOC/PAR が誤答、JUS だけ正答した失敗例で、4応答は構造も形式もほぼ同一。差は JUS が「対頂角 (vertical angles)」という**鍵概念を推論トレース中で正しく言語化**した一点。→ 「出力形式の厳密な強制より、正しい概念を理解・言語化できるかが成否を分ける」。

---

## 主要な実験結果 / 主張（数値）

- **ベースモデル**: Qwen2.5-VL-7B-Instruct。学習は 150 steps, batch 128, lr 1e-6, max response 1024 tokens, sampling temp 1。学習データ = GEOQA-8K（幾何、train 8,030 / test 754）と、独自構築 Doc-Mix（DocVQA/InfographicVQA/ArxivQA/TAT-DQA 混合, train 8,040）。
- **GEOQA-8K 学習（Table 1, in-domain 精度）**:
  - ベース Qwen2.5-VL-7B = **46.6**。D2I_jus = **65.0**（最良, Δ_base **+18.4**）、D2I_loc = 60.6 (+14.0)、D2I_par = 60.5 (+13.9)。
  - 本文の総括: **in-domain で D2I はベース比 ≥13.9%、GRPO 比 ≥7.4% 改善**。
- **Out-of-domain（数学: MathVerse/MathVista/MATH-Vision）**: D2I_loc・D2I_par は概ね **+1〜8%** の向上（MathVerse でわずかに低下する場合あり）。D2I_jus は +1〜6%（MATH-Vision でわずかに低下）。
- **GRPO†（intuitive 評価）比の伸び**が顕著な箇所: MME(sum) で D2I_loc は Δ_grpo† **+99.5**、D2I_jus は **+131.4**。MMVet で D2I_loc +9.3 など。
- **Doc-Mix 学習（Table 2）**: 数学ベンチへの転移は小幅だが一貫してプラス（GRPO† 比で MathVerse +5.5/+5.3、MathVista +3.5/+4.7、MATH-Vision +3.1/+2.2 等）。ドメインを跨いでも D2I > D2D/GRPO† の傾向は保たれる。
- **Pass@K 分析（Table 3, 数学3ベンチ）**: MathVista/MATH-Vision では PAR ベース D2I が Pass@1 で明確に良く、Pass@3 では複数推論パス生成の恩恵が大（top-1 に無くても top-3 で正答を捕捉）。MathVerse は top-1 でほぼ捕捉済みで候補追加の価値は小さい。→ **タスクの難しさ次第で「多様な候補を出して選ぶ」価値が変わる**。
- **比較対象**: GPT-4V/GPT-4o（クローズド）、Qwen2-VL/InternVL2/2.5（オープン汎用）、LLaVA-CoT/R1-Onevision/OpenVLThinker（推論特化）。D2I は一部 general ベンチで GPT-4o に及ばないが、オープン汎用・推論特化モデルには一貫して優位。

---

## izanagi のどの層・部品に効くか（なぜ）

**前提（重要な線引き）**: 本論文の *literal* な方法は **MLLM の RL ファインチューニング**であり、izanagi はモデルを学習しない（エージェント探索でコード/パラメータの CC variant を進化させる）。従って移植できるのは**設計原理レベル**であり、手法そのものではない。この線引きを外すと過剰一般化になる。

- **評価器 (Phase1) — 最も効く**。核心の主張「**複雑な報酬を足さず、ルールベースの format/format-style シグナルだけで転移可能な能力が育ち、しかも reward hack を招く複雑報酬より頑健**」は、izanagi の評価器設計思想（D3: 構造化フィードバックを毎 iteration 返す／D1: reward hack が湧く前に評価器を固める）と直結。izanagi の trace verifier は既に「pass/fail でなく構造化診断」を返す方針で、D2I の「format reward だけで足りる」知見はこの方向の追い風であり、**「性能報酬に何をどこまで足すか（足さないか）」の判断材料**になる。
- **層2（最適化移植ループ）— 概念的に効く**。D2I の中心アイデア「**探索/学習フェーズでは構造を厳しく強制し、成果物フェーズでは構造を外す**」は、izanagi の二相思想（開発相=trace-enabled で構造化検証を強制／性能計測相=trace-disabled でオーバーヘッドを外す, D4）と同型。izanagi では「観測者効果の分離」として既に実装済みだが、D2I はこれを**探索の誘導シグナル一般**へ拡張する視点を与える（探索中は冗長な構造的中間表現を要求→最終 variant はその足場を持たない）。
- **層3（variant 比較・選択）— Pass@K が効く**。「難タスクほど複数候補生成→選択の価値が上がる（Pass@3 > Pass@1）／易タスクでは候補追加の価値が薄い」は、izanagi の island model・複数シード並列進化・Pareto 選択の**予算配分の裏付け**。ワークロード難度に応じて variant 生成数を可変にする根拠になる。
- **層1（ベースCC選定）— ほぼ効かない**。本論文にワークロード→初期個体選定に対応する要素はない。
- **orchestrator/hook — 間接的**。「学習時の構造（trace-enabled build, patch 適用）と本番の非構造（trace-disabled）を別 run で分ける」orchestrator の流れは D4 と D2I の思想が一致。新規要素は薄い。

---

## 具体的に izanagi に移植できる要素（設計レベル）

1. **「探索フェーズ限定の構造化足場」を明示的な設計原則に格上げ**: 層2 の variant 生成/評価中は、LLM に「なぜこの最適化を移植するか」の構造化中間表現（rw依存の言語化・移植箇所の局在・期待効果のパース）を **強制**し、最終成果物（新CC＋レポート）ではその足場を要求しない。D2I の LOC/JUS/PAR の三分類は、この中間表現の型カタログとして流用可能（局在＝どのコード領域／justification＝なぜ効くか／parsing＝ワークロード構造の記号化）。
2. **format reward 相当を評価器の「軽量ゲート」として採用**: 性能・正しさの本体報酬に**複雑な報酬を足さず**、構造の充足（フィードバック形式・トレース形式・レポート形式が規定に合うか）だけを軽いルールで課す。D2I の「複雑報酬なしで頑健」を reward-hack 対策の一手として位置づける。
3. **JUS 型（自然言語 justification）を層3 の説明生成に橋渡し**: Case study の「形式強制より鍵概念の言語化が成否を分ける」は、izanagi の差別化核心（Polyjuice の policy table に対する言語説明）と直結。探索中に variant ごとに「効いた/効かなかった因果」を JUS 形式で残させ、それを層3 の最終レポートに集約する。
4. **難度適応の variant 予算**: Pass@K の知見から、ワークロード難度（contention/skew 等）が高いほど並列 variant 数・進化世代数を増やし、易しいワークロードでは絞る。層3 の Pareto 探索の停止条件に反映。
5. **D2I vs D2D の A/B を izanagi 流に翻訳した ablation**: 「探索中に構造を強制した variant」と「強制しない variant」の到達品質を比較する実験設計。D2I 論文の Table 1/2 が示す「in-domain（≒学習ワークロードそのもの）で効き、easy/汎用で逆転しうる」構図は、izanagi の「特化 CC は対象ワークロードで勝つが汎用ワークロードで劣化しうる」という**特化のトレードオフ**を測る枠組みとしてそのまま使える。

---

## izanagi に入れる際の障害・前提・リスク

- **手法の非対称性（最大の注意点）**: D2I は勾配更新を伴う RL 学習。izanagi はモデルを学習しない。よって「format reward」「GRPO」を literal に持ち込む場所はない。移植は**原理の類推**に留め、「izanagi にも format reward がある」と誤読しないこと。
- **general ベンチでの逆転（D2I < D2D）**: 「易しく多様なタスクでは構造化中間物が有益」という結果は、izanagi でも「探索足場の強制が常に得とは限らない」ことを示唆。ワークロード次第で足場強制をオフにする分岐が要る。
- **中間出力の品質保証がない前提**: D2I の優位は「中間出力が低品質でも本番でそれに邪魔されない」ことに依存。izanagi の場合、中間表現（rw依存や移植理由）が低品質だと**探索の方向づけ自体が誤る**ため、D2I ほど気楽に「中間品質は問わない」とは言えない。ここは非対称。
- **スケール依存**: 実験は 7–8B モデル・150 step・8K サンプルの小規模。結論の一般性（大モデル・別ドメイン）は本論文からは特定できず。
- **統計的頑健性**: 乱数シード数・分散/信頼区間の記載は本文から特定できず。ベンチ間で符号が割れる小差（例 MathVerse で数点低下）もあり、効果量の解釈は慎重に。
- **CC ドメインへの外挿の未検証**: 本論文はマルチモーダル数学/文書 VQA。CC/トランザクション最適化探索での妥当性は当然ながら本論文の射程外（本文から特定できず）。

---

## 小山田さんに聞くべき質問（議論を深める鋭い問い）

1. **「format reward だけで足りる」は izanagi の評価器にどこまで持ち込めるか**: D2I は複雑報酬を避けて頑健性を得たが、izanagi の探索誘導では中間表現（移植理由・rw依存）の**質**が探索方向を決める。「中間品質を問わない」D2I の割り切りと、izanagi の「診断の中身が探索を導く」（D3）は緊張関係にある。探索誘導シグナルは軽く保つべきか、それとも診断の質にこそ投資すべきか——どちらに賭けますか？
2. **deliberate/intuitive の非対称を izanagi の二相（trace-enabled/disabled, D4）にマップする発想は妥当か**: D2I の「学習で型を強制し本番で外す」は izanagi の観測者効果分離と同型に見えるが、izanagi の"本番"は生成された CC 成果物であってモデル応答ではない。この類推はどこまで有効で、どこで破綻すると見ていますか？
3. **JUS が LOC/PAR に勝った case study（形式強制 < 概念の言語化）を、izanagi の説明可能性（層3）にどう活かすか**: 探索中に variant ごとの因果を自然言語で残させる設計は、Polyjuice の policy table に対する izanagi の差別化と直結する。「効いた理由の言語化」を探索の誘導と最終レポートのどちらに重心を置いて設計すべきでしょうか？

---

## 引用/リンク

- 本論文: Yu, Dong, Oyamada. *Learning Deliberately, Acting Intuitively: Unlocking Test-Time Reasoning in Multimodal LLMs.* CoRR 2025. arXiv:2507.06999. https://arxiv.org/abs/2507.06999
- 関連（本論文が依拠）: DeepSeek-R1 (guo2025deepseek, GRPO/RL for reasoning); Qwen2.5-VL-7B (bai2025qwen2, ベースモデル); R1V / GEOQA-8K (chen2025r1v, 学習設定・データ)。
- izanagi 側の対応箇所（read のみ、非コピー）: `docs/decisions.md` D1（reward hack と評価器固め）/ D3（構造化フィードバック）/ D4（観測者効果の #ifdef 分離）; `docs/roadmap.md` §2 層2・層3（island model, Pareto）; `docs/phase1.md`（trace verifier, calibrator）。
