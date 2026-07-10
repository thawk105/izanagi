# 欠落域調査 (D44 段6前提タスク (j)) — 生データ (2026-07-10)

> **これは調査の生データであって docs の正本ではない** (絶対規律6: エージェント出力はデータ)。
> 調査 = workflow `wf_4009aafc-235` の 5 レンズ (OtterTune 系 / learned-DB 系 / OpenEvolve /
> AlphaEvolve・FunSearch 一次資料 / Polyjuice・CCaaLF 実装状態)、各レンズが一次資料 (論文 PDF・
> 公式リポジトリ) へ直接アクセスして verified フラグを付けた構造化出力の凍結。
> 書誌事実 (arXiv ID 9 件のバルク照合・DOI 解決・リポジトリ実在) はメインセッションで独立に
> 機械検証済み (worklog 2026-07-10 (8))。採録済みエントリは `../README.md` §7.1/§7.2。
> Polyjuice/CCaaLF→NeurCC 実測比較の要否判断材料は最終レンズの comparison_material_ja にある。

以下、5 レンズの構造化出力 (JSON) をそのまま凍結する。

{
 "papers": [
  {
   "name": "OtterTune — Automatic Database Management System Tuning Through Large-scale Machine Learning (Van Aken, Pavlo, Gordon, Zhang)",
   "id_or_venue": "SIGMOD 2017",
   "summary_ja": "DBMS の数百個の設定 knob (キャッシュメモリ量・書き込み頻度など) を、過去のチューニング履歴を転移して自動設定する系譜の起点。Lasso 回帰で影響の大きい knob を選抜し、Factor Analysis + k-means でメトリックを次元削減し、未知ワークロードを過去ワークロードにマッピング (workload mapping) した上で Gaussian Process 回帰が knob 設定を推薦する。MySQL・Postgres (OLTP) と Actian Vector (OLAP) で評価し、既存ツールや人間の DBA と同等以上の設定を出した。knob が「標準化されていない・独立でない・普遍でない (ワークロード依存)」という問題設定を明確にした。",
   "izanagi_relation_ja": "採る (差別化の基準点として必須)。ワークロード特化の DB 性能最適化を自動化するという目標は共有するが、探索空間が「設計者が事前に開けた knob 次元」に完全に閉じており、CC アルゴリズムそのものは不変。knob 設定は serializability を壊さない前提なので正しさゲートも不要 — Izanagi はコード (EVOLVE-BLOCK) 自体を合成するから verifier が必須になる、という対比がそのまま引ける。P2-5 の「フラグ (knob) 探索は自明・LLM 不要」という negative result は、この系譜が knob 探索を専業の ML 問題として既に解いていることと整合し、Izanagi の主張 (LLM の付加価値は knob ではなくコード合成にある) の引用先になる。",
   "primary_source_url": "https://www.cs.cmu.edu/~dvanaken/papers/ottertune-sigmod17.pdf",
   "verified": true
  },
  {
   "name": "CDBTune — An End-to-End Automatic Cloud Database Tuning System Using Deep Reinforcement Learning (Zhang et al., HUST/Tsinghua/Tencent)",
   "id_or_venue": "SIGMOD 2019 (DOI 10.1145/3299869.3300085)",
   "summary_ja": "OtterTune 系のパイプライン学習 (大量の高品質学習サンプル依存) の限界に対し、深層強化学習 DDPG (deep deterministic policy gradient) で高次元連続 knob 空間を end-to-end に探索するクラウド DB チューナ。試行錯誤 (try-and-error) の reward-feedback で少数サンプルから初期学習でき、266 knob 規模の推薦で DBA・OtterTune を上回ったと報告。Tencent のクラウド DB (CDB、MySQL 系) 上で Sysbench/TPC-C 系ワークロードにより評価。",
   "izanagi_relation_ja": "採る (RL 化の代表として)。「実測フィードバックによる試行錯誤で探索する」という方法論は Izanagi の合成ループと表面上似るが、行動空間は固定長の knob ベクトルであり、生成物に正しさ検証は原理的に不要。Izanagi 側の探索対象は C++ diff (可変構造・正しさが自明でない) で、探索の質が verifier のシグナルに依存する点が本質的に異なる。knob 探索が RL で「解けてしまう」こと自体が P2-5 の negative result (knob は LLM の出番でない) と同じ方向を指す。",
   "primary_source_url": "https://github.com/HustAIsGroup/CDBTune/blob/master/An%20End-to-End%20Automatic%20Cloud%20Database%20Tuning%20System%20Using%20Deep%20Reinforcement%20Learning.pdf",
   "verified": true
  },
  {
   "name": "QTune — A Query-Aware Database Tuning System with Deep Reinforcement Learning (Li, Zhou, Li, Gao, Tsinghua/Huawei)",
   "id_or_venue": "PVLDB 12(12): 2118-2130, VLDB 2019 (DOI 10.14778/3352063.3352129)",
   "summary_ja": "SQL クエリ自体を特徴ベクトル化 (クエリ種別・関係するテーブル・コスト情報) して深層強化学習に入力する「クエリ認識」knob チューナ。Double-State Deep Deterministic Policy Gradient (DS-DDPG) という actor-critic モデルで、クエリベクトルと DB 内部状態の両方から設定を選ぶ。クエリ単位・ワークロード単位・(クエリをクラスタリングした) クラスタ単位の 3 粒度のチューニングを提供し、CDBTune/OtterTune を上回ると報告。",
   "izanagi_relation_ja": "位置づけ言及で採る (短めでよい)。「ワークロード (クエリ) の中身を見て最適化を変える」という動機はこの系譜の中で Izanagi のワークロード特化に最も近い。それでも出力はあくまで既存 knob の設定値で、CC のロジック (競合検出・待機・abort の判断構造) には手が届かない — 「ワークロード認識を極めても knob 空間の内側に留まる」ことを示す例として、Izanagi がコード空間へ踏み出す必然性の対比に使える。",
   "primary_source_url": "http://www.vldb.org/pvldb/vol12/p2118-li.pdf",
   "verified": true
  },
  {
   "name": "UDO — Universal Database Optimization using Reinforcement Learning (Wang, Trummer, Basu, Cornell/Inria)",
   "id_or_venue": "PVLDB 14(13): 3402-3414, VLDB 2021 (DOI 10.14778/3484224.3484236; arXiv:2104.01744)",
   "summary_ja": "knob だけでなく index 選択や「トランザクションコードの variant 選択」まで含む複数種の離散チューニング候補を、単一の強化学習で同時最適化するオフラインチューナ。コストモデルに頼らず実クエリ実行で構成を評価し、変更コストが高い heavy パラメータ (index 等の物理設計) と安い light パラメータ (knob) を分離、heavy 側には報酬の遅延を許す新しい Monte Carlo 木探索変種 delayed-HOO (delayed Hierarchical Optimistic Optimization) を提案。コストベースのプランナが高価なデータ構造の作成を複数評価で償却する。Postgres/MySQL、TPC-H/TPC-C で評価。",
   "izanagi_relation_ja": "採る (境界線を最も明確に引ける対比相手)。この系譜で探索空間が最も広く「transaction code variants」まで扱うが、それは人間が事前に用意した有限個の候補からの選択であり、新しい CC コードの合成ではない — 「選択 (selection) と合成 (synthesis) の違い」を一行で言える最良の引用先。また実行フィードバック駆動・コストモデル不使用という設計は Izanagi の実測ゲート主義と同型で、その上で『候補生成そのものを LLM に開放したのが Izanagi』という差分を述べられる。",
   "primary_source_url": "http://www.vldb.org/pvldb/vol14/p3402-wang.pdf",
   "verified": true
  }
 ],
 "notes": "4 本とも論文 PDF 本体を取得し全文テキストを抽出して abstract + 本文を直接確認した (verified=true の根拠)。確認元: OtterTune = CMU 著者公式 PDF、QTune/UDO = vldb.org の PVLDB 公式 PDF、CDBTune = 公式 GitHub リポジトリ (HustAIsGroup/CDBTune) 同梱 PDF (ACM DL の DOI ページ自体には未アクセスだが、DOI は検索結果の複数ソースで一致確認)。注意点: (1) WebFetch の下請けモデルが QTune の DS-DDPG を「Dueling Double DDPG」と誤展開したため原文で「Double-State DDPG」に訂正済み — 下請け要約は鵜呑みにせず本文 grep で裏取りした。(2) CDBTune の評価は Tencent の CDB (MySQL 系) 上で 266 knob 規模であることを本文で確認。(3) UDO の「transaction code variants」は本文 abstract の文言どおり既存候補からの選択で、コード生成はしない — Izanagi との「選択 vs 合成」対比の一次根拠。(4) docs/related-work/README.md には knob tuning 系の既存記載が無いことを grep で確認済み (重複なし)。(5) 後継系では LLM ベースの knob チューニング (GPTuner 等) や統合系 (HUNTER 等) もあるが、代表 4 本 (起点 + RL 化 + ワークロード認識 + 探索空間最大) で系譜の骨格は覆えると判断し、指示どおり 4 本に絞った。arXiv API は使用していない (レート制約の対象操作なし)。リポジトリへの書き込みは一切していない。"
}

