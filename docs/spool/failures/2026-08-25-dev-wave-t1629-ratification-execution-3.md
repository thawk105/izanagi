---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1629-ratification-execution
seq: 3
---

## 新規

### {{F:ratification-expired-before-use}}. 人間が行った enforcement closure 批准が、一度も使われないまま自分の branch 上で失効していた [ドリフト] [手順漏れ]

- 事象: 2026-08-24 に人間が `hooks/enforcement-source-closure-ratifications.v1.jsonl` を新設し、
  現行 closure の digest `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44` を
  1 行追記した (commit `6188a8d4`、`AI-Agent: none`、branch
  `worktree-dev-wave-paper-story-a1-paired-20260824`)。追記時点でこの digest は当該 commit の
  25 blob から再計算した値と一致していた。ところが同 branch はその後 main を 2 回取り込み
  (`07415b5c`、`9550728a`)、tip の closure digest は
  `1111720da46ae17801b13af608c0b9e119b23c87a6eeb8686df7df478d64df71` へ移った。
  main 側の digest も同じ `1111720d…` である。したがって批准行は**どの ref から見ても現行
  closure に対応しない**。`authority` field を持つ v2 lock は当該 branch にも main にも 0 件で、
  この批准は一度も使われていない。
- 根本原因: 批准は closure 版 (25 path の blob map) に束縛されるのに、批准してから official な
  新規 campaign を起動するまでの間に closure を動かす操作 (main 取り込み、25 path を触る wave の
  着地) を挟む運用になっていた。F498 が「批准と official 新規 campaign の起動は近接させる必要が
  あり、間に 25 file を触る wave が着地すると再び塞がる」と書いた運用上の含意が、
  そのまま実際に発火した形である。人間手番を先に消費してしまうため、
  失効するたびに同じ手番が再発生する。
- 恒久対応: {{D:ratification-execution-impossibility}} — 批准は official 起動の直前に行い、
  批准と起動の間に main 取り込みを挟まない (just-in-time) ことを、どの択を採る場合でも
  共通の運用条件として裁定へ含めた。機械側の fail-closed は既に
  `orchestrator/campaign/enforcement_source_ratification.py` の
  `require_ratified_closure` が担っており、失効した批准で走り出すことは構造的に起きない。
- 再発検知: 批准後に 25 path のいずれかが動いた時点で digest が変わり、次の official 新規
  campaign 初期化が `enforcement-source-closure-unratified` で即座に fail-closed する
  (`orchestrator/campaign/ident.py` の `_capture_current_loader_binding`)。実害は時間損失に限られる。
