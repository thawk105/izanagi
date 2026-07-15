# 調査ノート: LaMDAgent: An Autonomous Framework for Post-Training Pipeline Optimization via LLM Agents

- **論文:** EMNLP 2025 (Main), 著者: Taro Yano, Yoichi Ishibashi, **Masafumi Oyamada** (全員 NEC Corporation)。
  DOI: 10.18653/v1/2025.emnlp-main.1529 / arXiv: 2505.21963。
  **本文取得経路:** `fetch_article_fulltext(doi=…emnlp-main.1529)` は失敗（Unpaywall=連絡先メール未共有でskip / Semantic Scholar=404 / PMC=PMCIDなし / Crossref TDM=リンクなし / DOIランディングページはHTMLスクレイピング要）。arXiv DOI 経由の取得も Crossref 未登録で失敗。最終的に **web_search で arXiv 2505.21963 を特定 → `https://arxiv.org/html/2505.21963v1` を curl で取得（HTML 288KB, LaTeXML 生成 v1）**、正規表現でテキスト抽出して精読。数値は本文表・図キャプションから採取。

- **問題設定 / 一言要約:**
  SFT・選好学習・モデルマージといった **post-training の各手法は個別に研究されてきたが、完全な post-training パイプライン全体（どのデータをどの順で、どの手法をどう組み合わせるか）を自動構築する研究は手薄**。LaMDAgent（Language Model Developing Agent）は、LLM エージェントに「モデル改善アクション」を選ばせ、下流タスクのスコアを報酬として **パイプライン全体を自律探索・最適化**するフレームワーク。人手設計が見落とす有効な戦略を発見できる、と主張。

- **手法の核（4ステップの反復ループ）:**
  1. **Action Enumeration（アクション列挙）:** 「Object（Llama/Gemma などのモデル、GSM8k などのデータ、ハイパラなどの具体物）」と「Action type（"SFT"・"TIES-Merging" など、複数 object を入力に取り新モデルを出す改善手法）」を定義し、**アクション = (action type, objects) の全組み合わせを列挙**する。反復途中で生成されたモデル・データも object pool に加わる。
  2. **Action Selection（2段推論での選択）:** エージェント（`gpt-4o-2024-08-06`）に **まず action type を1推論で選ばせ → 必要な object 型を確定 → 次の推論で object をまとめて選ばせる**。1発で全部やらせると parse 失敗が増えるため段階化。object は順序依存を避けるため単一推論でまとめて選ぶ。プロンプトには過去試行を要約した memory を含める。
  3. **Model Evaluation（数値スコアのフィードバック）:** 生成モデルを下流タスクで評価しスカラースコアを返す。マルチタスクは **スケール係数付き加重和 `s_multi = Σ_k α_k · s_single^k`**（各タスクの最大寄与が均一になるよう α を設定。例: MT-Bench=10点満点なので α=1/10、AceBench=1点満点なので α=1）。
  4. **Memory Update（テキスト記憶の自己反省更新）:** 直近＋過去の (action, score) と旧 memory を LLM に渡し、**「経験の要約 + 次に探索すべき有望な方向」を数文のテキストとして更新**（プロンプトテンプレートは Fig 2 に明示）。次の Action Selection の入力になる。
  - **実務上の重要な発見（プロンプト工学）:** 予備実験で **mode collapse（同じアクションを選び続ける）** が起きたため、プロンプトに**明示的な探索指示**を追加。さらに中間生成モデル（"Model i" と命名）が初期モデル（"Model GSM8k"）より選ばれにくい**命名バイアス**を観測し、**debias 指示**を追加した。
  - **正しさゲートは持たない。** 評価は純粋にスカラー報酬（タスク精度）のみ。「壊れたモデルを弾く」検証相当は存在せず、破壊的アクションは **報酬フィードバック経由で「学習して回避」**する設計（Exp2 の catastrophic forgetting 回避の説明）。

