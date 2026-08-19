---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1373-launcher-path
seq: 2
---

## {{D:waiter-main-launch-conflicts-with-d403}}. main checkout 側絶対 path からの waiter 起動は D403 と構造的に矛盾するため見送る

**決定:** 「`.claude/commands/dev-wave.md` の受入 lease claim/release 呼出しを、wave tip 側
worktree の相対パスから main checkout 側の絶対 path へ書き換える」案は実装しない。

**理由:**
- D403 は「claim 前に main の blob と比較する早期照合」を、待ち手を編集する wave を永久に
  受入不能にするという理由で明示的に却下している。本提案は main checkout 側の絶対 path から
  waiter を直接起動するため、`_verify_waiter_source_bytes` (tools/dev_wave_wait.py:2001-2080)
  が比較する running source bytes が main 側 (未反映) のものになり、待ち手を編集する wave では
  tested_tip の blob と恒久的に不一致になる。D403 が却下した設計と実質的に同型の帰結である。
- D524 は「親の固定起動点を launcher へ移すこと」を「起動権を wave tip の外へ出す唯一の形」と
  認めつつ D253 抵触懸念を理由に後続タスクへ先送りしたが、D403 との整合性確保の方法は示して
  いなかった。本決定はその欠落を明確化する。
- main checkout を cwd にして起動する代替案 (waiter CLI に main path 専用引数が無いため cwd を
  変える以外の実行経路が無い) も、`docs/pegasus-runbook.md` が明記する既存の復旧手順 (mismatch
  時は新しい tip の木から待ち手を起動し直すことだけが直し方) と構造的に矛盾する。
- 独立した 2 レンズの敵対相談 (正しさ境界 / 実効性・所有範囲) が、それぞれ file:line で
  この帰結と技術的不整合を実証した。

**却下した選択肢:**
- main 絶対 path を argv へ埋め込むメタ変数記法 — waiter の acceptance サブコマンド
  (tools/dev_wave_wait.py:1607-1625) に main path を受け取る引数が無く実行不能。
- main checkout を cwd にして waiter を起動する — 待ち手を編集する wave の受入を恒久的に閉じる
  (上記理由と同じ)。

**閉じていない残余:** 協調境界に残る「改変された tip 側待ち手は launcher を起動せず受領証を
自作できる」は未解決のまま。解くには acceptance_launcher.py と同型の bootstrap 層 (main 側固定
entry point が tip 側 tree から waiter ロジックの blob を exec する) を waiter にも新設するか、
launcher 呼出しの正しさを land 側でより厳密に検証する方向への転換が要る。いずれも本決定の
scope 外であり、設計選択はユーザー裁定に委ねる。
