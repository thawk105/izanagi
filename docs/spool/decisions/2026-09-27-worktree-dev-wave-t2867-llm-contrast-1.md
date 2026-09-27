---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: worktree-dev-wave-t2867-llm-contrast
seq: 1
---

## {{D:silo-policy-contrast-draft}}. silo-function-policy 軸の LLM 対 非 LLM 生成器の対照は 4 arm・族 A と族 B の 2 族で事前登録を起草し、D2258 の実行契約は規則として継承して job 1 を系列開始 stock と初期点にし、LLM の待ちを全部計算ノードの外へ出す (草稿、未発効)

**決定:** D2259 が指した「なぜ LLM か」の対照を、`docs/silo-policy-generator-contrast-preregistration.md` の草稿として次の形で起草した。本決定は草稿の設計判断であり、
発効・実装・試走・計算投入の認可ではない (発効は規模の択一と node 時間のユーザー確認の後、D2212 項 4)。記録は `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md`。

1. **arm は 4:** LLM×C++・LLM×IR (K0、R0、planner なし、LLM 候補に auditor)、random×IR (型付き grow 法の乱択)、進化×IR (型付き subtree 変異の (1+1)、親は初期点を含む自系列の最良)。
   write-heavy だけ、各 n = 12、B = 10 (上限)、A = 30、共通の初期点 k = 2 (新骨格内の静的 5・10 µs)、N_eval = 5。
2. **比較族は 2 つ:** 族 A = LLM×IR 対 random・進化 (同じ IR 上の探索法)、族 B = LLM×C++ 対 random・進化 (空間拡張を含む)。各族を Holm α = 0.05。
   LLM×C++ 対 LLM×IR は記述だけ。判定規則は B-5 v1 §7 から block の条件を外した形で、生成不成立は探索点で数える。
3. **実行契約:** D2258 の 1 評価 1 job・429 の構造化判定と期限なしの保留・critic への入力の要請を継承する。job 1 は系列開始 stock と初期点 2 個とし、評価 1 を job 2 に回す
   (初期点が同 job の対照を担う)。LLM の親は 1 原提案ごとに新しい session。critic は、新しい結果 (job 1 の結果または評価 1 回) がある原提案機会の最初の役割として回す
   (driver の coder 入力は throughput を持たず、性能は critic 経由でだけ届く)。
4. **流用可否:** D2258 の系列制御・起動器・round tool は B-5 の backoff 値・K2・planner・`p3_s4_loop` に結合しており、コードとしては使えない。429 の判定関数と report の統計の核は呼べる。
   政策 driver の系列ごとの campaign identity・停止規則の切り離し・機械生成 IR の口・stock と参照の口・同時検査の key・job body が発効前に要る (driver と `tools/pegasus/` は T-2865 の担当)。
5. **見積り (換算):** 推奨規模で約 59〜69 node 時間、LLM の原提案 240〜720 機会・直列 40〜120 時間 (平均の単価)。暦時間は LLM の週上限に依存し測れていない。

**理由:**
- random との差だけでは LLM の事前知識とフィードバックの利用を分けられず、差分分析 P2 も進化探索を比べる手法に挙げる。
- 比較基盤 (D2220) の S3 を足す条件は LLM×C++ を比較 A の族に入れないと定め、設計 (D2214) は比較 A と B を混ぜないと定める。
- 初期点を置く比較基盤 §4.5 の下では、評価 1 を job 1 に置かなくても同 job の対照が残り、原提案 1 の node 上の待ち (24 系列で 1.7〜6.8 h の換算) と job 1 での 429 の測り直しの規則が要らなくなる。
- 系列の状態は driver が coder 入力に載せるので親の記憶は要らず、resume による文脈の増加 (B-5 v1 で 1 機会 +0.45 M token) を止められる。

**却下した選択肢:**
- 3 arm (random だけ) — 草稿 §11.3 に費用の択一として残し、推奨にしない。
- 4 比較を 1 族にする — LLM×C++ を比較 A の族に入れることになる。
- D2258 項 1 どおり評価 1 を job 1 に置く — 初期点がある構成では待ちを node 上に置く理由が無い。
- B-5 v2 を土台にした差分登録 — v2 は発効しておらず (D2259)、継承する規則は本文に書き直した。
