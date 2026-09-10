## 総括

**今回は候補なしとし、診断結果で閉じることを推奨します。** 最新完了6走ではt080の1 nodeが最大worker占有の約88%を占めます。しかし、そのworkerだけを短縮してwallへ反映できる余地は、他workerの終了時刻を固定すると **3.801〜7.666秒**です。規律2を維持した局所的な重複作業削減について、効果を見込める1件を今回の静的解析では確定できませんでした。

親の「最大shard wallは320.826〜349.854秒、最大占有はgw8の233.707〜247.270秒、各2 item」は独立検算で一致しました。ただし、これは**受入投入から完了までの経過時間ではありません**。

### 完了6走の検算結果：観測事実

一次資料は[受入成果物root](/work/1/SFC/tanab/.izanagi-acceptance-shards/)配下の各runの `shard-{0,1,2}/report.json` と `junit.xml`。3 shardの成果物が存在し、`selected` と `finished` が一致する走を選びました。対象18 shardはすべて `pytest_rc=0`、JUnitのfailure/errorは0でした。

確認時点で未完了の `2f3d232882…` と `af9701ff22…` は除外しました。

単位は秒。tailは「gw8終了 − 他workerの最終終了」で、全6走とも相手はgw9です。

| run先頭10桁 | shard-0 wall | shard-1 wall | shard-2 wall | gw8占有 | 非重複tail |
|---|---:|---:|---:|---:|---:|
| aa816b219e | 336.325 | 211.511 | 207.431 | 247.270 | 5.624 |
| 01a5db37cc | 338.828 | 209.134 | 207.180 | 247.009 | 5.100 |
| 549722180c | 345.937 | 228.732 | 206.444 | 240.058 | 6.744 |
| b3031f5eb2 | 349.854 | 209.365 | 224.652 | 235.038 | 7.666 |
| f88a815b9f | 320.826 | 205.051 | 202.579 | 233.707 | 3.801 |
| 1f198f2d42 | 325.161 | 200.729 | 204.013 | 241.728 | 4.688 |

各shardの開始時刻は一致していません。JUnitのtimestampとtimeから計算した「最初のsuite開始から最後のsuite終了まで」は、表の順で **336.325 / 340.834 / 401.662 / 349.882 / 395.637 / 452.042秒**です。最後に終了するshardも順に0 / 0 / 2 / 0 / 2 / 1でした。この包絡時間にも投入前のキュー待ち等は含まれません。

### 最大workerの構成：時間和による推定

占有は各nodeのsetup・call・teardownのdurationを合算したものです。[集計コード](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/tools/acceptance_shards.py:929)ではworker別の開始・終了境界も記録しますが、nodeとworkerの対応自体はreportに保存していません。

そこでJUnit全itemから、丸め誤差を許容してgw8の占有に一致する2 itemの組を列挙しました。**6走すべてで一致する組は1組だけ**でした。

- `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`
- `test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[use-reported-eligible]`

| run | t080 node | 同居node | 和 |
|---|---:|---:|---:|
| aa816b219e | 217.835 | 29.435 | 247.270 |
| 01a5db37cc | 217.143 | 29.866 | 247.009 |
| 549722180c | 210.241 | 29.817 | 240.058 |
| b3031f5eb2 | 205.450 | 29.588 | 235.038 |
| f88a815b9f | 204.207 | 29.500 | 233.707 |
| 1f198f2d42 | 212.191 | 29.537 | 241.728 |

これは強い数値的整合であり、worker割当の直接観測ではありません。また、t080 nodeの204〜218秒をfixture構築費だけと解釈することもできません。

### 非重複tailと残余

最新走のshard-0は、既存時刻から次のように分解できます。

| 区間 | 秒 |
|---|---:|
| suite開始 → 最後のworker collection完了 | 53.245 |
| collection完了 → 最初のtest開始 | 29.015 |
| 最初のtest開始 → gw9終了 | 241.649 |
| gw9終了 → gw8終了 | **5.624** |
| gw8終了 → suite終了 | 6.793 |
| 合計 | **336.325** |

最初のtest開始から最後の終了までとgw8占有との差は約0.003秒です。全6走でも同差は約0.003秒にとどまります。

`wall − 最大占有` は83.433〜114.816秒ですが、これは独立な床でも除去可能量でもありません。collection前後と終了処理などが含まれる残余です。fixture内部のbuild・copy・子process・待機の各区間は既存資料から分離できません。gw8の記録済みreal-repo lock区間は空ですが、他の待機がない証明にはなりません。

**条件付き予測：**

- gw8だけをδ秒短縮し、他worker・割当・前後処理を固定すると、shard wallの短縮は `min(δ, 非重複tail)`。観測6走では最大3.801〜7.666秒です。
- shard-0を300秒未満にするには20.826〜49.854秒超の短縮が必要です。gw8単独の改善では届きません。
- 共通fixtureの改善なら他の上位workerにも作用し得ますが、共通部分の時間と実発火回数が未観測なので短縮秒数は見積もれません。

### 現行コードからの採否

| 読んだ箇所 | 判断 |
|---|---|
| [process内memoとprivate copy](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:868) | 引数別memoは既存。consumerは破壊的変異を行うためprivate copyを共有物へ置換できません。build回数とcopy費用は今回未観測です。 |
| [fixture構築](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:987) | 現行source配置、historical basis復元、runtime source配置には別の役割があります。上書きされるコピーはありますが、失敗挙動まで保つ局所変更と有意な費用を確定できません。 |
| [draft・validate・finalize・verify・gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:1190) | `finalize_receipt`も内部で[validate_draftを呼びます](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/campaign/t080_freeze_migration.py:2035)。ただし明示的validateの削除は、検査呼出しと反復時の検出機会を減らすため採用しません。 |
| [ccbench-current分岐](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:1458) | held/releasedの正例、checkoutだけの不一致、commit済みgitlink不一致を別々に検査しています。verifyの反復を不要な重複とは扱えません。 |
| [約30秒の同居node](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_holdout_freeze.py:2173) | earlier/selectedの実run構築とeligibility導出、public candidate builderの拒否確認があります。検査を保って削れる処理は、この読取範囲では確定できません。 |

また、[現行の履歴走査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/campaign/t080_freeze_migration.py:1145)は安価なraw diffを先行し、必要時だけ再走査します。`--find-copies-harder`は使いません。**D104の採否条件は維持しますが、当時の「約80秒が履歴検証」という費用内訳は今回の説明には使えません。**

### 未実測と終了判断

今回行ったのは既存成果物の読取・集計と静的解析だけです。新規実装、probe、harness、テスト、成果物ファイルは作成していません。pytest実行や新たな性能効果は報告しません。

候補を選定していないためA-B/B-Aへ進める変更はありません。**安全な短縮が不可能と証明したのではなく、許可された範囲で実測へ渡せる候補を確定できなかった**という診断で閉じることを推奨します。