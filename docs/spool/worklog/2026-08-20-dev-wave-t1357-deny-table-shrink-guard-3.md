---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1357-deny-table-shrink-guard
seq: 3
title: '[T-1357] 段8 自己改善候補: 背景 job worktree での codex 起動2点を記録するだけに留めた (docs のみ)'
---

## 本文

- **段8 自己改善候補 (実装せず記録のみ):** 背景 job・worktree 隔離セッションで
  `DW-O01` の `nohup setsid bash -c '<cmd>; echo $? > <log>.done'` 形をそのまま使うと、
  外側の呼び出しが返った後にプロセスが早期に reap され、python3 codex 呼び出しが
  途中 (99KB の events.jsonl まで進行) で消える near-miss を実測した (本 wave 冒頭)。
  harness 標準の `run_in_background: true` (Bash tool の native パラメータ) で同じ
  wrapper `.sh` を起動し直すと確実に生存した。また wrapper 末尾の `echo $? > done` だけでは、
  task-notification の summary に出る「exit code」が **外側スクリプト自身の値** (常に0に
  近い) であり、内側コマンドの実成否は `.done` の中身を見ないと分からない罠も実測した。
  dev-wave docs (3層とも予算満了・exact pin 脆弱) への直接編集は本 wave では行わず、
  裁定パッケージ候補として記録に留める。
- 択一 (ユーザー裁定候補): (a) 記録のみで留め置く (今回の対応)。(b) `DW-O01`/`DW-C01` へ
  「背景job + worktree隔離セッションでは harness native `run_in_background` を使う」旨の
  1行を追記する (予算超過の可能性が高く、超過時は reference への統合または見送りが必要)。
  (c) 見送る。

## 次の一手差分
