## 修正内容

- F1/F2: body 分類を分離し、正準 TU の compile/run finding を `UNAVAILABLE` に変更しました。[sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix1/orchestrator/campaign/sort_swo_oracle.py:596)
- F3/F4: auditor veto と旧 oracle 説明を現行保証へ修正しました。[auditor.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix1/.claude/agents/auditor.md:60)
- F5/F8/F9/F10: public rejection、権威15件の admission、旧保証文言不在、恒真 compile assertion を修正しました。[test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix1/orchestrator/tests/test_sort_swo_oracle.py:310)
- F6: critic に exact rule/stage 射影と表示を追加しました。[digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix1/orchestrator/critic/digest.py:292)
- F7 の ledger は指示どおり未変更です。commit も実行していません。

## 検査

指定 full file は数分空けて2回実行しましたが、いずれも `qstat -Q preflight rc=1`、child 未起動の `rc=16` でした。したがって実走件数は 0 で、104件維持は確認不能です。

focus node と meta-test も同じ `rc=16` でした。実装済み・未実走です。

軽量 probe では、受理集合 79/79、権威集合 15/15、F1 は `sort-ir.expression-shape.v1`、F5 の2例は `REJECT sort-ir.envelope.v1` を確認しました。7 Python file の AST parse と `git diff --check` は成功しています。

## 波及可能性

- 所有外 caller: P3 は `UNAVAILABLE` を attempt-infra として停止、S1 は retryable prepare failure として扱います。PASS への倒し込みはありません。
- 共有 fixture: `_get_oracle_environment`、compiled artifact memo、consumer registry。nodeid の新設・改名はありません。
- consumer: WAL attempt record、critic material rendering、receipt/contract identity。checker source変更に伴う current contract ID literalは独立再計算値へ追随済みです。
- `docs/`、禁止4 production file、ledger、`s6_sort_sweep.CANDIDATES` は未変更です。

## 総括

1. F1〜F6・F8〜F10を裁定どおり修正し、F2は正準IRの全findingを候補REJECTから分離しました。  
2. 指定full fileは2回ともrc=16・child未起動で、104件の実走確認はできませんでした。  
3. 未実走はfull file、focus node、consumer inventory/ledger meta-test。残赤は観測されていません。  
4. 波及先はP3/S1、oracle共有fixture、WAL/critic/receipt consumerです。F7 ledger更新は親の実測待ちです。