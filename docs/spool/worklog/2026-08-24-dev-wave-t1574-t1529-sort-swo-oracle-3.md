---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1574-t1529-sort-swo-oracle
seq: 3
title: sort SWO oracle の再有効化を強い capability 隔離まで停止した (docsのみ、branch worktree-dev-wave-t1574-t1529-sort-swo-oracle、実装差分ゼロ)
---

## 本文

- D696とユーザー指定のpre-sort snapshot pipe案を実装前に検査した。現行baselineはPegasus request `941852.nqsv`で`orchestrator/tests/test_sort_swo_oracle.py` 62 passed / 5.57秒だったが、共有Masstree cacheが`config.h/libjson.a/*.o`を持つ環境でありclean-source自立性は証明しない。
- 段2 plan、段3敵対相談2本、ユーザー再裁定後の段2b plan、段3b敵対相談2本を隔離Codexで実行した。段3b linkage初回はF45 output 0 byteで不受理、output-first retryで回復した。
- 同一TU案はcandidateがbaselineとpost frameを偽造でき、別TU案もpost pipe fd capabilityを共有するため防壁完了にならないと確定した。ユーザーは規律2を優先し、強いprocess/memory capability隔離まで再有効化しない推奨を裁定した。正本は{{D:sort-swo-strong-isolation-before-reactivation}}、失敗型は{{F:same-process-oracle-protocol-capability}}。
- A2、Masstree clean fixture、wire protocol、golden consumerの実装は行っていない。実装差分ゼロのため変異matrixは免除し、次waveは起動しなかった。

## 次の一手差分

### 更新

- [T-1574] **P1・ユーザー裁定済み、強い隔離設計待ち**: pre-sort pipeや別TUだけではcandidateのpost fd capabilityを分離できない。candidateがprotocol fdを一度も所有せず、実型snapshot対象memoryへのwriteを強制拒否・観測できるprocess/memory境界を設計・実証してから、A1/A2/environment修理とprotocol更新を同じ閉包で行う。正本={{D:sort-swo-strong-isolation-before-reactivation}}。
  base: 61184e871f5cc5874597a90d5e8069d03581128f29294d1e405ec49dabc34681
- [T-1529] **P1・強い隔離設計待ち**: `test_sort_swo_oracle.py`のMasstree build残骸依存は未修理。test-owned clean source fixtureと明示正負例は、corpus mutation防壁の強い隔離設計が確定した後に同じ閉包で実装し、実測前には再有効化しない。
  base: 6a817ae316cd3350227cecfdd7cf2a3a40b008fee29fa7e47fc0d163ff546df4
