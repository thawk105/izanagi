| 再検査項目 | 判定 | 現物確認 |
|---|---|---|
| 旧7／新13 nodeid台帳 | **closed** | source の全 `test_*` と parametrize ID を静的展開。launcher **24/24**、land **300/300**、hold-contract **37/37**で、missing/stale は各0。旧stale 10 keyも再検出0。[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_acceptance_launcher.py:175)・[land](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:957)・[hold-contract](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_flaky_test_holds_contract.py:294) |
| mutation proof | **partial** | 事前登録はprobe-firstだが、final anchor後のprobe、観測node集合登録、KILLED本走はいずれも未了。[mutation-prereg.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/mutation-prereg.md:3) |

source key 検索による攻撃でも反証はありませんでした。対象3ファイルに `pytest_generate_tests` や動的テスト登録はなく、全parametrize suffixを含むsource集合がledger集合とexact一致しています。

HEAD対現行ledgerの直接比較でも、対象外は **17,278→17,278**、追加0・削除0・共通keyの値変更0でした。現行実エントリ17,639と `nodeid_count=17639` も一致しています。[ledger](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/acceptance_duration_ledger.json:17643)

新規must-fixはありません。既知のmutation partialにより、B-057 mutation proofだけは引き続き成果物受理根拠として参照不可です。指定どおりテスト/JUnitは再実走していません。

## 総括

前回の台帳regressed所見は **closed** へ更新できます。対象3集合のsource-level exactness、旧stale 10件の消滅、対象外17,278 key/value不変を現物で確認しました。mutation proofのみ **partial** のままです。