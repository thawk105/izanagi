焦点再レビューの結論は、production correctness の2件は closed、台帳は regressed、mutation proof は partial です。新規の独立 must-fix はありませんが、proof-chain はまだ受理不可です。追加テストは実走していません。

| 前 review の must-fix | 判定 | 根拠 |
|---|---|---|
| post-provenance D987 時系列 | closed | [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1634) は `preflight → D987 → provenance → preflight → D987` を固定し、初回通過・2回目だけ拒否、permanent/release-safe、main不変まで確認する。初回2回呼出しやpost-recheck削除の変異では通らない。 |
| active fold の release-safe分類 | closed | [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:7819) がactive planとfinal-main mismatchを重ね、`release_safe=False`、`retryable_same_request=False`、provenance非実行、fold非再開、main不変を固定している。 |
| 旧7／新13 nodeid台帳 | regressed（新側はclosed） | 新nodeidは登録された一方、現在のsourceに存在しない台帳項目が少なくとも10件残る。land旧名1件 [ledger](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/acceptance_duration_ledger.json:5118)、hold-contract旧param ID 7件 [ledger](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/acceptance_duration_ledger.json:6577)、旧関数名2件 [ledger](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/acceptance_duration_ledger.json:6609)。`nodeid_count=17649`はJSON内件数とは一致するが、現collectionとのexact一致を示さない。 |
| mutation preregのanchor／失敗node集合 | partial | [mutation-prereg.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/mutation-prereg.md:3) はprobe-first、完全観測集合、helper内scope、post-recheck callsite、存在/type guard分割へ改善された。ただしfinal anchor commit、一意性確認結果、観測node集合、KILLED本走結果は未記録で、記述も未来形のまま。 |

F57 hold自体は適切です。[flaky_test_holds.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/flaky_test_holds.py:200) は完全nodeid 1件だけを登録し、`F57`と`t-1079`へ束縛しています。live contractも、登録行数・exact key・digestを固定する[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_flaky_test_holds_contract.py:294)と、live summaryの件数・digestを固定する[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_flaky_test_holds_contract.py:989)を備えています。

未解消時の影響:

- 台帳: 存在しない10 nodeidが受理対象に残るため、exact nodeid coverage／所要時間台帳を成果物proofとして参照できません。
- mutation: production受理集合への直接変更はありませんが、B-057のmutation proofを成果物受理根拠として参照できません。

## 総括

post-provenance再照合、active-fold lease保持、F57 exact hold、live registry contractには修正後の退行を見つけませんでした。親実測の「launcher 24 passed、land 299 passed / 1 held skip、hold contract 37 passed」は所与のまま扱っています。

一方、台帳にはstale nodeidが残り、mutationはprobe手順の改善に留まって実測proofが未完成です。したがってproduction実装は裁定整合、proof-chainとしては受理不可です。