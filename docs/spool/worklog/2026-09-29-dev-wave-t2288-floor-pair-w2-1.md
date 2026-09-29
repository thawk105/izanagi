---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2288-floor-pair-w2
seq: 1
title: [T-2288] B-4 床値の w2 と finalize を w1 と同じ submit-tree から走らせ、証拠確認 (24 h 分離・n = 62・欠測 0) を通して集約を発行した — 床値の候補 0.09691 (rr50 w2 の標本最大)、採用裁定は材料のみ (計測 + insight、branch worktree-dev-wave-t2288-floor-pair-w2)
---

## 本文

- 一次資料 = `output/insights/2026-09-29/t2288-floor-pair-w2/README.md`。成果物 10 本 (窓 JSONL 6・summary 3・集約 1) は submit-tree 上の
  commit `f315186c8` (親 = H `2ba400087`) を wave branch へ `--no-ff` で取り込んだ。
- **ユーザー確認 (2026-09-29 14:27 JST):** w1 の job Elapse (12,934 s) から w2 3.6〜3.84 + finalize 上限 1.5 (walltime 30 分 × 3、実測単価なし)
  + 受入 0.25 = 3.9〜5.6 node 時間と見積もって示し、「w2 と finalize を承認」を得てから投入した。実使用は w2 12,915 s + finalize 15 s
  ≈ 3.59 node 時間 (受入を除く)。finalize の単価は 1 job 5 s (Elapse) と実測できた。
- w2: rr95 `35164` / rr50 `35235` / rr5 `35275` (.nqsv)、4151〜4580 s で 3 本とも terminal `complete`・62 / 62・欠落 0。finalize 3 本は
  いずれも `generated` (上限 rr95 0.0370 / rr50 0.0969 / rr5 0.0388)。証拠確認者 (D1641 決定 1、AI) として 24 h 分離 231.6〜231.8 h、
  6 campaign とも n = 62・欠測 0、probe 全 clear、rep rc 全 0、throughput 全有限正値、両窓の HEAD = H・同一 binary を確認した。
  集約 (D1974) は D2138 項 8 の予測名どおり発行 (sha256 `4896a1fd…`)。集約が記録した expected_specs 3 組は D2138 項 7 の表と全桁一致
  (実行 argv は保存していない)。
- 段 6 相当の read-only review 1 本 (codex `review`、gpt-6-sol / medium、16 call、331 秒): GO、must-fix 0。所見 2 件 (should: expected_specs の取得元の主張が argv 未保存で
  独立に確かめられない → 一致の主張へ狭めた、nit: 強調記号) をともに real・採用で反映した。数値・hash・件数の不一致は 0。
- 受入 1 回目 (tip `e67ea485d` → post-claim merge `62a4987cc`、claimed main `8cd0ef4a3`) は rc=70、赤 3 件はすべて
  `orchestrator/tests/test_t810_coordinator.py` (`test_prepare_group_accepts_external_root_with_anchor_union` と `…_rejects_forged_git_identity…`・
  `…_rejects_self_consistent_foreign_git_identity…`) の `cannot read worktree registration: file is absent`。計算ノードの単独再走 (request
  `35681.nqsv`) でも 3 件再現し、欠けていた file は他 session の撤去途中の `.git/worktrees/dev-wave-vhash-forwarding-proof/gitdir` だった
  (`dev_wave_cleanup.py` が走行中で、管理 dir に `modules` だけが残っていた)。テストは共有 `.git/worktrees/` の全管理 dir を読む。本 wave の差分
  (計測データ・docs) は `tools/pegasus/t810_coordinator.py` にもテストにも届かないので非帰属と判定し、撤去の終了後に受入を取り直した。
- 採用裁定 (D1641 決定 2) と §5 floor 欄の記入はしていない (依頼が「材料を返す」まで)。§5 に書く pin 文字列と、統計関数が標本最大値で
  床値が 372 差分中の 1 標本で決まる性質を insight の材料節に並べた。
- セッション事象: `EnterWorktree(name)` が "Could not read the repository git config to neutralize filter drivers" で 2 回失敗 (同日の
  gen-opt md_2 に続く)。`git worktree add -b` + lock で手作業作成し、`EnterWorktree(path)` も `git worktree list` の 10 秒上限で失敗した
  ので絶対 path で続けた。新規 worktree の入れ子 submodule (shirakami) が未初期化で、`--recursive --no-fetch` で揃えた。

## 次の一手差分

### 更新

- [T-2288] **P1・(b) w2・finalize・証拠確認・集約発行まで完了。残るのは採用裁定 (D1641 決定 2) と §5 floor 欄の記入**: 集約
  `output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json`
  (sha256 `4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf`、床値 ≈ 0.09691、出所 rr50 summary)。D1641 決定 3 の受理条件は
  すべて満たした。採用すれば `docs/phase3-b4-reflux-ablation-preregistration.md` §5 の floor 欄 (現 `未記入`) へ
  `artifact_path=<上の path>; sha256=<上の hash>` を書き、D に記録する (§5 記入担当者 = thawk105 名義で AI、D1641 決定 1)。材料は
  `output/insights/2026-09-29/t2288-floor-pair-w2/README.md` の「採用裁定の材料」。submit-tree
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree`、HEAD `f315186c8`、locked) は 3 段が終わり撤去してよい状態。
  base: 3ad1ac0873209d07f8819c40ea8fea9c39fc736de59f1a66ff33b7ab4040efbc
