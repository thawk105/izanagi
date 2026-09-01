---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t441-grammar-version-canon
seq: 1
---

## 再発

### F453

- **再発: 2026-09-01** — dispatch queue timeout 起点の同型だが、**sidecar を両方消した後に
  第 3 の阻害が出た**。1 回目は baseline の job が待ち行列のまま 900 秒で時間切れになり
  (`source_state: unchanged`、`dirty_paths: []`)、repo 内の
  `output/pegasus-dispatch/orphan-hold.json` と submission_dir を除去して再投入したところ、
  2 回目は job-dir 側の `<out>.orphan-stop.json` で即停止した (既知の 2 種類目)。
  両方を除去した 3 回目は収集段が `rc=16, collected=0,
  artifact_error='receipt scheduler_logs.stdout.path がない'` で落ち、
  4 回目は **`fresh --attempt-out が既に存在する`** で起動前に止まった。
  `--attempt-out` は attempt ごとに新しい path が要り、`--wrapper-attempt` と対で変える必要がある。
  既存記述はこの点を持たない。runner を `--attempt-out`/`--wrapper-attempt` を引数化した
  `.sh` に替えて 5 回目で完走した (12/12 KILLED)。
  毎回 `qstat` で対象 request の不在、作業ツリーの clean、変異の復元を確認してから再投入し、
  手動 `qdel` は使わなかった。**変異の内容は 1 件も変えていない。**
- **再発検知の追記:** orphan-hold からの再投入は、2 種類の sidecar の除去に加えて
  `--attempt-out` の path と `--wrapper-attempt` の番号を前回と変えること。
  同じ値で再投入すると起動前に止まる。