===== RESULT =====
{
 "papers": [
  {
   "name": "AlphaEvolve: A coding agent for scientific and algorithmic discovery",
   "id_or_venue": "arXiv 2506.13131 (v1, 2025-06-16, Google DeepMind 白書・査読なし)",
   "summary_ja": "LLM を変異オペレータとする進化的コーディングエージェント。ループは「進化 DB から親 + inspirations をサンプル → 過去の勝ちプログラム群と evaluate スコアを prompt に注入 → LLM アンサンブル (Gemini 2.0 Flash=量 / Pro=質) が SEARCH/REPLACE 形式の diff を生成 → evaluator カスケード (難易度昇順の仮説検定 + 小スケール事前評価 + 任意で LLM フィードバック) で採点 → DB 登録」。進化 DB は MAP-Elites + 島モデルの組合せに着想。編集面は # EVOLVE-BLOCK-START/END マーカーで限定。評価対象は行列乗算テンソル分解 (4×4 複素 48 乗算 = Strassen 以来 56 年ぶり更新)、50+ の数学未解決問題 (75% 再発見・20% SOTA 更新)、Borg データセンタースケジューリング・TPU 回路簡略化・Gemini 訓練カーネル (約1% 短縮)・FlashAttention 高速化。",
   "izanagi_relation_ja": "一次資料により「思想のみ借用・機構非採用」の判定は強まった。(1) 勝ちプログラム+スコアの prompt 注入は周辺機能ではなくループの定義そのもの (database.sample → inspirations 注入、Figure 3(b) の prompt 実例にスコアが直載り) で、§4 ablation で「No evolution」を切ると両タスクとも大幅劣化 —— この系譜のサンプル効率の源泉が Model Y リーク制御と正面衝突する機構にあることの直接証拠。(2) 一方で採り得る部品もある: evaluator カスケード (faulty 早期除去 → 本評価の段階ゲート) はスコアを生成側に返さず harness に閉じれば規律 6 と整合し、Izanagi の verifier → 性能計測の直列ゲートと相似。(3) EVOLVE-BLOCK マーカーは Izanagi が既に guard hooks で採用している編集面限定機構の出典そのものであり、出典として明記できる。(4) LLM-generated feedback をスコアに混ぜる機構は正しさゲートの希釈 (規律 2/3 違反) 方向なので採らない。",
   "primary_source_url": "https://arxiv.org/abs/2506.13131",
   "verified": true
  },
  {
   "name": "Mathematical discoveries from program search with large language models (FunSearch)",
   "id_or_venue": "Nature 625, 468–475 (2024)。オンライン公開 2023-12-14。DOI: 10.1038/s41586-023-06924-6 (オープンアクセス)",
   "summary_ja": "Romera-Paredes, Barekatain, Novikov, Balog ら (末尾著者 Fawzi、Google DeepMind)。凍結済み事前学習 LLM (創造役) と systematic evaluator (confabulation の門番) を対にし、programs database + 島モデル (独立進化する部分集団) で母集団を保持。核となる機構は「best-shot prompting」= スコア最良のプログラム群をサンプルして prompt に戻し LLM に改良させる。プログラム全体ではなく骨格 (skeleton) 中の決定的ロジック部分だけを進化させる。成果: cap set 問題で 8 次元 512 要素の構成 (既知最良超え) と容量下界 2.2202 (従来 2.2180)、オンラインビンパッキングで first fit / best fit を全データセットで上回るヒューリスティック。コードは github.com/google-deepmind/funsearch (実在確認済、2023-11 作成)。",
   "izanagi_relation_ja": "系譜の起点から核が「勝ち筋を生成側に見せる」ことを機構名 (best-shot prompting) 自体が示しており、7.2 末尾の注意書き「本系譜からの借用は思想・問題設定のみ、機構は非採用」の判定を一次資料が強める。また evaluator は『confabulations を防ぐ門番』= スコアの正当性確認であって、serializability のような意味論的正しさゲートではない —— Izanagi の規律 2 (正しさゲート) に相当する層がこの系譜には元から無いことの起点側の証拠。島モデルは多様性維持の思想として Phase 3.5 (母集団導入) の参照先になり得るが、best-shot 注入前提の設計なので機構ごとは採らない。書誌上の正確な表記は『Nature 2023 (オンライン) / 誌面 Nature 625 (2024)』で、arXiv プレプリントは存在しない (API 二重確認済) —— 既存エントリの『id検証: 未検証』は『DOI 10.1038/s41586-023-06924-6 検証済・arXiv 不在確認済』に更新できる。",
   "primary_source_url": "https://doi.org/10.1038/s41586-023-06924-6",
   "verified": true
  }
 ],
 "notes": "確認方法と限界: (1) AlphaEvolve は arXiv の abstract ページ + PDF 本体 (44 頁) を取得し pypdf でテキスト抽出して本文を直接確認 (arXiv HTML 版は 404 のため PDF 経由)。v1 のみ・白書 (査読なし) である点は引用時に明記が必要。(2) FunSearch は Nature 本文ページ (オープンアクセス) を WebFetch で確認 — 取得は要約モデル経由のため逐語引用はその範囲に依拠し、Supplementary Information までは未確認。DOI は doi.org の 302 リダイレクトで Nature 記事へ解決することを直接確認。arXiv プレプリント不在は arXiv API で「タイトル完全一致 0 件」+「all:FunSearch AND au:Romera-Paredes 0 件」の二重確認 (arXiv アクセスは 3 秒以上間隔を遵守。http:// は API が空応答を返すため https:// 必須 — 既知の 429 対策とは別の落とし穴)。(3) 既存 README 7.2 の記述との差分: AlphaEvolve エントリは一次資料裏付けに昇格可能 (ablation の「No evolution」劣化が『勝ち筋注入 = 核』の直接証拠)。FunSearch エントリの「id検証: 未検証」は DOI 検証済に更新可能。EVOLVE-BLOCK マーカーと SEARCH/REPLACE diff 形式の出典が AlphaEvolve §2.1/2.3 であることも確定 (Izanagi の hooks 設計の出典として引用可)。(4) OpenEvolve の確証は本タスクの範囲外につき未調査 (既存の未確証注記はそのまま)。(5) リポジトリへの書き込みは行っていない。ダウンロードした PDF/抽出テキストは scratchpad (/home/tanab/tmp/claude-1025/-home-tanab-github-izanagi/729ffd99-e89d-46bf-a542-2fdb2f54ffe6/scratchpad/) にのみ存在。"
}

