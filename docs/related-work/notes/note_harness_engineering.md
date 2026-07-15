# 調査ノート: Effective Harness Engineering for Algorithm Discovery with Coding Agents

- **論文**: Effective Harness Engineering for Algorithm Discovery with Coding Agents
  - venue/year: CoRR (arXiv preprint) 2026、cs.SE、v1 (2026-05-13)、License CC BY 4.0
  - authors: Yoichi Ishibashi, Taro Yano, Masafumi Oyamada (NEC)
  - arXiv: 2605.15221 / https://arxiv.org/abs/2605.15221 (DOI 10.48550/arXiv.2605.15221 は CrossRef 未登録。本文は arXiv HTML 版から取得した)

---

## 問題設定 / 一言要約

LLM×進化探索によるアルゴリズム自動発見 (FunSearch / AlphaEvolve) の成否は、モデル能力だけでなく **harness (足場=実行インフラ全体: プロンプト構成・データ設計・評価パイプライン・並列エージェント管理)** の設計に大きく左右される、という主張。既存 OSS 実装 (OpenEvolve, CodeEvolve) は LLM を **stateless なコード生成器** (単発 API 呼び出し) として使っており、2025 年以降急速に進歩した coding agent (Claude Code / Codex CLI) の能力を活かせていない。本論文は自作 harness **Vesper** を通じて 3 つの問いに実証的に答える:

1. 固定トークン予算下で、**浅い思考で多数**生成すべきか **深い思考で少数**生成すべきか
2. **評価ハック** (生成プログラムがスコア関数の欠陥を突く) にどう対処するか
3. フルファイルシステムアクセスを要するエージェントをどう**安全に並列**実行するか

結論の核: **深く考えて少数を作る方が予算効率が良い**。そして **能力の高いモデルほど評価ハックを高率で生成する** ため、モデルがスケールするほどハック検出が必要になる。

---

## 手法の核 (Vesper の harness 構成要素)

Vesper は OpenEvolve の改造ではなく、**coding agent を設計前提にゼロから構築**した harness。進化の対象を**リポジトリ**とし、**Git ブランチを単位に進化木**を構築する。1 サイクル: (1) program DB から親ブランチをサンプル → (2) そのブランチから Git worktree を作り隔離実行環境を構築 → (3) worktree 内で coding agent を起動、program DB を参照しつつ自律的にコード改善+テスト → (4) 評価器がスコア計算 → (5) ハック検出で整合性検証 → (6) 通過した候補ブランチを program DB に追加。多様性は **island model のみ**で維持 (AlphaEvolve の MAP-Elites は使わない)。

1. **Coding agent 統合 (§4.2)** — stateless 単発 API を自律 coding agent に置換。エージェントは 1 セッション内でソース読解・評価実行・エラー検査・関連モジュール参照・多段デバッグ・自己修正を行う。単一関数変異の制約から解放され、どの関数をどう直すかをエージェント自身が決める。出力は「コード変更 + 試みたアプローチ + スコア改善の根拠」を含む構造化形式で記録され、DB observation の入力になる。
2. **評価ハック検出 (§4.3)** — 候補が評価を通過した後に、**独立した二次エージェントセッション**が候補の実装コードを検査し、「本当に問題を解いているか / 評価機構を悪用しているか」を判定。ハックと判定された候補は**親選択プールから除外**し、退行的戦略が進化系統に広がるのを防ぐ。既存フレームワークにこの機構は存在しない。
3. **DB observation (§4.4)** — SQLite ベースの program database。worktree ごとのリポジトリ情報・ブランチ系譜・評価結果・アルゴリズム記述・コード diff・改善アイデアをリレーショナルに蓄積。要点は「プロンプトに要約を注入」ではなく **DB パスをエージェントに渡し、エージェント自身が SQL を実行**して必要情報を取りに行かせること (coding agent はツール実行能力を持つため)。親系譜を辿って過去の失敗を避けたり、他 island で急伸した変更を調べて自分の改善に活かせる。
4. **Git worktree 隔離 (§4.5)** — 各エージェントに専用 Git worktree を割り当て、リポジトリ全体を clone せずに**完全なファイルシステム隔離**を達成。Vesper のエージェントは workspace 内でファイルシステムに無制限アクセスするため、共有 FS での同時書き込みは race condition と状態破壊を招く。全リポジトリ clone は大規模リポジトリではディスク・初期化時間の点で非現実的なので worktree を使う。
5. (探索基盤) **island model** — 5 islands, migration interval 50, migration rate 0.1, exploration 0.3, exploitation 0.7 (OpenEvolve 公式設定を両システムで統一)。
6. (終了基準) **トークン消費上限 (40M tokens) を終了条件**に採用。生成アルゴリズム数でなくトークンを基準にするのは、per-iteration コストが異なるシステム間の公平比較のため、かつ API コスト制約に直接対応する実務的基準だから。

