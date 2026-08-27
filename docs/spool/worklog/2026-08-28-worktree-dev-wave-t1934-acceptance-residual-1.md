---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1934-acceptance-residual
seq: 1
title: [T-1934] 受入のwall−最遅worker残差は4成分へ識別不能と確定し、実装差分ゼロで閉じた (docsのみ、branch worktree-dev-wave-t1934-acceptance-residual、変異matrix免除)
---

## 本文

- ユーザー指示どおり既存timestamp、JUnit、runner log、receipt/reportだけを使い、K=2/K=3の
  全5 shardを再解析した。一次資料は
  `output/insights/2026-08-28_t1934-acceptance-residual/`。
- **依頼の4成分加算モデルが成立しない。** `worker_occupancy.duration_s` はworker連続所要でなく、
  観測済みの有効なtest report durationの和である。残差にはcollection、worker起動、prewarm、
  finalizationだけでなくscheduler idleとcritical worker不一致が混ざり、phaseも重なる。同じartifactに
  対し、残差全体を前置遅延、idle、内部finalizationのどれへ置く反例も成立する。
- K=3のJUnit session残差は59.223/49.039/49.557秒、K=2は73.535/54.726秒だった。
  prewarm consumerは両走ともshard-0だけで、receipt 36件、oracle 28件。prewarm無しshardにも
  49〜55秒の混合残差がある。prewarm有無との差10〜19秒はreal-repo成分、割付、node、idleと
  共線で、prewarm因果値・上下界ではない。
- finalizationについて確定できるのはJUnit cutoff後のrunner tail約0.32秒だけで、最後のtestから
  cutoffまでの内部finalizationは0〜残差の粗い界しかない。親briefの「finalizationは1秒未満」と
  「prewarmは最大約10秒」を敵対レンズが反証し、親が撤回した。
- login独立collectionはK=3現物で7.98秒、最初のcompute JUnit session開始前にartifact化した。
  terminal joinを支配しなかった可能性が高いが、資源競合の寄与ゼロとは一般化しない。
- 最大成分、現行mainでの成分別反復、単一の局所所有pathがいずれも確定しないため、ユーザーの
  実装条件は不成立と裁定した。`tools/run_tests.py`、`tools/acceptance_shards.py`、
  `orchestrator/tests/conftest.py`を含む実装面は0 byte。paired性能再測定と変異matrixは発火しない。
- 規律2を緩めず、skip、deselect、selection縮小、timeout緩和、独立collection/report/JUnit/
  loadgroup/freeze/oracle gateの省略を行っていない。T-1933、別成分、恒久計装、新監視基盤も
  同waveへ持ち込んでいない。
- Codex子は3本 (plan 1、敵対consult 2)。全て`gpt-5.6-sol` / `reasoning=xhigh` / read-only、
  launcher rc=0、`check_codex_output.py` rc=0。本waveでpytest/buildを直接起動していない。
- **段7でF333を再発させた。** commitとfull-history provenanceを同じ短い前景commandへ繋ぎ、
  dispatch親だけを打ち切ってrequest `953513.nqsv`とorphan holdを残した。qdelせず終端を待ち、
  child未起動のqueue-wait-timeoutとsource clean/HEAD不変を確認した。holdは回復処理が解除し、
  full-history監査を単独commandで再走して6717件・新規違反なしを得た。同型と恒久対応はF333に
  既記録なのでreference/入口は変更せず、再発だけをfailures fragmentへ追記する。
- 最終受入はD838とDW-O12に従い、本記録commitを含むtipで通常lease経路から1回行う。その結果値は
  tested tip一致を壊す後追いcommitを避けるため本entryへ含めず、専用handoffと最終報告へ残す。

## 次の一手差分

### 完了

- [T-1934] 既存artifactだけでは4成分の最大項を識別できず、局所修理の発火条件が不成立と確定した。
  remaining: none
  base: e71bc17587e9e299772b8976dca3564a575ecdd004315d9811a0c912598550e4
