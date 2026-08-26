---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 8
---

## 新規

### {{F:shared-source-tree-blocks-parallel-workloads}}. 同時投入した計測 job が同じ被験ソース木を奪い合って 2 本が即死した [手順漏れ]

- 事象: B-10 の計測 job を 3 workload 分同時に投入したところ、1 本目だけが走り、
  残り 2 本が 16 秒で `patchharness: git apply 失敗 ... patch does not apply` で死んだ。
  3 本とも `PBS_O_WORKDIR` が同じ repository を指し、driver は同じ CCBench submodule の
  作業ツリーを使っていた。1 本目が patch を当てている間、残りが同じ木へ当てに行った。
- 根本原因: **並行実行を前提にした job なのに、被験ソース木が job 間で共有だった。**
  patch は sweep の全区間 (数時間) 当てたままなので、**lock で直列化しても順番待ちになるだけで
  並行にはならない** — 隔離でしか解けない型である。既存の計測 job
  (`tools/pegasus/certify_calibration.sh`、`tools/pegasus/mocc_trace_pilot.sh`) は
  job 固有 scratch へ detached worktree を作って既にこれを解いていたが、参照されなかった。
- 恒久対応: job body が gitlink commit から job 専用の detached worktree を scratch へ作り、
  両 driver へ明示的に渡す。渡された木は実在・worktree root・HEAD 一致・tracked 清潔を
  fail-closed で検査し、**検証失敗時に共有木へ落ちる経路を持たない。**
- 再発検知: `orchestrator/tests/test_backoff_extended_sweep.py` の
  `test_invalid_explicit_worktree_cannot_fall_back_to_valid_shared_tree` が、
  有効な共有 fallback が実際に選べる状況を先に作ったうえで、
  誤 HEAD と tracked dirty の明示 worktree が停止し fallback 呼び出しが増えないことを固定する
  (負例が実際に落ちる形にしてあり、述語は恒真でない)。加えて
  `test_b10_job_exit_trap_removes_worktree_on_normal_and_abnormal_exit` が
  正常系と異常系の両方で後始末が走ることを固定する。

## 再発

### F498

- **再発: 2026-08-27** — 批准台帳は 2026-08-25 02:59 に 1 行で開設されたが、
  **その行は開設時点で既に古かった。** closure は開設の 4 時間前 (2026-08-24 23:00) に
  別 wave の commit で動いており、以後さらに 4 commit が動かしている。
  結果として `enforcement-source-closure-unratified` は解除されず、
  **2026-08-24 23:00 以降 main では certified campaign の新規初期化が誰にも出来ない**
  状態が続いていた。B-10 の計測 job が計算ノードで 22.6 分走り、依存ビルド・CCBench ビルド・
  凍結木照合をすべて越えた後、campaign 開始時にこの fail-closed を踏んで判明した。
  D526 は追記 API・CLI・自動更新を作らないと定め、wave 側での追記を
  「弱化した本人が批准する形になる」として却下しているため、**AI は解除できない。**
  F498 が記した「批准は closure 版ごとにしか効かない」という運用上の含意が、
  **批准と land の競走**という形で顕在化した — 批准行を書いてから投入するまでの間に
  25 path のいずれかが動けば、その批准は投入時点で無効になる。
