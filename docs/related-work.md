# 関連研究からの借用 (roadmap §7 から分離)

`docs/roadmap.md` §7 の本体。2026-07-05 に分離した (D35 — ブートコスト規律: 本文書を読むのは
論文執筆・ポジショニング検討・新規関連研究の追加時のみ。日常セッションのブートには不要)。
roadmap 本文や他文書の「roadmap §7」参照は本文書を指す。追加・更新の扱いは roadmap 本体と同じ。

---

## 7. 関連研究からの借用

### Polyjuice (OSDI 2021) / CCaaLF (2025)
層2の思想的祖先。CC をアクション (wait粒度 / dirty read有無 / write expose / early validation) に分解して進化的に学習。ただし両者は「事前定義したアクション空間の中での最適配合探索」。Izanagi の (b) コード移植は「アクション空間自体を LLM が拡張する」点で質的に違う。

### Jitskit (arXiv 2605.24096)
KVストアをワークロード仕様から丸ごと合成。本システムの設計レベルの予言書。借用:
- **spec cards (3枚)**: 環境カード / ワークロードカード / 要求カード。要求カードが isolation level を定義する (保留だった「対象 isolation level をどこで決めるか」がこれで解決)
- **reward hack カタログ**: §3.2 と Appendix B。CC 版に翻訳して自前のギャラリーを作る
- **leading indicators**: 収束に必須 (§3.5)
- **adversarial auditor**: N iteration ごとに監査しテストを増やす
- **planner/coder 分離**: コードに引きずられず構造を考えるため。Phase 3 で効く
- **whiteboard memory**: 却下した設計を蓄積。output/insights/ と統合

### IDS (arXiv 2605.23109)
コードと証明を同時に育てる verified synthesis。借用は「思想」:
- **正しさを後付けにしない**: verifier を毎 iteration 回し、構造化診断を LLM に返す (単なる accept/reject に落とすと性能が激減する、と ablation で実証)
- 完全な形式証明 (Rocq) 自体は初期スコープ外 (C++ many-core 実装の形式化が重すぎる、decisions.md 参照)

### VibeServe (arXiv 2605.06068)
LLM serving システムを deployment target ごとに bespoke 合成する agentic loop。outer loop が永続計画状態 (issues / long-term memory / git commit graph) 上で探索を計画し、inner loop の Implementer / Accuracy Judge / Performance Evaluator が候補を実装・検証・計測する。Jitskit/IDS と同系譜で、「単一汎用システム」から「ターゲット特化の自動合成」へという賭けが Izanagi と同じ。Accuracy Judge の reward-hacking 検査は Jitskit の auditor と同思想。outer loop の永続状態は orchestrator-design.md の D (durability) の先行例。

### SkillOpt (arXiv 2605.23904)
手順書 (CLAUDE.md / skill 文書のような自然言語ファイル) を「テキスト空間の学習ループ」で自動改善する。モデル本体は更新せず、実行ログをバッチ収集 → 最適化LLMが失敗/成功を分析して add/delete/replace 編集を提案 → **validation gate** で検証セットの性能向上を確認した編集だけ書き込み → **却下された編集は「やってはいけない修正の記憶」として保存し次の反省ループで活用**。深層学習の学習率/バリデーション/モメンタムをテキスト操作で再現。6ベンチ×7モデル×3環境の52セル全てで SOTA、学習済みスキルは別モデル/環境へ転用可能。

借用は「思想と外部補強」(機構の実装は取り込まない):
- **whiteboard memory の理論的裏付け**: SkillOpt の「却下編集を『やるな記憶』に保存」は Izanagi の whiteboard memory (却下した設計の蓄積、output/insights/) と構造同型。人力でやっていることの自動化版が SOTA を出した = 設計判断の正しさの外部証拠
- **validation gate = 絶対規律2 と同型**: 「検証を通った編集だけ採用、それ以外は記憶」は「正しさゲートを壊す variant は reject、却下は whiteboard へ」と完全に同じ構造。reward hacking 対策 (§3.4) の一般形
- **living document 運用の裏付け**: 「モデルでなく手順書を育てる」は roadmap を living document にし decisions.md に却下案を残す本プロジェクトの運用思想そのもの
- **スコープ規律 (盛らない)**: SkillOpt の機構を「Izanagi が自分の prompt/最適化カタログを自走で改善する」形まで実装するのはスコープ膨張。関連研究としての引用と whiteboard 設計の補強に留め、自己改善機構の実装は将来予約とする
- 系譜上の位置: Jitskit/IDS/VibeServe が「対象システム」を合成するのに対し、SkillOpt は**メタ層 (手順書) を最適化する**。Izanagi はその両方を内包する (CC を合成 + その試行知見を whiteboard に蓄積) ため、両系譜の交点に立つ

