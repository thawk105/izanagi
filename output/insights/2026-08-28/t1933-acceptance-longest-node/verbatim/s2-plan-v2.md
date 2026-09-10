## 総括

判定は「意味のある共有化候補なし」です。plan v2は実装0 byteとし、author段へ進めません。

共有化できそうな最大1原因は、snapshotごとのGit ignore規則取得です。しかし、共有するとlive repo再観測またはoptimized/reference独立性を失います。安全条件を維持したまま共有できる範囲も、固定slice全体や最長nodeへ意味のある効果を持ちません。

## baselineによる前提更新

- 確定baselineは4 passed / 147.55秒ですが、これは提供済み結果であり、本段でtestは実走していません。[baseline-argv.md:17](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/baseline-argv.md:17>)
- snapshot両nodeは4.18秒と2.61秒、合計6.79秒です。旧ledgerの79秒と50秒は効果gateに使用できません。[baseline-argv.md:19](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/baseline-argv.md:19>)
- T-080本体2 nodeは86.57秒と51.93秒、合計138.50秒で、固定sliceの93.9%を占めます。
- snapshot両nodeを仮に全消去しても、owned slice wallの理論上限は6.79秒、4.60%にすぎず、固定slice最長86.57秒は変わりません。実際に共有可能なのはnode全体ではなく規則取得の一部なので、実益上限はさらに小さくなります。
- acceptance全体最長はscope外の140秒nodeです。[acceptance_duration_ledger.json:8185](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/acceptance_duration_ledger.json:8185>) したがってsnapshot短縮は全体最長にも影響しません。

## 現物のコスト境界

検討した1原因は、`git_ignored_output_snapshot_rules()`の反復実行です。

- helper自身が、末尾の`git ls-files -o -i`でsnapshot時点の実在状態を観測するため、process内memoを意図的に禁止しています。[output_snapshot_ignores.py:206](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/output_snapshot_ignores.py:206>)
- floor optimized版とreference版は別々に規則を取得します。[test_s8b_floor_campaign.py:1647](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1647>) [test_s8b_floor_campaign.py:1676](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1676>) 対象nodeも変異の前後で両実装を再実行します。[test_s8b_floor_campaign.py:1736](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1736>)
- T-080 snapshotも呼出しごとに規則とtreeを再観測します。[test_s8b_oracle_driver.py:562](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:562>) 対象nodeには前後4回のsnapshotがあります。[test_s8b_oracle_driver.py:613](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:613>)
- 規則取得だけを共有しても、floorのtree walk、digest、referenceの独立した`rglob`は残ります。[test_s8b_floor_campaign.py:1619](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1619>) [test_s8b_floor_campaign.py:1656](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1656>) [test_s8b_floor_campaign.py:1682](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1682>)
- T-080本体では、defaultと`distinct_basis_blob=True`が別cache keyです。[test_s8b_oracle_driver.py:909](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:909>) [test_s8b_oracle_driver.py:1371](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1371>) 両者の共通prefixを再利用する案は除外済みのvariant統合に当たります。production履歴走査が真の律速であることも確定authorityに明記されています。[authority-v2.md:20](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/s2/authority-v2.md:20>)

したがって、この1原因は安全性gateと効果gateの両方を通りません。

## plan v2

1. 対象2 test file、直接helper、productionを変更しない。実装差分は0 byte。
2. snapshot規則のcache、optional引数、optimized/reference間の値源共有を導入しない。
3. T-080 base共有の拡張、異なる`distinct_basis_blob` variantの共通化、node grouping、case縮小を行わない。
4. 段5 author、after timing、変更後testへは進まない。baselineは効果不成立の根拠としてのみ保持する。
5. 受理nodeid集合、順序、固定argvは現状のままとする。[baseline-argv.md:6](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/baseline-argv.md:6>)

## 検出力と変異

0 byteなので、以下の検出力はそのまま残ります。

- floor snapshot: `runs`配下を除外し、`runs-visible`の追加をoptimized/reference双方が検出します。[test_s8b_floor_campaign.py:1736](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1736>)
- reference独立性: optimized関数、walk、digestをpoisonしてもreferenceだけで期待値を導出します。[test_s8b_floor_campaign.py:1815](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1815>)
- T-080 snapshot: ignored変異を除外しつつ、prefix衝突する`runs-visible`を検出します。[test_s8b_oracle_driver.py:613](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:613>)
- draft-finalize node: fixture固有basis変異、held-marker失敗、HELD解除、receipt削除後のmalformed分類を独立に検査します。[test_s8b_oracle_driver.py:1078](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1078>) [test_s8b_oracle_driver.py:1383](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1383>) [test_s8b_oracle_driver.py:1449](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1449>)
- ccbench-current node: checkout-only不一致と、そのgitlinkをcommitした状態を別々に観測し、最終的に単一exact reasonを要求します。[test_s8b_oracle_driver.py:1481](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1481>) [test_s8b_oracle_driver.py:1520](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1520>) [test_s8b_oracle_driver.py:1534](</work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1534>)

本段では変異実走もtest実走もしておらず、新たな緑は報告しません。

## blockerとscope外

実装上のblockerではなく、効果不成立による正常終了です。意味のある短縮には、確定authorityが真の律速とするproduction履歴走査か、棄却済みのT-080共有方式へ踏み込む必要があります。

duration ledger、runner、conftest、production、T-1934残差、T-1938の共通helper分離はscope外です。Web、書込み、旧plan参照は行っていません。
