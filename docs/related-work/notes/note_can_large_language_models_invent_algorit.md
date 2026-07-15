# 調査ノート: Can Large Language Models Invent Algorithms to Improve Themselves?

- **論文**: Yoichi Ishibashi, Taro Yano, Masafumi Oyamada. "Can Large Language Models Invent Algorithms to Improve Themselves?: Algorithm Discovery for Recursive Self-Improvement through Reinforcement Learning." NAACL 2025 (Long). DOI: 10.18653/v1/2025.naacl-long.519 / arXiv:2410.15639 (v5)。全著者 NEC Corporation。
- **本文取得経路**: `fetch_article_fulltext(doi=...)` は失敗（Unpaywall はメール未共有でスキップ、Semantic Scholar 404、PMC に PMCID なし、CrossRef に TDM リンクなし、DOI landing は HTML スクレイピング要）。**arXiv HTML 版 `https://arxiv.org/html/2410.15639v5` を curl 取得**して精読（v5 は副題付きで NAACL 版とタイトル一致）。数値・引用はこの arXiv v5 本文に基づく。

---

## 問題設定 / 一言要約

LLM の改善手法は人間の設計に縛られている。本論文は、**LLM 自身が「モデル改善アルゴリズム」を Python コードとして生成・評価・改良する**フレームワーク **Self-Developing** を提案。外部の強力モデル（GPT-4 等）も人間のフィードバックも使わず、シードモデル自身の能力だけで自己改善する。具体例として **model merging（モデルマージ）**アルゴリズムの自動発見に適用し、人間設計手法（Task Arithmetic 等）を上回る新規マージ戦略を発見できることを示した。

## 手法の核（Self-Developing の反復サイクル）

1. **二成分の同時進化**: (i) **seed model M0**（改善対象）と (ii) **algorithm factory π^g**（改善アルゴリズムを生む生成器 LLM）。factory は初期状態で M0 のクローンから始まる（π₁ = M0）。改善アルゴリズムは「モデルを受けてモデルを返す任意の Python コード」で、本研究ではマージ対象モデルの **task vector（= 候補モデル − M0 の重み差）を合成する関数**に具体化。
2. **Algorithm Generation**: factory が prompt から N 個のアルゴリズム（マージ関数のコード）を生成。プロンプトは 1-shot 実装例入りで全イテレーション固定。
3. **Algorithm Evaluation（安いゲート→性能評価の二段）**: まず **実行不能・タイムアウトのコードを除去**（3000 生成 → フィルタ後の実行可能関数は typically 100〜300 個）。残りを M0 のマージに適用してモデルを作り、**開発セット**のタスクスコアで有効性を測る。**テストセットへの間接リークを防ぐため学習データ D は開発セットスコアのみで構成**。
4. **Algorithm Factory Refinement（生成器そのものを学習）★核心**: スコア上位 pw%（=3%）を chosen、下位 pl%（=10%）を rejected とする **選好ペア D を作り、DPO で factory を訓練**。これにより「効くアルゴリズムの特徴」を factory が学習し、次イテレーションでより良いコードを生む。LoRA rank 256、lr 1e-6、DPO β=0.01。
5. **Iterative Improvement + elitism**: これを 3 イテレーション反復。exploration-exploitation 調整のため **温度を減衰**（T1=1.2、減衰率 0.2 → T3=0.85）。t≥2 では **各前イテレーションの上位 3 アルゴリズムを D に持ち越す（エリート保存）**。生成アルゴリズムは常に固定の M0 に適用（factory は M0 改善に特化して訓練される）。
6. **既存手法との差別化（Related Work で明示）**: 従来の LLM アルゴリズム発見は「(1) 生成器自体が改善されない」「(2) GPT-4 等の外部強モデルに依存」の 2 限界を持つ。Self-Developing は **生成器を DPO で継続訓練** し **外部モデル非依存**でこの両方を克服。「アルゴリズムとそれを生む LLM の両方を再帰的に改善した初の研究」と主張。

## 主要な実験結果 / 主張（数値）