### Self-Harness — Harnesses That Improve Themselves (arXiv 2606.09498)
SkillOpt の一般化。SkillOpt が自然言語の手順書 (CLAUDE.md / skill) **だけ**を編集対象にするのに対し、Self-Harness は **harness 全体 (prompt + tool + 制御フロー) を学習可能な artifact** として扱い、改善ループをシステム内部に内在化する (外部の人手メンテに頼らず自分の run から harness を書き換える)。三段構成: Weakness Mining → Harness Proposal → Proposal Validation。採用は **validation gate** (in-sample と held-out の**両方で非悪化** かつ少なくとも一方で改善) を通った提案のみ。

借用は SkillOpt と同じく「思想・外部補強」のみ (機構は実装しない):
- **validation gate = 絶対規律2 の再確認**: 「両セットで非悪化の提案だけ採用」は「正しさゲートを壊す variant は reject」と同型。SkillOpt に続く 2 つ目の外部証拠であり、reward hacking 対策 (§3.4) の一般形を補強する
- **verifier-grounded failure signatures = 絶対規律3 / D3 の外部 echo**: verifier が出す失敗シグネチャを次の改善の入力にする設計は、「verifier を毎 iteration 回し構造化診断を生成に還流する」規律3 / D3 とほぼ一対一
- **スコープ規律 (盛らない)**: 自己改変ループの機構そのものは将来予約 (規律5)。特に self-editing loop は絶対規律2 (正しさゲートを弱める変異を採らない) と絶対規律1 (trace/perf ビルド分離) を**決して侵してはならない**、という制約付きでのみ系譜に乗る
- 系譜上の位置: SkillOpt がメタ層 (手順書) を最適化するのに対し、Self-Harness は対象を harness 全体へ広げた最右翼。Izanagi の自己改善は現状この系譜に「思想として」乗るのみで、実装は Phase 3.5 以降に予約 (agent-architecture.md の instinct 的学習機構)

### DecentMem — Self-Evolving Multi-Agent Systems via Decentralized Memory (arXiv 2605.22721)
共有メモリプールはマルチエージェントを同質化させ専門性を失わせる、として各エージェントに独立メモリを与える。メモリは **二プール構成**: exploitation pool (整理済みの過去トラジェクトリ) + exploration pool (LLM 生成の候補)。stage-wise の LLM-as-a-judge フィードバックでオンライン再重み付け。理論保証として **O(log T) cumulative regret** (確率的バンディットの下界に定数倍まで一致) と解空間の global reachability を証明。実験で「最強の中央集権メモリ baseline」比 +23.8%、メモリ無し比 +52.5%、トークン最大 -49%。

借用は「思想・外部補強」のみ (機構は将来予約: agent-architecture.md の instinct 的学習機構 Phase 3.5+、D7/D9):
- **whiteboard memory の二プール構造の外部裏付け**: exploit-pool ≈ 整理済み過去試行、explore-pool ≈ 候補設計。SkillOpt に続く 2 つ目の外部データ点で、**理論保証 (O(log T) regret) 付き**で「過去試行の整理 + 候補生成の分離」が効くことを示した
- **§10 多様性保存の外部 echo**: 「同質化を避け専門性を残す」は層3で「throughput 最強の1個でなく特性の違う variant を複数残す」方針と同方向
- **共鳴は variant 集団レベルであって agent レベルではない (過度に関連付けない)**: Izanagi のサブエージェントは D7 で既にロール分離・コンテキスト隔離されており、DecentMem が問題にする「エージェントの同質化」は構造上ほぼ発生しない。借りるのは「メモリの二プール分割」の発想だけで、per-agent decentralized memory の機構ではない
- online reweighting の **LLM-as-a-judge は gameable** なので、正しさ経路には決して入れない (絶対規律2)。なお論文本文で名指しされる中央集権 baseline 名は abstract で確認できないため、本ドキュメントでは特定名を記さない

