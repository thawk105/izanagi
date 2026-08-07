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
- 恒久対応: memory `fix-prompt-allow-double-forbid-production-relaxation` —
  段 6 の fix prompt に「呼び先の signature を検査して安全側の引数を落とす互換分岐を
  入れてはならない」を明記し、代役 signature の修正を許可経路として名指しする
  (本 wave の第 4 巡 prompt が先例)。加えて親は fix 成果を統合する前に diff を読み、
  production 側の緩和を差し戻す。**`docs/dev-wave/workers.md` への統合は byte 予算
  (`docs/dev-wave/**` の 25200) に収まらず断念した。** 予算を上げないため memory を実体とする。
- 再発検知: 認可述語を無効化する登録変異 (本 wave の変異 matrix M2〜M6) が、この種の
  fail-open を入れると期待 node ではなく広い範囲を落とすため MISMATCH として顕在化する。
  加えて sink の必須 keyword-only 引数は signature 検査テストで固定されている。

### {{F:stale-base-worktree-integration}}. 古い base の fix worktree から統合し、新しい変更を上書きした [手順漏れ]

- 事象: 段 6 の fix 第 4 巡で、第 3 巡より前の commit から作った worktree を使い、
  ファイル比較による統合を行った。その worktree では第 3 巡の 2 ファイルが基準時点の内容
  (= 差分なし) のままだったため、統合スクリプトが「差分あり」と判定して**古い内容を
  上書きコピー**し、採用済みの fix 2 件が消えた。親が直後の diff 確認で気づき、
  当該 2 ファイルを第 3 巡の worktree から復元して回復した (実害は残っていない)。
- 根本原因: 隔離 session からは他 worktree へ git を向けられないため、統合手段が
  ファイル比較コピーになっている。この方式は「両者が同じ base から出ている」ことを前提に
  するが、fix 巡ごとに worktree を作り直す運用でその前提が崩れた。
  作成時の base commit を検査する手順が無かった。
- 恒久対応: memory `fix-worktree-must-branch-from-last-integration` —
  fix 用 worktree は直前の統合 commit から作り、古い base の worktree から統合しない。
  こちらも byte 予算のため `docs/dev-wave/workers.md` へは統合していない。
- 再発検知: 統合前に対象 worktree の `HEAD` が直前の統合 commit と一致することを確認する。
  不一致なら統合せず作り直す。
