---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1647-a2-cert-run
seq: 2
---

## 新規

### {{F:mutation-run-broken-by-parent-commit}}. 親が変異走行中に commit して HEAD を動かし、harness を fail-closed で止めた [手順漏れ]

- 事象: 16 変異の probe を計算ノードへ投入した直後、親が待ち時間を使って main の merge を
  commit した。harness は `run 中に HEAD が変化: expected=9405a080..., actual=1b703335...` で
  中断し、走行中の 1 変異が失われた。`output/pegasus-dispatch/orphan-hold.json` が残り、
  同 worktree からの全 dispatch が塞がった。
- 根本原因: 変異走行中の禁止事項を「tree へ書かない」とだけ理解していた。
  harness が束縛するのは working tree ではなく **HEAD** であり、commit は tree を汚さずに
  HEAD を動かす。`git status` が clean のままなので、禁止に触れている自覚が生まれない。
- 誘発要因: 変異走行が数十分かかるため、その間に別の作業を進めたくなる。
  merge も commit も「tree を汚さない安全な操作」に見える。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M05` が要求する単一走行の理解を
  「HEAD を動かす操作 (commit / merge / reset / checkout) も禁止」まで広げる。
  実体は harness 自身の HEAD 束縛検査 (`run 中に HEAD が変化` で fail-closed) であり、
  この検査は既に存在する。欠けていたのは親側の運用規律である。
- 再発検知: 変異 ledger の `repo_head` と harness の中断理由。走行中に HEAD を動かすと
  必ずこの理由で止まるため、静かに壊れることはない。
- 波及: orphan hold は request の終端 (`child_rc=0`、scheduler 上で消滅) と
  木の clean / HEAD を確認する recovery 手順を踏む。本件では harness 自身が撤去していた。

## 再発

### F498

- **再発: 2026-08-25** — paper-story A-2 の 4-cell certification 実走 2 回目が、
  同じ `enforcement-source-closure-unratified` で 16 秒で止まった
  (attempt `t1647-20260825b`、request `946056.nqsv`、`driver_rc=1`)。
  本 wave は閉包 25 path のいずれにも触れておらず、HEAD の closure digest は main と
  完全に一致する (`1111720da46ae17801b13af608c0b9e119b23c87a6eeb8686df7df478d64df71`)。
  批准台帳 `hooks/enforcement-source-closure-ratifications.v1.jsonl` は
  **main に存在しない**。2026-08-25 02:59 に人間が開設した commit `6188a8d4` は
  branch `worktree-dev-wave-paper-story-a1-paired-20260824` にあり未着地で、
  そこで批准された digest `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44`
  は A-1 が `loop.py` と `pipeline.py` を変更した後の closure に対応する。
  すなわち **main の現行 closure には批准行が 1 件も無い**。
  D526 により追記経路は AI に閉じており、解除は人間手番である。
  A-1 の land か、main の現行 digest の批准のいずれかが要る。