---

## 主要な実験結果 / 主張

タスク: **Circle Packing (n=26)** — 単位正方形に 26 個の非重複円を詰め半径和を最大化。ハック検出は全条件で gpt-5.1-codex-mini を使用。ターゲットは AlphaEvolve の 2.635、human best 2.6340。数値は 2 run 平均/最良。

- **Finding 1 (coding agent 置換が効く)**: 同一モデル・同一トークン予算で Vesper (gpt-5.2-codex, ハック検出なし) が OpenEvolve を大きく上回る。**約 5M トークンの時点で OpenEvolve の最終スコアを既に超える**。安価な gpt-5.1-codex-mini ですら OpenEvolve の gpt-5.2 を上回り、効果はモデル規模に依存しない = harness 設計だけで大きな差が出る。
- **Finding 2 (質 > 量)**: OpenEvolve (gpt-5.2) は 23.9K tok/algo で 1,671 候補生成するが best は低い (Raw Best 2.41852)。Vesper (gpt-5.2-codex, ハック検出なし) は 89.6K tok/algo で **わずか 452 候補**だが AlphaEvolve と human best を両方超える。安価モデルでも Vesper 110 候補が OpenEvolve 1,487 候補を上回り human best に迫る。**固定予算下では per-algorithm の推論をスケールさせる方が世代数をスケールさせるより効果的**。
- **Finding 3 (能力↑ ⇒ ハック↑)**: gpt-5.2-codex では 352 アルゴリズム中 **29 件 (8.2%)** がハックとして検出・除外され、ハック検出 **on が off を上回る**。一方 gpt-5.1-codex-mini ではハックが 1 件も発生せず、ハック検出 on は off を**下回る** (ハック不在時は検出のオーバーヘッドが世代数を削り逆効果)。**ハック検出の必要性はモデル能力に比例して増す**。
- **Finding 4 (DB observation の効果は限定的)**: 2 run では明確な便益なし。gpt-5.1-codex-mini / gpt-5.2-codex いずれ (ハック検出 on) でも DB observation on が off を下回る。DB 参照がトークンを消費し同一予算下の生成数を減らすため、過去参照の便益を相殺している可能性。
- **並列 (Table 2)**: 4 並列エージェントで並列度 (直列総時間÷実時間) は **3.2x〜3.9x**。最も計算集約な条件で実時間を **約 70 時間 → 20 時間**に短縮。
- **コスト分析 (§6)**: Codex CLI モデルは per-token コストが高い (gpt-5.2-codex $9.77/M vs stateless $2.68/M ≈ 3.7x 差)。それでも:
  - **等コストでも質重視戦略が優位**: OpenEvolve のトークン予算を Vesper と等コストの 146M tokens (約 $392) に増やし 4,239 アルゴリズム生成しても Vesper との差は埋まらない。
  - **高価モデルの方がコスパ良い**: gpt-5.2-codex ($9.77/M) は gpt-5.1-codex-mini ($1.05/M) より 1 ドルあたり到達スコアが高い。
  - **$38 (3.9M tokens) で AlphaEvolve/human best 水準に到達**。安価モデルも $42 で human best に接近。

---

## izanagi のどの層・部品に効くか

Vesper の 4 本柱は izanagi の設計語彙とほぼ 1:1 で対応し、**設計判断の実証的裏付け**として直接使える。

