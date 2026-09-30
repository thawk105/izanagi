許可された 3 ファイルに U1 を実装し、commit は作っていません。controller は `pytest_configure_node` で共有 session に同期参加し、可視 output の `result.json` 成功後に default と active-v2 の base を並列構築します。終了時は合計 900 秒を上限に thread を join し、error を回収して controller の lock を閉じます。T1〜T7 と、指定された既存 harness への patch も追加しました。変更箇所は [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/conftest.py)、[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/test_s8b_oracle_driver.py)、[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/test_real_repo_serialization.py) です。

変更前は非受入走で何も起きず、非絞り込みの受入 shard 実行では可視 output の写しだけが先行していました。変更後も非選択時は起動せず、選択時にはその写しの成功を待って 2 key の base を先行構築します。`workerinput` に key は追加していません。

**検査:** `py_compile`、T1〜T7 の AST 上の存在確認、`git diff --check` は通りました。実走できた test nodeid は **ありません**。`tools/run_tests.py` 経由で T1〜T7、`t080_shared_base or t080_visible_output`、`early_memo or memo_barrier`、`configure_node` を試みました。AST consumer/nodeid 固定、hold inventory、real-repo consumer 名簿、file 集合列挙の meta-test も試みました。いずれも Pegasus dispatch の `qstat -Q` preflight が `rc=1` となり、test child は起動していません。`-n 0` での再試行も同じ結果です。したがって全件 **実装済み・未実走** です。

所有外への波及として、AST consumer 名簿と実 repo 分類は `test_real_repo_serialization`、hold と file 集合は `test_hold_inventory`、configure 時の配線は `test_acceptance_schedule_order` が検査対象です。共有 fixture の import 利用者である `test_s8b_binding_driftguards`、`test_b4_binary_record`、`test_s8b_dependency_prefix_bridge` も親の実走で確認が必要です。

変異の静的見込みは、M1→T1（起動なし）、M2→T2（写し成功前の build）、M4→T4（builder error の破棄）、M5→T5（非選択時の起動）です。各期待 node は当該機構を直接見ており、別層の拒否による mask は見込みません。M3→T3 は controller 参加と木の寿命を直接見ますが、変異の具体形によっては T1 も赤になり得ます。M6→T7 は base と consumer copy の実体を比較しますが、既存の copy 独立性 test も赤になり得ます。**期待 node だけが赤になることは、未実走のため確定していません。**

## 総括

U1 の実装と T1〜T7 の追加は完了し、未 commit です。
test は dispatch 障害により全件未実走です。
主な残る危険は、実走でのみ分かる test・meta-test の失敗と、M3・M6 の赤 node の重複です。