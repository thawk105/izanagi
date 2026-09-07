---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-wait-duration-cap
seq: 1
title: CLAUDE.md「作業の進め方」9 に待ちの長さの決め方と無音上限 30 分を明文化した (docs のみ、branch worktree-dev-wave-wait-duration-cap、実装面の差分 0)
---

## 本文

- ユーザーが置換後の 6 行を逐語で指定し、30 分という値の根拠も依頼の中で確定させた
  (wave では再検討しない)。親は文面を起草せず、逐語をそのまま当てた。
  差分は +457 バイトで、依頼が予告した増分と一致した。
- 現行文が持っていたのは**下限だけ** (短い間隔で状態確認を繰り返さない) で、
  上限が無かった。今回足したのは上限である。詳細は {{D:wait-duration-and-silence-cap}}。
- 既存裁定との関係を親が調べた。現行の項目 9 は D676 (2026-08-23 のユーザー裁定)
  「無駄なポーリングでトークンを使わない — 短周期の状態確認を繰り返さず、
  待ちは完了通知で終わる 1 本にする」に由来する。今回の追加は 30 分に 1 回の確認を
  **許す**方向なので、字面だけ見ると逆を向く。親は「衝突しない」と裁定した —
  30 分は D676 の言う短周期ではなく、D676 の目的 (無駄なトークン消費を避ける) を
  反対側から補完する。加えて今回はユーザー本人の直接指示である。
- 親が実測した前提 4 件。いずれも依頼の主張と一致した。
  (1) `tools/check_docs.py` に CLAUDE.md の byte 予算は無い。CLAUDE.md は living docs の
  一員だが、禁じられるのは行番号参照と可変状態の再掲だけで、追加文はどちらにも当たらない。
  (2) CLAUDE.md 全体を pin する sha256 は tracked file に無い (whole-file pin を持つのは
  cleanup-branches の skill と command だけ)。
  (3) 待機間隔の規律は CLAUDE.md・AGENTS.md・docs 配下に既存が 1 件も無い。
  AGENTS.md に「作業の進め方」節は無く、CLAUDE.md へ委譲している。
  (4) `docs/dev-wave/operations.md` の `DW-O27` が「`--poll-seconds` は no-op」と明記しており、
  待ち手がブロックするという依頼の前提を repo 側が裏づける。
- `docs/pegasus-runbook.md` が項目 9 を**項番で**参照している。本文は引用していないため、
  項番を 9 のまま保った今回の差し替えで参照は生きたまま壊れない。
- docs のみ・実装面の差分 0 のため、軽量版で段 2・3 と段 6 の review 子を起動しなかった
  (`DW-C00` の「docs-only は子ゼロでよい」)。変異 matrix は `DW-S04` により免除、
  受入全走は免除されないので実走した。

## 次の一手差分
