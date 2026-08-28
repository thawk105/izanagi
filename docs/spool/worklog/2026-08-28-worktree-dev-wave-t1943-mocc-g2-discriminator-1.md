---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1943-mocc-g2-discriminator
seq: 1
title: [T-1943] MoCC G2 payload-lineage discriminatorを実装し、固定1-cellをno-g2で閉じた (code + tests + insight、branch worktree-dev-wave-t1943-mocc-g2-discriminator、変異5/5 KILLED)
---

## 本文

- 停止authorの外来差分を回収監査し、D95 Codex author、敵対review 2本、fix 3巡、実機/受入blocker fix、focus 3本を経て、実装/fix commit `d8a6410da`、`267741106`、`7cf109b6e`、`a97835f79`を作成した。CCBench local branchは`ae6880f7..e9e477ca`の2 commitで、pushしていない。
- TRACE=0 identity checkerは旧`058d0c4e`から`e9e477ca`まで16 context全一致。最初のacceptance 12赤はouter gitlinkのS8b freeze衝突11件とpytest-only allowlist漏れ1件で、freezeを変えずouter gitlinkをBASEへ戻し、local main submodule repoへ診断branchを移した。焦点走は200 passed / 2 skippedとS8b pin 1 passed。
- final固定HEAD `a97835f79`の変異はbaseline PASSED、事前登録5/5 KILLED、shared snapshot一致、teardown完了だった。
- request `956466.nqsv`の固定1 cellはTRACE=0 absence gateを通り、verifier clean/anomaly 0、専用discriminator `no-g2`を得た。結果依存の追加cellは投入していない。
- completed receipt公開前に計算ノードPython互換性でartifact classificationが停止したため、結果はnon-certifying raw observationであり、`output/insights/2026-08-28_t1943-mocc-g2-discriminator/RESULT.md`へdigestと主張上限を記録した。失敗は{{F:compute-path-stat-keyword}}。
- provenanceはouter履歴で新規違反0、既知54件。submodule履歴はIzanagi provenance導入commitを含まずpost-history監査不能で、commit前message検査だけが通った。
- 42-run再実行、一般replay、他CC展開、Silo対照だけの追加、性能値、upstream pushは実施していない。

## 次の一手差分

### 完了

- [T-1943] 固定1-cellでG2識別観測を行い、no-g2と主張上限を記録した。
  remaining: none
  base: c1725979e9137cac5bdb589d49a24fdcf2015bf206f125339a7cb489a5fbf77c
