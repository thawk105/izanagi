## 実装した file と構造 (関数・node)

[test_t2630_scan_boundary_reach.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2630-scan-boundary-reach-probe/orchestrator/tests/test_t2630_scan_boundary_reach.py) のみ新設しました。

独立 clone・同一 worktree で reference/current を観測し、実 resolve、TU 前処理、追加観測、証拠保存を実装。例外は段階別に保持し、node の call 内で失敗させます。

## 自己検査の結果 (collect-only の node 一覧、8 変異の git apply --check 結果)

`py_compile` 成功。collect-only は次の 4 node を収集しました。

- `test_stock_identity`
- `test_variant_identity`
- `test_stock_owner_tu`
- `test_variant_owner_tu`

未変異 template、M0、M1、M2、M3a、M3b、M4、M4b、M6 の `git apply --check` はすべて rc=0。

common-dir の path・inode の独立性と、未登録 node 文脈での実 guard 通過も確認しました。

## 実走していないこと

baseline・変異 runner、configure、TU 前処理、object 生成は未実走です。4 node の PASSED や変異の到達は未確認です。

## 波及可能性 (所有外 caller・共有 fixture・meta-test)

既存 tracked file の差分はありません。共有 fixture・登録 literal・製品 caller は未変更です。meta-test は未実走。probe を含む全体収集では、この 4 node も対象になります。

## 総括

指定の 1 file を実装し、自己検査を完了しました。commit・push はしていません。計算ノードでの本走は親へ引き継ぎます。