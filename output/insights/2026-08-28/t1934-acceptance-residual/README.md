# T-1934 受入の wall−最遅worker 残差診断

- authority: none
- default_effect: no-state-change
- wave: `worktree-dev-wave-t1934-acceptance-residual`
- 基準 main: `f34e19be94a3608099773ac6c1a12a98ae992048`
- 実装面差分: 0 byte

可変状態の正本ではない。T-1934 の完了実績は worklog、既存の受入契約は decisions を正本とする。

## 結論

最大成分は識別できず、ユーザー条件を満たす局所修理が無いため実装しなかった。

既存artifactの `worker_occupancy.duration_s` は worker の連続所要でなく、各testの観測済み有効
`report.duration` の和である。したがって

`JUnit session time - max(worker report-duration sum)`

は collection、worker起動、prewarm、finalizationの非負4成分和ではない。最後に終わったworkerと
最大busy-time workerの不一致、worker内idle、phaseの重なりも混ざる。同じartifactに対し、残差全体を
前置遅延、scheduler idle、内部finalizationのいずれへ置く反例が成立する。

このため最大成分、現行mainでの成分別再現性、単一の局所所有pathの3条件がすべて不成立である。
恒久計装や新監視基盤は作らず、T-1933や別成分も同waveで直していない。

## 既存5 shardの再計算

| K | shard | JUnit session | 最大の観測済みworker和 | 混合残差 | receipt prewarm consumer | oracle prewarm consumer |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | 285.521 s | 211.986 s | 73.535 s | 36 | 28 |
| 2 | 1 | 225.128 s | 170.402 s | 54.726 s | 0 | 0 |
| 3 | 0 | 160.920 s | 101.697 s | 59.223 s | 36 | 28 |
| 3 | 1 | 123.215 s | 74.176 s | 49.039 s | 0 | 0 |
| 3 | 2 | 146.192 s | 96.635 s | 49.557 s | 0 | 0 |

prewarm無しの3 shardにも49〜55秒の残差があるため、prewarmは残差の必要原因ではない。
prewarm有りとの差10〜19秒は、real-repo成分、割付、node、idleと共線であり、prewarmの因果値・
上界・下界のどれでもない。

## 4成分で同定できたこと

| 成分 | 同定できたこと | 同定できないこと |
|---|---|---|
| collection | 各compute shardで48 workerが同じ全universeをcollectし、同一digestを返した | 開始・終了・critical-path寄与 |
| worker起動 | runner logに48/48 worker作成と担当item数が残る | process生成・import・collectionとの分離時間 |
| prewarm | consumerを持つshard-0だけでreceipt/oracleが各1回同期発火する | raw duration、overlap後のwall寄与 |
| finalization | JUnit cutoff後のrunner tailは約0.32秒 | 最後のtestからJUnit cutoffまでの内部finalization |

login側の独立collectionはK=3現物で7.98秒だった。全dispatch process開始後に併走し、最初のcompute
JUnit session開始前にartifact化したためterminal joinを支配しなかった可能性が高い。ただしCPU、memory、
filesystem競合の寄与がゼロとは主張しない。compute workerごとのcollectionとは別の独立性gateである。

旧tipで記録された48-worker・全collection・0-testの12.86秒は歴史的観測として保持するが、現行の
collection、launch、finalizationの界には使わない。selection縮小を再現実験として新たに行っていない。

## 守った境界

- skip、deselect、selection縮小、timeout緩和を行っていない。
- independent collection、selected==finished、report/JUnit完全性、loadgroup、恒久除外、
  freeze/oracle gateを変更していない。
- `tools/run_tests.py`、`tools/acceptance_shards.py`、`orchestrator/tests/conftest.py` を変更していない。
- paired性能再測定は修理が無いため発火しない。最終受入は記録commit後の通常lease経路で行う。

## 逐語

| file | sha256 |
|---|---|
| `verbatim/s1-brief.md` | `e437116ed06e3069d1e8a9087893e70ca2a02defb8abe479a5527ff46ce91a0c` |
| `verbatim/s2-plan.md` | `1da2f46fea5777f4bca6bb08cc1cf5d6172aa8182fd1295add1747acf0804423` |
| `verbatim/s3-timing-identifiability.md` | `dc9d881d7e68c35afb283d5155bfc4abb19b0ef6b554f9b799841bc5eeee796a` |
| `verbatim/s3-correctness-closure.md` | `1794b697953a0d7aeac96c6e1ff931bd8e95af78077575e8ca066a2d6727825a` |
| `verbatim/s4-adjudication.md` | `80c363af814f55d2405a8b6c80b40df45e56fd6f60a1cfcb635873e9cbe664f0` |
