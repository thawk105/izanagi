# 関連研究からの借用 (roadmap §7 から分離)

`docs/roadmap.md` §7 の本体。2026-07-05 に分離した (D35 — ブートコスト規律: 本文書を読むのは
論文執筆・ポジショニング検討・新規関連研究の追加時のみ。日常セッションのブートには不要)。
roadmap 本文や他文書の「roadmap §7」参照は本文書を指す。追加・更新の扱いは roadmap 本体と同じ。

2026-07-10 にスタイルを再編した (統一エントリテンプレート + 判定タグ + 逆引き索引 + 柱分類、
ShinkaEvolve 深掘りは `shinka-deepdive.md` に分離)。技術的判断・ニュアンスは
再編前から変えていない。arXiv ID は 2026-07-10 に arxiv_get_papers または arxiv_search で
実在確認済みのもののみ記載し (CCBench 2009.11558 / AlphaEvolve 2506.13131 / OCC-timestamp
1811.04967 は arxiv_get_papers で全文メタデータを取得、他は arxiv_search 結果レコードで
タイトル・著者・発表年を照合)、未確証の基盤研究は venue/名称のみ (捏造回避)。
2026-07-15 追加分 (7.2/7.4/7.5 の NEC 小山田グループ 7 本) は curl による arXiv abstract
ページのタイトル照合で実在確認した。

---

## 7. 関連研究からの借用

### 7.0 読み方

各エントリは次の統一スキーマ。冒頭の構造化ヘッダで「採るのか・どの規律に接地するのか・
ID をいつ検証したか」が一目で追える:

```
### <名前> <`arXiv id` または venue>
`判定: <タグ>` · `接地: <規律/決定/節>` · `id検証: <日付 または 未検証>`
**一言:** 何をする研究か
**採る:** 借用する思想/部品 (無ければ「なし」)
**採らない:** 非採用の機構と理由 (該当時のみ)
**系譜上の位置:** 他エントリとの関係
```

**判定タグの語彙:**

| タグ | 意味 |
|---|---|
| `採用` | 機構/部品を実装に取り込み済み (§参照付き) |
| `部品予約` | 特定部品を借用するが着手は将来段 (規律5) |
| `思想` | 設計思想・問題設定のみ借用、機構は非実装 |
| `外部補強` | Izanagi の既存判断を裏付ける外部証拠 |
| `反面教師` | "採ってはいけない" 設計として参照 |
| `点検レンズ` | 既存設計が業界経験則と外れていないかの sanity check |
| `引用元` | 論文執筆時の論拠/引用に使う (実装しない) |

複合判定 (例: ARA = `採用`+`部品予約`+`反面教師`) はタグ併記。

**逆引き索引 (論文執筆時はまずここを見て本文へ飛ぶ):**

| 研究 | 識別子 | 判定 | 接地する Izanagi 要素 | 柱 |
|---|---|---|---|---|
| CCBench | `2009.11558` (VLDB 2020) | `外部補強` | 素材コーパスの学術的出自 | 7.1 |
| Polyjuice / CCaaLF→NeurCC | `2105.10329` / `2503.10036` (SIGMOD 2026) | `思想` | 層2 の祖先、新規性主張の核 | 7.1 |
| ATCC | `2603.13906` | `思想` | 未知/エージェント的ワークロードへの CC 適応 (最新競合) | 7.1 |
| DB knob チューニング系譜 (OtterTune/CDBTune/QTune/UDO) | SIGMOD 2017 ほか | `引用元` | 「選択 vs 合成」の境界線、P2-5 の外部文脈 | 7.1 |
| learned DB components 系譜 (Kraska/ALEX/PGM/Neo/Bao) | `1712.01208` ほか | `引用元`+`外部補強` | 物語の源流、実行時推論ゼロの必然性 | 7.1 |
| AlphaEvolve | `2506.13131` (白書) | `思想` | 進化的コード合成の源流、EVOLVE-BLOCK の出典 | 7.2 |
| Darwin Gödel Machine | `2505.22954` | `思想` | 自己改善系譜の理論的源流 | 7.2 |
| FunSearch | *Nature* 625 (2024) | `思想` | LLM×進化ループの先駆 | 7.2 |
| ShinkaEvolve | `2509.19349` (ICLR 2026) | `反面教師`+`部品予約` | 最直接の比較対象、リーク制御の対極 | 7.2 |
| Effective Harness Engineering (Vesper) | `2605.15221` | `外部補強` | auditor / worktree / 少数深掘り / digest 射影 | 7.2 |
| Best-of-∞ | `2509.21091` | `部品予約` | 正しさ検証の逐次停止 / learned selector 排除 | 7.2 |
| DISC | `2502.16706` | `思想` | 評価予算の難所配分 / 分布比較 | 7.2 |
| Jitskit | `2605.24096` | `採用`(部品多数) | spec cards / auditor / leading indicators 他 | 7.3 |
| VibeServe | `2605.06068` | `思想` | 対象特化合成の賭け、orchestrator D の先行例 | 7.3 |
| IDS | `2605.23109` | `思想` | 「正しさを後付けにしない」= 規律3 | 7.3 |
| SkillOpt | `2605.23904` | `外部補強` | whiteboard / validation gate=規律2 | 7.4 |
| Self-Harness | `2606.09498` | `外部補強` | validation gate=規律2 / verifier-grounded=規律3 | 7.4 |
| DecentMem | `2605.22721` | `外部補強` | whiteboard 二プール構造の理論裏付け | 7.4 |
| ARA | `2604.24658` | `採用`+`部品予約`+`反面教師` | anti-fabrication isolation (§3.4) 他 | 7.4 |
| Self-Developing | `2410.15639` | `部品予約` | accept/reject による生成器ステアリング | 7.4 |
| LaMDAgent | `2505.21963` | `反面教師` | 層2 ループの近傍例 / 正しさゲート欠落との対比 | 7.4 |
| How AI Agents Reshape Knowledge Work | `2606.07489` | `引用元` | 二段構え (Tier0-3/profiling) の経済学的引用元 | 7.5 |
| 12-factor-agents | github | `点検レンズ` | orchestrator/サブエージェント設計の sanity check | 7.5 |
| ECC | github | `点検レンズ`(運用参考3点) | tools/model 明示 / hooks 機械執行 | 7.5 |
| cotomi Act | `2605.03231` | `反面教師` | evaluator-integrity / コンテキスト衛生 | 7.5 |
| D2I (Learning Deliberately, Acting Intuitively) | `2507.06999` | `外部補強` | 二相分離 / 層3 の機序説明 | 7.5 |

