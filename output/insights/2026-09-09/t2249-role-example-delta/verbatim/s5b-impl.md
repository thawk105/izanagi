## 総括

段 5 は未完了です。A と C は実装済みですが、adapter 2 件は `test -w` rc=1 のため親の render 待ちです。  
指定 pytest 5 件は dispatch infrastructure failure で子が起動せず、実装済み・未実走です。  
`check_codex_agents.py` は想定内の adapter parity 1 件だけで rc=1、`check_docs.py` は rc=0 でした。  
commit、add、stash、branch 操作は行っていません。

## 事前確認 (git diff が 3 file だけか)

開始時の差分は指定どおり次の 3 file だけでした。

- `.claude/agents/coder-v4-autonomous.md`
- `.claude/agents/planner-v4.md`
- `orchestrator/codex_roles/review_ledger.py`

現在は C を加えた 4 file のみです。`git diff --check` は rc=0 です。

## A. Reviewed 注記

[review_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2249-role-example-delta/orchestrator/codex_roles/review_ledger.py:25) の対象 2 entry に、日付 `2026-09-09`、ticket `T-2249` の Reviewed 行を追加しました。既存 Reviewed 行は変更していません。

## B. adapter — test -w の rc と結果 (書けたか / 親の render 待ちか)

`test -w .codex/role-adapters/coder-v4-autonomous.json` は **rc=1** でした。迂回や別 path への書込みは行っておらず、**親の render 待ち**です。

read-only oracle と `git show HEAD:<path>` の比較では、両 adapter とも差分は指定の 4 pointer だけでした。

- coder expected bytes: 9719、SHA-256 `70cb1be6d2e067a751b70618ca20d8bf44f23b6c157f0445b9af50854372b54a`
  - `/developer_instructions`: SHA `7ee700…e2e5` → `0daf92…5173`、該当 fragment は `delta_pct: -1.2` → `delta_pct: null`
  - `/review_ledger/source_file_sha256`: `4073ac…10d` → `ba6c9c…806`
  - `/semantic_digest`: `564287…7c7` → `4e8cd6…150`
  - `/source/sha256`: `4073ac…10d` → `ba6c9c…806`

- planner expected bytes: 8532、SHA-256 `963034a11ff1ec88681405a565ef117ce01e9fd0e9095b58a3cec0ed5a21adce`
  - `/developer_instructions`: SHA `5f83df…7f49` → `fbbf9b…4929`、該当 fragment は `last_delta_pct: -1.2` → `last_delta_pct: null`
  - `/review_ledger/source_file_sha256`: `089364…cb0e` → `3a3d35…8374`
  - `/semantic_digest`: `ac06f0…be1f` → `6a9956…d22`
  - `/source/sha256`: `089364…cb0e` → `3a3d35…8374`

既知 4 pointer を期待値へ置換した旧 JSON と期待 JSON の全体一致は両方 `True` で、5 件目の変化はありません。

## C. originless baseline の実測内訳と追随結果

[test_reflux_originless_compatibility.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2249-role-example-delta/orchestrator/tests/test_reflux_originless_compatibility.py:598) に `_extend_t2145_role_source_baseline` と同型の T-2249 helper を追加しました。

独立実測結果:

- journals: 旧 planner SHA が 6 row、各 count 1、合計 6
- reports: `[[旧 SHA, 6]]` の 1 row、合計 6
- 追随後: journals は旧 0 row、新 6 row
- 追随後 reports: `[[新 SHA, 6]]`

planner SHA は実 bytes で旧 `0893644a…cb0e`、新 `3a3d35fa…8374` を確認しました。coder は対象にしていません。

## 期待赤の事前列挙と実走結果の突き合わせ

adapter 未反映による期待赤として、実走前に `test_codex_agents.py` の次の 6 nodeid を列挙しました。

- `test_current_sources_render_byte_exact_and_native_is_empty`
- `test_all_adapters_pin_model_policy_and_blocked_runtime_activation`
- `test_source_body_is_embedded_exactly_once_before_product_override`
- `test_any_native_discovery_toml_is_rejected`
- `test_project_config_native_role_is_rejected_and_globals_are_allowed`
- `test_consumer_required_field_drift_is_detected_from_source_ast`

pytest 子が起動しなかったため、この 6 件は未観測で突き合わせ不能です。

`check_codex_agents.py` は事前予想どおり、coder adapter の `rendered adapter byte parity drift` 1 findingだけで rc=1でした。追加 finding はありません。

## 実走した nodeid と rc

pytest nodeid は一つも実行されていません。以下はすべて `tools/run_tests.py` rc=16、`child_started=false`、`qstat -Q preflight rc=1` でした。

- `orchestrator/tests/test_codex_agents.py`
- `orchestrator/tests/test_codex_role_runtime.py`
- `orchestrator/tests/test_reflux_originless_compatibility.py`
- `orchestrator/tests/test_p3_s4_loop.py`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`

したがって全件「実装済み・未実走」です。

- `python3 tools/check_codex_agents.py`: rc=1、想定内の parity finding 1件
- `python3 tools/check_docs.py`: rc=0、違反なし
- `git diff --check`: rc=0

## 走らせていない consumer test の波及可能性

静的な参照関係は次のとおりです。

- `review_ledger.py` → `spec.py`:
  - `test_codex_agents.py` が ledger、spec、adapter を直接参照
  - `test_codex_role_runtime.py` が launcher 経由で spec を参照
  - `test_p3_s4_loop.py` の対象 production path が `get_role_spec()` を使用
  - 指定外では `test_effort_levels.py` が spec を import
- `planner-v4.md` → `p3_autonomous_workload_trial.ROLE_FILES["planner"]` → `FixtureRoleProvider`:
  - `test_p3_autonomous_workload_trial.py`
  - `test_reflux_originless_compatibility.py`
  - `test_role_session_isolation.py`
- `coder-v4-autonomous.md` は `ROLE_FILES["coder"]` ではなく、spec/adapter parity 側だけが consumer です。

これらはすべて未実走です。

## 受理・拒否挙動の変化

runtime の受理集合を変える変更はありません。schema、mode、consumer、runtime activation、`_DELTA_PCT_LIVE=False`、`WhiteboardLeakError`、whiteboard exact 5-key/`None` 検査は未変更です。

ただし現在の中間状態は adapter が旧 bytes のため、repository integrity checker が意図どおり拒否します。

## 未了・要裁定

- 親による adapter 2 件の期待 bytes への render が必要です。
- render 後、指定 pytest 5 file と `check_codex_agents.py` の再実走が必要です。
- queue/dispatch 復旧までは pytest 結果を確定できません。
- wrapper が各失敗走行の diagnostic receipt を `output/pegasus-dispatch/` に自動保存しましたが、tracked 差分には含まれていません。