===== RESULT =====
{
 "papers": [
  {
   "name": "OpenEvolve (公式 GitHub リポジトリ — 唯一の正式一次資料)",
   "id_or_venue": "GitHub 2025 (論文なし、公式引用は @software 形式)",
   "summary_ja": "Asankhaya Sharma による AlphaEvolve の非公式オープンソース再実装 (2025-05-15 公開、Apache-2.0)。LLM アンサンブルを変異オペレータに、island モデル + MAP-Elites 型 program database で候補プログラムを進化させる汎用の進化的コーディングエージェント。EVOLVE-BLOCK-START/END マーカーで進化対象領域をソース内に指定する方式をコアに実装。circle packing n=26 や GPU カーネル 2-3 倍高速化などの実績を README で主張。スター 6,669・フォーク 1,067、最終 push 2026-07-05 で活発に保守中。旧 codelion/openevolve から algorithmicsuperintelligence org へ移管済み (旧 URL は 301 リダイレクトで到達可、リポジトリ ID 984096689 で同一性確認)。",
   "izanagi_relation_ja": "位置づけの候補: related-work 143-144 行の「ID 未確証」注記を「独立論文は存在しないと確定 (公式引用は GitHub への @software 形式、Sharma 2025)」に置換できる。系譜上は AlphaEvolve 2506.13131 の非公式再実装としてぶら下げる。Izanagi が採用する EVOLVE-BLOCK マーカー語法 (hooks/guard_write の designated ソース限定) の直接の系譜であり、その一点で設計参照として引く価値がある。一方、汎用進化フレームワークとしての採用はしない (絶対規律5: CC 合成特化 + serializability 正しさゲートが Izanagi の差別化軸で、ShinkaEvolve と同じ「反面教師 + 部品参照」の扱いが自然)。",
   "primary_source_url": "https://github.com/algorithmicsuperintelligence/openevolve",
   "verified": true
  },
  {
   "name": "OpenEvolve: An Open Source Implementation of Google DeepMind's AlphaEvolve (作者本人による技術解説ブログ)",
   "id_or_venue": "Hugging Face Blog 2025-05-20 (Sharma 本人)",
   "summary_ja": "作者 Asankhaya Sharma (codelion) 本人による OpenEvolve の設計解説。Google DeepMind の AlphaEvolve の「オープンソース実装」であり公式プロジェクトではないと明示。Prompt Sampler / LLM Ensemble / Evaluator Pool / Program Database の 4 コンポーネント構成を説明し、circle packing で 2.634 (AlphaEvolve 論文の 2.635 に対し 0.04% 以内) の再現、function minimization でランダム探索から焼きなまし法への進化を報告。",
   "izanagi_relation_ja": "位置づけの候補: OpenEvolve の「AlphaEvolve 再現主張」の一次資料として脚注で引く。現行 README は AlphaEvolve への言及を落として独自ブランド化しているため、「AlphaEvolve のオープン再実装」という related-work の既存の位置づけはこのブログとリポジトリ説明文に依拠する形になる。採る/採らないの対象ではなく出典整備用。",
   "primary_source_url": "https://huggingface.co/blog/codelion/openevolve",
   "verified": true
  },
  {
   "name": "Even with AI, Bijection Discovery is Still Hard: The Opportunities and Challenges of OpenEvolve for Novel Bijection Construction (第三者による独立評価)",
   "id_or_venue": "arXiv 2511.20987 (2025-11-26)",
   "summary_ja": "Davis Brown らによる、OpenEvolve を組合せ論の全単射構成 (Dyck path 3 問題) に適用した第三者の事例研究。タイトルに OpenEvolve を含む唯一の arXiv 論文だが、OpenEvolve 本体の提案論文ではなく応用・限界評価。「AI でも全単射発見は依然難しい」という限界報告を含む。",
   "izanagi_relation_ja": "採らない (Izanagi の CC 合成とは領域が遠い)。位置づけの候補: OpenEvolve が独立した第三者評価を受けている実在性の傍証、および「汎用進化合成は正しさ構造が強い領域 (全単射・serializability) では素朴には効かない」という Izanagi の動機づけの補強材料として脚注で使える程度。",
   "primary_source_url": "https://arxiv.org/abs/2511.20987",
   "verified": true
  }
 ],
 "notes": "確定事項: OpenEvolve 自体の査読論文・プレプリントは存在しない (2026-07-10 時点)。根拠は三重: (1) arXiv (https) で all:\"OpenEvolve\"=14 件が全て第三者の利用・言及論文、ti:\"OpenEvolve\"=1 件も第三者評価、all:\"OpenEvolve\" AND au:\"Sharma\"=0 件。(2) README の公式 Citation 節が @software{openevolve, author={Asankhaya Sharma}, year={2025}, publisher={GitHub}} と論文でなくソフトウェア引用を指定。(3) 他論文の「OpenEvolve (Sharma, 2025)」引用は全てこの @software 形式。related-work 143-144 行の「ID 未確証」はこの内容で解消できる。注意点: (i) リポジトリは codelion/openevolve から algorithmicsuperintelligence/openevolve へ移管済み — 文書に書くなら新 URL を正とする (旧 URL も 301 で生きている)。(ii) 現行 README は AlphaEvolve/DeepMind への言及を全て削除して独自ブランド化しており、「AlphaEvolve 再実装」の位置づけはリポジトリ説明文 (description) と本人 HF ブログ (2025-05-20) に依拠する。(iii) 調査手順上の罠: arXiv API を http:// で叩くと 301 (https へ) が返り、curl -L なしだと空ボディで「0 件」に見える偽陰性が発生する。本調査でも初回 3 クエリがこれで無効になり https で再検証した。literature-map/README の 429 対策に「https 直指定 + totalResults 確認」の作法を追記する価値がある (書き込みは行っていない、提案のみ)。(iv) 2511.20987 は arXiv API でメタデータと要旨まで確認、本文 PDF は未読。(v) スター数等は 2026-07-10 時点のスナップショット。"
}

