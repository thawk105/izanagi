# ShinkaEvolve 深掘り (related-work.md §7.2 の付録)

> `related-work.md` の ShinkaEvolve エントリ本体から分離した詳細 (2026-07-10、D35: 実装検討時のみ読む)。
> 9 サブシステム深読み・62 技法の敵対検証 (2026-07-07、72 エージェント作業フロー) の全記録。
> 本文の要約と技術的判断は同一 — こちらは根拠の全展開。

---

### ShinkaEvolve (Sakana AI, ICLR 2026 / arXiv 2509.19349, github.com/SakanaAI/ShinkaEvolve)
LLM×進化アルゴリズムでプログラムを合成する公開フレームワーク (AlphaEvolve / Darwin-Gödel Machine の直系)。プログラム母集団を島モデル + global archive で保持し、LLM アンサンブルを変異オペレータ (diff / full / crossover の3変異種) として使い、UCB バンディットでモデルを cost-aware に選択、code embedding + LLM novelty judge で近重複を除き、meta-recommendation と prompt evolution (システムプロンプト自体の進化) を回し、eval を並列化して 5-10x を謳う。**Izanagi の (b) コード合成と同一の問題設定 (verifier がある所で正しさを保ちつつ性能指標を最適化) を解く、現時点で最も直接的な実装比較対象**であり、かつ Jitskit/IDS/VibeServe と違い、公開され動作する実装である。

9 サブシステムを深読みし 62 技法を抽出、各々を絶対規律に対して独立に敵対検証した (72 エージェントの作業フロー、2026-07-07)。**結論は「直採用ゼロ」**: finder が adopt/adapt と推した技法は一つ残らず inspiration-only 以下に格下げされた。これは失敗でなく最大の findings で、**同一問題の上で Shinka と Izanagi の設計哲学が正反対に振れている**ことの実証である。Shinka の価値の中核 — スコア付き勝ちプログラムの prompt 注入によるサンプル効率と、並列 eval が賄う母集団機構 — が、Izanagi のリーク制御 (Model Y) と計測直列 (絶対規律4) に正面衝突する。

**反面教師 (本エントリの主眼、"採ってはいけない"):**
- **スコア付き勝ちプログラムの inspiration 注入** (`shinka/prompts/prompts_base.py` の construct_eval_history_msg が過去プログラム全文 + combined_score をそのまま prompt へ載せる — 本調査で実物を確認): Model Y リーク制御の直接否定。coder は untrusted で勝ち筋値を見せない設計を解体し、合成可能性 (synthesisability) テストを複写テストへ退化させる (絶対規律6)。**Shinka の価値の源泉そのものが Izanagi では毒**という、この比較の核。
- **crossover / prompt evolution**: 前者は勝者2本の全コード+スコアを注入する最濃リーク、後者はほぼ無監査 (最小の長さチェックのみ) の LLM 生成物を最高権限のシステムプロンプトへ昇格させる (データ→指示の格上げ = 絶対規律6 違反 + 母集団すら無い段階での第2進化ループ = 規律5 前倒し)。
- **並列 eval を前提にした機構群** (島モデルの予算配分 / EWMA 適応 oversubscription / 逐次統計 early-stop): Shinka の "5-10x async" はまさに Izanagi が捨てた前提の上に立つ。単一テナント直列・単一系統の Izanagi には in-flight/待ち行列が構造的に不在で、移植は絶対規律4 と非互換。early-stop は向きが逆 (Izanagi は測定を信用できるまで reps を増やす — §3.6(4))。
- **インデント寛容な fuzzy patch 適用**: 適用率を上げる自動補正 = fail-open で、fail-closed 思想 (絶対規律2) の対極。

**外部追認 (Izanagi の設計が上位互換であることの確認):**
- EVOLVE-BLOCK マーカー規約は両者共通 (AlphaEvolve 系譜) だが、Shinka の marker_validation は「マーカーが生存したか」の緩い検査に留まり EVOLVE-BLOCK 全体を LLM に書き換えさせる。Izanagi の diff_quarantine (変更行 ⊆ hole 物理行域 + フレーム byte 不変) + source_digest (preprocess 後ハッシュの build 出口 TOCTOU 再照合) は fail-closed の上位互換 (D33)。
- 「正しさを性能から混ぜず硬いゲートに保つ」「guardrail を可変成果物でなく不変フレームに置く」原則を Shinka も soft prompt で実演しており、Izanagi の機械強制 (verifier hard-reject / 三層可変性 / hooks) がその上位互換であることが外部追認された。
- **素材:** Shinka の example 付属の素朴 validate vs Izanagi の敵対 verifier は、両系譜の正しさ哲学差 (最適化圧力を敵と見るか否か) の比較の核。

**将来段への銀行預け (借用は思想・部品のみ、機構は段階順に予約):**
- **Phase 3.5 (母集団導入) の最高価値ピース**: 親選択の novelty ボーナス `1/(1+children_count)` + MAD ロバスト sigmoid。多様性保存 (§10) をパラメタ1個で入れられ、スコア/重みは harness に閉じ coder には従来どおり値なし方向のみ渡す形なら規律6 と整合。roadmap §10 の「新規性報酬は Phase 3.5」と符合。
- **段5/6 (EVOLVE-BLOCK が hole 1行 → 多行/複数マーカーに拡張された時)**: 全書き換えの再構成スプライスと複数マーカー可変域算出。ただし Shinka は不整合マーカーに fail-OPEN するので、完全性 predicate は Izanagi 独自に fail-closed で作り直す (Shinka は反面教師)。
- **段4 のまま中立に足せる薄い上乗せ** (着手判断は worklog): committed-cost 型の $ 予算停止理由 / WAL 相境界 ts からの pipeline 相計時の未計上分の分解 (観測者効果ゼロ) / whiteboard の public-private allowlist 硬化 / critic の attribution→recommend firewall 明文化。

**系譜上の位置:** Jitskit/IDS/VibeServe と同じ「対象特化の自動合成」系譜かつ AlphaEvolve/DGM 直系だが、他が論文・クローズドなのに対し Shinka は動く実装ゆえ Izanagi にとって最も直接の比較対象。決定的な差は前提: Shinka は「正しさは素朴 validate で足り、最適化圧力は敵でない」設計で、Izanagi の絶対規律 (敵対前提の正しさゲート・リーク制御・計測直列) を共有しない。**この哲学差こそが本エントリの結論であり、Izanagi の規律が「不便な保守主義」でなく問題設定から要請された選択であることの外部証拠になる。**
