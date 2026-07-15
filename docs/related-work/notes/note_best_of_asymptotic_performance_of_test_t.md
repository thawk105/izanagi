# 調査ノート: Best-of-∞ - Asymptotic Performance of Test-Time Compute

- **論文**: Best-of-∞ – Asymptotic Performance of Test-Time Compute (CoRR 2025, arXiv:2509.21091)
  - 著者: Junpei Komiyama (MBZUAI / NYU / RIKEN AIP), Daisuke Oba (Institute of Science Tokyo), Masafumi Oyamada (NEC)
  - URL: https://arxiv.org/abs/2509.21091 / DOI: 10.48550/arXiv.2509.21091
  - **本文取得経路**: `fetch_article_fulltext(doi=...)` は CrossRef 404 で失敗（DOI 未登録）。arXiv HTML 版 `https://arxiv.org/html/2509.21091v1`（LaTeXML 生成, 2025-09-25）を直接取得し全文精読。
  - 注記: arXiv abstract ページのタイトルは "...Asymptotic Performance of Test-Time **LLM Ensembling**"、本文ヘッダと DOI は "...Test-Time **Compute**"。同一論文の表記ゆれ。

## 問題設定 / 一言要約

Best-of-N（N 個生成して選ぶ）のうち **多数決 (majority voting) による選択** を対象に、テスト時計算を無限に増やした極限 **N→∞（= best-of-∞）** の漸近性能を理論的に定義・分析し、(1) 有限予算でその極限に迫る**適応サンプリング**、(2) 複数 LLM の**最適重み付きアンサンブル**（MILP で解ける）を提案した論文。核心の主張は「多数決は reward hacking に頑健で、N を増やすほど得をする（reward model のような過学習が起きない）」こと。

## 手法の核

1. **best-of-∞ の定義**: BoN 多数決を「答え分布からのサンプリング」と見なし、N→∞ で確定する母集団多数決を best-of-∞ 性能と定義。実験では BoN 精度は N=10¹→10² あたりで大きく伸び、その後漸近する（Figure 1）。
2. **適応サンプリング (Algorithm 1)**: 答え空間の台が未知なので **Dirichlet 過程事前分布 DP(H, α)** で答え分布をノンパラメトリックにモデル化。各生成後に「現在の最頻答えが真の多数派か」を **Bayes factor (BF)** で評価し、BF が閾値 B を超えたら（または N_max に達したら）生成を停止。**Theorem 1**: N_max, B→∞ で best-of-∞ 性能にほぼ確実に収束（一貫性）。BF は事後 Dirichlet からの Monte Carlo（1,000 サンプル）で推定。
3. **多数決の優位性の主張**: 追加のモデル化も追加生成も要らず、**reward hacking に頑健**。reward model は N を増やすと過学習しうるが、多数決は追加生成のリスクが最小（§Introduction）。
4. **LLM アンサンブル = 重み付き多数決**: K 個の LLM を重み w（確率単体上）で選んで生成し多数決。**Bo1 では最良単一 LLM に全振りが最適 (Lemma 1)** だが、**N>1 では非最良 LLM を混ぜる方が得になりうる**。目的関数 f(w) は**非凹 (Lemma 2)**（勾配法は不可）。
5. **MILP 定式化**: 「答え j が多数派になる w の集合」は**ポリトープ (Lemma 3)**。よって f(w) 最大化は補助 0/1 変数 y_q を導入した **混合整数線形計画 (MILP) (Lemma 4)** に帰着。NP 困難だが、OSS ソルバ (HiGHS/highspy) で K≈10¹ LLM・N≈10³ 問題・|答え空間|≈10¹ の規模まで実用的に解ける。
6. **max-margin 解**: best-of-∞ の最適解は連続領域を成すので、有限 N でも安定な「最も内側」の解をマージン ξ の二分探索で選ぶ。

## 主要な実験結果 / 主張（数値）

