---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-roadmap-revision
seq: 2
title: 活動範囲を新規最適化の創出へ広げる roadmap の協議改訂 — 文献にあって CCBench に無い最適化の実装 (段 A) と、文献に無い仕組みの合成 (段 B) を開き、新しい仕組みに足す正しさ関門の原則 2 つを置いた (docs のみ、branch dev-wave-gen-opt-roadmap-revision)
---

## 本文

- 依頼: 並行 gen-opt wave の md_1 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_1.txt`、共通指示は同 dir の `common.txt`)。ユーザーは 2026-09-29 に親セッションの提案の (a) に「この形に改めて良い」と同意した。(b) 優先度には明示の回答が無く、親セッションが推奨どおり「計算を使わない手順だけ今から並行」と解釈した。発話の逐語と親の解釈の区別、却下した選択肢は {{D:gen-opt-activity-scope}}。
- 台帳に「活動範囲を新規最適化の創出へ広げる roadmap 改訂」を含む item は無かった。本 wave が依頼の全体を届けるので、完了済みの item を新たに立てず、このエントリだけで記録した。
- 一次資料: `output/insights/2026-09-29/gen-opt-direction/` (ユーザー発話の逐語と提案全文を、repo 外の原本から bytes 一致で写した)。
- roadmap の文言を逐語で固定する test・道具は無かった (tests/・tools/・orchestrator/tests/・hooks/ を検索)。roadmap は改訂後 78,556 byte で、読み取り hook の全読上限 80,000 byte まで約 1.4 KB である。
- scope 外で改訂と食い違ったまま残る箇所: `docs/phase3.md` 後続段 7 の「b2 本格投資は 8b + 層3 の後に再判断」と、`README.md` 三層図の「他CCからの移植は拡張予約 D32」。追随を独立の docs 作業として起票した (段 6 review の指摘で、段 A の試しの着手時から分けた)。
- 新規 item の優先度 (P2・P3) は、ユーザーの明示回答が無い (b) 優先度に対する親の暫定である。
- エージェント工数: (段 6 後に記入)

## 次の一手差分

### 新規

- {{T:gen-opt-stage-a-trial}} **P2・新規**: 段 A の試し 1 本 ({{D:gen-opt-activity-scope}})。文献カードの wave (gen-opt-literature-cards) と正しさ関門の設計の wave (gen-opt-correctness-gate) がともに main に着地してから、CCBench に無い文献の最適化を 1 つ選び、関数単位の空間 (silo-function-policy の経路、D2214) で Silo に入れる。正しさ関門は今の検査に、roadmap §2 層2 の 2 原則 (検査用記録の差し込み点を編集範囲の外に固定・仕組みごとの小さいモデルでの全場面検査) を正しさ関門の設計に従って足す。計算は 1 タスク合計 2 node 時間未満の規模にし、超えるなら見積りを添えてユーザーに確認する。優先度は親の暫定。
- {{T:gen-opt-evolution-run}} **P3・新規**: 母集団型の探索 (進化探索) の本走 ({{D:gen-opt-activity-scope}})。段 A の試し ({{T:gen-opt-stage-a-trial}}) で「正しく作れる」ことを確かめ、探索枠組みの設計の wave (gen-opt-evolution-design) が main に着地してから、条件数 × 1 条件の所要 (node 時間) と LLM の直列時間・週枠の見積りを添えてユーザーに確認し、承認後に投入する。「進化探索」の呼び名は、母集団・世代・選択を実装して寄与を測ってから使う (roadmap §2 探索戦略・§10)。優先度は親の暫定。
- {{T:gen-opt-docs-follow}} **P2・新規**: roadmap §2 層2 の 2026-09-29 協議改訂 ({{D:gen-opt-activity-scope}}) に、`docs/phase3.md` 後続段 7 の着手条件文 (「b2 移植・カタログ化への本格投資は 8b + 層3 の後に再判断」) と `README.md` 三層図の「他CCからの移植は拡張予約 D32」を追随させる (docs のみ、計算なし)。phase3.md は同文書の更新契約に従う。追随までの間、カタログ化の着手条件は roadmap (戦略層) の改訂を優先して読む。優先度は親の暫定。
