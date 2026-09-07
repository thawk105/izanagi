---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t583-qsub-oe
seq: 2
---

## 再発

### F355

- **再発: 2026-09-08** — [T-583] wave の変異本走の待ち手で 1 回観測した。producer 生存・
  `.done` 不在・成果物不在のまま `tools/dev_wave_wait.py producer` が rc=0 で戻り、
  標準出力は空だった (2026-09-02 の再発が記録した縮退メッセージすら出ていない)。
  `--receipt-file` の receipt も書かれなかった。`.done` と成果物の不在で偽完了を捕まえ、
  待ち手を張り直して正しい完了を拾った。**張り直しに使った自前の
  `until [ -s <done> ] || ! kill -0 <pid>` ループも即座に離脱した** — `nohup setsid` で
  detach した producer に対し、別 shell から `kill -0` が生存を判定できなかったためで、
  これは待ち手 tool の欠陥ではなく張り直し側の作り方の誤りである。生死条件を外して
  `.done` の実在だけを見るループにしたら正しく待てた。**縮退した待ち手を張り直すときは、
  生死判定を pid でなく成果物の実在に寄せる。**

### F810

- **再発: 2026-09-08** — [T-583] wave 用 worktree の初期化で 1 回観測した。
  `tools/dev_wave_submodule_init.py --worktree <ABS>` の 1 回目が
  `runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}` で rc=1 になった。
  同 worktree で `git submodule update --init --recursive --no-fetch` を直接実行すると rc=0 で
  何も出力せず、その後に同じ tool を再実行して rc=0 になった。実装子用 worktree では 1 回目から
  rc=0 で通っており、本 wave では 2 worktree 中 1 回の発生だった。根本原因は本 wave でも
  切り分けていない。