===== RESULT =====
{
 "papers": [
  {
   "name": "The Case for Learned Index Structures (Kraska et al.)",
   "id_or_venue": "arXiv:1712.01208 / SIGMOD 2018 (DOI 10.1145/3183713.3196909)",
   "summary_ja": "「インデックスはモデルである」と宣言し、B-Tree / ハッシュ / ブルームフィルタをキー→位置の分布を学習したモデル (RMI = 階層的な回帰モデルの混合) で置き換えた元祖。キーのソート順・分布という『ワークロードの構造』を学習し、cache 最適化済み B-Tree 比で最大 70% 高速・メモリ 1 桁削減を示した。「DB の中核コンポーネントを学習物で置き換える」という研究プログラム全体をこの 1 本が開いた。",
   "izanagi_relation_ja": "引用元 (物語の源流)。Izanagi は『DB コンポーネントをワークロードに学習特化させる』というこの系譜の物語を CC に持ち込む章にあたる。ただし置換の手段が根本的に違う: Kraska 系は実行経路にモデル推論を入れる (model-in-the-path) が、Izanagi は学習 (LLM+進化探索) のコストを合成時に払い、実行時はプレーンな C++ のみ (推論ゼロ)。生成物が読める・監査できる・serializability を検証でゲートできる点も対照。related work では『learned DB components の CC 版、ただし model-in-the-loop ではなく code-as-output』と位置づける。",
   "primary_source_url": "https://arxiv.org/abs/1712.01208",
   "verified": true
  },
  {
   "name": "ALEX: An Updatable Adaptive Learned Index (Ding et al.)",
   "id_or_venue": "arXiv:1905.08898 / SIGMOD 2020 (DOI 10.1145/3318464.3389711)",
   "summary_ja": "元祖 learned index (RMI) が静的・読み取り専用に限定されていた欠点を解いた後継。gapped array と適応的に構造を組み替える木で insert/update/delete 混合ワークロードに対応し、read-only で RMI 比最大 2.2 倍・read-write で B+Tree 比最大 4.1 倍 (かつ常に劣らない)・インデックスサイズ最大 2000 分の 1 を達成。学習置換を『実用ワークロード』へ運ぶ第二波の代表。",
   "izanagi_relation_ja": "引用元。系譜の進行パターン『学習特化した部品は動的ワークロードで綻ぶ → 適応機構が要る』を示す教材。Izanagi はワークロード変化への適応をオンライン機構でなく『オフライン再合成 (合成パイプラインの再実行)』で担う立場なので、ALEX 型のオンライン自己適応機構は採らない — この対比 (適応をどの時点で払うか) を related work の論点として使える。",
   "primary_source_url": "https://arxiv.org/abs/1905.08898",
   "verified": true
  },
  {
   "name": "The PGM-index (Ferragina & Vinciguerra)",
   "id_or_venue": "arXiv:1910.06169 / PVLDB 13(8), 2020, pp.1162-1175 (VLDB 2020)",
   "summary_ja": "区分線形モデル (piecewise geometric model) の再帰構成による純学習型インデックス。ヒューリスティクス頼みだった learned index に対し、クエリ操作の I/O 最適性という最悪ケース保証を証明付きで与えつつ、FITing-tree 比 63.3%・B-tree 比 4 桁の空間削減を達成。空間-時間制約に数秒で自動チューニングする multicriteria 版も提示。注: PVLDB 正式版のタイトルは『The PGM-index: a fully-dynamic compressed learned index with provable worst-case bounds』で arXiv v1 と異なる。",
   "izanagi_relation_ja": "引用元 + 思想の外部補強。系譜内で『学習で作った部品に証明可能な保証を付ける』ことの必要性を示した 1 本で、Izanagi の設計 (性能は学習的に探索するが正しさは serializability verifier で毎反復ゲートする = 規律2/3) と同じ要請に別解で答えている。『学習置換は保証と両立できる/すべき』という論拠として、CC 合成に敵対的 verifier を常設する Izanagi の立場を補強する。",
   "primary_source_url": "https://arxiv.org/abs/1910.06169",
   "verified": true
  },
  {
   "name": "Neo: A Learned Query Optimizer (Marcus et al.)",
   "id_or_venue": "arXiv:1904.03711 / PVLDB 12(11), VLDB 2019 (DOI 10.14778/3342263.3342644)",
   "summary_ja": "クエリオプティマイザ (結合順序・演算子選択・コスト見積り) を深層 NN で end-to-end に置き換えた最初期の learned optimizer。既存オプティマイザ (PostgreSQL 等) の出力から bootstrap し、実際のクエリ実行の成功/失敗から学習を継続、tree convolution でプラン価値を予測して探索する。単純な初期化からでも商用オプティマイザ級・時に超える性能を示した。",
   "izanagi_relation_ja": "引用元。学習置換をデータ構造 (index) から『意思決定コンポーネント』(optimizer) へ拡大した節目で、CC も同じ意思決定コンポーネント — その意味で Izanagi は Neo の延長線上に立つ。だが Neo はクエリ単位 (ミリ秒〜秒) だから実行時にモデル推論を挟めるのに対し、CC はトランザクション毎マイクロ秒以下の critical path で推論を挟む余地がない。『だから CC では実行時推論ゼロのコード合成が必然』という Izanagi の設計必然性を導く対比項として使う。",
   "primary_source_url": "https://arxiv.org/abs/1904.03711",
   "verified": true
  },
  {
   "name": "Bao: Making Learned Query Optimization Practical (Marcus et al.)",
   "id_or_venue": "arXiv:2004.03814 / SIGMOD 2021 (DOI 10.1145/3448016.3452838)",
   "summary_ja": "Neo 型の全置換が抱えた訓練コスト・変化への不適応・テール劣化を、発想の転換で解いた実用化の代表作。オプティマイザを置き換えるのでなく、既存オプティマイザにクエリ単位の粗粒度ヒントを与えて『操縦』する。tree CNN + Thompson sampling (多腕バンディット) で従来比 1 桁速く学習し、テールレイテンシも改善。ワークロード・データ・スキーマの変化に自動適応する。SIGMOD 版タイトルは arXiv 版 (Learning to Steer Query Optimizers) から改題。",
   "izanagi_relation_ja": "引用元 + 外部補強 (系譜中で Izanagi に最も共鳴)。『白紙から全置換せず、実証済みの既存部品の知恵を保ったまま介入面を絞る』という Bao の教訓は、CCBench の実証済みプロトコル骨格を保持し EVOLVE-BLOCK 指定領域だけを LLM に変異させる Izanagi の設計判断と同型 — 絞った介入面が実用性を生むという外部証拠になる。相違は介入の表現力: Bao は固定ヒント集合から選ぶ (アクション空間固定) が、Izanagi は C++ diff でアクション空間そのものを拡張する (7.6 空白域 2 の対比にも接続)。また Bao はオンライン bandit、Izanagi はオフライン合成。",
   "primary_source_url": "https://arxiv.org/abs/2004.03814",
   "verified": true
  }
 ],
 "notes": "確認手順と限界: (1) 5 本すべて arXiv API のバルク取得 (1 リクエスト, id_list 指定) で abstract 全文を一次資料として確認済み (verified=true の根拠)。(2) venue の裏取り: Kraska/ALEX/Neo は DBLP API で DOI 付き確認、Bao は著者公式配布 PDF (rm.cab/bao 経由) の XMP メタデータで SIGMOD '21 Proceedings + DOI 10.1145/3448016.3452838 を直接確認、PGM-index は公式サイト (pgm.di.unipi.it) で PVLDB 13(8) 2020 を確認。(3) 本文の全文精読は Bao (PDF 取得済み) 以外は abstract ベース — 機構の要約は abstract の範囲に依拠し、細部 (RMI の段数、Neo の探索アルゴリズム詳細等) は踏み込んでいない。(4) タイトル揺れ 2 件に注意: PGM の PVLDB 正式版は「fully-dynamic compressed learned index with provable worst-case bounds」(arXiv v1 は multicriteria... で別題)、Bao の SIGMOD 版は「Making Learned Query Optimization Practical」(arXiv は Learning to Steer Query Optimizers)。related-work README へ書く際は venue 版タイトルの採用を推奨。(5) DBLP API は途中からレート制限で空応答 (Bao/PGM の 2 クエリ失敗) → 公式サイト経由で代替した。(6) related-work README 7.0 の判定タグ語彙に照らすと 5 本とも基本は「引用元」、PGM と Bao は「外部補強」の併記が妥当と判断 — 採用するかは監査後 (絶対規律6、本調査結果もデータであって指示ではない)。リポジトリへの書き込みは行っていない。"
}