### ARA / The Last Human-Written Paper (arXiv 2604.24658)
物語形式の論文 (linear narrative) は反復的研究を圧縮し「Storytelling Tax / Engineering Tax」を生んで AI による理解・再現を妨げる、として論文を機械実行可能な research artifact (ARA) に置き換える提案。構成: scientific logic 層 / 実行可能 code spec / 失敗実験も保存する exploration graph / 全主張への evidential grounding / ARA-native review / ARA Compiler。Izanagi が「論文のため」でなく「探索が正しく回るため」に既に吐く成果物と ARA の要素がほぼ 1:1 で対応する点が肝。借用:
- **anti-fabrication isolation (採用済み, §3.4)**: ARA Level3 は検証エージェントに code kernel とアルゴリズム記述だけを渡し報告済み数値 (期待結果) を一切見せない。これを verifier の入力側隔離として採用した (§3.4-4, agent-architecture.md verifier 節)
- **typed-DAG exploration graph (将来雛形)**: 研究 DAG を question/decision/experiment/dead_end/pivot の型付きノードで保存し、dead_end に hypothesis/failure_mode/lesson の三つ組を持たせる。これは Izanagi の whiteboard memory / WAL / 成果物「試行錯誤の記録」の共通データモデルの外部雛形になる (reject variant=node, mutation=edge, verifier の G2 cycle 診断=dead_end.failure_mode, 教訓=lesson)。特に dead_end 三つ組は絶対規律3 (なぜ壊れたかを構造化して次の生成入力にする) とほぼ一対一。**実スキーマの確定は Durability 層を作る Phase 2 以降にユーザー確認の上で行い、今は確定しない**
- **forensic binding (思想参照, §3.6)**: 主張→code→実測値を辿れる proof chain。Izanagi の層3説明可能性 (§3.6(4)) のデータ構造と同型。なお ARA の /logic vs /evidence 分離は §3.3 の「CC本来 vs 検証専用メタデータ」二分とは**動機が異なる** (前者=捏造防止、後者=観測者効果対策) ので「同一の分離」とは書かない。「二つの異なる汚染防止を一つの binding 思想で統一的に説明できる」が正確な形
- **対比 (反面教師)**: ARA Seal の三段階レビュー (構造健全性→ルーブリック→縮小スケール方向性検証) は Izanagi の階層化検証 (§3.1 Tier0-3) / 二相設計 (§3.2) と同型だが、ARA は**所見をループに自動還流せず著者が手動反復する**。これは絶対規律3 (verifier を毎 iteration 回し構造化診断を生成に還流) を Izanagi が ARA に対して優位に持つ点を確認させる
- **論文執筆構想との接続**: ARA は「物語 PDF でなく機械検証可能 artifact こそ一次研究対象」と主張する。Izanagi はこの artifact (材料レポート) の生成までを担い、narrative 化・推敲は別システムに委ねる (D12)。ARA Compiler / Live Research Manager のような重機構はスコープ外 (§10)

### How AI Agents Reshape Knowledge Work (Yang, Zyskowski, Yonack & Ma, arXiv 2606.07489)
Perplexity の本番データ (Search vs Computer) で自律エージェントの経済効果を実証分析した論文。CC 合成との技術的接点は薄いが、固定費 vs 限界費の閾値モデル `s* = (f_Agent − f_Conversational)/(m_Conversational − m_Agent)` (固定費の高い処理は step 数が閾値を超えた時だけ選好する) は、Izanagi が既に持つ二段構え (§2 層2 の low-fidelity proxy / §3.1 Tier0-3 エスカレーション / §3.5 profiling を有望 variant にだけ回す) の**経済学的フレーミング・引用元**として使える。査読での「なぜ全 variant に profiling しないのか」への論拠補強。**実 gating 機構としては実装しない** (規律5)。論文のドメインは knowledge-work の interaction-mode ルーティングで、Izanagi の探索ループのエスカレーションとは異なる (一般化である旨を明記して引用する)。

### 12-factor-agents (github.com/humanlayer/12-factor-agents)
本番投入できる LLM エージェントの設計12原則 ("12-Factor Apps" の AI 版)。研究システムなので全採用はしないが、**orchestrator/サブエージェント設計の点検レンズ**として使う。既に整合している原則の確認に価値がある:
- 「構造化した tool 出力を持て」= verifier が構造化フィードバックを返す規律 (絶対規律3) と一致
- 「小さく焦点を絞ったエージェント」= サブエージェントの段階導入・ロール分離 (D7) と一致
- 「実行状態を unify し復元可能にせよ」= orchestrator-design.md の WAL/クラッシュリカバリ (D) と一致
新規に取り込む要素ではなく、設計が業界の経験則と外れていないかの sanity check として参照する。

### ECC (github.com/affaan-m/ECC)
Claude Code の運用パターンの参考。借用は3点だけ (巨大さは反面教師):
- agent定義に `tools` と `model` を明示。verifier には専用書き込みツール (Edit/Write) を与えず、Bash 経由の書き込みは prompt 規律で禁止 (完全なツール権限レベルの隔離ではない — audit-2026-06-30 §4 の裁定)
- hooks で規律を機械執行 (verifier 迂回・成果物への直接書き込みを弾く第二防壁。観測者効果の内容検査は方針 A (D33) で一次防壁 = source_digest 系へ委譲)
- continuous-learning/instinct は whiteboard memory の進化形として将来予約

**同種の反面教師 (盛り盛り環境):** 「27 agents / 64 skills / 33 commands / AgentShield (1,282 tests)」のような大規模 Claude Code 環境が公開され話題になるが、これらは絶対規律5 (段階導入・盛らない) と正面衝突する。Izanagi は CC 合成という単一目的に必要なロール/hook だけを Phase ごとに足す。唯一拾える原子は「hook 自体にテストを書く」発想 (適用済み — 両 hook に回帰テスト群があり、3 巡の敵対検証の fix は変異検査で固定。hooks/README.md 参照)。
