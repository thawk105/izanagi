---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-a1-pilot-attempt2
seq: 1
title: A-1 pilot attempt-0002 を投入した — F852 は閉じ 3 job は preflight を通ったが、group receipt の公開が Lustre で決定的に失敗し bench に入らなかった (docs + insight、branch worktree-dev-wave-a1-pilot-attempt2、実装面の差分ゼロ)
---

## 本文

- 一次資料は `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md`。**pilot の測定値は 1 点も無い。**
- ユーザー裁定として本 wave に与えられたのは「本題の投入と記録だけ」「投入元 checkout は記録を書かない
  別 worktree」「3 job の preflight 通過を投入前に実測で示す」「生存判定は `qstat` 一覧の行頭 ID 照合」
  「測定・sizing・本走 policy の凍結は attempt-0002 の結果を見てから」「仮想リスク向けの gate・検査・
  台帳・一般化は scope 外」。
- 投入前に、捨て request 1 本を gen_S へ投げて生きた `qstat -f` 出力に production の
  `_observe_qstat_visibility` を通し、`visible/state=RUN/queue=gen_S` を得た。F852 は実機で閉じている。
  本番 3 request でも同じ関数が可視性を書いた。
- 投入は 3 本とも受理されたが、group receipt の公開だけが `Invalid argument` で落ちた
  ({{F:a1-noreplace-publish-lustre}})。3 job は body preflight を通過し (`job-terminal.json` に
  `expected_head == observed_head`、`porcelain` が空、`pbs_o_workdir` = 投入元 submit-tree)、
  group receipt を 60 秒待って fail-closed で終わった。bench・build・verify は 1 つも走っていない。
- 記録用 worktree と投入元 checkout を分ける運用は実測で効いた。attempt-0001 は親が投入元を汚して
  preflight で落ちており、この経路は今回はじめて観測できた。
- 段 4 で「実装しない」と裁定したため、段 5・6 を飛ばして `4→7→8→9` で進めた。実装面の差分はゼロで、
  変異 matrix は `DW-S04` により免除、受入全走は行った。
- 公開機構の直し方は 3 案を実測表つきで裁定パッケージにして返す (insight §7)。親推奨は
  `os.link()` による公開 — 既存先に `EEXIST` を返すので排他性を落とさない。素の rename への退避は
  既存先を黙って上書きするため採らない。
- 運用で 1 件: `tools/dev_wave_submodule_init.py` の内部 timeout が 30 秒固定で、負荷の高い login node
  では CCBench の checkout が間に合わず `runtime-io-failure kind=update-no-fetch` で落ちた。
  同じ argv を直接走らせれば通り、その後に同 tool を走らせると rc=0 になる。

## 次の一手差分

### 新規

- {{T:a1-noreplace-publish-fix}} **P1・新規**: A-1 driver の group submission receipt 公開を Lustre で
  成立する機構へ直す。insight `2026-09-07_a1-pilot-attempt-0002` §7 の裁定を受けてから着手し、
  `complete` の completion receipt 公開と materialize 側も同族として棚卸しする。Codex `role=author`、
  正例・負例を同じ commit へ。
- {{T:a1-pilot-attempt-0003}} **P1・新規**: 上記の修正着地後に fresh wave で attempt-0003 を投入する。
  attempt-0002 は残す (ready / bench-go / bench-start が無いので先行 bench barrier の検査は拒否しない)。
  再走理由は `scheduler-or-infrastructure-failure-before-bench`。投入元 checkout は記録用と分ける。
