# Izanagi サブフィールド 文献マップ

**対象サブフィールド:** AI / LLM によるワークロード特化並行性制御 (Concurrency Control) の自動合成、およびそれを可能にする周辺手法。

Izanagi (`~/github/izanagi`) の位置づけ — CCBench を素材コーパスとし、入力ワークロードに最適な CC を選定し、他 CC 実装の最適化を移植して variant を進化させ、「新 CC + 速さの理由 + 試行記録」を生成するシステム — を踏まえ、その土台となる文献を6つの柱に整理した。

- **収集手法:** arXiv (OpenAlex は API キー未設定のため今回は不使用) を並行性制御・合成・進化・検証・自己改善の語彙で横断掃引 (547件収集) → 関連度スコアリング → LLM による関連度判定 (0-3) と偽陽性除去 → 6柱に分類。
- **採録:** 29 本 (うち ★ = Izanagi の `docs/related-work.md` が既に引用する 8 本のアンカー論文、全て arXiv 上で実在を検証済み)。
- **注:** 検証は 2026-07-09 時点。arXiv ID `26xx`/`25xx` は 2026/2025 年の最新プレプリント。

---

## 柱1 — 学習型・自動設計の並行性制御 (Izanagi の直球)

*ワークロードに合わせて CC プロトコル/最適化を学習・自動設計する系譜。Izanagi の層2の直接の先行研究。*

論文数: 4