---

### 7.1 並行性制御側の系譜 (素材コーパス + 学習型 CC)

Izanagi の直球。ワークロードに合わせて CC を設計/学習/合成する系譜と、その素材となる古典 CC。

#### CCBench `2009.11558` (VLDB 2020)
`判定: 外部補強` · `接地: 層1/層2 の素材コーパス` · `id検証: 2026-07-10`
**一言:** Takayuki Tanabe; Takashi Hoshino; Hideyuki Kawashima。主要 in-memory CC プロトコルを
共通基盤に再実装し同一ワークロードで比較する分析プラットフォーム。
**採る:** Izanagi の層1/層2 が変異させる「素材」そのものの出自。CC 側 related-work の一次アンカー。
**系譜上の位置:** 以下の素材プロトコルの共通実装基盤。Izanagi はこの固定設計の集合をかき混ぜて
variant を析出させる。

CCBench が実装し Izanagi が素材とする各プロトコルの正典出典
(`external/ccbench/docs/protocols_en.md` より接地):
- **Silo** — Tu et al., SOSP 2013
- **TicToc** — Yu et al., SIGMOD 2016
- **MOCC** — Wang et al., VLDB 2017
- **Cicada** — Lim et al., SIGMOD 2017
- **ERMIA (+SSN)** — Kim et al., SIGMOD 2016; Wang et al., VLDB 2017
- **MVTO** — Reed, 1978
- **SS2PL / SI / Oze / D2PL** — baseline locking / snapshot isolation / MV-OCC variant / deterministic 2PL

近傍の実測研究として **OCC のタイムスタンプ粒度の性能影響** (`1811.04967`, Huang; Bai; Kohler) —
Silo 系 OCC のチューニング軸を実測で示しており、Izanagi がフラグ空間外に求める
「新しい変異軸」の探索対象の一例。

#### Polyjuice / CCaaLF→NeurCC `2105.10329` (OSDI 2021) / `2503.10036` (SIGMOD 2026)
`判定: 思想` · `接地: 層2, 新規性主張` · `id検証: 2026-07-10 (実装状態調査 worklog 2026-07-10 (8) で v4 改題・採択を確認)`
**一言:** CC をアクション (wait粒度 / dirty read有無 / write expose / early validation) に分解して
進化的に学習する、層2 の思想的祖先。CCaaLF は CC を学習可能関数としてモデル化し関数近似へ一般化 —
v4 (2026-03) で **NeurCC に改名**され SIGMOD 2026 (PACMMOD Vol.4 Issue 3, DOI 10.1145/3802088) に
採択済み。引用時は CCaaLF = NeurCC の名前対応を明記する。
**採る:** 「CC をアクション列に分解して探索する」問題設定。
**採らない:** 「事前定義したアクション空間の中での最適配合探索」に留まる点 — Izanagi の (b)
コード移植は「アクション空間自体を LLM が拡張する」点で質的に違う (新規性の核)。
**実装と比較可能性:** 両者とも公開実装あり — Polyjuice = github.com/derFischer/Polyjuice (OSDI 2021
公式アーティファクト、2021 年凍結・TF 1.14 世代 toolchain)、NeurCC = github.com/neurdb/neurcc
(Docker あり、コミット 1 本)。**いずれも Silo codebase 上の実装で CCBench とは別基盤** — 絶対値の
直接比較は CCBench 自身の中心主張 (プロトコル比較は同一基盤で測れ) と衝突する。**実測比較は
見送りで決着** (ユーザー協議 2026-07-10、worklog 2026-07-10 (9)): 事前登録の headline 4 対照は
CCBench 内 + LLM なし対照で完結し、査読対応は本エントリの質的差別化 + 論文数値のオーダー引用で
足りる。再判断は「学習型 CC を定量的に上回る」を headline へ昇格させる場合のみ (最小構成・工数は
worklog 2026-07-10 (8) の材料が正本)。
**系譜上の位置:** 学習型 CC の起点。ATCC が同系譜の最新。

#### ATCC `2603.13906`
`判定: 思想` · `接地: spec card ワークロード設定` · `id検証: 2026-07-10`
**一言:** LLM 駆動エージェントの非決定的トランザクション特性に適応する学習型並行制御。
**採る:** 「未知・適応的ワークロードへの CC 適応」という問題設定 — Izanagi の対象設定
(spec card で与えられる未知ワークロード) と正面から重なる直近の比較対象。
**系譜上の位置:** Polyjuice → CCaaLF → ATCC と続く系譜の最新。

> **系譜の重心移動 (2021→2026):** 固定アクション空間の配合最適化 (Polyjuice) → 学習可能関数化
> (CCaaLF) → 未知/エージェント的ワークロードへの適応 (ATCC)。Izanagi の賭け — *LLM が
> アクション空間自体をコードで拡張する* — はこの延長線上で最も外側にあり、既存研究が正面から
> 扱う例は本調査では未発見 (新規性主張の外堀は埋まっている)。

