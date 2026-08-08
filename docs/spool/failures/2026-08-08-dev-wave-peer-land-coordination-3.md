---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-peer-land-coordination
seq: 3
---

## 新規

### {{F:mutation-runner-ran-local}}. 変異 harness の baseline が、runner の local 実行で `PARSE_ERROR` になった [手順漏れ] [観測]

- 事象: `--runner-mode dispatch` で変異 harness を起動したが、baseline が
  `status=PARSE_ERROR` / `artifact_error="receipt 表示行が exactly one でない: 0"` で中断した。
  rc は 0、所要 3.9 秒、captured stdout は空だった。
- 根本原因: runner の `tools/run_tests.py` は、ログインノードに余裕があると**計算ノードへ
  dispatch せず local で走る**。local 経路は harness が dispatch mode で要求する receipt 行を
  出さないため、harness は成果物を特定できず fail-closed で止まる。harness の
  `--runner-mode dispatch` は「runner が dispatch する」ことを保証しない。
- 恒久対応: 変異 harness へ渡す runner argv に `--force-dispatch` を必須とする。所在は
  環境 runbook の変異走行手順。`--runner-mode dispatch` と runner の実経路が食い違ったときは
  harness が中断するので、偽の緑にはならない (fail-closed 側の失敗である)。
- 再発検知: 同型 (harness の mode 宣言と runner の実経路の不一致) が別の runner で再現したら、
  runner 側に「dispatch mode で呼ばれたら local へ落ちない」検査を足すことを裁定へ返す。

### {{F:acceptance-walltime-exceeded}}. 受入全走が計算ノードの既定 walltime 30 分を超えて SIGKILL された [観測]

- 事象: 受入全走が約 99% まで進んだところで
  `Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)`、
  Elapse 1809 秒で打ち切られ rc=16 になった。直近の同種走行は 1146 秒、再走は 1267.64 秒で完走した。
- 根本原因: dispatch の既定 walltime は 30 分 (`DEFAULT_WALLTIME = "00:30:00"`) で、
  `tools/run_tests.py` はこれを上書きしない。並行 wave の受入 job が同時に走ると 30 分に届く。
  **受入所要が単独走行時の実測に対して余裕 2 割程度しかない**ことが可視化されていなかった。
- 恒久対応: 本 wave の受入 lease ({{D:acceptance-lease-advisory}}) が、受入窓を 1 本へ直列化して
  同時走行そのものを減らす。所在は環境 runbook の受入 lease 節。
  既定 walltime の引き上げは行わない (裁定対象として起票する)。
- 再発検知: lease 運用下でも 1800 秒に届く走行が出たら、walltime 既定値の裁定へ回す。
