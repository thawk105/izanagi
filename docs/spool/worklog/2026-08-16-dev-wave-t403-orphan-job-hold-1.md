---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t403-orphan-job-hold
seq: 1
title: 孤児 job が生きうる間の投入・復元・廃棄・受入掃除を fail-closed で止めた — 署名を job_may_remain 1 語へ単純化し、ハーネス側に dispatcher 非依存の二重化を置いた (コード + テスト、branch worktree-dev-wave-t403-orphan-job-hold、変異 matrix = 13/13 KILLED、焦点走 1493 passed)
---

## 本文

- D142 の qdel gate が取消を見送った job は孤児として計算ノードに残る。変更前は receipt と
  stderr 1 行の警告だけで、次回投入・変異 source の復元・変異 worktree の廃棄・受入 probe の
  掃除のいずれも止まらなかった。設計判断は {{D:orphan-hold-latch}}。
- 親が brief 前に実測した 3 点。(1) `qdel.job_may_remain` の非テスト consumer は
  `_print_qdel_remaining_warning` の 1 個だけで、stderr へ 1 行印字する以外の副作用が無い。
  (2) 実 receipt 135 件の内訳は正常完了 124 / cleanup 未 claim の infra 8 / gate 許可 + qdel rc=0 が 2 /
  孤児 1 で、唯一の孤児事例は request 907709.nqsv (`_SignalAbort: signal 15`、gate は RUN で
  `state-not-cancellable`)。(3) job script は `cd "$REPO"` してから dispatcher を exec するため、
  計算ノードの job は login 側 worktree の source をその場で読む。
- 段 2 プランは「照会で対象が見えない」「監視ループが終端を観測した」を免除条項に置いたが、
  段 3 の敵対レンズが、前者は投入直後の未反映と区別できず、後者は対象非束縛 parser 由来で
  偽陽性になりうると実証した。段 4 で免除条項を全廃し、署名を `job_may_remain is True` の 1 語へ
  単純化した。
- 段 3 は 2 本とも「qsub を打っている最中に止められた窓では記録も判定も武装しない」を指摘した。
  投入前から結果不明状態へ入り、不明のまま抜けたら照会だけ行って記録を先に立てる形にした。
  **qdel を実行する経路は 1 本も増やしていない** (ユーザー裁定)。
- 段 6 レビューが 2 つの実害を出した。(1) 記録を書けなかった場合にハーネスが素通りする
  (受入は receipt の印を読んでいなかった)。(2) 停止記録が通常台帳を `--out` で上書きするため、
  保全後に案内される `--resume` が schema 不一致で必ず失敗する。両方 fix で閉じた。
  前者の教訓は {{F:receipt-sample-survivorship}}。
- 段 4 の過剰拒否正例 1 本は、5 つの独立した検出面を 1 変異にまとめており単一理由性を
  満たさないと段 6 レビューが指摘した。1 面 (ハーネス検出) だけを登録し、残り 4 面は
  完全集合を静的に確定できないため**登録しなかった** (DW-M01 の「確認できなければ登録しない」)。
- 変異 matrix は使い捨て worktree (`tools/mutation_worktree.py`、runner=dispatch) で 2 回走らせた。
  1 回目は否定変異 12/12 KILLED、正例 1 本が MISMATCH。ただし期待ノードは落ちたうえで
  6 件多く落ちており、殺せていないのではなく期待集合が不完全だった。完全集合で再登録した
  2 回目が **13/13 KILLED、MISMATCH 0、baseline PASSED**。1 回目は probe として扱い、
  台帳は `/work/1/SFC/tanab/dev-wave-jobs/t403-mutation-out/ledger-run2.json`。
- 1 回目の wrapper は matrix 完走後の evidence 退避だけ EXDEV で失敗した
  (`--out` が `/home`、scratch が `/work` で別デバイス)。matrix 自体は完走しており、
  再走では出力先を scratch と同一デバイスへ置いて teardown まで rc=0 になった。
- 背景待ち手の完了通知が 1 度**偽**だった。成果物も完了印も無く producer は生存していたため、
  3 点照合 (成果物実在・完了印・producer 死) で検出して張り直した。
- この wave が保証しないことを明示する。hold は latch であって相互排他 lock ではない。
  qsub 前の永続 claim は解決 (削除) 経路を新設することになり、その欠陥が全 dispatch を
  恒久停止させうるため実装していない。したがって SIGKILL と discovery 中の再 signal の窓は残る。
  保護範囲は `dispatch_compute` 経由の dispatch と変異 harness / 受入 checker に限り、
  `tools/pegasus/submit_*.sh` の直接 qsub、`orchestrator/campaign/patchharness.py` の
  checkout 復元・worktree 強制削除、local 実行経路は対象外である。

## 次の一手差分

### 完了

- [T-403] 孤児 job の後始末を 4 層 (発行・投入・復元・廃棄) + 受入 probe 掃除で fail-closed にした。
  変異 13/13 KILLED、焦点走 1493 passed。残余と scope 外は本エントリ本文と {{D:orphan-hold-latch}} に明記した。
  remaining: none
  base: cdb120627cd7372bf05f7bed0537a82bb4e262235e973dacc0cef826e83703a6

### 新規

- {{T:orphan-hold-lifecycle-lock}} **P2・新規**: dispatch claim・変異 source 復元・evidence 退避・
  teardown を直列化する per-checkout の共有 lifecycle lock。現状の hold は latch であって
  相互排他ではなく、「同一 checkout で harness を経由しない並行 dispatch」の窓が残る。
- {{T:orphan-hold-unprotected-submitters}} **P2・新規**: `tools/pegasus/submit_floor.sh` /
  `submit_certify.sh` / `submit_silo_ladder_rung1.sh` の直接 qsub と、
  `orchestrator/campaign/patchharness.py` の checkout 復元・worktree 強制削除が hold を見ない。
  T-403 の保護範囲に含めるか、対象外と明記し続けるかの裁定が要る。
- {{T:orphan-hold-local-runner-scope}} **P3・新規**: local (非 dispatch) 実行経路を hold の停止対象に
  含めるかの裁定。local は計算ノード job を作らないが、孤児が生きている間の tree 書換えという
  危険は共有する。
- {{T:orphan-hold-durable-claim}} **P2・新規**: qsub 前の永続 claim と、対象束縛された終端証拠による
  解決 (tombstone)。SIGKILL・discovery 中の再 signal の窓を閉じる恒久形。解決経路の欠陥が
  全 dispatch を恒久停止させうるため、設計は解除の安全性から始める。
- {{T:orphan-hold-fanout-diagnostics}} **P3・新規**: fan-out の driver report と top-level stderr へ
  hold path・request ID・submission dir を転記する。成果物の値は変わらず復旧時間だけの問題。
- {{T:orphan-hold-positive-controls}} **P3・新規**: 過剰拒否を検出する正例変異を、dispatch 署名・
  dispatch 検出・worktree 検出・受入検出の 4 面へ登録する。本 wave では完全集合を静的に
  確定できず登録を見送った。