- **規模**: 11 個の instruction-tuned LLM（≤32B）× 4 つの重推論データセット（AIME2024, AIME2025, GPQA-DIAMOND, MATH500）、各 (LLM, 問題) ペアで **≥80 世代**生成（技術報告で標準的な 8 世代の一桁上）。生成物を公開。
- **適応サンプリングの効率 (Set 1, GPT-OSS-20B / MATH500)**: 適応平均 **N̄=3 が固定 N=10 と同精度**、**N̄≈10 が固定 N=100 と同精度** → **計算 2–5 倍削減**。約 80 サンプルで best-of-∞ にほぼ到達。
- **アンサンブルの優位 (Set 2, GPQA-Diamond)**: 5 モデル最適重み w=(0.018, 0.035, 0.269, 0.415, 0.264) のアンサンブルが N≥5 で任意の単一 LLM を上回る。
- **相補性 (AIME2025)**: GPT-OSS-20B が best-of-∞ で **90.0%**、Nemotron-Nano-9B-v2 が **73.0%**、両者のアンサンブルが **93.3%**（弱いモデルでも相補的なら寄与）。
- **重み学習 (Set 3, AIME2025)**: わずか 5 問で学習した重みが最良単一 LLM 性能に接近。最適重みの極限精度 93.3% vs 最良単一 90.0%。
- **転移 (Set 4)**: AIME2024 で学習した重みを AIME2025 に適用、165 個の 3 モデル組合せ中 **106 個 (64.2%)** でアンサンブルが最強単一モデルに一致 or 上回った。
- **選択法比較 (Set 5, Bo5, AIME2025, GPT-OSS-20B 生成)**: 多数決 **85.42±2.01** > LLM-as-judge (tournament) 82.92 / (set) 81.25 > reward model (INF-ORM 79.79 / Skywork-V2 79.79–80.00) > self-certainty 75.83、random 76.25。上界 Omniscient 91.04。**多数決がすべての learned selector を上回った。**
- ハイパラ: α=0.3 固定、BF は 1,000 MC サンプル、結果は 100 独立試行の平均。

## izanagi のどの層・部品に効くか

**主戦場は「評価器 (Phase1)」と、探索予算の設計思想。** 論文はコード合成でなく答え集約の話なので、機構の直輸入ではなく「逐次停止・予算配分・reward hacking 頑健性」という**方法論と外部証拠**として効く。

- **評価器 §3.2（二相設計・確率的正しさ保証）★最有力**: izanagi は「seed を変えて N 回回して全部 cycle 無し → 信頼度 1-εⁿ」という素朴な固定回数の確率保証。Best-of-∞ の **Bayes factor 逐次停止**は、この「何 seed 回せば多数派の判定を信頼できるか」を**原理的な逐次ベイズ検定**に置き換える直接の型。「簡単な variant は早く止め、際どいものだけ深く回す」＝ izanagi の二段構え (screening→検証相) の定量版。
- **評価器 §3.6（測定安定性・自動再測定）**: 「CV が閾値超過→自動再測定、規定回数で収束しなければ unstable フラグ」を、Bayes factor 的な逐次停止則で置換・厳密化できる。ただし throughput は**連続量**で本論文の**カテゴリ多数決**とは型が違う（後述リスク）。
- **§3.4 reward hacking 対策への外部証拠**: 「LLM-as-judge は gameable なので正しさ経路に入れない」という izanagi の設計判断に対し、**Bo5 比較表（多数決 > LLM-as-judge > reward model）が引用可能な実証データ点**になる。「gameable なスカラ報酬より頑健な集約を選ぶ」の一般則。
- **探索予算の設計（層2 / §5 計算リソース）**: 「BoN は N=10¹→10² で伸び、その後漸近」「80 世代は標準 8 世代の一桁上」は、izanagi の「一晩 1 万 run 回す／variant を何個試すべきか」の**収穫逓減カーブと予算設計の外部フレーム**。
- **層3（variant 比較・選択）＝弱い共鳴**: MILP アンサンブルの相補性は「throughput 最強 1 個でなく特性の違う variant を残す」§10 多様性保存と方向が同じ。ただし izanagi の最終成果物は**単一 CC** なのでアンサンブル出力は直行しない（後述の議論候補）。

## 具体的に izanagi に移植できる要素（設計レベル）