#### DB 自動チューニング (knob tuning) 系譜 — OtterTune / CDBTune / QTune / UDO
`判定: 引用元` · `接地: P2-5 negative result (フラグ探索は自明) の外部文脈` · `id検証: 2026-07-10 (一次資料 PDF 4/4 精読、worklog 2026-07-10 (8))`
**一言:** DBMS の設定 knob を ML/RL で自動チューニングする系譜。OtterTune (Van Aken et al.,
SIGMOD 2017) = GP 回帰 + workload mapping の起点 / CDBTune (SIGMOD 2019) = DDPG による
end-to-end 強化学習化 / QTune (VLDB 2019) = クエリ認識 (DS-DDPG、3 粒度) / UDO (`2104.01744`,
VLDB 2021) = knob + index + トランザクションコード variant 選択を統合する強化学習 (delayed-HOO)。
**採る (引用のみ):** 差別化の基準点。この系譜は探索が「設計者が事前に開けた knob 次元」に閉じ、
CC のロジック (競合検出・待機・abort の判断構造) には手が届かない。系譜内で探索空間が最大の UDO
の「transaction code variants」ですら人間が用意した有限候補からの**選択**であり、Izanagi の**合成**
(アクション空間自体の拡張) との境界線を一行で引ける最良の引用先。knob 探索が専業 ML/RL で解けて
しまうこと自体が P2-5 (フラグ探索に LLM の付加価値なし) と同方向を指す外部証拠。
**採らない:** 機構すべて — Izanagi は knob 探索をしない (P2-5 で既反証)。
**系譜上の位置:** 「ワークロード特化の DB 自動最適化」の最古参。Izanagi はこの目標を knob 空間から
コード空間へ持ち出す位置に立つ。

#### learned DB components 系譜 — learned index / learned query optimizer
`判定: 引用元`+`外部補強` · `接地: 層2 の物語 (部品の学習特化)、実行時推論ゼロの設計必然性` · `id検証: 2026-07-10 (arXiv バルク 5/5 + venue 裏取り、worklog 2026-07-10 (8))`
**一言:** DB 中核部品を学習物で置き換える系譜。Kraska et al. (`1712.01208`, SIGMOD 2018) =
「インデックスはモデルである」の元祖 (RMI) / ALEX (`1905.08898`, SIGMOD 2020) = 更新対応の第二波 /
PGM-index (`1910.06169`, PVLDB 13(8) 2020) = 最悪ケース保証の証明付き / Neo (`1904.03711`,
VLDB 2019) = learned query optimizer の最初期 / Bao (`2004.03814`, SIGMOD 2021) = 既存 optimizer を
粗粒度ヒントで「操縦」する実用化 (arXiv 版と venue 版でタイトルが異なる点に注意)。
**採る (引用 + 外部補強):** (1) 物語の源流 — Izanagi は「learned DB components の CC 版」の章に
あたる。ただし手段が根本的に違う: この系譜は model-in-the-path (実行経路にモデル推論を挟む) だが、
Izanagi は code-as-output (学習コストは合成時に払い、実行時はプレーン C++・推論ゼロ)。CC は
トランザクション毎 µs 以下の critical path なので推論を挟む余地がなく、この違いは好みでなく必然
(Neo/Bao との対比から導出)。(2) 外部補強 2 点 — PGM の「学習部品に証明可能な保証を付けよ」という
要請は、CC 合成に serializability verifier を常設する規律 2/3 と同じ問いへの別解。Bao の「白紙から
全置換せず実証済み部品を保ち介入面を絞る」は EVOLVE-BLOCK 設計 (stock 骨格温存 + 指定領域のみ変異)
と同型の教訓。
**採らない:** ALEX 型のオンライン自己適応機構 — Izanagi のワークロード適応はオフライン再合成
(合成パイプラインの再実行) で担う立場。
**系譜上の位置:** index (データ構造) → optimizer (意思決定) と学習置換が拡大してきた延長線上に
CC (意思決定 + 正しさ制約が最も強い部品) がある。

---

### 7.2 AI 探索・進化的合成の系譜 (層2 (b) の方法論)

LLM を変異オペレータとして進化探索でコードを合成する系譜。verifier がある所で正しさを保ちつつ
性能指標を最適化する、Izanagi (b) と同一の問題設定。

#### AlphaEvolve `2506.13131` (Google DeepMind 白書、査読なし・v1 のみ)
`判定: 思想` · `接地: 層2 (b) コード合成、EVOLVE-BLOCK 機構の出典` · `id検証: 2026-07-10 (一次資料 PDF 44 頁精読、worklog 2026-07-10 (8))`
**一言:** 進化的コーディングエージェント。進化 DB (MAP-Elites + 島モデルに着想) から親 +
inspirations をサンプルし、**過去の勝ちプログラム群と評価スコアを prompt に注入**、LLM アンサンブル
(Gemini Flash = 量 / Pro = 質) が SEARCH/REPLACE 形式の diff を生成、evaluator カスケード (難易度
昇順の段階ゲート) で採点して DB に登録。成果は 4×4 複素行列乗算 48 回 (Strassen 以来 56 年ぶりの
更新)・数学未解決問題 50+ (75% 再発見・20% 更新)・Borg スケジューリング・Gemini 訓練カーネル等。
**採る:** (1) 進化探索でコードを合成する問題設定 (ShinkaEvolve が直系とする源流)。(2) **EVOLVE-BLOCK
マーカー (§2.1) と diff 形式の編集面限定 (§2.3) は Izanagi が hooks/guard_write で採用している機構の
出典そのもの** — 出典として明記して引用できる。(3) evaluator カスケード (不良の早期除去 → 本評価) は
スコアを生成側に返さず harness 内に閉じる限り規律 6 と整合し、Izanagi の Tier0→verify→bench 直列
ゲートと相似。
**採らない:** 勝ちプログラム + スコアの prompt 注入は周辺機能でなく**ループの定義そのもの**で、
§4 の ablation (No evolution を切ると両タスクで大幅劣化) がそれを直接証明 — この系譜のサンプル
効率の源泉が Model Y リーク制御と正面衝突する機構にあることの一次証拠 (7.2 末尾の注意の裏付け)。
LLM-generated feedback をスコアに混ぜる機構も正しさゲート希釈の方向 (規律 2/3) で不採用。
**系譜上の位置:** FunSearch の後継、ShinkaEvolve/DGM の源流。

