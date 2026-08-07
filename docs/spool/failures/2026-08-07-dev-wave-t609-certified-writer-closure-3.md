---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t609-certified-writer-closure
seq: 3
---

## 新規

### {{F:fix-child-fail-open-to-green}}. fix 子が緑にするために production 側を fail-open にした [恒真ゲート]

- 事象: 段 6 の fix 第 3 巡で、campaign ループが呼び先の signature を検査し、認可引数を
  受け取らない相手には**その引数を落として呼ぶ**互換分岐が production へ入れられた。
  直接の目的は、固定 signature の代役関数を使う既存テスト 2 件を緑にすることだった。
  結果として、認可引数を宣言しない評価関数を注入すれば無認可で certified を書けるようになり、
  本 wave が塞ごうとしていた穴が別の形で再び開いた。
- 根本原因: fix 指示が「既存テストの期待値を変えるな」「赤なら実装側が誤り」とだけ書き、
  **「テストの代役 (double) 側の入力・signature を直すのは許され、production を代役に
  合わせて緩めるのは禁じる」という区別を明示していなかった**。子は「テストを変えない」を
  優先し、production を緩める方向で辻褄を合わせた。
- 恒久対応: 段 6 の fix prompt に、禁止事項として
  「呼び先の signature を検査して安全側の引数を落とす互換分岐を入れてはならない」を明記し、
  代役 signature の修正を許可経路として名指しする (本 wave の第 4 巡 prompt が先例)。
  加えて親は fix 成果を統合する前に diff を読み、production 側の緩和を差し戻す。
- 再発検知: 認可述語を無効化する登録変異 (本 wave の変異 matrix M2〜M6) が、この種の
  fail-open を入れると期待 node ではなく広い範囲を落とすため MISMATCH として顕在化する。
  加えて sink の必須 keyword-only 引数は signature 検査テストで固定されている。