- **層2 (最適化移植ループ) の中枢 ★最重要** — Finding 2 の「質 > 量」は izanagi 層2 の「LLM 誘導で少ない試行で収束」(roadmap §2 層2) と、層1 の「初期個体の質より mutation operator/evaluator の質が支配的」の両方を実証で支える。coding agent が自律的に読解・テスト・自己修正するループは、izanagi の coder/critic/profiler が回す variant 生成そのもの。
- **評価器 / §3.4 reward hacking 対策 / auditor / hook** — Finding 3 は izanagi の最重要リスク (§3.4 reward hacking) に対する**定量的根拠**を与える。izanagi は既に「据え置きの正しさゲート」「adversarial auditor (Phase3)」「verifier 迂回を弾く hook2」を設計済み。Vesper の「独立二次エージェントによる事後ハック検査」は、izanagi の trace verifier (決定的な cycle 検出) が構造上見逃しうる**意味論的ハック** (問題を解かず評価機構を突く) を捕まえる相補的機構。
- **orchestrator (Isolation / 並列)** — izanagi orchestrator-design は既に「worktree 分離」を Isolation の実装として明記。Vesper の Table 2 (3.2–3.9x) はその具体的機構と実効値の裏付け。
- **DB observation ↔ WAL / whiteboard memory / program database** — izanagi の SQLite ベース WAL・whiteboard・program DB 構想と一致。ただし Finding 4 (効果限定的) は「入れる=正義」ではないという警告として重要。
- **予算設計** — トークン上限を終了基準にする発想は、izanagi の「何回 variant を試せば報われるか」(Best-of-∞ 系) の予算設計に転用可能。ただし後述の重大な差 (izanagi の律速はトークンでなくベンチ実時間) に注意。

---

## 具体的に izanagi に移植できる要素 (設計レベル)

1. **独立二次エージェントによる評価ハック検出パス** — verifier (Tier1 決定的 trace 検査) を通過した候補に対し、**別コンテキストのエージェントが「この variant は本当に CC 問題を解いているか / 評価機構を突いていないか」を検査**する層を追加。izanagi の Phase3 auditor 仕様に、Vesper の「事後・独立セッション・親選択プールから除外」というワークフローを具体化して組み込む。
2. **能力↑⇒ハック↑を ablation 軸に昇格** — izanagi の campaign 同一性設計 (search-tag による ablation 分離) を使い、「使用モデル能力 × ハック検出 on/off」を明示的 ablation 軸にする。Vesper の Finding 3 (安価モデルでは検出が逆効果) は「ハック検出を常時 on にしない、モデル能力に応じて出し入れする」設計判断を示唆。
3. **質重視の探索戦略 (per-variant により深い agent 推論)** — 層2 で「多数の安い variant」でなく「少数の深く練られた variant」を回す方針を default にする。roadmap §2 層2 の「LLM に次の一手を考えさせる」を、単発 diff でなく **1 セッション内多段 (実行→エラー観測→修正) の自己修正ループ**に格上げする。
4. **DB observation = agent 自身に SQL を叩かせる方式 (+ 効果の ablation)** — whiteboard/WAL を「プロンプトに要約注入」でなく「**DB パスを渡してエージェントに SQL クエリさせる**」方式で実装する。ただし Vesper Finding 4 に倣い、**便益は自明でない前提で必ず on/off ablation を組む** (izanagi の campaign 設計はこれを素直に表現できる)。
5. **worktree 隔離の実効値をベンチマークに含める** — izanagi orchestrator の Isolation 実装で、Vesper Table 2 のように「worktree あり/なしの並列度・実時間短縮」を計測してログに残す。
6. **構造化エージェント出力 (コード変更 + アプローチ + 根拠)** — Vesper のエージェント出力形式 (試みたアプローチと改善根拠を構造化) は、izanagi 層3 の説明生成 (差別化の核心) の原料にそのまま使える。coder サブエージェントの出力仕様に組み込む。

---

## izanagi に入れる際の障害・前提・リスク