#### Darwin Gödel Machine (DGM) `2505.22954`
`判定: 思想` · `接地: 自己改善 (§7.4 と連結)` · `id検証: 2026-07-10`
**一言:** 自己改変で自らを進化させるエージェント。
**採る:** 自己改善の理論的枠組み (SkillOpt/Self-Harness の源流としての位置づけ)。
**系譜上の位置:** AlphaEvolve 系譜かつ 7.4 自己改善系譜の理論的源流。

#### FunSearch (Romera-Paredes et al., *Nature* 625, 468–475, 2024; オンライン 2023-12)
`判定: 思想` · `接地: 層2 (b)` · `id検証: 2026-07-10 (DOI 10.1038/s41586-023-06924-6 解決確認。arXiv プレプリント不在を API 二重確認 — Nature のみが一次資料)`
**一言:** LLM を進化ループに組み込み数学的・アルゴリズム的発見を行った先駆。凍結済み LLM (創造役)
と systematic evaluator (confabulation の門番) を対にし、programs database + 島モデルで母集団を
保持。核となる機構は **best-shot prompting** = スコア最良のプログラム群を prompt に戻して改良させる。
プログラム全体でなく骨格 (skeleton) 中の決定的ロジックのみ進化。成果 = cap set 8 次元 512 要素
(既知最良超え)・オンラインビンパッキング。実装 = github.com/google-deepmind/funsearch。
**採る:** LLM×進化ループという方法論の起点としての位置づけ。島モデル (多様性維持) は Phase 3.5
(母集団導入) の思想的参照先候補。
**採らない:** best-shot prompting — 機構名自体が「勝ち筋を生成側に見せる」ことを示す。また
evaluator は幻覚防止の門番であって serializability 級の意味論的正しさゲートではない — **規律 2
相当の層がこの系譜には起点から存在しない**ことの証拠 (Izanagi が verifier を足す必然性の対比項)。
**系譜上の位置:** AlphaEvolve/ShinkaEvolve の起点。
> **OpenEvolve** (github.com/algorithmicsuperintelligence/openevolve、旧 codelion/openevolve から
> 移管・旧 URL は 301 で到達可) = AlphaEvolve の**非公式**オープン再実装 (Asankhaya Sharma、
> 2025-05 公開、Apache-2.0、活発に保守中)。**独立した査読論文/プレプリントは存在しないと確定**
> (2026-07-10 三重確認: arXiv 全文検索で該当 0・公式 Citation 節が @software 形式・他論文の引用も
> 全て @software 形式。一次資料 = リポジトリ + 作者の Hugging Face ブログ 2025-05-20)。EVOLVE-BLOCK
> マーカー方式を実装するオープン系の代表だが、勝ち筋注入系譜のため機構は ShinkaEvolve と同じ扱い
> (思想のみ・機構非採用)。第三者の独立評価 (`2511.20987`、全単射構成への適用) が実在性の傍証。

#### ShinkaEvolve `2509.19349` (Sakana AI, ICLR 2026, github.com/SakanaAI/ShinkaEvolve)
`判定: 反面教師 (直採用ゼロ) + 部品予約` · `接地: Model Y リーク制御, 絶対規律2/4/6, Phase 3.5` · `id検証: 2026-07-10`
**一言:** LLM×進化アルゴリズムでプログラムを合成する公開フレームワーク (AlphaEvolve/DGM 直系)。
母集団を島モデル + global archive で保持、LLM アンサンブルを変異オペレータに使い、eval を
並列化して 5-10x を謳う。**同一問題設定を解く現時点で最も直接的な実装比較対象**であり、
かつ他 (Jitskit/IDS/VibeServe) と違い公開され動作する実装。
**採る (思想のみ):** Phase 3.5 (母集団導入) で親選択の novelty ボーナス `1/(1+children_count)` +
MAD ロバスト sigmoid を借用予約 (スコア/重みは harness に閉じ coder には値なし方向のみ渡す形なら
規律6 と整合)。段5/6 拡張時の再構成スプライス/複数マーカー可変域算出も予約。
**採らない (反面教師の核):** スコア付き勝ちプログラムの prompt 注入 (`construct_eval_history_msg`
が過去プログラム全文 + combined_score を prompt へ載せる — 本調査で実物確認) は Model Y
リーク制御の直接否定。crossover / prompt evolution / 並列 eval 前提の機構群 / fuzzy patch も
すべて絶対規律 (2/4/5/6) と衝突。
**系譜上の位置:** 決定的な差は前提 — Shinka は「正しさは素朴 validate で足り、最適化圧力は
敵でない」設計で、Izanagi の絶対規律を共有しない。**この哲学差こそが結論であり、Izanagi の
規律が「不便な保守主義」でなく問題設定から要請された選択であることの外部証拠になる。**
→ 62 技法の敵対検証 (2026-07-07)、反面教師/外部追認/銀行預けの全詳細は
**`shinka-deepdive.md`** に分離 (D35: 実装検討時のみ読む)。

> **注意 (7.2 全体):** AlphaEvolve/FunSearch/DGM/Shinka は同じ「勝ち筋を生成側に見せる」
> サンプル効率機構を核とする。ShinkaEvolve 深掘りの結論「直採用ゼロ」はこの系譜全体に適用され、
> **本系譜からの借用は思想・問題設定のみ、機構は非採用**。

#### Effective Harness Engineering (Vesper) `2605.15221`
`判定: 外部補強` · `接地: §3.4/D38 (auditor), D40 (worktree), §3.8/D31 (質>量), D39 (digest 射影)` · `id検証: 2026-07-15`
**一言:** coding agent を進化探索へ組み込む harness Vesper の実証研究。深い少数生成、独立した
評価ハック検出、Git worktree 並列、探索 DB の効果を同一実験面で比較する。
**採る:** 能力の高いモデルほど評価ハックが増えた Finding 3 (gpt-5.2-codex で 8.2%) を、auditor
(D38) の必要性と auditor を被監査側と同等以上の tier に置く方針の定量的外部証拠にする。ハック検出
on/off × モデル能力は coder を安価モデルへ下げる実験の ablation 軸に予約する。固定予算下の
per-variant 深掘り優位を少数深掘り運用に、worktree 並列 3.2–3.9x を D40 に接地する。DB observation
の効果が限定的だった結果は、リーク制御付き digest 射影 (D39) を維持する判断の補強に使う。
**採らない:** トークン予算を終了基準へ直輸入しない。Izanagi の律速はベンチ実時間であり、8c では
ベンチ実秒予算へ翻訳する。worktree は FS 競合対策であって、物理干渉を防ぐベンチ排他ロックの
代替ではない。
**系譜上の位置:** OpenEvolve/AlphaEvolve 系 harness の実証研究。Izanagi が独立に先取りした
auditor/worktree/構造化出力へ実測値を与える。NEC 小山田グループ。
**調査ノート:** notes/note_harness_engineering.md

