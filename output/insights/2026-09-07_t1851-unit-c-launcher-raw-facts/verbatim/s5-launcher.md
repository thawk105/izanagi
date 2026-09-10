C1a の raw facts 面を実装しました。v2 sealed evidence API など C1b の範囲には触れていません。

主な変更:

- [launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-launcher/orchestrator/campaign/s8b_floor_attempt_launcher.py:62)
  - reservation に protocol、mode、perf receipt、marker を追加。
  - v2 と marker を副作用前に専用署名で拒否。
  - protocol digest、mode、receipt由来 `use_perf`、`reps` を一括検査。
  - launcher 固定 classification authority を導入し、public API の注入引数を削除。
  - pre-probe、capture例外、post-probe、open例外を terminal 経路へ統合。
  - launcher 私有 rep sink を open 後に snapshot。
  - probe result を exact 4-key/typeで検査。
- [launcher tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-launcher/orchestrator/tests/test_s8b_floor_attempt_launcher.py:731)
  - M1〜M12 の指定名 node を追加。
  - marker forwarding、mode、official perf、nested callable の下層直接検査も追加。
  - fake token を `ScalePoint` 同形へ更新。

検査結果:

- launcher 全29 node相当を test関数 direct-call: 29 passed / 0 failed。
- spawn-site在庫とtest-file列挙 meta: 4 passed / 0 failed。
- `py_compile`: passed。
- `tools/check_codex_agents.py`: passed。
- `tools/check_docs.py`: passed。
- pytest wrapper は2回とも `qstat -Q` preflight rc=1、child未起動、rc=16。したがって pytest と自走 harness は未実走です。

所有外への波及:

- `s8b_attempt_registry.py` は launcher が importする adapterであり、既存 `consumption_marker` 引数へ明示転送します。変更なし。
- `test_ccbench_spawn_sites.py:212` の `_owned_post_probe: 1` pin は不変で、直接検査済みです。
- production caller は引き続き0件。C2で接続する際は reservationの新4 fieldとpublic API変更への追随が必要です。
- 共有fixture、consumer test、docsは変更していません。

## 総括

- 変更: launcher +220/−35行、launcher test +400/−37行。
- 新設test: 17 node、総数29 node。
- direct-call: launcher 29 passed / 0 failed、meta 4 passed / 0 failed。
- pytest: child未起動のため0 passed / 0 failed、未実走。
- 所有外変更なし。commitなし。
- 未実装: C1b、C2、D2は契約どおり対象外。