1. **正しさ検証の逐次ベイズ停止則**: §3.2 検証相の「固定 N seed」を、多数決判定（serializable / anomaly 有り）に対する Bayes factor 逐次停止に置換。閾値 B が信頼度、N_max が予算上限。「易しい variant は 3–5 seed で確定、際どいものだけ深掘り」で 2–5 倍の検証コスト削減が期待できる（カテゴリ判定なので DP/BF 機構がほぼそのまま乗る）。
2. **性能測定の逐次停止（連続版）**: §3.6(2) の CV ベース再測定を「baseline との差が noise floor を跨ぐか」の逐次検定に格上げ。差が明確に分離した variant は早期停止、境界付近だけ反復増。連続量なので BF でなく izanagi が既に挙げる Mann-Whitney U の逐次版 / 逐次 t 検定を使う（機構は差し替え、思想は同型）。
3. **reward-hacking 頑健性の設計原則の明文化**: 「集約は gameable なスカラ報酬でなく構造的多数決/客観検査で行う」を Bo5 表を根拠に decisions.md へ。verifier を trace-cycle 検出（客観）に据える現行判断の外部裏付け。
4. **予算配分の経済フレーム**: §2 low-fidelity proxy・§3.5 profiling-only-for-promising の「際どいケースに予算を寄せる」を Best-of-∞ の cost-analysis（N̄=3≈fixed10）で定量的に引用。査読の「なぜ全 variant を深く測らないのか」への論拠補強（既存の arXiv 2606.07489 引用と併用）。
5. **（保留）アンサンブル/ポートフォリオ出力**: 層3 で単一 CC でなく「ワークロード相ごとに切替える CC ポートフォリオ」を出す拡張の理論的裏付けとして MILP 重み最適化・相補性を将来予約（現スコープは単一 CC）。

## izanagi に入れる際の障害・前提・リスク

- **型の不一致（最大の壁）**: 本論文の Bayes factor / Dirichlet 過程は**離散カテゴリ出力（どの答えが多数派か）**用。izanagi の性能測定は**連続量 throughput** なので DP/BF はそのまま乗らない（連続用の逐次検定に差し替え要）。一方 **正しさ判定（pass/fail のカテゴリ）には直接適用可能** — ここが移植のスイートスポット。
- **i.i.d. 前提 vs 非定常ノイズ**: 適応停止は「固定分布からの i.i.d. サンプル」を仮定。izanagi の一晩ループは熱スロットリング・他プロセス等で分布が**ドリフト/非定常**（§3.6）。逐次停止則が非定常下で偽の早期停止を招く危険。
- **合成 ≠ 集約**: 本論文は「生成済み答えの集約」で、izanagi の関心である**プログラム空間の探索・合成**ではない。variant 探索への適用は類推であって直輸入ではない（ノートでは明確に区別すべき）。
- **アンサンブル前提の齟齬**: MILP は**固定された K モデル**を前提。izanagi の variant は探索で**生成される**もので、事前固定集合ではない。層3 への適用は概念借用に留まる。
- **本文から特定できず**: 適応サンプリング単体の削減率の全データセット横断値、GPQA 以外のアンサンブル重み、α や B の感度分析の詳細（Appendix F 記載だが本精読では未確認）。

## 小山田さんに聞くべき質問

1. **非定常下の逐次停止**: 適応サンプリングの Bayes factor 停止は固定分布・i.i.d. を前提していますが、izanagi のベンチ測定は一晩で熱/負荷ドリフトが混入する非定常環境です。分布自体が動くとき、偽の早期停止を防ぐ形で DP/BF 逐次停止をどう頑健化しますか（あるいは連続量には別の逐次検定を推す）？
2. **learned selector を排除する境界**: Bo5 表で多数決が LLM-as-judge・reward model を上回りました。izanagi は正しさ経路から LLM-as-judge を排除していますが、**性能ランキング（層3 の soft な選択）**でも learned selector は避けるべきという立場ですか、それとも reward model が安全に効く領域はありますか？
3. **単一 CC vs ポートフォリオ出力**: MILP の相補性（弱いモデルも相補的なら寄与）を CC 合成に持ち込むと、「単一の最速 CC」でなく「ワークロード相ごとに切替える CC ポートフォリオ」を出す価値はありますか？ best-of-∞ の complementarity 論は「遅いが特定相で相補的な CC」にも一般化できると見ますか？

## 引用/リンク

- 本論文: arXiv:2509.21091 — https://arxiv.org/abs/2509.21091 (HTML: /html/2509.21091v1)
- izanagi 設計ドキュメント（参照のみ）: docs/roadmap.md §2（三層）, §3.2（二相設計）, §3.4（reward hacking）, §3.6（測定安定性）, §5（計算リソース）, §10（スコープ外・多様性保存）
- 関連（dossier Tier A）: Effective Harness Engineering (arXiv:2605.15221), Can LLMs Invent Algorithms (NAACL 2025), DISC (NeurIPS 2025)