#### Best-of-∞ `2509.21091`
`判定: 部品予約` · `接地: §3.2 (検証相の seed 数), §3.6 (反復測定), §3.4 (learned selector 排除)` · `id検証: 2026-07-15`
**一言:** 多数決の best-of-N を無限計算極限から捉え、Bayes factor による適応サンプリングと
LLM アンサンブルの予算配分を理論化する。
**採る:** カテゴリ判定 (serializable / anomaly) の seed 数を固定 N から Bayes factor 逐次停止へ
置換する部品を予約する。論文実測では計算を 2–5 倍削減しているが、bench-first v2 の方針採用
(D58) には含めず、別設計・別裁定とする。将来採用しても S-1 事前登録には適用しない。Bo5 の
「多数決 > LLM-as-judge > reward model」は LLM-as-judge を正しさ経路へ入れない現行判断の
外部証拠とする。
**採らない:** Dirichlet 過程/Bayes factor を連続量 throughput へ直用しない。型不一致に加え、一晩
ループの非定常ドリフトで i.i.d. 前提が壊れるため、連続量には逐次 t 検定系を使い、between-run floor
丸め (§3.6(4)) は主防壁のままにする。単一 CC を成果物とする §10 に反する MILP アンサンブルも採らない。
**系譜上の位置:** 探索でなく集約の理論。Izanagi へは逐次停止・予算配分の方法論として効く。
NEC 小山田グループ。
**調査ノート:** notes/note_best_of_asymptotic_performance_of_test_t.md

#### DISC `2502.16706`
`判定: 思想` · `接地: §3.6(4) (分布比較), 層2 探索戦略` · `id検証: 2026-07-15`
**一言:** 推論を難所ほど細かく動的分解し、限られた評価予算を難しい箇所へ集中する推論
スケーリング手法。
**採る (思想のみ):** 累積シグナルが閾値 σ に達したら止める適応的打ち切りから「評価予算を難所に
寄せる」思想を借り、Best-of-∞ の逐次停止と同じ承認案件で検討する。統計推定に依存する段では
低温度で分散を抑えるという ablation 知見も参照する。
**採らない:** z-score 受理規準は採らない。between-run floor 丸めが主防壁であり、location-scale
仮定は throughput の非定常ノイズで壊れる。自己回帰 prefix 分解にも variant 系譜への自然な写像が
ないため直輸入しない。
**系譜上の位置:** 推論スケーリングの分解粒度制御。Izanagi では思想の借用に留める。共著に
小山田氏。
**調査ノート:** notes/note_disc_dynamic_decomposition_improves_llm_.md

---

### 7.3 対象特化システムの自動合成 (設計レベルの予言書)

LLM エージェントがワークロード仕様からシステム丸ごとを bespoke 合成する系譜。

#### Jitskit `2605.24096`
`判定: 採用 (部品多数)` · `接地: spec cards, §3.2, §3.5, §3.4, planner-coder 分離, whiteboard` · `id検証: 2026-07-10`
**一言:** KVストアをワークロード仕様から丸ごと合成。本システムの設計レベルの予言書。
**採る:**
- **spec cards (3枚)**: 環境カード / ワークロードカード / 要求カード。要求カードが isolation level を定義する (保留だった「対象 isolation level をどこで決めるか」がこれで解決)
- **reward hack カタログ**: §3.2 と Appendix B。CC 版に翻訳して自前のギャラリーを作る
- **leading indicators**: 収束に必須 (§3.5)
- **adversarial auditor**: N iteration ごとに監査しテストを増やす
- **planner/coder 分離**: コードに引きずられず構造を考えるため。Phase 3 で効く
- **whiteboard memory**: 却下した設計を蓄積。output/insights/ と統合
**系譜上の位置:** VibeServe/IDS と同系譜の「対象特化の自動合成」。借用部品が最も多い。

#### VibeServe `2605.06068`
`判定: 思想 (同系譜)` · `接地: orchestrator D (durability), §3.4` · `id検証: 2026-07-10`
**一言:** LLM serving システムを deployment target ごとに bespoke 合成する agentic loop。
outer loop が永続計画状態 (issues / long-term memory / git commit graph) 上で探索を計画し、
inner loop の Implementer / Accuracy Judge / Performance Evaluator が候補を実装・検証・計測する。
**採る:** 「単一汎用システム」から「ターゲット特化の自動合成」へという賭け (Izanagi と同じ)。
Accuracy Judge の reward-hacking 検査は Jitskit の auditor と同思想。
**系譜上の位置:** Jitskit/IDS と同系譜。outer loop の永続状態は orchestrator-design.md の
D (durability) の先行例。

#### IDS `2605.23109`
`判定: 思想` · `接地: 絶対規律3, decisions.md (Rocq スコープ)` · `id検証: 2026-07-10`
**一言:** コードと証明を同時に育てる verified synthesis。
**採る:** **正しさを後付けにしない** — verifier を毎 iteration 回し、構造化診断を LLM に返す
(単なる accept/reject に落とすと性能が激減する、と ablation で実証)。
**採らない:** 完全な形式証明 (Rocq) 自体は初期スコープ外 (C++ many-core 実装の形式化が
重すぎる、decisions.md 参照)。
**系譜上の位置:** Jitskit/VibeServe と同系譜。正しさゲートの思想的支柱。

