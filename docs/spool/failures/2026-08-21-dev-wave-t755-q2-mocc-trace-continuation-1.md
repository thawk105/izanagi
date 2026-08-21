---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t755-q2-mocc-trace-continuation
seq: 1
---

## 再発

### F425

- **再発: 2026-08-21** — T-755 Q2 継続 wave で、T-816 (silo trace-v2) の実測手順を調べる
  read-only 一次資料調査を fork へ委任した際、継承した `/dev-wave` manager 役定義を自分の
  役目と誤認する事故が再発した。約49分・32万 token・30 tool call を消費し、依頼した調査結果
  (T-816 の cmake/実行/verifier 呼び出しコマンド) を一切返さず、自分自身の agentId を三人称で
  語りながら「coordinator (main) への転送準備が整っている」という越権的な中間報告
  (agent-message) を親へ送った。`git reflog` に `reset: moving to HEAD` が1件記録されたが、
  HEAD commit・working tree の内容 (並行していた正規 Codex 実装子の新規ファイル) はいずれも
  無傷で、fork 起因と断定できる実害は確認できなかった。親の memory
  (`fork-inherits-command-context-can-misact-as-manager.md`) を fork 起動前に読み返さなかった
  ことが直接原因 (同 memory は既に11件の再発を記録し「forkを使う前に必ず読む」を結論として
  いた)。
