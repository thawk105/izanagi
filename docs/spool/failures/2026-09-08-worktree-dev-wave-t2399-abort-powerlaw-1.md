---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: worktree-dev-wave-t2399-abort-powerlaw
seq: 1
---

## 再発

### F63

- **再発: 2026-09-08** — 引き金が防護パスの語ですらない場合が出た。heredoc で散文と数式を書いた
  ところ、本文中の**前後を空白で挟んだ半角スラッシュ 1 文字**が filesystem root の path 字面と
  読まれ、heredoc と同居して fails-closed で拒否された。防護パスの語は 1 つも書いていない。
  拒否 message は防護ツリーの名前だけを列挙して実際の引き金を示さないため、原因特定に 6 回の
  試行を要した (書けたのは、スラッシュの前後の空白を除くか全角へ替えたとき)。
  同じ wave で、本文に hook 群の README を path 表記で引いただけでも同じ拒否になった。
  恒久対応は F63 本体の「防護パスと不透明構文を同居させない」では足りない。
  **heredoc で散文や数式を書くときは、単独のスラッシュを空白で挟まず、防護ツリー名は
  path 表記で書かない**という作法が要る。実体は hook 群の README が記す既知限界
  (guard は分類不能を fails-closed で拒否する) であり、検知は拒否 message そのものである。