---

### 7.4 自己改善・メタ最適化 (whiteboard memory の外部裏付け)

手順書・プロンプト・メモリ・ハーネス自体を学習ループで改善する系譜。借用は思想・外部補強のみで、
機構は Phase 3.5 以降に予約 (規律5)。

#### SkillOpt `2605.23904`
`判定: 外部補強` · `接地: whiteboard memory, 絶対規律2, §3.4, living document 運用` · `id検証: 2026-07-10`
**一言:** 手順書 (CLAUDE.md / skill 文書) を「テキスト空間の学習ループ」で自動改善。モデル本体は
更新せず、実行ログ → 最適化LLMが add/delete/replace 編集を提案 → validation gate で性能向上を
確認した編集だけ書き込み → 却下編集は「やってはいけない修正の記憶」として保存。52セル全てで SOTA。
**採る (思想・外部補強):**
- **whiteboard memory の理論的裏付け**: 「却下編集を『やるな記憶』に保存」は Izanagi の whiteboard memory (output/insights/) と構造同型。人力の自動化版が SOTA = 設計判断の正しさの外部証拠
- **validation gate = 絶対規律2 と同型**: 「検証を通った編集だけ採用、それ以外は記憶」= reward hacking 対策 (§3.4) の一般形
- **living document 運用の裏付け**: roadmap を生きた文書にし decisions.md に却下案を残す運用思想そのもの
**採らない:** SkillOpt の機構を「Izanagi が自分の prompt/最適化カタログを自走改善する」形まで
実装するのはスコープ膨張。引用と whiteboard 設計の補強に留め、自己改善機構は将来予約。
**系譜上の位置:** Jitskit/IDS/VibeServe が「対象システム」を合成するのに対し、SkillOpt は
**メタ層 (手順書) を最適化**。Izanagi は両方を内包 (CC 合成 + 知見の whiteboard 蓄積)。

#### Self-Harness `2606.09498`
`判定: 外部補強` · `接地: 絶対規律2, 絶対規律3/D3, 規律1/5` · `id検証: 2026-07-10`
**一言:** SkillOpt の一般化。harness 全体 (prompt + tool + 制御フロー) を学習可能な artifact
として扱い、改善ループを内在化。三段構成 Weakness Mining → Harness Proposal → Proposal Validation。
採用は validation gate (in-sample と held-out の両方で非悪化 かつ少なくとも一方で改善) を通った提案のみ。
**採る (思想・外部補強):**
- **validation gate = 絶対規律2 の再確認**: SkillOpt に続く 2 つ目の外部証拠
- **verifier-grounded failure signatures = 絶対規律3 / D3 の外部 echo**: verifier の失敗シグネチャを次の改善入力にする設計は規律3/D3 とほぼ一対一
**採らない:** 自己改変ループの機構は将来予約 (規律5)。特に self-editing loop は絶対規律2 と
絶対規律1 (trace/perf ビルド分離) を**決して侵してはならない**制約付きでのみ系譜に乗る。
**系譜上の位置:** SkillOpt がメタ層を最適化するのに対し、Self-Harness は対象を harness 全体へ
広げた最右翼。Izanagi の自己改善は現状「思想として」乗るのみ、実装は Phase 3.5 以降
(agent-architecture.md の instinct 的学習機構)。

#### DecentMem `2605.22721`
`判定: 外部補強` · `接地: whiteboard 二プール, §10 多様性保存, D7/D9, 絶対規律2` · `id検証: 2026-07-10`
**一言:** 共有メモリプールはマルチエージェントを同質化させるとして各エージェントに独立メモリを与える。
二プール構成 (exploitation pool = 整理済み過去トラジェクトリ + exploration pool = LLM 生成候補)。
理論保証として O(log T) cumulative regret と global reachability を証明。中央集権 baseline 比 +23.8%。
**採る (思想・外部補強):**
- **whiteboard memory の二プール構造の外部裏付け**: exploit-pool ≈ 整理済み過去試行、explore-pool ≈ 候補設計。**理論保証 (O(log T) regret) 付き**で「過去試行の整理 + 候補生成の分離」が効くことを示した
- **§10 多様性保存の外部 echo**: 「同質化を避け専門性を残す」は層3 で「throughput 最強の1個でなく特性の違う variant を複数残す」方針と同方向
**採らない:**
- 共鳴は variant 集団レベルであって agent レベルではない。Izanagi のサブエージェントは D7 で既にロール分離・コンテキスト隔離済みで、DecentMem が問題にする「エージェントの同質化」は構造上ほぼ発生しない。借りるのは「メモリの二プール分割」の発想だけで per-agent decentralized memory の機構ではない
- online reweighting の **LLM-as-a-judge は操作されうる (gameable)** なので正しさ経路には決して入れない (絶対規律2)。論文本文で名指しされる中央集権 baseline 名は abstract で確認できないため特定名を記さない
**系譜上の位置:** 機構は将来予約 (agent-architecture.md の instinct 的学習機構 Phase 3.5+、D7/D9)。

