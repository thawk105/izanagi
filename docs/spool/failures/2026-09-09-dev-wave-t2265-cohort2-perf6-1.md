---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2265-cohort2-perf6
seq: 1
---

## 再発

### F22

- **再発: 2026-09-09** — [T-2265] の投入・待機 script で、NQSV の実機表記を消費側と突合しないまま
  4 件の欠陥が積み上がった。`qstat -f` を PBS Pro の `Job Id:` / `job_state =` で parse (実機は
  `Request ID:` / `Current State`)、`qsub` の stdout を素の job ID として検査 (実機は
  `Request <id> submitted to queue: <q>.`)、投入側 RequestID から期待 file 名を組み立て
  (job 内の `PBS_JOBID` にだけ `0:` prefix が付く。**本項が既に名指ししていた prefix である**)、
  state 語彙検査を `qstat` 一覧の全行へ適用 (他 session の job で監視が死ぬ)。
  子は 4 件すべてを偽 `qstat` / 偽 `qsub` で緑にしており、実機書式は親が測るまで誰も知らなかった。
  2 番目の欠陥では job が queue に入ったのに台帳へ記録されず、警告が発火して `qdel` で取り消した。
  恒久対応 (a) の「消費側との突合まで」は表記を fixture 化した certification 経路には効いていたが、
  **新しく書く消費側には効かない**。実効的に閉じたのは `DW-O16` の「実行環境依存の実装は
  レビュー通過で closed とせず実機で動かす」であり、親が実機の `qstat` で待ち手を 1 回走らせ、
  実機に 1 本投げて `qsub` の出力を採ったことで 4 件とも顕在化した。
