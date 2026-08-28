---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: worktree-dev-wave-t2006-noncertifying-a1
seq: 1
title: [T-2006] 非認証成果物型とA-1投入器を認証経路と分離して実装した (code + tests + insight、branch worktree-dev-wave-t2006-noncertifying-a1、変異9/9 KILLED)
---

## 本文

- ユーザーの過剰ガードレール禁止を反映し、同一userの全bundle偽造はscope外、supported pathの事故防止だけを鍵・記録・schema・consumerの4層で閉じた。外部trust root、certified v2 cutoff、批准frameworkは追加していない。
- 実装/fix commitは`dd6ec73b9..fb7b8dbba`の5本。通常decoderが拒否する非認証lock、registered non-certifying projection、create-only intent/submission/completion、signed sidecar、exact viewをA-1へ結線した。
- 既存certified gate、v1/v2 lock、result/receipt schema、環境契約、source binding、trace/perf分離、anomaly rejectを維持した。`require_environment_contract=False`、skip、xfail、既存期待値の削除・反転は使っていない。
- D95 author初回はtoken上限で中断し、別authorが未監査差分を回収した。敵対review2本のreal7件、focusのqstat raw binding1件、親焦点赤をCodex fixで閉じ、最終focusはreal findingなし。
- 初回全受入は共有fixtureとexact process inventory未追随の4件だけが赤 (18,789 passed / 62 skipped)。4件とも本waveへ帰属させ、D95 authorがcreate-only intent、3 process site、non-certifying config/identity/eager layout順序へexact追随させた。production・gate変更、免除、期待値緩和はない。
- 変更7 test filesは711 passed、source closure/fig4/B-4 consumer meta testsは207 passed。修正後全受入はtested main`93fcb4663`、tested tip`0fad792a2`でchild-green、18,828 passed / 67 skipped、red/flake 0、loadgroup、log SHA`c55e830b...ebd1c`。checkerと全史provenanceはgreen。
- final tip`fb7b8dbba`の変異matrixはbaseline PASSED、marker/schema/tag/registry/COMMIT/artifact/anomaly/view/submit-onceの9/9 KILLED、expected node完全一致。
- 正式qsub、正式A-1測定、批准一般の再設計、D905/D906代替、push、次wave起動は行っていない。
- 一次資料は`output/insights/2026-08-29_t2006-noncertifying-a1/`。

## 次の一手差分

### 完了

- [T-2006] 非認証成果物型とA-1投入器を同じ変更単位で実装し、認証経路を緩めず昇格不能性を4層の負例で検証した。
  remaining: none
  base: f02ce24b629c9decbb76d36d9bd08ce62aa009c49fdd9c58915d9a06cc8fe63e
