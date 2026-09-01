## 総括

- [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/orchestrator/campaign/b10_backoff_shape_sweep.py:2800)
  - `DurableRootPolicy.forbidden_roots` を `(Path("/tmp"), Path("/scr"))` に変更。
- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/orchestrator/tests/test_b10_backoff_shape_sweep.py:1568)
  - 負例は実際の `/tmp` 配下を official root に設定し、実 `write_capability_for_directory` が `candidate が forbidden root 配下` で拒否することを確認。
  - 正例は `/var/tmp` 配下の外部 root が同じ実経路を通り、write capability を取得できることを確認。
  - 既存 M2 正例は期待値を変えず、一時 repository を `/var/tmp` に移して新しい禁止規則と整合させた。

実走した pytest nodeid はありません。次の15 nodeを `tools/run_tests.py` 経由で2回に分けて要求しましたが、両方とも `qstat -Q preflight rc=1`、`rc=16`、`child_started=false` で停止しました。

- 新規 A5 負例・正例、既存 `test_t1905_m1_*`、`test_t1905_m2_*`、`test_t1905_m3_*`、`test_formal_campaign_layout_and_writer_share_resolved_root_and_policy`
- shell 契約 node
- `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `test_ccbench_spawn_sites.py` の参照 inventory 2 node
- `test_condition_meaning_gate.py::test_patch_target_decoder_and_fixture_holes_are_independently_anchored`
- `test_official_perf_closure.py` の consumer 2 node
- `test_p3_build_authority_cli.py` の consumer 2 node

非pytest検査は以下が成功しました。

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0
- 変更Python 2ファイルの AST parse: 成功
- 禁止された判定面・正しさゲート名に対する追加削除行: なし

A1、A2、A3、A4、A6、A7、およびレビューBの cohort ID 所見には手を出していません。段5から存在した shell 差分と未追跡 insight にも触れていません。テスト wrapper が生成した2つの一時 dispatch receipt directoryだけは除去しました。

未解決は pytest 全体が未実走である点です。したがって「実装済み・未実走」であり、`closed` とは申告しません。commit も作成していません。