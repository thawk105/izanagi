## 総括

**NO-GO（比較driverの修正待ち）、must-fix 1件。** productionの受理述語を弱める変更は、静的監査では見つかりませんでした。

比較起点 `b2037abf` から対象2ファイルは計719行追加／19行削除。回収commit `30fe5cc3` 自体はテストselectorの7行置換のみで、production変更なし。別途117行の比較driverを監査しました。

テスト・変異・性能測定は**未実走**です。authorの未受理報告を成功証拠には数えていません。

## 所見

1. **real／中／must-fix：同じtimeout結果でも比較driverが成功する。**
   [ab_compare.py:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2686-recovery-codex/ab_compare.py:113)の成功条件は、canonical一致・main一致・旧＞新process数だけです。

   静的な再現経路は、候補探索後の共通処理`git cherry`が各走でcommand timeoutになる場合です。[check_branch_landed.py:2073](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/tools/check_branch_landed.py:2073)はこれを捕捉し、観測に`assessment-timeout`を記録して処理を続けます。ほかのpayloadが一致しprocess数が減れば、4走ともtimeoutを含んだままdriverはrc=0になります。

   **影響：** 「正常完走時のpayload一致」の受入証拠として、不完了の比較を成功扱いできます。productionのlanded判定を直接弱める問題ではありません。
   **最小修正：** driver内で各走のtimeout・実行／parse失敗を判別し、正常完走比較の成功条件へ含める。raw成果物は残す。意味上の`indeterminate`や仕様上の観測省略を一律拒否する必要はありません。

2. **real／低／非阻害：親裁定のargv説明に算術誤り。**
   [s4-adjudication.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2686-exact-state-union-walk/s4-adjudication.md:21)の「固定argv約400 B＋env約300 Bを足しても1/2未満」は、`65,536 + 700 = 66,236 > 131,072 / 2`なので成立しません。
   **影響：** 閾値の説明の誤りで、候補受理条件への直接影響はありません。**最小修正：** 「path部分を64 KiBに制限し、残りを固定費等に充てる」へ説明を訂正。

3. **refuted／阻害なし：期待値変更・証拠削減による回収。**
   実差分は`log`条件の追加だけで、walk期待値0/1、hot path除外、timeout原因・例外同一性・再走査回数のassertionは維持されています。

   productionでは初出順のdistinct commit集約、親別entryのname合併、`limit+1`件と上限判定前の正証拠照合を保持。root・rename・gitlink用オプション、bytes処理、旧per-path fallbackもあります。負判定のclosed-world条件、parse失敗・timeoutのindeterminate経路に弱体化は見つかりませんでした。ただし全DAG・全設定での候補列同一性を証明したという意味ではありません。

## 根因対応表

| 項目 | 判定 | 根拠・限界 |
|---|---|---|
| 観測selector混同 | **closed（静的）** | [test_check_branch_landed.py:2382](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2382)で`diff --name-only`を除外。期待値・assertion不変。370 pass／3 failは親報告で、今回の実走結果ではない。 |
| timeout注入 | **closed（静的）** | [同:2430](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2686-recovery-codex/orchestrator/tests/test_check_branch_landed.py:2430)の注入・捕捉と偽Gitの対象がunion logで一致。再走査deadline検査も維持。発火確認は親の実走待ち。 |

時間内完走集合の同一性、時間の非退行、一般的な高速化率は、この監査から主張できません。
