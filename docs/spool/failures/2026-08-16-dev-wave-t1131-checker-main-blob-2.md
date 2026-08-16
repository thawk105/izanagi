---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1131-checker-main-blob
seq: 2
---

## 再発

### F102

- **再発: 2026-08-16 ([T-1131] wave の段 6 fix 第 1 巡)** — **初めて fix 段で起きた。**
  既載の再発はすべて consult / review / focus 段の prompt が原因だったが、本件は発火段も経路も
  新しい。親が敵対レビュー成果物に書かれた迂回手口の記述を、そのまま fix prompt の
  「直す所見」節へ引き写した。レビュー側の prompt には防御目的を明記していたのに、
  fix prompt では定型ごと落としていた。子は 34 model call・526 秒を使い、todo をすべて完了して
  **実装を完走した後**、最終メッセージ生成時に `turn.failed`
  (`This content was flagged for possible cybersecurity risk`) で rc=1・出力 0 bytes。
  対応表 (closed/partial/regressed) と期待 node の静的列挙を失い、焦点再レビューで撮り直した。
  **新しい教訓は「手口の記述は成果物間を伝播する」ことである。** 敵対レビューは設計上
  迂回手口を具体的に書くので、その成果物を次段の prompt へ引き写すと、防御的 framing を施した段の
  出力が framing の無い段の入力になる。恒久対応は `DW-O02` の既存要求
  (「親 brief と前段の子成果物は同 subdirectory のファイルへ置き、prompt へ全文複製せず
  絶対パスで読ませる」) の遵守であり、引き写す場合は防御目的の定型と出力形式の制約を
  必ず同時に持ち込む。本 wave の後続 focus / fix prompt はこの 3 点
  (冒頭の防御目的と自チーム文脈、手口の段取りを被覆の記述へ置換、依頼の動詞を「確認せよ」へ)
  で書き換えて rc=0 で完走した。差分は working tree に残るため、再投入でやり直さず回収して継続する。