- **主要な実験結果 / 主張（数値）:**
  - **Exp1（Gemma2 2B ベースモデルに複数スキル付与、GSM8k/CQA/TriviaQA を multi-task、100 iterations, temp=0）:** LaMDAgent Top-1 の平均 **0.458 vs Fully Fine-Tuned 0.439（+1.9 点）**、Top-2 は 0.463。特に **数学系4タスク平均で Fully Fine-Tuned を +3.7 点**上回り、他タスクは維持。この設定では Fully Fine-Tuned > TIES(Grid Search) 0.363 で、**「複数スキル獲得はマージより学習が有効」**（一部先行研究と逆）。
  - **アクション選択の ablation（Table 2, validation は括弧内）:** Policy=LLM+Actions(SFT,TIES) **0.527 (val 0.603)** > Policy=Random 同アクション **0.508 (val 0.556)** > Policy=LLM+Actions(TIESのみ) **0.398 (val 0.456)**。→ **LLM 選択は random にわずかに勝つが差は小さい。むしろ与えるアクション空間の設計が支配的**（SFT を外すと大崩れ）。
  - **Exp2（Gemma2 2B **Instruct** に tool-use を付与しつつ instruction-following を維持、AceBench + MT-Bench turn1）:** ベスト生成モデルで **AceBench 0.410 → 0.500（+9.0 点）、MT-Bench 0.804 → 0.810 で維持**。一方 naive な全データ SFT は両方悪化（alignment tax / catastrophic forgetting 仮説）。Fig 5 は **avg score が100 iterations にわたり単調に近く上昇しつつ、max score 改善と非ゼロ標準偏差で exploit と explore が両立**することを示す。
  - **「訓練分布と目標分布が乖離するほど LaMDAgent の利得が大きい」**（Exp2 > Exp1 の差の説明）。
  - **計算コスト削減:** **データサイズスケーリングは有効**（小データで良いパイプラインは 2/4/6 倍でも Top-1 が最良を維持 = low-fidelity proxy が効く）。**モデルサイズスケーリングは限界あり**（2B→9B 転移で、2B で ~3点差だった Top-1 vs Top-50 が **9B で逆転** [2B: 0.603 vs 0.573 → 9B: 0.797 vs 0.803]。5点超の大きな差は保たれる）。教訓: **「消えかねない小さな差を追うより、アクション空間を多様化して大きな差を探せ」**。
  - **限界（本文明記）:** ベースは Gemma2 のみ・英語のみ・アクション種は SFT/TIES に限定（選好学習・データ生成・他マージ手法は未検証）・モデルサイズスケーリングは positive transfer に至らず。

- **izanagi のどの層・部品に効くか:**
  - **層2（最適化移植ループ）＝ 直撃・最重要。** LaMDAgent の 4 ステップ（列挙→選択→評価→memory 更新）は izanagi 層2 の「抽出→生成→評価→取捨」と **アーキテクチャがほぼ 1:1**。しかも著者に小山田さんを含む NEC 内製の実装知見であり、izanagi 層2 ループの**参照実装**として最も近い先行例。特に (a) パラメータ粒度探索（roadmap §2「まず (a) を主軸」）と、object×action-type の有限組み合わせ列挙が同型。
  - **評価器（Phase1）＝ 反面教師的に効く。** LaMDAgent は**正しさゲートを持たずスカラー報酬のみ**。izanagi の絶対規律2（据え置きの正しさゲート）・§3.4 reward hacking 対策が LaMDAgent に対する**明確な差別化点**であることを裏書きする（＝ izanagi の新規性ポジショニングの補強材料）。
  - **orchestrator（探索ループ制御）＝ mode collapse / debias の実装知見が効く。** プロンプトによる探索継続の強制は roadmap §3.4-3「探索の自己崩壊対策」の具体的手口。
  - **層3（比較・選択）＝ スケーリングの教訓が効く。** 「小さな差は消える／逆転する」は izanagi §3.6 noise floor・§4 スケール感度検出と同方向の**独立した経験的証拠**。
  - 層1（ベース CC 選定）への直接寄与は薄い（LaMDAgent はベース選定でなくパイプライン構築）。

- **具体的に izanagi に移植できる要素（設計レベル）:**
  1. **アクションの (type, objects) 二段構造と 2 段推論選択:** izanagi 層2 の variant 生成を「まず最適化カテゴリ（CCBench の CPU cache / delay-on-conflict / version lifetime の3カテゴリ）を選ぶ → 次に具体パラメータ/移植元 object を選ぶ」の2段に分解。**parse 失敗と選択の順序依存を減らす**具体策として直接採れる。roadmap §2 の「最適化カタログ（前提/効果/実装）」が LaMDAgent の action-type 定義に対応。
  2. **テキスト memory による探索方向づけ（whiteboard memory の具体テンプレ）:** Fig 2 の memory 更新プロンプト（過去結果＋旧 memory＋新結果 → 「要約＋次の有望方向」を数文で）は、izanagi の whiteboard memory / LLM 誘導探索（roadmap §2「層2 → 探索戦略」の「過去試行を context に入れて次の一手を方向づけ」）の**すぐ使えるプロンプト雛形**。
  3. **mode collapse 対策と命名バイアス対策:** 探索指示の明示化＋生成物の命名バイアス除去。izanagi の variant も「Model i」的な命名になるため、**同じバイアスを先回りで潰す**設計に採れる。
  4. **データサイズスケーリングによるコスト削減:** 「小規模で選抜 → 有望パイプラインだけデータ増」は izanagi §2 の low-fidelity proxy / §5 スケールダウン運用の**実証済み裏付け**。izanagi の「小スケールで screening → 有望 variant だけ本ベンチ」を LaMDAgent の Fig 7 結果で正当化できる。
  5. **モデル/スケール転移時の「大きな差だけ追え」原則:** 層3 選択と §3.6(4) 分布比較に、「スケール変更で消える差は採否根拠にしない」の**外部証拠**として引用。izanagi の noise-floor 丸めと同じ結論に別ドメインから到達している。
  6. **LLM-vs-random ablation の実験設計テンプレ:** izanagi Phase 2 の「全探索 vs LLM 誘導」比較（roadmap §9 Phase2）の**対照実験の型**として流用可能。加えて「アクション空間そのものの寄与を測る」ablation（LaMDAgent が SFT 抜きを比較）も CCBench 最適化フラグの取捨で再現できる。

