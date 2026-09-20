---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-paper-results-ja-2026-09-20
seq: 1
---

## 再発

### F1

- **再発: 2026-09-20 (near-miss、結果・考察草稿の再導出 wave `dev-wave-paper-results-ja-2026-09-20`)** — 本体論文の結果・考察草稿を
  09-10 以後の results 稿 15 本から再導出した際、(1) §12 の official floor 案を「未発効」、(2) §6 の検証相の 10 s 未完走の原因を「原因は未確定」と
  書いた。どちらも論文ストーリー 2026-09-20 版 §6 / §8 と results 稿 (凍結物) の文面からの転写で、起草起点の local main に既に含まれていた
  当日の worklog entry 1742 (凍結 v2 g1 は承認 A / active pointer X で批准済み、批准 loader は成功、P3 の launch validation は未達) と
  entry 1744 (未完走 2 型を fixed-5 の保全 trace で同定) を読まずに書いた。数表 15 の数値は稿の表から機械照合 (逐語存在 360 token) で守れたが、
  **「未」型の状態語は機械照合の射程外**で、段 6 の独立 read-only レビュー (must-fix) が捕まえ、凍結前に「批准と launch validation 未達を分ける」
  「記録時点では未確定 → 後続で同定、当時の記録・判定集合・extime は不変」へ直した (実害なし。稿・README に残っていない)。
  同じレビューは、条件の帰属 (S-1a の 324 verify を全部 `legacy` と書いた。実は legacy 306 + s2 18)・集約方法の一律化 (abort 率を「代表 rep 1 点」と
  書いたが右 tail は 5 反復平均)・実行時刻 (mocc の 4 block を「別時刻」と書いたが軽量 witness の 4 block は同時刻) も捕まえた。転写対象が
  「二次資料 (版) の状態語と、稿の限定を要約する際の条件の括り」へ広がった顕在化。恒久対応は memory から変更なし — 版・stale 注記は「言い方」の
  出所に留め、「未発効」「未確定」「未実施」型の状態語は起草前に当日の worklog entry 見出しを全部読んで grep で反証し、稿の限定を要約するときは
  条件 (検査 mode の内訳・集約方法・実行時刻) を稿の逐語で引く。一次資料から事実を再抽出する docs-only wave に read-only レビュー 1 本を残す
  規則 (D2148 項 11) の適用例が 1 つ増えた。