### Polyjuice: High-Performance Transactions via Learned Concurrency Control
`2105.10329` · 2021-05 · cs.DB · 関連度 ●●● · [arXiv](http://arxiv.org/abs/2105.10329v3)

*Jiachen Wang; Ding Ding; Huan Wang; Conrad Christensen et al.*

機械学習でワークロード特化型の並行制御アルゴリズムを自動合成し、既存手法を上回る性能を実現。

### Modeling Concurrency Control as a Learnable Function
`2503.10036` · 2025-03 · cs.DB · 関連度 ●●● · [arXiv](http://arxiv.org/abs/2503.10036v4)

*Hexiang Pan; Shaofeng Cai; Tien Tuan Anh Dinh; Yuncheng Wu et al.*

機械学習でCC関数を学習し、多様なワークロードに最適化された並行制御を自動設計する。

### ATCC: Adaptive Concurrency Control for Unforeseen Agentic Transactions
`2603.13906` · 2026-03 · cs.DB · 関連度 ●●● · [arXiv](http://arxiv.org/abs/2603.13906v1)

*Weixing Zhou; Zhiyou Wang; Zeshun Peng; Hetian Chen et al.*

LLM駆動エージェントの非決定的トランザクション特性に適応する学習型並行制御を提案し、ワークロード特性自動検出の基礎を実現。

### Declarative Concurrent Data Structures
`2404.13359` · 2024-04 · cs.DB · 関連度 ●● · [arXiv](http://arxiv.org/abs/2404.13359v1)

*Aun Raza; Hamish Nicholson; Ioanna Tsakalidou; Anna Herlihy et al.*

DBMSの汎用CC機構を活用し、宣言的仕様から並行データ構造を自動生成する枠組み提案。ワークロード特化型CC設計への基礎的な自動化アプローチ。

## 柱2 — 同期合成・ロック推論・弱メモリ (PL/検証の源流)

*並行プログラムの同期を仕様や可換性から自動合成する古典〜現代の系譜。CC を「正しく」合成するための意味論的基盤。*

論文数: 6

### The Semantics of Transactions and Weak Memory in x86, Power, ARM, and C++
`1710.04839` · 2017-10 · cs.PL · 関連度 ●● · [arXiv](http://arxiv.org/abs/1710.04839v2)

*Nathan Chong; Tyler Sorensen; John Wickerson*

弱メモリモデルとトランザクションメモリの相互作用を形式化し、CC合成の基礎となる正確な意味論を確立する。

### Veracity: Declarative Multicore Programming with Commutativity
`2203.06229` · 2022-03 · cs.PL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2203.06229v2)

*Adam Chen; Parisa Fathololumi; Eric Koskinen; Jared Pincus*

プログラマが可換性条件を宣言的に指定し、コンパイラが並列化を自動推論するアプローチ。CC合成の基盤となる可換性解析を提供。

### Implementing and Verifying Release-Acquire Transactional Memory (Extended Version)
`2208.00315` · 2022-07 · cs.PL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2208.00315v1)

*Sadegh Dalvandi; Brijesh Dongol*

弛緩メモリ下のTM実装を形式化・検証し、自動CC設計の基盤となる同期プリミティブの正当性保証を提供する。

### Fence Synthesis under the C11 Memory Model
`2208.00285` · 2022-07 · cs.DC · 関連度 ●● · [arXiv](http://arxiv.org/abs/2208.00285v2)

*Sanjana Singh; Divyanjali Sharma; Ishita Jaju; Subodh Sharma*

C11メモリモデル下で正確性を保ちながら効率的なフェンス組み合わせを合成する最適化手法。弱メモリ同期制御の基盤技術。

### Sound Atomicity Inference for Data-Centric Synchronization
`2309.05483` · 2023-09 · cs.PL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2309.05483v1)

*Hervé Paulino; Ana Almeida Matos; Jan Cederquist; Marco Giunti et al.*

データ中心の同期制御モデルAtomiSは、型安全な原子性推論により、手動注釈の負担を軽減し、自動化されたCC設計の基盤となる宣言的フレームワークを提供する。

### Bounded Synthesis of Synchronized Distributed Models from Lightweight Specifications
`2502.13955` · 2025-02 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2502.13955v1)

*Pablo F. Castro; Luciano Putruele; Renzo Degiovanni; Nazareno Aguirre*

分散システムの同期仕様から実行可能モデルを自動合成し、形式検証を通じて正確性を保証する古典的合成手法。

## 柱3 — LLM×進化的プログラム合成

*LLM を変異オペレータとして進化探索でコードを改良する系譜 (AlphaEvolve/FunSearch/DGM 直系)。Izanagi の (b) コード合成と同一問題設定。*

論文数: 2

### ShinkaEvolve: Towards Open-Ended And Sample-Efficient Program Evolution ★
`2509.19349` · 2025-09 · cs.CL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2509.19349v1)

*Robert Tjarko Lange; Yuki Imajuku; Edoardo Cetin*

LLMを用いた進化的プログラム合成の効率化フレームワーク。workload特化型CC設計の自動化に応用可能。

### EvoLattice: Persistent Internal-Population Evolution through Multi-Alternative Quality-Diversity Graph Representations for LLM-Guided Program Discovery
`2512.13857` · 2025-12 · cs.AI · 関連度 ●● · [arXiv](http://arxiv.org/abs/2512.13857v2)

*Kamer Ali Yuksel*

LLMガイド下のプログラム進化において、DAG内の複数選択肢を保持し探索空間を効率化する手法。CC設計への直接応用は限定的だが、適応的合成の基盤技術として有用。

## 柱4 — エージェント型の対象特化システム合成

*LLM エージェントがワークロード仕様からシステム丸ごとを bespoke 合成する系譜。Izanagi の設計レベルの予言書。*

論文数: 2

### The Time is Here for Just-in-Time Systems: Challenges and Opportunities ★
`2605.24096` · 2026-05 · cs.DB · 関連度 ●●● · [arXiv](http://arxiv.org/abs/2605.24096v1)

*Shu Liu; Alexander Krentsel; Shubham Agarwal; Mert Cemri et al.*

LLMエージェントが仕様からKVストアを自動合成し、ワークロード特化型システム設計を実現する先駆的手法。

### VibeServe: Can AI Agents Build Bespoke LLM Serving Systems? ★
`2605.06068` · 2026-05 · cs.AI · 関連度 ●● · [arXiv](http://arxiv.org/abs/2605.06068v1)

*Keisuke Kamahori; Shihang Li; Simon Peter; Baris Kasikci*

LLMエージェントループが異なるワークロード向けにLLMサービングスタック全体を自動合成し、システム専門化の実現可能性を示す。

## 柱5 — 検証付き・正しさ保存の合成

*生成コードの正しさを形式検証で毎反復ゲートする系譜。Izanagi の「正しさを後付けにしない」絶対規律の外部裏付け。*

論文数: 9

### Inductive Deductive Synthesis: Enabling AI to Generate Formally Verified Systems ★
`2605.23109` · 2026-05 · cs.AI · 関連度 ●● · [arXiv](http://arxiv.org/abs/2605.23109v1)

*Shubham Agarwal; Alexander Krentsel; Shu Liu; Mert Cemri et al.*

形式検証を伴うLLMベースシステム合成により、分散システム正当性保証を自動化し、CC設計検証の基盤技術を提供。

### CIR+CVN: Bridging LLM Semantic Understanding and Petri-Net Verification for Concurrent Programs
`2604.09318` · 2026-04 · cs.PL · 関連度 ●●● · [arXiv](http://arxiv.org/abs/2604.09318v1)

*Kaiwen Zhang; Guanjun Liu*

LLMが自然言語仕様からPetriネット検証可能な並行制御構造を合成し、正確性を保証する検証駆動型アーキテクチャを実現。

### Checking Robustness Against Snapshot Isolation
`1905.08406` · 2019-05 · cs.LO · 関連度 ●● · [arXiv](http://arxiv.org/abs/1905.08406v2)

*Sidi Mohamed Beillahi; Ahmed Bouajjani; Constantin Enea*

トランザクション一貫性モデル間の正確性保証を検証する手法。弱い一貫性下での安全性確認により、CC合成時の仕様検証の基盤を提供。

### Proof2Silicon: Prompt Repair for Verified Code and Hardware Generation via Reinforcement Learning
`2509.06239` · 2025-09 · cs.AI · 関連度 ●● · [arXiv](http://arxiv.org/abs/2509.06239v2)

*Manvi Jha; Jiaxin Wan; Deming Chen*

形式検証可能なコード生成を強化学習でプロンプト最適化により実現し、安全性が必須のシステム合成の基盤となる。

### AutoICE: Automatically Synthesizing Verifiable C Code via LLM-driven Evolution
`2512.07501` · 2025-12 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2512.07501v1)

*Weilin Luo; Xueyi Liang; Haotian Deng; Yanan Liu et al.*

LLM進化探索でC言語の検証可能コード合成を自動化。形式検証対応の正確な合成技術がCC設計の信頼性基盤になる。

### Reducing the Costs of Proof Synthesis on Rust Systems by Scaling Up a Seed Training Set
`2602.04910` · 2026-02 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2602.04910v3)

*Nongyu Di; Tianyu Chen; Shan Lu; Shuai Lu et al.*

Rust システムの形式証明合成を大規模データで自動化し、検証済みコード生成の信頼性を向上させる技術。

### VeriAct: Beyond Verifiability -- Agentic Synthesis of Correct and Complete Formal Specifications
`2604.00280` · 2026-03 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2604.00280v1)

*Md Rakib Hossain Misu; Iris Ma; Cristina V. Lopes*

形式仕様の自動合成と検証フィードバックによるプロンプト最適化は、正確性を保証するコード生成の基盤技術となる。

### Neuro-Symbolic Generation and Validation of Memory-Aware Formal Function Specifications
`2603.13414` · 2026-03 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2603.13414v1)

*Liao Zhang; Tong Chen; Xiwei Wu; Qi Liu et al.*

LLMが生成したC関数の形式仕様を自動生成し、検証可能な低レベルシステムコードの正確性を保証する基盤技術。

### Event-B Agent: Towards LLM Agent for Formal Model Synthesis and Repair
`2605.17475` · 2026-05 · cs.SE · 関連度 ●● · [arXiv](http://arxiv.org/abs/2605.17475v1)

*Hongshu Wang; Xinyue Zuo; Yuhan Sun; Qin Li et al.*

形式手法とLLMを統合し、正確性保証された自動化されたシステム設計を実現する基盤技術であり、CCプロトコル合成の検証保証に直結。

## 柱6 — 自己改善エージェント・メタ最適化

*手順書・プロンプト・メモリ・ハーネス自体を学習ループで改善する系譜。Izanagi の whiteboard memory と自己改善機構の系譜。*

論文数: 6

### SkillOpt: Executive Strategy for Self-Evolving Agent Skills ★
`2605.23904` · 2026-05 · cs.AI · 関連度 ●● · [arXiv](http://arxiv.org/abs/2605.23904v2)

*Yifan Yang; Ziyang Gong; Weiquan Huang; Qihao Yang et al.*

エージェントスキルを凍結モデルの外部状態として最適化する体系的テキスト空間オプティマイザで、自己改善ループの安定性を実現。

### Self-Harness: Harnesses That Improve Themselves ★
`2606.09498` · 2026-06 · cs.CL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2606.09498v1)

*Hangfan Zhang; Shao Zhang; Kangcong Li; Chen Zhang et al.*

LLMエージェントが環境との相互作用を仲介するハーネスを自己改善する枠組み。自動化された適応的な制御システム設計の基盤技術。

### The Last Human-Written Paper: Agent-Native Research Artifacts ★
`2604.24658` · 2026-04 · cs.LG · 関連度 ● · [arXiv](http://arxiv.org/abs/2604.24658v3)

*Jiachen Liu; Jiaxin Pei; Jintao Huang; Chenglei Si et al.*

AI研究を機械実行可能な形式で記録し、エージェントによる研究の再現・拡張を支援するプロトコル。自己改善型エージェントの基盤となる。

### Self-Evolving Multi-Agent Systems via Decentralized Memory ★
`2605.22721` · 2026-05 · cs.MA · 関連度 ● · [arXiv](http://arxiv.org/abs/2605.22721v1)

*Guangya Hao; Yunbo Long; Zhuokai Zhao*

LLM駆動の自己進化マルチエージェント学習を分散メモリで実現し、エージェント多様性と自己改善の基盤を提供。

### MemEvolve: Meta-Evolution of Agent Memory Systems
`2512.18746` · 2025-12 · cs.CL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2512.18746v1)

*Guibin Zhang; Haotian Ren; Chong Zhan; Zhenhong Zhou et al.*

LLMエージェントのメモリ構造を自動進化させる枠組みで、自己改善とメタ最適化を実現する基盤技術。

### SePO: Self-Evolving Prompt Agent for System Prompt Optimization
`2606.04465` · 2026-06 · cs.CL · 関連度 ●● · [arXiv](http://arxiv.org/abs/2606.04465v1)

*Wangcheng Tao; Han Wu; Weng-Fai Wong*

プロンプト最適化エージェント自身のプロンプトも進化させる自己参照設計で、メタ最適化による自動改善を実現。

---

## 系譜の源流 (関連研究として要位置づけ・今回 arXiv ID 未検証)

以下は Izanagi の `related-work.md` および柱3/柱4 が直系と位置づける基盤研究。arXiv がレート制限 (HTTP 429) を返したため今回は ID の自動検証ができず、名称と発表元のみ記す (ID を確定させたい場合は再取得可能)。

- **AlphaEvolve** (Google DeepMind, 2025) — LLM×進化探索でアルゴリズム/コードを発見。柱3 の直系の源流。
- **FunSearch** (DeepMind, *Nature* 2023) — LLM を進化ループに組み込み数学・アルゴリズム的発見を行った先駆。柱3 の起点。
- **Darwin-Gödel Machine (DGM)** — 自己改変で自らを進化させるエージェント。柱6 の理論的源流。
- **Polyjuice** (OSDI 2021, arXiv `2105.10329`) — 本マップの柱1 に採録済み。CC をアクション列に分解して進化的に学習する、Izanagi 層2 の思想的祖先。

---

## Izanagi から見た地図

- **柱1 (学習型 CC)** が Izanagi の直接の競合・比較対象。Polyjuice (2021) → CCaaLF/学習可能関数モデル化 (2025) → ATCC (2026, エージェント的トランザクションへの適応) と、この 5 年で「固定アクション空間での配合最適化」から「未知ワークロードへの適応」へ重心が移動している。Izanagi の賭け — *LLM がアクション空間自体をコードで拡張する* — はこの延長線上で最も外側にある。
- **柱3 (LLM×進化合成)** と **柱4 (エージェント型システム合成)** が Izanagi の方法論を支える両輪。特に Jitskit / VibeServe (共に 2026-05) は「単一汎用システム」から「ターゲット特化の自動合成」への転換という点で Izanagi と同じ賭けをしており、spec cards・adversarial auditor・leading indicators の直接の供給源。
- **柱5 (検証付き合成)** は 2025 末〜2026 に急増しており (AutoICE, CIR+CVN, Event-B Agent, VeriAct 等)、Izanagi の「正しさを後付けにしない」規律が学界の潮流と合致していることを示す。ただし多くは Rust/C の逐次コードや形式仕様が対象で、**C++ many-core CC 実装を敵対的 verifier で毎反復ゲートする** Izanagi の設定は依然として空白域。
- **柱6 (自己改善エージェント)** の SkillOpt / Self-Harness / DecentMem は Izanagi の whiteboard memory を理論・実験両面で追認するが、`related-work.md` が明記するとおり機構の直採用ではなく思想の裏付けにとどまる (Model Y リーク制御・計測直列の絶対規律と衝突するため)。
- **空白域 (Izanagi の機会):** ①CC 合成に特化した敵対的 verifier + リーク制御を備えた進化ループ、②LLM がアクション空間そのものをコードで拡張する CC 合成、③「新 CC + 速さの理由 + 試行記録」を成果物とする ARA 的研究アーティファクト — いずれも既存文献に正面から取り組む研究は見当たらない。