- **izanagi に入れる際の障害・前提・リスク:**
  - **正しさ次元が完全に欠落している。** LaMDAgent の評価はスカラー精度のみで serializability 検証も reward-hack 防御もない。izanagi は絶対規律2 の正しさゲートを LaMDAgent の memory/報酬機構の**外側**に据え置く必要があり、memory 経由で「正しさを緩めれば速い」を学習させてはならない（DecentMem/SkillOpt に対する izanagi の一貫姿勢と同じ）。
  - **LLM 誘導の利得は小さいかもしれない。** Exp1 では LLM 選択が random に対し test で +1.9 点、val で 0.603 vs 0.556 程度。izanagi の有限な CCBench フラグ空間（~2^7）では **全探索が現実的なぶん、LLM 誘導の速度優位が小さく出る恐れ**がある。izanagi の主価値は探索速度より層3 の説明生成にある、という前提と整合させておくべき（期待値の較正）。
  - **スカラーのみで100 iteration 収束した事実が Jitskit の主張と緊張する。** izanagi は §3.5（Jitskit）に依拠して「スカラー throughput だけだと 8–12 iteration で停滞、leading indicators が収束に必須」としているが、LaMDAgent は **leading indicator なしのスカラー報酬 + テキスト memory で 100 iteration にわたり単調改善**（Fig 5）を示している。この差が「タスク構造の違い」か「テキスト memory の効き」かは未解明で、izanagi の leading-indicators 前提を無条件に信じる根拠を弱める可能性がある（→ 小山田さんへの質問）。
  - **アクション空間が固定・パラメータ粒度に留まる。** LaMDAgent は SFT/TIES の2種のみで、コード粒度（izanagi の (b) EVOLVE-BLOCK）やアルゴリズム粒度は扱っていない。izanagi 層2 の (a) を支えるが **(b) の裏付けにはならない**。
  - **評価コストの前提が違う。** LaMDAgent の1アクション = 実訓練 run（重い）。izanagi は1 variant = 数十秒ベンチ（roadmap §5）。反復回数や探索予算の設計はそのまま流用できず、izanagi 側のコスト構造で再設計が要る。
  - **観測者効果・測定安定性の概念がない。** temp=0 で乱数は消しているが、izanagi の §3.3 観測者効果分離・§3.6 測定分布の規律は LaMDAgent には存在しない。移植するのはループ構造であって評価規律ではない。

- **小山田さんに聞くべき質問（1〜3個）:**
  1. **「LaMDAgent はスカラー報酬 + テキスト memory だけで 100 iteration 単調改善した（Fig 5）。一方 Jitskit 系は『スカラーだけだと 8–12 iteration で停滞し leading indicators が必須』と言う。この差は何が効いたのか——タスク構造（post-training は破壊的アクションが少ない？）か、テキスト memory の反省機構か？ izanagi の CC 探索でも leading indicators なしのテキスト memory で十分収束すると思うか、それとも CC は observability（lock contention 等）が本質的に効くと見るか？」** ← izanagi の §3.5 前提の根幹を突く。
  2. **「Exp1 で LLM 選択の random に対する優位は test で +1.9 点と小さく、アクション空間の設計（SFT 抜きで大崩れ）の方が支配的だった。izanagi のように探索空間が有限で全探索可能な場合、LLM 誘導の価値はどこにあると考えるか——到達速度か、それとも到達解の説明（izanagi の層3 の核心）か？」** ← izanagi の新規性ポジショニングの検証。
  3. **「モデルサイズスケーリングで小さな順位差が逆転した（2B Top-1 vs Top-50 が 9B で反転）。izanagi はラップトップでスケールダウンして測り、ランキングを信じたい。LaMDAgent では『どの差が本物か／スケールで消えるか』をどう線引きしたのか。noise floor のような定量基準はあったか、それとも『5点超だけ信じる』のような経験則だったか？」** ← izanagi §3.6 noise floor / §4 スケール感度検出の設計裏付け。

- **引用/リンク:**
  - 論文（ACL Anthology）: https://aclanthology.org/2025.emnlp-main.1529/ （DOI: 10.18653/v1/2025.emnlp-main.1529）
  - arXiv: https://arxiv.org/abs/2505.21963 / 本文取得元 HTML: https://arxiv.org/html/2505.21963v1
  - 主要参照: Table 1（Exp1 主結果）, Table 2（アクション選択 ablation）, Table 3（モデルサイズ転移）, Fig 2（memory 更新プロンプト）, Fig 4–5（Exp2）, Fig 7（データサイズスケーリング）
  - izanagi 側の対応箇所: roadmap §2（三層・層2 (a)/(b)/(c)、および「探索戦略」節）, §3.4 reward hacking, §3.5 leading indicators, §3.6 測定安定性, §4 calibration/scale sensitivity, §9 Phase2（全探索 vs LLM誘導）; agent-architecture.md（whiteboard memory）; orchestrator-design.md（探索ループ）
