---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2778-child-worktree-cleanup-2
seq: 1
title: T-2778 の remove-child の変換属性検査を superproject 限定に直し、段 9 の dogfood を閉じる (コード、branch worktree-dev-wave-t2778-child-worktree-cleanup-2)
---

## 本文

- entry 1706 (D2163) の続き、同一 session。1706 の land (main baba46bb7) 後の段 9 で、新 mode `remove-child` を本物の author 子木
  `.codex/worktrees/t2778-author` に当てたところ rc=20 `backup-precheck` 「tracked file has conversion attributes」で拒否された (wave 本体の撤去は
  removed)。原因は fix1 が足した `_assert_child_submodules` の再帰 `_assert_child_no_conversion(module)` で、submodule `external/ccbench` の
  `.gitattributes` `* text=auto eol=lf` を拒否した。この repo の子木は全て ccbench 初期化済みなので、1706 時点の tool は実子木を 1 本も撤去できなかった
  (dogfood の正例が赤 = 段 6 の tmp fixture は submodule に属性を持たず回帰を捕まえていない)。
- 裁定 (親): 変換属性の検査は superproject だけに掛ける。submodule の内容は退避せず pin 一致・clean・reflog 到達・primary store 実在で守るので、
  submodule 側の属性は内容喪失の経路にならない。Codex author が再帰呼出しを外し、fixture の submodule に属性を足して `[clean]` が回帰を検出する形にした。
  受入・変異・land の結果と、子木・wave-2 木の撤去結果は専用 handoff (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/HANDOFF.md`) と
  `output/insights/2026-09-19/t2778-child-worktree-cleanup/README.md` §6 に記録する。
- 学び: 実 repo の子木を 1 本撤去する dogfood を wave の完了判定に置いたから捕まった。tmp fixture は submodule の属性・primary store・dispatch 下の
  signal を再現しない (同 insight §4、memory)。

## 次の一手差分
