## 総括

**指定の停止条件に該当するため、編集前に停止しました。** B の変更・test 関数の削除は **0 件**。commit 操作もありません。

T-126 の付け替えには、単位 C 所有の [test_t126_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-b-shell/orchestrator/tests/test_t126_pegasus_tools.py:4573) の更新が必要です。

- `_attempt` / `_submit_fixture` は staging root 外に依存を作り、旧 policy locator を設定しています。
- `_install_job_dependency_marker` は旧 locator に対する `git rev-parse HEAD` を監視します。
- `test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value[canonical]` は、その監視 marker と旧 path の診断を要求します。shell を新 root に切り替えるとこの契約が成立しません。

これは静的に確認した波及です。所有外テストは変更していません。

実走結果は `test_plain_runner_coverage.py` の次の全 3 node、**rc=0** です。

- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_this_metatest_is_itself_self_runnable`

**付け替え済み job body・解決変数：なし。** 15 本すべて未変更です。現行の受理・拒否挙動も変更していません。予定する変更は source の出所だけを staging root 配下へ移し、HEAD・dirty・存在検査を維持するものです。

期待赤 4 file は未実走で、実際の赤との突き合わせは未実施です。実走した meta-test に赤はありません。その他の契約テスト、実 job、計算ノード走行、build、README 更新も未実施で、**closed ではありません**。T-126 の共有 fixture・監視 helper を C 側で対応する必要がある点が停止理由です。