- **【最重要】律速資源の違い: トークン ≠ ベンチ実時間** — Vesper の予算・終了基準・コスト分析はすべて**トークン**を軸にする。しかし izanagi の律速は **性能ベンチの実時間** (1 variant = 数十秒、しかもベンチは排他ロック必須 = 並列不可、orchestrator-design I)。Vesper の「深く考えて少数」は izanagi ではさらに強く効く可能性がある (ベンチ回数を減らせる) が、コスト計算式 (トークン単価比較) はそのまま移せない。izanagi 版は「ベンチ実時間予算」で再定式化が必要。
- **worktree はファイルシステム race を解くが、ベンチ干渉は解かない** — Vesper の worktree 隔離は FS 競合対策。izanagi の Isolation はそれに加え **CPU/cache/メモリ帯域の物理干渉** (観測者効果の延長) が本質で、worktree では解けない。izanagi は worktree (ビルド/検証の並列化) と**ベンチ排他ロック**を別物として維持する必要がある。ここを混同すると性能数値が汚染される。
- **ハック検出器も LLM = それ自身がハックされうる** — Vesper のハック検出は独立エージェントだが、izanagi の verifier は「入力側隔離 (期待値・throughput を見せない)」「出力側隔離 (Edit/Write 権限を外す)」を絶対規律にしている。Vesper の検出エージェントにこの隔離が入っているかは本文から特定できず。izanagi へ移植する際は izanagi の隔離規律を必ず被せる。
- **DB observation の効果が限定的** — Finding 4 は 2 run のみで統計的に弱い。izanagi の whiteboard/DB observation を「効くはず」で作り込むのは危険。ablation で効果を確認してから投資を決める。
- **タスク特性の差** — 本論文の実証は Circle Packing (幾何最適化、正しさ=スコア関数、単一目的) 1 タスク・2 run のみ。izanagi の CC 合成は **正しさ (serializability) と性能が別軸** (Pareto、層3) で、評価が本質的に多次元。「質 > 量」の一般化可能性は CC ドメインで再検証が要る。
- **MAP-Elites 不使用** — Vesper は island model のみで MAP-Elites を捨てた。izanagi の層3 Pareto 選択・多様性維持で MAP-Elites 相当 (behavior descriptor による多様性) が要るかは別途判断が必要。

---

## 小山田さんに聞くべき質問

1. **予算軸の転換について**: Vesper はトークンを律速資源に据えていますが、izanagi のような「ベンチ実時間が律速 (しかも排他ロックで並列不可)」なドメインでも「深く考えて少数」の優位性は保たれるとお考えですか。むしろベンチ回数削減でより強く効く一方、コスト定式化はトークンからベンチ時間へ全面的に書き換えが要ると見ていますが、Vesper 設計時にこの「非トークン律速」ケースは想定されましたか。
2. **ハック検出器の隔離**: 独立二次エージェントによるハック検出で、その検出器自身が「期待スコアや性能数値を見て緩い判定を出す」ように毒される経路はどう塞いでいますか (izanagi は verifier の入力側/出力側隔離を絶対規律にしています)。また Finding 3 の「能力↑⇒ハック↑」は、検出器を被検体と同等以上に強いモデルにしないと検出が破れる、というスケーリングの含意を持ちませんか。
3. **DB observation が効かなかった理由**: Finding 4 の「効果限定的」は、(a) 情報の届け方 (SQL を叩かせる方式) の問題か、(b) Circle Packing が過去試行の共有からあまり益を得ないタスクだったからか、(c) トークン消費のトレードオフが便益を食ったからか、どれが主因とお考えですか。izanagi のように「試行ログの因果込み蓄積」が成果物 (説明可能性) そのものであるケースでは、DB observation の投資対効果は変わりうると見ていますか。

---

## 引用/リンク

- 本論文: arXiv:2605.15221, https://arxiv.org/abs/2605.15221 (DOI 10.48550/arXiv.2605.15221)
- 関連: AlphaEvolve (Novikov et al. 2025) / FunSearch (Romera-Paredes et al. 2024) / OpenEvolve (github.com/algorithmicsuperintelligence/openevolve) / CodeEvolve (Assumpção et al. 2025, arXiv:2510.14150) / Can LLMs Invent Algorithms to Improve Themselves? (Ishibashi, Yano, Oyamada 2024, arXiv:2410.15639) / reward hacking = Concrete Problems in AI Safety (Amodei et al. 2016)
- izanagi 対応箇所: roadmap.md §2 (三層), §3.4 (reward hacking 対策), §3.5 (leading indicators); orchestrator-design.md (Isolation/worktree, WAL, campaign 同一性); agent-architecture.md (verifier/auditor/coder 仕様, hooks); phase1.md (評価器)
