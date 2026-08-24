---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1623-t1635-occupancy
seq: 4
---

## 再発

### F282

- **再発: 2026-08-25** — **独立 3 例目**。変異本走を待つ待ち手が exit 0 で完了通知を出したが、
  `.done` も成果物 `mut-final-out.json` も無く、`pgrep -af mutation_harness` で harness が
  生存していた。起動から 1 分しか経っておらず、所要見積りは約 22 分だった。
  3 点照合で弾いて張り直したが、**張り直した待ち手も同じく即座に完了扱いになり**、
  さらに旧待ち手が同じ完了通知を重複して送ってきた。本 wave では合計 3 回誤検出した。
  新事実 2 件。(a) `tools/dev_wave_wait.py producer` 版だけでなく、
  **素の `until [ -f <done> ]; do sleep 20; done` を背景 job で回す形でも同じ**に即戻る。
  待ち手の実装ではなく背景 job の完了判定側の問題である可能性が高い。
  (b) `Monitor` へ切り替えると正しく約 22 分待って `MUTATION_DONE rc=0` を報せた。
  完了と異常終了の両方を拾う条件にしてある。
  恒久対応の 3 点照合はそのまま効いた — 実測を挟まず通知だけを信じていれば、
  変異が当たったままの tree を land しかけていた。

### F453

- **再発: 2026-08-25** — 起点が dispatch queue timeout ではなく **hang 変異そのもの**だった
  新しい型。循環停止 (`seen`) を落とす変異が意図どおり無限ループになり、
  harness の 900 秒 hang timeout は発火したが、PBS job (Elapse 935 秒) の終端証拠が取れず
  `orphan-hold` が張られ、**変異を当てたまま**中断した
  (`mutation-left-in-place`、dirty path = `tools/check_worktree_occupancy.py`)。
  本件の sidecar は repo 内の `output/pegasus-dispatch/orphan-hold.json` と
  `output/pegasus-dispatch/orphan-holds/<request>.json` の 2 個で、
  job-dir 側の `<out>.orphan-stop.json` は生じなかった。**両方が git 管理外**であることを
  `git status --porcelain -- <path>` で確認してから削除した。
  復旧は hold が指示する順序どおり — `qstat` で対象の不在を確認 (job は既定 walltime の
  1 時間で自然終端するのを待った)、`git checkout --` で dirty source を復元、
  clean と HEAD 一致を確認、そのうえで hold と sidecar を削除。
  **手動 qdel は F47 ラッチを武装させ解除がユーザー手番になるため行わなかった。**
  待ち時間は約 40 分。`DW-M06` は「timeout は証拠として記録し harness 全体を落とさない」と
  定めるが、**dispatch 経路では job の終端証拠が取れず結果として全体が止まる**。
  本 wave は hang 変異を本 matrix から外し、TIMEOUT 観測だけを証拠として残して本走を通した。
