---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t656-walltime
seq: 1
title: [T-656] dispatch の既定 walltime を 40 分へ上げ、下限を余裕比で pin した (コード + docs、受入 7393 passed / 1 failed / 20 skipped = F57 再発・単独再走 8 passed、変異 2 走で KILLED 2/2、branch worktree-dev-wave-t656-walltime)
---

## 本文

- **ユーザー裁定は (b) 既定値自体を上げる**で、40 分という値まで指定された。(a) `run_tests.py` への
  walltime plumbing と (c) 受入全走の分割は不採用。[T-653] は同じ問いなので本項へ統合して閉じた。
  設計判断は {{D:dispatch-default-walltime-40min}}。
- 軽量版で走らせた。設計択一はユーザー裁定済み、正しさ防壁に触れない、受理集合不変のため
  段 2 / 3 と段 6 の review 子を省いた。実装面は Codex `role=author` 1 本が書き、親は直接編集していない。
- **段 1 の実測で裁定の前提を確かめた。** `qstat -Qf gen_S` の Per-Req Elapse Time Limit は
  Max 86400S で、40 分は上限内。定数を実際に 40 分へ書き換えて測ると赤は 1 件だけで、
  `test_t471_restore_bound.py` の `elapstim_req=00:30:00` は別の凍結 PBS script のもので
  既定値とは無関係だと確認できた。probe は `git checkout --` で復元した。
- **実装子は「実装済み・未実走」と正直に申告した。** codex の sandbox が socket を拒み
  (`qstat -Q` が `Can't create socket`)、dispatch 経路のテストを 1 度も走らせられなかった。
  緑を主張せず静的な閾値計算だけを報告したので、テストの実測はすべて親が行った。
- **変異 matrix は 2 本とも KILLED**、観測 node は事前登録と完全一致だった。M1 (既定値を 30 分へ戻す)
  は新設 gate だけを、M2 (qsub argv を固定文字列にする) は伝播 gate と既存 override gate だけを
  赤にした。baseline は 137 passed。これで新設 gate が恒真でないことも同時に示せている。
- 受入全走は Elapse 1213 秒で完走し、**40 分枠が実際に効いていること自体をこの走行が実証した**
  (`Remaining Elapse 1187S` = 確保 2400 秒)。赤 1 件は `git cat-file --batch-check` の 15 秒 timeout
  で落ちたもので、F57 の再発である。単独再走は 8 passed / 39.51 秒で再現せず、
  本 wave の差分 (dispatch の定数とその検査) は当該コードへ到達しないため `DW-O18` により帰属しない。
- **段 5 の投入で 1 回空振りした。** detached 起動の `bash -c` に cwd を渡さず、harness が
  `tools/mutation_harness.py` を見つけられず rc=2 で即死した。ledger は生成されておらず
  実害は再投入のみ。単発の操作ミスなので `DW-G03` に従い族一般化しない。

## 次の一手差分

### 完了

- [T-656] 既定 walltime を `00:40:00` へ上げ、qsub 伝播の期待値を定数導出へ移し、
  既定値が受入全走の実測最大所要 (1809 秒) の 1.25 倍以上であることを測る gate を新設した。
  受入全走の実測 Elapse は 1213 秒で、確保 2400 秒に対し余裕が戻っている。
  remaining: none
  base: 99c5943bec3e96eda87e44b418654dfb0258447ed5d0640ed0996cba64cce7f9
- [T-653] 同じ問いへの裁定として (b) が確定し、既定値の引き上げで閉じた。
  lease による直列化だけでは単一走行の所要が縮まないため不十分だと裁定文へ記録した。
  remaining: none
  base: 32c82b59fda9944d8b0b2943dbe85bf40a09185d8b372ac7353f7a7efc24c18c

### 新規

- {{T:walltime-queue-wait-correlation}} **P3・新規**: 要求 `elapstim_req` を増やすと gen_S の
  queue 待ちが延びるかは未実測のまま。40 分化で全 dispatch の待ちが恒常的に伸びるなら、
  受入形だけ枠を分ける判断が再燃する。既存 receipt の `queue_wait` 系 field を
  30 分期と 40 分期で比較すれば新規計測なしで測れる。