#### ARA / The Last Human-Written Paper `2604.24658`
`判定: 採用 + 部品予約 + 反面教師` · `接地: §3.4 (採用済み), whiteboard/WAL データモデル, §3.6, 絶対規律3, D12` · `id検証: 2026-07-10`
**一言:** 物語形式の論文は反復研究を圧縮し「Storytelling Tax / Engineering Tax」を生んで AI に
よる理解・再現を妨げるとして、論文を機械実行可能な research artifact (ARA) に置き換える提案。
Izanagi が「探索が正しく回るため」に既に吐く成果物と ARA の要素がほぼ 1:1 で対応する点が肝。
**採る (採用済み):**
- **anti-fabrication isolation (§3.4)**: ARA Level3 は検証エージェントに code kernel とアルゴリズム記述だけを渡し報告済み数値を一切見せない。これを verifier の入力側隔離として採用 (§3.4-4, agent-architecture.md verifier 節)
**採る (将来雛形):**
- **typed-DAG exploration graph**: 研究 DAG を question/decision/experiment/dead_end/pivot の型付きノードで保存、dead_end に hypothesis/failure_mode/lesson の三つ組。whiteboard memory / WAL / 成果物「試行錯誤の記録」の共通データモデルの外部雛形 (reject variant=node, mutation=edge, verifier の G2 cycle 診断=dead_end.failure_mode, 教訓=lesson)。dead_end 三つ組は絶対規律3 とほぼ一対一。**実スキーマ確定は Durability 層を作る Phase 2 以降にユーザー確認の上で行い、今は確定しない**
- **forensic binding (思想参照, §3.6)**: 主張→code→実測値を辿れる proof chain。層3説明可能性 (§3.6(4)) のデータ構造と同型。ARA の /logic vs /evidence 分離は §3.3 の「CC本来 vs 検証専用メタデータ」二分とは**動機が異なる** (前者=捏造防止、後者=観測者効果対策) ので「同一の分離」とは書かない。「二つの異なる汚染防止を一つの binding 思想で統一的に説明できる」が正確
**採らない (反面教師):** ARA Seal の三段階レビュー (構造健全性→ルーブリック→縮小スケール方向性検証)
は Izanagi の階層化検証 (§3.1 Tier0-3) / 二相設計 (§3.2) と同型だが、ARA は**所見をループに
自動還流せず著者が手動反復する**。これは絶対規律3 を Izanagi が ARA に対して優位に持つ点を確認させる。
ARA Compiler / Live Research Manager のような重機構はスコープ外 (§10)。
**系譜上の位置:** ARA は「物語 PDF でなく機械検証可能 artifact こそ一次研究対象」と主張。Izanagi は
この artifact (材料レポート) の生成までを担い、narrative 化・推敲は別システムに委ねる (D12)。

#### Self-Developing (Can LLMs Invent Algorithms to Improve Themselves?) `2410.15639`
`判定: 部品予約` · `接地: §7 SkillOpt/Self-Harness 系譜, 絶対規律2, D9 (Phase 3.5 予約)` · `id検証: 2026-07-15`
**一言:** accept/reject されたアルゴリズムを選好データへ変換し、改善案を生成する LLM 自体を
DPO で反復更新する自己改善ループ。
**採る (Phase 3.5 予約):** 取捨で終わらせず accept/reject を生成器へのステアリング信号にする
レシピを予約する。上位 3% chosen / 下位 10% rejected、エリート top-3 持ち越し、温度減衰を参照し、
着手時は DPO 訓練ではなく whiteboard 射影を拡張した in-context ステアリングから始める。
開発/テスト分離によるリーク防止は §3.6 と整合する。
**採らない:** 正しさゲートを選好信号へ溶かさない。serializability 違反は低スコアでなく即 reject
とし、選好対にすら入れない (絶対規律2)。GPU 前提でコスト構造が合わない毎反復 DPO 訓練も採らない。
**系譜上の位置:** SkillOpt/Self-Harness と同じメタ層最適化だが、生成器そのものを訓練する
最右翼。NEC 小山田グループ。
**調査ノート:** notes/note_can_large_language_models_invent_algorit.md

#### LaMDAgent `2505.21963`
`判定: 反面教師` · `接地: 絶対規律2, §3.4, P2-5/D21/D29, §3.6(4), §8 (ポジショニング)` · `id検証: 2026-07-15`
**一言:** post-training のアクションを列挙・選択・評価し、テキスト memory を更新する層2ループの
近傍実装。評価は正しさゲートを持たず、スカラー報酬に一元化される。
**採る (外部補強として):** LLM 選択の random に対する優位が test +1.9 点に留まりアクション空間
設計が支配的だった ablation を P2-5 の negative result (D21/D29) の独立補強に使う。2B→9B の
転移で小さな順位差が逆転した結果を、スケールで消える差を採否根拠にしない §3.6(4) floor 丸めの
外部証拠とする。memory 更新雛形と mode collapse/命名バイアス対策は §3.4-3、D44/D48 と照合する。
**採らない (反面教師):** 正しさゲートなしのスカラー報酬一元は採らない。これは §8 の差別化点で
ある。一方、スカラー + テキスト memory だけで 100 iteration 改善した結果は、§3.5 の leading
indicators 前提と緊張する事実として記録し、どちらも無条件には信じない。
**系譜上の位置:** 層2ループ (列挙→選択→評価→memory 更新) の最も近い参照実装。ただし評価規律は
移植しない。NEC 小山田グループ。
**調査ノート:** notes/note_lamdagent_an_autonomous_framework_for_po.md

---

### 7.5 運用・設計の点検レンズ (取り込みでなく sanity check)

#### How AI Agents Reshape Knowledge Work `2606.07489` (Yang, Zyskowski, Yonack & Ma)
`判定: 引用元 (実装しない)` · `接地: §2 層2 proxy, §3.1 Tier0-3, §3.5 profiling` · `id検証: 2026-07-10`
**一言:** Perplexity の本番データ (Search vs Computer) で自律エージェントの経済効果を実証分析。
**採る (引用元):** 固定費 vs 限界費の閾値モデル `s* = (f_Agent − f_Conversational)/
(m_Conversational − m_Agent)` (固定費の高い処理は step 数が閾値を超えた時だけ選好) は、Izanagi の
二段構え (§2 層2 の low-fidelity proxy / §3.1 Tier0-3 エスカレーション / §3.5 profiling を有望
variant にだけ回す) の**経済学的フレーミング・引用元**。査読での「なぜ全 variant に profiling
しないのか」への論拠補強。
**採らない:** 実 gating 機構としては実装しない (規律5)。論文ドメインは knowledge-work の
interaction-mode ルーティングで Izanagi の探索エスカレーションとは異なる (一般化である旨を明記して引用)。