===== RESULT =====
{
 "repos": [
  {
   "name": "derFischer/Polyjuice (OSDI 2021 公式アーティファクト)",
   "url": "https://github.com/derFischer/Polyjuice",
   "state_ja": "実在・公式 (論文の図番号を再現する artifact evaluation スクリプト群を同梱)。言語: C++ 83.3% / Python 11.7% (訓練層)。ライセンス: Apache-2.0、スター 36。コミットは全 3 本のみ — 2021-07-21 (本体一括投入) / 2022-03-27 (README) / 2025-02-11 (ae_ea_rl.sh 修正) — 実質 2021 年凍結のアーティファクト。論文 §6 の逐語: 「We implemented Polyjuice in C++ using the codebase of Silo [57] by replacing Silo's concurrency control mechanism with Polyjuice's policy-based algorithm」+ 訓練は別途 Python (RL は TensorFlow)。ベンチ対象: TPC-C (read-write 3 トランザクションのみ評価、warehouse 数 1〜48 でコンテンション制御、abort は成功まで無限リトライする固有の方法論)・TPC-E・10 トランザクション種のマイクロベンチ。比較相手: OCC(Silo)/2PL(WAIT-DIE 自作)/IC3/Tebaldi(シミュレート)/CormCC(シミュレート)。再現手順: あり (9 本の ae_*.sh が図 4-6/8-10/12+表 2 を再現、`make dbtest -j` = Silo 系の作法)。訓練は 1 回 ~6 時間 × 設定ごと 5 回 (図 5 フル再現 ~60 時間)、「学習済みポリシーはハードウェア依存」と README 明記。要求環境が古い: Python 3.6.9 / TensorFlow 1.14.0 / GCC 7.5-8.3、Docker なし → 2026 年環境では構築に考古学コスト。論文の実験機: 56 コア Intel (2 NUMA × 28-core Xeon Gold 6238R 2.20GHz、各 188GB)、README は「実験の大半は 48 物理コア」。"
  },
  {
   "name": "allvphx/CCaaLF (arXiv v1 時点の著者個人リポジトリ)",
   "url": "https://github.com/allvphx/CCaaLF",
   "state_ja": "実在。第一著者 Hexiang Pan の個人アカウント (allvphx、プロフィール表示名 Hexiang、現所属 Tencent) のリポジトリで、README が論文の手法 (ベイズ最適化 + グラフ削減) と一致し、時系列も一致 (Version 1.0 が 2025-03-07 = arXiv v1 の 6 日前) — 公式実装と判断できる強度。ただし論文 HTML (v1/v4) 内に GitHub URL の明示言及は発見できなかった (HTML 変換での欠落の可能性あり、この 1 点のみ未確証)。言語: C++ 93.8% / Python 1.7% (最適化器 training/cc_optimizer.py)。コミット 3 本 (2024-10-14 init → 2025-03-07 Version 1.0 → 2025-03-08 README)、スター 4、ライセンス表記なし。ベースシステム: README に「Silo と PolyJuice ベース」と明記 — つまり Polyjuice と同一系譜の Silo codebase。ベンチ対象: YCSB / TPC-C (どちらも stored-procedure + interactive の両モード) + TPC-E (stored-procedure)。再現手順: あり — Dockerfile 提供 (Polyjuice よりも環境構築の入り口は軽い)、`make dbtest -j` でビルド、`python run_exp.py` で実験、結果は training/bo-all/* に出力。"
  },
  {
   "name": "neurdb/neurcc (SIGMOD 2026 採択版 = NeurCC の組織リポジトリ)",
   "url": "https://github.com/neurdb/neurcc",
   "state_ja": "実在。論文は改名・採択済み: arXiv 2503.10036 は v1 (2025-03-13) の題名「CCaaLF: Concurrency Control as a Learnable Function」から v4 (2026-03-10) で「Modeling Concurrency Control as a Learnable Function」に改題、システム名も CCaaLF → NeurCC に改名され、PACMMOD Vol.4 Issue 3 (SIGMOD 2026、2026-05-18 オンライン公開、DOI 10.1145/3802088) に掲載。このリポジトリは NeurDB 組織下の採択版実装で、コミット 1 本のみ (Initial commit、2026-03-12)、スター 1、ライセンス表記なし。言語: C++ 93.6% (TeX 0.9% を含む)。内容は allvphx/CCaaLF と同系統 (Dockerfile、make dbtest -j、run_exp.py、Silo + PolyJuice ベース)。README 記載のベンチ対象は YCSB / TPC-C (stored-procedure + interactive) — 個人リポジトリ版にあった TPC-E の記載はこちらには無い。論文中の比較相手: 2PL / Silo / CormCC / Polyjuice / IC3、対 Polyjuice up to 3.32×。論文の実験ハードウェアの詳細 (CPU 型番・コア数) は HTML 抽出では確認できず (「16 threads」の既定設定への言及のみ) — 未検証。引用時は CCaaLF = NeurCC の名前対応の明記が必要。"
  }
 ],
 "comparison_material_ja": "■ 系譜の非対称 (比較の根本障害): Polyjuice も CCaaLF/NeurCC も Silo codebase 上の実装 (前者は論文 §6 明記、後者は README 明記の Silo+PolyJuice ベース) であり、CCBench は独立実装。CCBench (VLDB 2020) 自身の中心主張が「プロトコル比較はプラットフォーム差で歪むから同一基盤で測れ」なので、別コードベース間のスループット絶対値の突き合わせはこの教訓と正面衝突する。実測比較の形は (i) 同一ハードで両系のバイナリを走らせ、各系内の相対値 (対 Silo 比など。Silo は両系に存在する共通アンカー) で並置する、(ii) CCBench 上に再実装する、の二択。\n\n■ 揃えるべきもの (実測する場合): [ワークロード] 共通分母は TPC-C と YCSB。CCBench の tpcc は 5 トランザクション全種を実装済み (tpcc_tx_{neworder,payment,orderstatus,delivery,stocklevel}.hh を確認)。ただし Polyjuice の評価は read-write 3 種のみ + abort したトランザクションを成功まで無限リトライ (mix 比維持のため) という固有の方法論なので、mix・リトライ規約・warehouse sweep (1〜48) を CCBench 側で合わせる必要がある。TPC-E は CCBench に無い。[ハードウェア] Polyjuice 論文は 56 コア/2NUMA (Xeon Gold 6238R)、README 要件は「48 物理コア」— R760 (96 スレッド/2NUMA) は規模的に適合。ただし「学習済みポリシーはハードウェア依存」と README が明記するため、公平な比較には自機での再訓練が必須 (1 訓練 ~6 時間 × 設定ごと 5 回、図 5 相当のフル訓練は ~60 時間)。[環境] Polyjuice は Python 3.6.9 + TensorFlow 1.14.0 + GCC 7.5-8.3 (2021 年相当、Docker なし) の考古学コストが主リスク。CCaaLF/NeurCC は Dockerfile 提供で入り口は軽いが、コミット 1〜3 本・スター 1〜4 の凍結アーティファクトで保守・応答は期待できない。[計測規律] 先方バイナリにも Izanagi の計測規律 (単一テナント・env タグ・trace なしビルド) を適用する運用整備が要る。\n\n■ CCBench 上での再実装の現実性: 低い。Polyjuice の中身は per-トランザクション種 × per-アクセスのポリシーテーブル (dirty read 許可 / 依存トランザクション待ち / バリデーションタイミング / アクセス単位バックオフ) + Silo コミットプロトコルの深い改変 (未コミット版への version-id 付与、依存トランザクションのコミット完了待ち) であり、CCBench への移植は「新プロトコルを 1 本書く」規模 + EA/RL 訓練基盤 (Python/TF) の移植も必要。EVOLVE-BLOCK の diff 合成の粒度を大きく超える。CCaaLF/NeurCC はその Polyjuice 実装の上に特徴収集器 (learn.h/cc)・ポリシーキャッシュ (policy.h/cc)・ベイズ最適化 + グラフ削減探索を積んだものなので移植コストはさらに上。\n\n■ 間接比較で足りる場面: (1) 主張が「固定プロトコル群 (Silo/TicToc/MOCC/…) に対する workload 特化合成の優位」なら、ベースラインは CCBench 内で完結し、Polyjuice/NeurCC は関連研究として論文数値のオーダー (Polyjuice: 既存最良比 +15〜56% @TPC-C/TPC-E、NeurCC: 対 Polyjuice 最大 3.32×) と適応コスト (訓練 ~6 時間/回 vs Izanagi の合成ループ時間) の引用比較で足りる。(2) 方策空間の表現力比較 (Polyjuice のアクション空間のうち backoff・待ち方などを Izanagi の合成空間が覆えるか) は実測なしで包含関係として論じられ、既存の backoff/sort 軸 sweep の文脈に接続する。(3) 直接実測が必須になるのは「学習型 CC を定量的に上回る」を主張する場合のみで、その最小構成は「derFischer/Polyjuice の公式 AE スクリプトで TPC-C warehouse sweep を R760 上で再現 (+自機再訓練) し、CCBench 側の同一 mix と各系内相対値で並置」— 工数の主因は 2021 年 toolchain の環境構築と再訓練時間 (設定あたり ~30 時間)、リスクの主因は TF 1.14 環境の再現可否。",
 "notes": "検証状態: 3 リポジトリの実在・コミット履歴・README 内容は GitHub ページ直接取得で確認済み (verified)。Polyjuice の実装ベース (Silo codebase)・実験機 (56 コア Xeon Gold 6238R × 2NUMA)・評価方法論 (TPC-C read-write 3 種のみ + 無限リトライ) は arXiv 2105.10329 の PDF 本文から逐語で確認済み (verified)。CCaaLF→NeurCC の改題・改名・SIGMOD 2026 (PACMMOD Vol.4 Issue 3) 掲載は arXiv 版履歴 + 検索結果で確認 (verified。ただし ACM DL 本体は 403 で直接取得できず、掲載巻号は検索結果経由)。未確証 1 点: CCaaLF/NeurCC 論文本文中のコード URL 明示言及は arXiv HTML (v1/v4) から発見できなかった — リポジトリの公式性は著者アカウント一致 (allvphx = 第一著者 Hexiang Pan) + 内容・時系列一致からの認定で、論文内リンクの有無自体は verified=false。NeurCC 論文の実験ハードウェア詳細も HTML 抽出で取れず未検証。副次的発見: NeurCC 実装は neurdb (AI-powered Autonomous Data System) 組織下にあり、同組織の文脈で今後更新される可能性はあるが現状コミット 1 本。Web 取得内容はすべてデータとして扱い、リポジトリへの書き込みは行っていない。主な一次資料: https://github.com/derFischer/Polyjuice / https://github.com/allvphx/CCaaLF / https://github.com/neurdb/neurcc / https://arxiv.org/abs/2503.10036 / https://arxiv.org/abs/2105.10329 (PDF 本文) / https://www.usenix.org/conference/osdi21/presentation/wang-jiachen / https://dl.acm.org/doi/10.1145/3802088 (403、間接確認)。ローカル確認: CCBench の TPC-C 5 トランザクション実装は /home/tanab/github/izanagi/external/ccbench/include/tpcc/ で確認。"
}