---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-md2-push-pack-hint
seq: 2
---

## 再発

### F1

- **再発: 2026-09-29 (near-miss)** — cleanup-branches command の予算引き上げで、親の段 4 裁定と check_docs のコメント
  (commit 6524efd42) が「D782 手順による引き上げ」と書いた。D782 と `docs/skill-self-improvement.md` の要約
  (「意味等価にできなければ D782 に従う…上限引き上げ時だけ報告」) だけを根拠にし、D782 が委任する D730 本文の条件
  (上限引き上げは「同型の実害が独立に 3 例以上」の例外の収容先を作れない場合に限る) を読まずに落とした。事象は 1 件で、
  条件を満たさない。段 6 の read-only review が must-fix R3 として検出し、「本 wave の個別裁定、D730 の 3 例例外ではない」と
  書き直した (a9a96fd2a、実害なし)。転写対象が**委任先の裁定の発動条件**へ広がった顕在化である。恒久対応は memory から変更なし
  — 裁定を根拠に引くときは、委任の連鎖 (D782 → D730) の末端の本文まで読む。