- **セットアップ**: seed=openchat-3.5-1210（Mistral-7B ベース、コード生成が強い）。マージ候補 3 個=Abel-7B-002 / OpenHermes-2.5-Mistral-7B / SciPhi-Mistral-7B-32k。mergekit で各 MLP 層の task vector に適用。GSM8k・MATH で 5-shot / Pass@1 / 貪欲デコード。A100 GPU。
- **GSM8k**: seed 70.1% → LLM 発見アルゴリズム最良 **76.1%（+6pt）**。人間設計 Task Arithmetic 71.9% を **+4.3pt**、TIES merge 71.8% を上回る（Model Stock は 39.5% と大きく劣化）。
- **MATH**: seed 0.5% → 最良 **8.5%**。Task Arithmetic 8.5% と同等、TIES 8.4% を僅かに上回る。
- **生成器訓練の効果（Table 2、イテレーション進行）**: GSM8k 70.1→75.8(M1)→76.0(M2)→76.1(M3)、MATH 0.5→7.0→7.5→**8.5**。**GSM8k は M1 で頭打ち、MATH は反復ごとに継続改善**。開発スコア分布も反復で低性能→高性能へシフト（Fig.4）。
- **転移性（Table 3、OOD 候補モデル WizardMath/Starling/BioMistral、再最適化なし）**: LLM 発見アルゴリズム上位 3 が GSM8k **78.8%** で、これら新候補向けに最適化した Task Arithmetic の最良 71.4% を **+7.4pt** 上回る。MATH でも 2.5% 対 TA 1.2% で 2 倍超。人間設計手法が事前定義の重み結合に縛られるのに対し、LLM は custom distance metric や適応的重み付けなど「より豊かなアルゴリズム空間」を探索できるのが要因。
- **限界（著者記載）**: 評価は数学推論タスク（GSM8k/MATH）のみ。計算資源制約で他ドメイン未検証。

## izanagi のどの層・部品に効くか

| izanagi 部品 | 効き方 | 強度 |
|---|---|---|
| **層2 最適化移植ループ** | 生成→評価→取捨→**生成器改良**の四段が Self-Developing のサイクルとほぼ同型。特に「取捨で終わらせず、accept/reject を選好データにして生成器を訓練する」は izanagi にまだ無い環。 | ★最強 |
| **評価器 (Phase1)** | 「実行不能/タイムアウト除去」= izanagi Tier 0（静的・構文チェック）と一致。**開発/テスト分離によるリーク防止**は izanagi の測定規律（§3.6）に直結。3000 生成→100〜300 実行可能という歩留まり数字は層2の試行予算設計に使える具体値。 | ★強 |
| **層3 選択** | 「開発セット上位 15 → テストで確定」「各反復の top-3 を持ち越す」= エリート保存 + Pareto 選択の骨格。多様性保存（roadmap §10）との対比材料。 | 中 |
| **orchestrator/hook** | 温度減衰スケジュール（explore→exploit）、選好ペア閾値（top 3% / bottom 10%）、反復回数=3 は orchestrator の探索制御パラメータの初期値参照になる。 | 中 |
| **層1 ベースCC選定** | 直接の対応はほぼ無し（seed=M0 をクローンして factory 初期化する程度）。 | 弱 |

## 具体的に izanagi に移植できる要素（設計レベル）

1. **選好データによる生成器の自己改善（DPO factory ループ）**: izanagi の生成器（Phase 3 coder / 将来の自己改善機構）を「固定プロンプト」から「過去の accept/reject を選好ペアにして継続訓練する生成器」へ格上げする設計。roadmap が Phase 3.5 に予約している自己改善機構（SkillOpt / Self-Harness 系譜）に対する**具体的かつ実証済みの実装レシピ**。
2. **選好ペア構築の閾値レシピ**: スコア上位 pw%=3% を chosen、下位 pl%=10% を rejected という閾値ベース抽出。izanagi の WAL / whiteboard に既に貯まる「採用/却下 + 性能分布」を、そのまま生成器へのステアリング信号（または訓練データ）に変換する具体手順。「却下を『やるな記憶』に留める」（SkillOpt）から一歩進め「却下を訓練負例として能動利用する」形。
3. **安いゲート→本評価の二段フィルタ + エリート持ち越し**: 「実行不能/タイムアウト即除去（μ秒級）→ 開発セット評価（高コスト）」は izanagi Tier 0 → Tier 1+ のエスカレーションと同型。加えて「各反復の上位 3 個を次反復に持ち越す」= island / 多様性保存の最小実装。
4. **温度減衰による explore-exploit 制御**: 反復初期は高温（多様性）、後期は低温（安定化）。izanagi 層2 の探索スケジューリングの初期設定。
5. **開発/テスト分離のリーク防止**: 選好データ D を開発セットスコアのみで作り、テストは最終 1 回だけ。izanagi の「測定シグナルの汚染防止」（§3.6）に整合する評価器規律。

## izanagi に入れる際の障害・前提・リスク

