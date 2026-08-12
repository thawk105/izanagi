単位 B を指定 4 ファイル内で実装しました。docs・単位 A 所有ファイル・official 拒否条件は変更せず、commit も作成していません。

主な変更:

- floor は site compiler を cell ループ外で一度解決し、同じ `cxx` を source evidence、同じ `cc/cxx` を build に渡します。
- hash 検証済み `VerifiedCalibration` の receipt と live cc/cxx/cmake を `floor_toolchain_matches()` で照合します。receipt 不在、compiler 定義の欠落・重複、各 identity 不一致は fail-closed です。
- live version は [`_observe_floor_tool()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1076) の `(result.stdout + result.stderr).strip()` で全文取得しています。
- `build_v2` は任意の `expected_toolchain_manifest` を再観測結果と完全一致検査します。既定 `None` は従来挙動のままです。
- 既存 floor 試験には private binder の共通 faithful fake を追加し、新規 binding 試験クラスではその fake を外しています。実 cmake は読みません。
- materializer registry meta-testも、floor が `expected_toolchain_manifest` を必ず渡すことを検査するよう強化しました。

検査結果:

- `py_compile`（変更 4 ファイル）: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- pytest 対象範囲:
  - `orchestrator/tests/test_buildcache_v2.py`
  - `orchestrator/tests/test_s8b_floor_campaign.py`
  - 新規 `test_v2_expected_toolchain_manifest_*`
  - `TestFloorToolchainBinding::*`
  - `test_build_cells_resolves_site_compilers_and_binding_once_before_cell_loop`
  - meta-test `test_materializer_registry_covers_all_python_build_launches`

pytest は未実走です。`tools/run_tests.py` がテスト開始前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。直接の `qstat -Q` も sandbox の socket 作成拒否でした。テスト赤ではなく dispatch infrastructure の偽赤であり、実装差分や submodule index lock には帰属しません。

所有外への静的波及:

- [`test_s8b_materialization.py::test_floor_manifest_golden_stable`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_materialization.py:442) は `build_cells` を直接呼び、`verified_calibration` を渡していません。所有外かつ no-touch 指定のため未変更で、現状は追随が必要です。
- `pipeline.py` など他の `build_v2` caller は新引数を省略するため、既定 `None` で影響しません。
- 共有 `conftest.py`、oracle consumer、Pegasus shell、freeze consumer は未変更です。

## 総括

- 変更: [`buildcache.py:575`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:575)、[`s8b_floor_campaign.py:1076`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1076)、両テストファイルへ再照合・gate・回帰試験を追加。
- nodeid: 上記 2 test file 全体と新規/meta nodeを投入したが、runner rc=16 (`qstat -Q`) のため未実走。
- 全文根拠: [`_observe_floor_tool:1104`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1104) の `(stdout + stderr).strip()`。
- 受理集合: 無束縛の floor → receipt/live/再観測が完全一致する floor のみに縮小。`build_v2(..., None)` は不変。
- 所有外波及: `test_s8b_materialization.py::test_floor_manifest_golden_stable` の直接 `build_cells` caller は追随要。