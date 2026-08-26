---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 7
---

## 新規

### {{F:job-identity-by-path-under-staging}}. 実行 payload の同一性を path 等価で検査し、scheduler の複製で必ず偽になった [恒真ゲート] [手順漏れ]

- 事象: B-10 計測 job が計算ノード上で 5 秒で停止した
  (`executed B-10 script is not the repository payload`)。job body は
  `${BASH_SOURCE[0]}` を実体化した path が repository 内の path と等しいことを要求していたが、
  **NQSV は投入された script を spool 領域へ複製してから実行する**ため、この条件は
  どの正しい投入でも成立しない。**通ることのない検査だった。**
- 根本原因: 守りたい不変条件は「実行された payload の**中身**が repository の payload と
  同一であること」なのに、述語が **path の等価**になっていた。path は複製で変わるが
  中身は変わらないので、述語は不変条件より狭く、しかも常に偽になる側へ狭かった。
  同じ repository の `tools/pegasus/b10_backoff_shape_campaign.sh` が既に
  SHA-256 の三者一致で正しく実装していたが、参照されなかった。
- 恒久対応: 実行中 script の SHA・`git cat-file blob <HEAD>:<path>` の SHA・投入側が固定し
  `qsub -v` で渡した SHA の**三者一致**へ置き換えた。
  `orchestrator/tests/test_backoff_extended_sweep.py::test_b10_job_script_identity_uses_three_sha256_values_not_path_equality`
  が、path 等価で束縛しないことと三者一致で束縛することを固定する。
- 再発検知: 上記テストに加え、**起動から計測開始までの全検査を列挙し、各々が計算ノード側で
  成立すると言える根拠を書く**ことを、この種の job body を書く際の手順に含めた
  ({{F:job-identity-by-path-under-staging}} と F683 は同じ round-trip 構造で 1 回に 1 件しか
  露出しない)。

## 再発

### F683

- **再発: 2026-08-27** — 同じ B-10 計測 job で、投入側 (ログインノード) で成立する前提を
  実行側 (計算ノード) へ持ち込む型が 2 度続けて出た。1 度目は必須コマンド一覧の `gnuplot`
  (ログインノードには在り計算ノードには無い)、2 度目は上記の path 等価
  (投入元では成立し実行先では複製により成立しない)。
  **起動時検査は fail-fast の直列鎖なので、1 回の投入で露出する欠陥は 1 件だけ**であり、
  1 件直すたびに queue 待ちを含む round-trip を 1 往復消費した。
  個別対処ではなく、**鎖の全項目を列挙して各々の成立根拠を実行側基準で書き出す**ことで
  残りを一括で潰した。