- **【最大の障害】正しさゲートの構造が根本的に違う**: 本論文には**ハードな正しさゲートが無い**。壊れたマージは「実行不能なら除去」「実行できれば低スコア」として扱われるだけで、"誤り" という概念が無い（性能スカラー一元）。izanagi では serializability 違反は**低スコアではなく即 reject**（絶対規律2、正しさは性能に対して辞書式優先）。したがって Self-Developing の「スコア上位/下位で選好ペア」をそのまま持ち込むと、**正しさゲートが選好学習に溶けて消える**危険がある。izanagi では「正しさ = 二値ゲート（据え置き）」と「性能 = 分布比較」を分けたまま選好データを作る設計が必須。
- **報酬信号が単一スカラー**: 本論文は task score 一元で回して成功しているが、**GSM8k は M1 で頭打ち（75.8→76.1）**。izanagi の roadmap §3.5（Jitskit 由来）は「スカラー一元では 8〜12 反復で探索が停滞する」と主張。本論文が 3 反復しか回していない点と GSM8k の早期プラトーは、この主張と整合する negative 傍証。izanagi は leading indicators を factory に返す必要がある（本論文にはこの環が無い）。
- **DPO 訓練コスト**: factory の毎反復 DPO 訓練（LoRA rank 256、A100）は GPU 前提。izanagi は当面ローカル/devcontainer 中心（D10）で、CC ベンチ自体が高コスト（1 variant 数十秒）。生成器訓練を毎反復挟むと予算が破綻しうる。izanagi では「生成器訓練」より軽い「in-context ステアリング（過去試行を prompt に入れる）」から始めるのが現実的で、DPO 化は Phase 3.5 予約が妥当。
- **探索対象の性質差**: 本論文の "アルゴリズム" は連続テンソル演算（重みの合成）で、微小な数式変化が連続的にスコアへ効く滑らかな空間。izanagi の variant は離散的な CC プロトコルコードで、正しさが崖のように壊れる。DPO の選好学習が効きやすい滑らかさが CC では保証されない。
- **reward hacking の入口が増える**: 生成器を性能スコアで訓練する = reward hack 圧力を生成器そのものに内在化させる。izanagi の auditor / hooks / verifier 入力側隔離（§3.4）を先に固めてからでないと、生成器が「検証を迂回して性能を稼ぐコード」を学習しかねない。

## 小山田さんに聞くべき質問（共著者への鋭い問い）

1. **正しさゲートと選好学習の両立**: Self-Developing は task score 一元で回りましたが、izanagi は serializability を「低スコア」ではなく「二値の据え置きゲート」で扱いたい。**正しさを選好学習に溶かさずに生成器を DPO で改善する**には、選好ペアをどう構成すべきでしょうか（例: 正しさ通過集合の中でだけ性能で chosen/rejected を切る、正しさ違反は選好対にすら入れない、等）。実験中に「正しさ相当の制約」を選好信号に混ぜて失敗した経験はありますか。
2. **スカラー報酬の停滞と反復回数**: 論文では 3 反復で、GSM8k は M1 で頭打ち・MATH のみ継続改善でした。**単一スカラーのまま反復を伸ばすとどこで停滞し**、leading indicator 的な追加信号を factory に返す設計は検討されましたか。izanagi が Jitskit 流に「lock contention / cache hit を生成器に返す」のは Self-Developing の自然な拡張になり得ますか。
3. **生成器訓練 vs in-context ステアリングの費用対効果**: 毎反復 DPO（LoRA/A100）は izanagi のベンチ高コスト環境では重い。**「生成器を訓練する」ことが「過去の高性能アルゴリズムを prompt に入れる in-context 手法」に対して本質的に効いた**のはどの局面か（ablation で分離できていますか）。エリート持ち越し（top-3）を prompt に入れるだけで DPO の利得の何割が再現できそうでしょうか。

## 引用/リンク

- 論文 (NAACL Anthology): https://aclanthology.org/2025.naacl-long.519/ ／ DOI: https://doi.org/10.18653/v1/2025.naacl-long.519
- arXiv (本文取得元): https://arxiv.org/abs/2410.15639 ／ HTML v5: https://arxiv.org/html/2410.15639v5
- 関連（izanagi 系譜）: Task Arithmetic (Ilharco+ 2023), TIES-Merging (Yadav+ 2023), mergekit (Goddard+ 2024), DPO (Rafailov+ 2023), AlphaEvolve (Novikov+ 2025)
- izanagi 内部対応: roadmap §2 層2 / §3.1 Tier0 / §3.5 leading indicators / §3.6 測定規律 / §7 SkillOpt・Self-Harness 系譜、agent-architecture.md coder/auditor/verifier
