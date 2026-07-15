# 調査ノート: cotomi Act: Learning to Automate Work by Watching You

- **論文**: CAIS '26 (ACM Conference on AI and Agentic Systems, demo track), 2026.
  著者: Masafumi Oyamada, Kunihiro Takeoka, Kosuke Akimoto, Ryoma Obara, Masafumi Enomoto, Haochen Zhang, Daichi Haraguchi, Takuya Tamura (NEC).
  DOI: 10.1145/3786335.3813203 / arXiv:2605.03231v1 [cs.AI].
  **本文取得経路**: DOI 経由 (fetch_article_fulltext) は landing page のみで本文取れず→ abstract のみ取得。
  arXiv HTML 版 (https://arxiv.org/html/2605.03231v1) を直接取得しテキスト抽出。本ノートは arXiv v1 全文 (本文+Appendix A–C) に基づく。
  なお本稿は CAIS の **demo/system paper** であり、評価は WebArena/WorkArena 上のベンチと proxy 評価。深い ablation は WebArena-Verified の scaffold 部分に限られる。

## 問題設定 / 一言要約
ブラウザ上で動く computer-using agent (CUA) に、(1) 長ホライズン web タスクを確実にこなす**推論能力**と、
(2) 組織固有の暗黙知（誰が何を承認する、社内ジャーゴン、進行中タスク）を持たせる。
後者を **「ユーザの普段のブラウジングを黙って観察し、それを段階的に抽象化して知識アーティファクト（タスクボード・wiki）にする」**
という behavior-to-knowledge パイプラインで実現。実行と知識の両輪を、ユーザとエージェントが双方向に編集できる共有ワークスペースで橋渡しする。
一言: **「見て学ぶ CUA」= 高信頼 scaffold + 観察からの組織知の受動学習 + 人間可読・可編集な共有知識。**

## 手法の核（具体的に）
1. **Agent scaffold の4機構（context bloat 対策が主眼）**:
   - **adaptive lazy observation**: 毎ステップ完全な accessibility tree を渡さず、viewport 内要素だけ送り、必要時に全ツリーをオンデマンド取得。精度ほぼ同等で応答時間 471s→184s（約 2.6×）。
   - **verbal-diff ベースの履歴圧縮**: 過去の生観測を保持せず「ステップ間で何が変わったか」を自然言語 diff（例: "New element: [42] button 'Submit'"）で表現。履歴に適用すると精度 +1.1pp・トークン 3.8×削減（23.9K→6.3K/step）。現観測に適用すると **+12.7pp（40.6→53.3%）** で位置ベース diff（+7.3pp）を上回る。NL の意味的 diff が標準 diff フォーマットに勝る点が主張。
   - **coarse-grained actions**: 抽象度の高いアクション（`scrollBy(x,y)` を `scrollInto(element)` に）で1インテント=少ステップに。
   - **task decomposition**: 推論モデルが複数の独立サブゴールを含む構造化プランを出したとき、focused context を持つ**並列サブエージェント**に分割。
2. **test-time scaling (TTS)**: best-of-N アクション選択（各ステップで N 個候補をサンプル→多数決、通常 N≤5、**明示的な事後 verifier を使わず事前合意で分散削減**）+ task decomposition。
3. **User Behavior Logger（二相）**: 軽量キャプチャ（サイト操作・タブ遷移・定期スクショ、diff 圧縮で重複除去）→ **LLM ベースの agentic ETL**（3段: エピソード分割→構造化要約+分類→知識アーティファクト集約）。fixed-rule 版と blind 比較（2アノテータ×50セッション）で agentic 版が勝った。opt-in + PII マスキングの privacy ゲート。
4. **Shared Knowledge Workspace**: activity timeline / task board / wiki の3種。**「各アーティファクトは agent 内部メモリでなく first-class なユーザアプリ」**という設計原則→双方向編集（agent が観察から起草、ユーザが検査・修正・承認）。**boundary object**（人間はタスク管理ツール、agent は次アクションの根拠として同じ物を見る）として機能し、post-hoc 説明でなく **transparency by construction** を狙う。
5. **オンデマンドな組織知取得**: scaffold は実行前に `search_workspace` ツール（NL クエリ→関連タスク/wiki/timeline を relevance 順で返す）をモデル自身の判断で呼ぶ。毎ターン無関係な context を注入しない。

## 主要な実験結果 / 主張（数値）
- **実行**: WebArena 179-task human-eval subset で **cotomi Act +TTS = 80.4%**（human baseline **78.2%** を上回る）。base scaffold のみで 76.5%、+TTS で **+3.9pp**。全 812 タスクでは 75.7%。他システム: OpAgent 71.6%(all)/74.9%(subset), CUGA 61.7/64.3, OpenAI Operator 58.1。cotomi は site-specific ヒント無し（answer-format 明確化のみ）で達成。
- **scaffold ablation**: WebArena-Verified, Gemma-4-31B-IT, 39 構成, 82 タスク×3 run。現観測 diff と履歴 diff は**部分的に代替**（合算 +22.1pp に対し併用 +13.8pp）。履歴は step20 で ~57K トークンに膨張するのを圧縮。
- **行動知識**: WorkArena-L1（6カテゴリ、~277 hints、coverage 0→100%）。coverage 増で成功率が **zero-coverage baseline(≈51%) 比 最大 +10pp**。**フォーマット依存**: raw trajectory は低 coverage で劣化（17% で −2pp）だが高 coverage で最強、script/insight は全域で安定。
- **service-catalog エピソード**: 48 scripts 生成。scripts 提供前 ≈75% → 後 ≈99%（Table2 mean 75.0%→99.2%）。行動知識が実行成功に直接因果的インパクトを持つ証拠。
- **評価器の信頼性**: WebArena 自動 scorer が非自明な割合で false positive/negative を出したため、3アノテータが全自動判定を手動検証（WebArena-Mod を公開）。

## izanagi のどの層・部品に効くか
- **評価器 (Phase1) ★最重要**: 「ベンチの自動 scorer 自体が信用できず手動検証が要った」は izanagi の中核信条「evaluator こそ loss 関数、嘘をつけば下流は全部ゴミ」の外部実例。**verifier が赤を出せることの証明（Phase1）** の必要性を裏書き。逆に cotomi が **事後 verifier を捨て best-of-N 事前合意 + 人手 curation で代替**する点は izanagi の絶対規律2/3（据え置き正しさゲート・毎 iteration verifier）と**正面から対立**する設計判断＝議論の主戦場。
- **層2（最適化移植ループ）**: agentic ETL の「生ログ→構造化→知識アーティファクト」の段階的抽象化は、izanagi の「最適化カタログ化（前提+効果+実装の三つ組）」と同型。best-of-N はランダム変異でなく複数提案の合意で分散を下げる screening として層2探索に翻訳可。§3.5 leading-indicator フィードバックの表現に verbal-diff が刺さる。
- **層3（選択+説明）**: boundary object / 双方向 curation / **transparency by construction** は izanagi の「人間検証可能な説明」「還元判断=ユーザ確認待ち」ゲートと同思想。ただし izanagi は post-hoc 説明生成、cotomi は構造で透明性を作る＝アプローチが逆で、対比が鋭い。
- **orchestrator/hook**: lazy observation・verbal-diff 履歴圧縮・並列サブエージェントの focused context は、一晩回す長ホライズン進化ループの context 管理に直結。opt-in+PII の privacy ゲートは hook（書き込み時防壁）の運用例。
- **層1**: 直接寄与は薄い（task decomposition の並列サブゴールは island seed の比喩程度）。

## 具体的に izanagi に移植できる要素（設計レベル）
- **verbal-diff（意味的 NL 差分）で per-iteration フィードバックを表現**: 変異内容 + metric/leading-indicator の**前 variant からの差分**を、位置差分でなく自然言語の意味的 diff で LLM に渡す。「NL 意味 diff > 標準 diff」は cotomi が +12.7pp で実証。§3.5・規律3 の具体化。
- **whiteboard memory の抽象度ラダー + 低データ/高データのクロスオーバー則**: trajectory/script/insight の3階層を持ち、キャンペーン序盤は抽象 insight を、試行が溜まったら raw trace を LLM に還流。「raw は低 coverage で劣化・高 coverage で最強、抽象は安定」という経験則を exploit/explore プール設計と還流粒度に反映。
- **best-of-N 事前合意を変異提案のスクリーニングに**: LLM に N 個の変異方向を出させ多数決で1手を選ぶ（N≤5）。低コストで分散削減。**ただし cotomi のように事後 verifier を外すのは izanagi では禁止**（screening であって正しさゲートの代替ではない、と明記して採る）。
- **evaluator-integrity チェックの明文化**: scorer/verifier 自体を known-good/known-bad で検証してから信頼する（cotomi の WebArena-Mod 相当）。izanagi の Phase1「わざと壊した CC で anomaly 検出」を、ベンチ scorer の FP/FN 監査にも拡張。
- **agentic ETL vs fixed-rule の blind 比較プロトコル**: 抽象化パイプラインの品質を2アノテータ blind 比較で測る評価法は、izanagi の「最適化カタログ化」品質評価に流用可。

## izanagi に入れる際の障害・前提・リスク
- **ドメイン適合性の断層**: cotomi は web GUI 自動化＝**正しさが緩く人間 curation で吸収できる**世界。CC serializability は**正しさが二値でハードゲート**。best-of-N 合意や人手 curation を「verifier の代替」に持ち込むと絶対規律2 を破壊する。移植は「探索効率の機構」に限定し「正しさの根拠」には決して使わない。
- **agentic ETL の自律性リスク**: LLM が分割/抽象度/ルーティングを自律決定するのは、正しさクリティカルな成果物では fabrication 経路（規律2, ARA anti-fabrication isolation §3.4）と衝突。抽象化の自由度をどこで pin するかの線引きが要る。
- **demo paper ゆえの証拠の薄さ**: 行動知識評価は成功トラジェクトリを user behavior の**proxy** とした controlled study（失敗・中断・探索の混入は未検証と本文が明記）。数値をそのまま一般化しない。
- **抽象度クロスオーバー点の予測不能**: 「低データで抽象・高データで raw」の切替点を何が決めるかは論文も示していない（本文から特定できず）。izanagi 側で adaptive に決める設計が別途必要。

## 小山田さんに聞くべき質問（鋭い問い）
1. **verifier を捨てる/残すの分岐**: cotomi は事後 verifier を外し best-of-N 事前合意 + boundary-object の人手 curation で置換、izanagi は逆に always-on verifier + post-hoc 因果説明に賭けています。「事前合意 + 人手 curation が verifier を代替できる条件」と「それが崩れる条件」をどう線引きしますか。正しさが二値ハードな CC ではどちらに賭けますか。
2. **抽象度クロスオーバーの一般則**: 「raw trajectory は低 coverage で劣化・高 coverage で最強、script/insight は安定」は experience-replay/agent memory の一般法則だと見ていますか。クロスオーバー点を予測する量は何で、izanagi のように試行が累積する探索ループで抽象度を adaptive に切り替えるとしたら何を signal にしますか。
3. **agentic ETL の自律性の安全域**: blind 比較で agentic ETL が fixed-rule に勝ったとのことですが、成果物が**正しさゲートに供給される**（izanagi の最適化カタログ）場合、分割/抽象化/ルーティングの LLM 自律をどこまで許し、どこを schema で固定すべきと考えますか。

## 引用/リンク
- 論文 (arXiv v1 全文): https://arxiv.org/abs/2605.03231 / https://arxiv.org/html/2605.03231v1
- CAIS '26 demo paper, DOI 10.1145/3786335.3813203 (会議: ACM Conference on AI and Agentic Systems, May 26–29 2026, San Jose, CA — 論文奥付より)
- NEC プレス (2025): https://jpn.nec.com/press/202508/20250827_02.html
- 関連（同著者、dossier Tier A/C と接続）: Komiyama+ "Best-of-∞" (ICLR'26, arXiv:2509.21091); Light+ "DISC" (NeurIPS'25, arXiv:2502.16706); Enomoto+ "Read More, Think More" (arXiv:2604.01535); Zhang+ "WebArena-Mod" (2025)
- ベンチ: WebArena (Zhou+ ICLR'24); WebArena-Verified (El hattami+ 2025); WorkArena-L1 (Drouin+ 2024)
