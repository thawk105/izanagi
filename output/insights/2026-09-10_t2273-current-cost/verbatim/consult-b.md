## 総括

**数値分解は概ね正しい一方、最新6走の集合は更新されています。「候補なしで終了」は保留し、局所コピー重複1件の費用診断だけを親へ返すことを推奨します。採用可能な改善実装は、まだありません。**

本相談はread-onlyの静的検査と既存JSON/XMLの再集計のみです。ファイル書込み、新規性能測定、pytest実走はしていません。

### real：最新6走の範囲と「全走wall」

確認時点では、planが未完了として除外した `2f3d23288242db9879936059107ffd32` が3 shardとも完了していました。親と同じdirectory mtime順で選んだ最新6件は次のとおりです。全件で `selected == finished`、`pytest_rc=0` を確認しました。

| run先頭 | 最大shard wall | 最大worker占有 | 最後1workerのtail | suite時刻の包絡 | 最後に終了するshard |
|---|---:|---:|---:|---:|---:|
| 2f3d232882 | 397.021 | 272.355 | 2.610 | 445.516 | 2 |
| aa816b219e | 336.325 | 247.270 | 5.624 | 336.325 | 0 |
| 01a5db37cc | 338.828 | 247.009 | 5.100 | 340.834 | 0 |
| 549722180c | 345.937 | 240.058 | 6.744 | 401.662 | 2 |
| b3031f5eb2 | 349.854 | 235.038 | 7.666 | 349.882 | 0 |
| f88a815b9f | 320.826 | 233.707 | 3.801 | 395.637 | 2 |

単位は秒。最大shardはすべて0、最大占有と最後のworkerはgw8、次点はgw9、gw8は2 itemでした。一次資料は[受入成果物root](/work/1/SFC/tanab/.izanagi-acceptance-shards/)配下の各 `shard-{0,1,2}/report.json` と `junit.xml`、追加完了分は[report.json](/work/1/SFC/tanab/.izanagi-acceptance-shards/2f3d23288242db9879936059107ffd32/shard-0/report.json)です。

旧6件の占有・tailも再計算で一致しました。したがって旧表の計算誤りではなく、**観測集合の更新**です。

[brief:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-current-cost/brief.md:2)の320.826〜349.854秒は、旧集合の最大shard所要時間です。受入全体の待ち時間と呼ぶのは不正確です。開始時刻がずれるため、shard-0短縮がsuite包絡を縮めない走もあります。包絡にも投入前の待ちは含まれず、shard間時計の比較限界があります。

### refuted：planが占有・tail・D104を混同している

この攻撃は成立しません。

- [plan:65](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/output/insights/dev-wave-t2273-current-cost/plan.md:65)は、他worker・割当・前後処理を固定した条件付きで `min(δ, tail)` としています。最大占有全体を短縮可能量とはしていません。
- 観測tailはworker終了時刻の最大と次点の差です。未実装prewarmの非重複tailではありません。更新後の範囲は2.610〜7.666秒です。
- `worker_occupancy`は[report durationの加算](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/tools/acceptance_shards.py:929)であり、CPU実作業量でもfixture構築費でもありません。新完了走のt080 nodeは243.176秒、同居nodeは29.179秒で和が最大占有と整合しますが、割当の直接証拠ではありません。
- planはD104充足を主張していません。既存6走にはA-B/B-Aも変更機構の直接発火観測もなく、**改善の採否証拠には使えません**。
- [現行履歴走査](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/campaign/t080_freeze_migration.py:1145)は安価なraw diffを先行します。D104当時の「約80秒が履歴検証」は現行費用へ転用できません。

### real：終了判断の前に残る診断1件

**scope内の診断候補は、fixture構築時の「後で上書きされる現行sourceコピー」の実作業費用に限定します。効果確認済みの実装候補とは扱いません。**

[初期copytree](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:1002)はorchestrator全体をコピーし、その後[historical basis復元とoperational配置](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:1051)が一部を上書きします。[復元helper](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:555)はGit blobを書き込みます。**上書き前のコピーが存在することはreal、そこを省いて有意に速くなることは未実測**です。runtime source配置やconsumer用private copyまで重複扱いしてはいけません。

既存[phase plugin](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measure/phase_plugin.py.txt:71)はhelper・copytree・subprocessの実呼出しを包みます。現行費用を再診断する入口はあります。ただし、次の限界があります。

- 元の用途は`-n 0`。serialのmemo再利用状態を48 workerの費用へ外挿できません。
- 子Python内部は観測されません。[子の起動](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2273-current-cost/orchestrator/tests/test_s8b_oracle_driver.py:1237)は`-I -B -c`であり、親側wrapperは内部へ伝播しません。
- copytreeと入れ子helperのdurationを足すと二重計上します。現状のpluginだけでは、上書き対象ファイルのcopy発火数・bytesを直接切り出せません。

### 推奨次手・未実測

親は計算ノードで`tools/run_tests.py`を通し、まず既存pluginによる現行の冷えたfixture構築のphase診断を行う。コピー費用に見込みがある場合だけ、別authorへ**上記重複コピーの回数・bytes・区間を観測する使い捨てprobe**を委譲するのが最小です。新しい恒久gate・検査・台帳・一般化は不要です。

その診断で見込みが残った場合に限り、同じ1件を実装候補として扱います。省略対象の同定と失敗挙動、fixture bytes・正負の受理/拒否・production呼出しを保持できることを確認し、同一allocationのA-B/B-Aで実発火減少と最大worker・shard wallを測る必要があります。単独nodeの短縮だけで受入全走の効果を認定してはいけません。

明示的validateやverify反復の削除、prewarm・共有cache、所有外conftest変更は今回の候補から除外します。**診断で費用が小さい、意味保存ができない、またはpaired比較で効果が出ない場合は、実装を残さず閉じる**。現時点で言えるのは「採用根拠が未成立」であり、「scope内の改善が不可能」ではありません。