---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-acceptance-fastest
seq: 1
title: [T-1933] T-080 process-cache仮説をpaired K=3で反証した（計測 + docs、正味実装差分0）
---

## 本文

- 受入最長nodeのT-080 cache重複仮説を、11 nodeからcache key共有の6 nodeへ敵対縮約して実装した。
- 焦点は実装前76.03秒、実装後75.77秒で同一worker化を確認したが、full K=3 paired中央値は244.810→245.707秒（+0.37%）で変化なし。{{D:t080-process-memo-noeffect}}により不採用にした。
- 実装`2ffb32a0e`とremoval`1bafd884a`で対象2fileはtested mainとbytes一致、正味実装差分0。改善していない配線を残していない。
- 3×3は全て18,598 items、18,536 passed/62 skipped、selected=finished、loadgroup、赤0。post 1走はauthoritative `child-green` receipt、残りはfixed-tip性能対照。
- 変異はbaseline PASSED、3/3 KILLED、期待node完全一致、SURVIVED/MISMATCH 0。正しい配線と速い配線を分けて裁定した。
- Codex subprocessは11本。accepted 10、初回plan 1本だけmodel-call上限で出力前停止し未採用。敵対レビューがsingle-use 4 nodeと冗長golden 14行を実装前後で削った。
- duration重み割付はD1019で既に利得0.0秒と不採用。job数を増やしてcritical conflict componentを分けたふりにしない。
- 一次資料は`output/insights/2026-08-28_t1933-acceptance-longest-node/`。

## 次の一手差分

### 更新

- [T-1933] **P1**: 受入の床を決める最長単体処理を短くする。T-080のprocess-memo groupingはpaired K=3中央値244.810→245.707秒（+0.37%、変化なし）で反証・撤去済み。次はfixed-tip full artifactのcritical workerで実際にwallを決める単体処理を特定し、その処理自体を短くする。
  base: 9bbe0554008ba25e21f3643030def27979f83361e0b704685aa96986863df9db