#### 12-factor-agents (github.com/humanlayer/12-factor-agents)
`判定: 点検レンズ` · `接地: 絶対規律3, D7, orchestrator-design.md WAL` · `id検証: N/A (github)`
**一言:** 本番投入できる LLM エージェントの設計12原則 ("12-Factor Apps" の AI 版)。
**採る (点検レンズ):** 既に整合している原則の確認 —
- 「構造化した tool 出力を持て」= verifier が構造化フィードバックを返す規律 (絶対規律3) と一致
- 「小さく焦点を絞ったエージェント」= サブエージェントの段階導入・ロール分離 (D7) と一致
- 「実行状態を統一し復元可能にせよ」= orchestrator-design.md の WAL/クラッシュリカバリ (D) と一致
**採らない:** 新規に取り込む要素ではなく、設計が業界経験則と外れていないかの sanity check として参照。

#### ECC (github.com/affaan-m/ECC)
`判定: 点検レンズ (運用参考3点、巨大さは反面教師)` · `接地: verifier ツール権限, hooks, whiteboard 将来形, 絶対規律5` · `id検証: N/A (github)`
**一言:** Claude Code の運用パターンの参考。
**採る (3点だけ):**
- agent定義に `tools` と `model` を明示。verifier には専用書き込みツール (Edit/Write) を与えず、Bash 経由の書き込みは prompt 規律で禁止 (完全なツール権限レベルの隔離ではない — audit-2026-06-30 §4 の裁定)
- hooks で規律を機械執行 (verifier 迂回・成果物への直接書き込みを弾く第二防壁。観測者効果の内容検査は方針 A (D33) で一次防壁 = source_digest 系へ委譲)
- continuous-learning/instinct は whiteboard memory の進化形として将来予約
**採らない (反面教師):** 「27 agents / 64 skills / 33 commands / AgentShield (1,282 tests)」のような
大規模 Claude Code 環境は絶対規律5 (段階導入・盛らない) と正面衝突する。Izanagi は CC 合成という
単一目的に必要なロール/hook だけを Phase ごとに足す。唯一拾える原子は「hook 自体にテストを書く」
発想 (適用済み — 両 hook に回帰テスト群、3 巡の敵対検証の fix は変異検査で固定。hooks/README.md 参照)。

#### cotomi Act `2605.03231`
`判定: 反面教師` · `接地: 絶対規律2/3, §3.8 (コンテキスト衛生), Phase 1 verify-red` · `id検証: 2026-07-15`
**一言:** web GUI 自動化を対象に、実行 scaffold とユーザー行動からの知識抽出を統合する。
自動 scorer の誤判定と、事後 verifier を使わない best-of-N 設計の両方を示す対照例。
**採る (思想・外部補強):** ベンチの自動 scorer に false positive/negative があり人手検証を要した
事例を、verify-red / positive control (D36-D38) の evaluator-integrity 外部例とする。trajectory /
script / insight の抽象度ラダーは whiteboard 還流粒度の将来参照にする。意味的な verbal-diff が
+12.7pp だった結果も参照するが、D39 のリーク制御と緊張するため、還流形式の変更は敵対レビューを
前提とする将来検討に留める。
**採らない (反面教師):** 事後 verifier を外し best-of-N 事前合意と人手 curation で代替する設計は、
正しさが二値でハードな CC の絶対規律2/3と衝突する。探索効率の機構へ翻訳できても、正しさの根拠には
決して使わない。
**系譜上の位置:** 正しさが緩く人手 curation で吸収できる web GUI 自動化の設計。ドメイン適合性の
断層を示す対照例。NEC 小山田グループ。
**調査ノート:** notes/note_cotomi_act_learning_to_automate_work_by_.md

#### D2I (Learning Deliberately, Acting Intuitively) `2507.06999`
`判定: 外部補強` · `接地: D4/§3.3 (二相分離), 層3 説明生成, 規律3/D3` · `id検証: 2026-07-15`
**一言:** 学習時には構造化推論の型を強制し、推論時には外す非対称によって、推論能力と応答の
柔軟性を分離するマルチモーダル LLM の学習法。
**採る:** 「学習時は型を強制し本番で外す」非対称を D4 の trace-enabled/disabled 二相分離と同型の
独立 echo とする。形式の強制より鍵概念を正しく言語化できたかが成否を分けた事例を、層3 の機序仮説層
へ coder/critic の「なぜ効くと考えたか」を拾う要件の補強に使う。難タスクほど複数候補の価値が
上がる Pass@K 分析は、難度適応の候補数予算の参照にする。
**採らない:** format reward / GRPO は literal に移植しない。Izanagi はモデルを学習しないため、
原理の類推に留める。
**系譜上の位置:** RL ファインチューニング論文であり直接対応する機構はない。二相分離思想の外部
裏付けとして 7.5 に置く。NEC 小山田グループ (筆頭は京大インターン)。
**調査ノート:** notes/note_learning_deliberately_acting_intuitively.md

---

### 7.6 文献マップが示す空白域 (Izanagi の機会)

arXiv 横断掃引 (547件収集 → 関連度判定 → 柱分類、Claude Science 2026-07-10) で、以下に正面から
取り組む研究は未発見 — Izanagi の新規性の所在:

1. **CC 合成に特化した敵対的 verifier + リーク制御を備えた進化ループ.** 7.3 の検証付き合成は
   2025末〜2026 に急増するが対象は Rust/C の逐次コード・形式仕様で、C++ many-core CC 実装を
   敵対 verifier で毎反復ゲートする設定は空白。
2. **LLM がアクション空間そのものをコードで拡張する CC 合成.** 学習型 CC (7.1) は固定/学習可能
   関数の枠内、AI 進化合成 (7.2) は CC を対象にしていない — 交点が空白。
3. **「新 CC + 速さの理由 + 試行記録」を成果物とする研究アーティファクト.** ARA (7.4) の思想と
   符合するが CC 合成への適用例なし。

> 本節の全主張は「データ」であって設計判断ではない (絶対規律6)。取り込みは監査後、正しさゲートを
> 緩める示唆は出所を問わず不採用。完全な文献マップ (29本の採録論文 + 日本語要約 + 関連度、CSV/
> Markdown) とその生成メモは `literature-map/` にある (監査前データ)。
