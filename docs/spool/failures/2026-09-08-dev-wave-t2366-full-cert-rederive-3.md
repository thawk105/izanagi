---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2366-full-cert-rederive
seq: 3
---

## 新規

### {{F:orphan-hold-silently-blocks-acceptance}}. 残った Pegasus orphan hold が受入を無言で止め続ける [観測面の欠落] [手順漏れ]

- 事象: 混雑で受入の dispatch が queue-wait-timeout になり、wave worktree に
  `output/pegasus-dispatch/orphan-hold.json` と `orphan-holds/unknown-<hex>.json` が残った。
  以後の受入は **8 回連続**で、テストを 1 件も走らせないまま失敗した (2026-09-08、[T-2366] wave)。
- 根本原因: hold があると dispatcher は scheduler command 自体を起動しない。しかし受入側に出る情報は
  `stage=acceptance-command rc=70 source_rc=16` と `reason=dispatch-attestation-missing`、
  子 log の `acceptance shard gate failed: dispatch-infrastructure` の 1 行だけで、**hold の存在も
  path も現れない**。混雑が続いていたため queue 詰まりと誤読し、D612 の上書き (queue-wait 3600 /
  overall-grace 600) を足して再投入したが、hold がある間は上書きは効かない。
- 診断の入口: hold の絶対 path と復旧手順は
  `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-0/dispatcher.log` にだけ出る。
- 恒久対応: 記憶 `orphan-hold-blocks-acceptance-silently` に、受入が
  `dispatch-attestation-missing` で 2 回以上続けて失敗したら混雑を疑う前に自分の worktree の
  `output/pegasus-dispatch/orphan-hold.json` を見る手順を置いた。撤去は `qstat` で hold の `job_name` の
  8 文字接頭辞の不在を確認し、`git status` が clean なことを確かめてから hold 2 file を消す。
  一般的な hold の扱いは `docs/pegasus-runbook.md` §7.6、混雑時の上書きは D612 が正本。
- 再発検知: 撤去直後の 1 回で受入が緑になること (本 wave で実測、21793 passed / 赤 0)。
  land 側の rc=29 と同じ対比で読める — 繰り返すなら自分の hold、単発なら競合。
