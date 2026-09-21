**F3 / F4 / F5 は実装済み・未実走です。F1 は差し替え範囲の確認待ちで未完了です。** テスト実行・commit・docs 編集はしていません。

1. 所見ごとの対応

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | 未着手 | 参考 fixture は指定された 2 種以外にも checkout・site・layout・condition gate 等を差し替えます。この準備用差し替えを許容するか確認中 |
| F3 | closed（未実走） | [test_b5_tier0.py:300](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/tests/test_b5_tier0.py:300)：pytest 自走入口を追加 |
| F4 | closed（未実走） | [p3_s4_loop.py:2364](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py:2364)：Tier0 前の追加認可呼出しを削除 |
| F5 | closed（未実走） | [p3_s4_loop.py:2012](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-a1/orchestrator/campaign/p3_s4_loop.py:2012)：ReviewReceipt の import・分岐・引数を削除 |

2. 変更ファイル

上記 2 ファイルのみです。本番の変更関数は `_b5_tier0_build_inputs` と `_run_one_iteration_resolved`。既存テストの期待値、参照専用ファイル、F2 は変更していません。

3. 静的検査

| 実行した検査 | rc |
|---|---:|
| `python3 -B - <<'PY' … PY`：変更 2 ファイルを `compile(..., "exec")` で構文確認、HEAD と本番関数 AST を比較 | 0 |
| `git diff --check` | 0 |

AST 比較でも本番の変更は上記 2 関数だけでした。bytecode は生成していません。

4. meta-test の影響

静的確認の結果です。meta-test 自体は実行していません。

- `test_ccbench_spawn_sites.py`：process／gateway 目録、build sink、condition gate の先行関係は変更なし。
- `test_s8b_floor_campaign.py`：新しい `"--build"` 字面なし。build の admission/context/evidence 引数は維持。
- `test_plain_runner_coverage.py`：追加した `__main__` 内に `pytest.main` があり、検出条件に対応。
- `test_check_subprocess_bytecode_guard.py`：subprocess 呼出しの追加なし。
- `test_campaign.py`：certified-writer caller inventory が追跡する `run_campaign` 2 呼出しと認可引数は維持。
- `test_official_perf_closure.py`：追跡対象の perf 呼出し・条件は変更なし。
- `test_p3_build_authority_cli.py`：authority 発行・登録箇所の追加なし。

5. 変異の再照準

**M1〜M3・M9〜M11 の新しい kill 先は未実装・未確定です。** 通常走の挿入点検査を追加していないため、変更箇所への到達根拠も提示できません。その他の M は変更なしです。KILLED の実測判定は行っていません。

6. 親の実走候補

現時点の差分については、`tools/run_tests.py` 経由で以下が候補です。

- `orchestrator/tests/test_b5_tier0.py`
- `orchestrator/tests/test_plain_runner_coverage.py`
- 上記 meta-test ファイル群

F1 の受入・変異走は、通常走 test の追加後に必要です。

## 総括

**一部実装済み・未実走。F1 が残っています。** 確認が必要なのは、ユーザー指示の「差し替えてよいのは 2 種だけ」が、参考 fixture の CLI 前段準備にも適用されるかという点です。厳密に適用すると、指定 fixture をそのまま再利用できません。