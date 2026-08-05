実装完了です。編集は指定された 2 ファイルだけで、docs・fixture・既存期待値・判定分岐は変更していません。git add / commit / branch 操作も行っていません。

### 変更内容

- [hooks/guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/hooks/guard_bash.py:174)
  - `_SANCTIONED_PATHS` に `tools/pegasus/fetch_third_party.py` を追加。
  - network 制約と runbook §7.0 の全 subcommand `local-ok` 実測分類をコメントに記載。
  - `_script_target` / `_is_sanctioned` / `_heavy_segment_violation` は変更なし。
- [orchestrator/tests/test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch/orchestrator/tests/test_hooks.py:893)
  - LOGIN の指定4綴り。
  - allowlist membership と `os.path.isfile` による exact 性。
  - `collect_receipt.py` / `run_probe.py` の拒否維持。
  - COMPUTE の指定4綴り受理。
  - 各新規テストに受理集合の性質を示す日本語 docstring を追加。

### 受理集合の差分

変更前は、指定4綴りは `PEGASUS_LOGIN` / `PEGASUS_SUSPECT` で「非 sanctioned Pegasus 実行体」として拒否され、`PEGASUS_COMPUTE` では通っていました。

変更後は、正規化後に `tools/pegasus/fetch_third_party.py` へ exact 解決される起動が LOGIN / SUSPECT でも通ります。指定された fetch / hydrate / verify / verify-deps の4経路をテストで固定しました。COMPUTE の受理は変更ありません。

`tools/pegasus/collect_receipt.py`、`run_probe.py`、`exec_calibrate.py` など他の Pegasus 実行体は拒否のままです。

### 検査結果

- 新設4 nodeid:
  - `test_bash_login_allows_fetch_third_party_sanctioned_spellings`
  - `test_bash_login_fetch_third_party_entry_is_exact`
  - `test_bash_login_fetch_third_party_does_not_sanction_siblings`
  - `test_bash_compute_allows_fetch_third_party_spellings`
  - 結果: `4 passed`, rc=0
- 範囲 `python3 -m pytest orchestrator/tests/test_hooks.py -q -rf`
  - 結果: `75 passed, 1 skipped`, rc=0
  - skip: `test_real_submodule_payload_edit`。既存条件「template patch 未適用 (marker 無し)」によるもの。
  - 同範囲で `test_settings_json_wires_all_hooks` と subprocess 煙テストも通過。
- 外部 meta-test:
  - `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - 結果: `1 passed`, rc=0
- `py_compile`、`git diff --check`、`tools/check_codex_agents.py`、`tools/check_docs.py`: すべて rc=0。

### 静的な波及確認

- caller: `.claude/settings.json` が `guard_bash.py` を Bash PreToolUse として呼ぶため、live 配線で受理集合が変わります。
- consumer: `test_pegasus_thirdparty_fetch.py` は取得ツール本体を検査しますが、本体は未変更です。
- meta-test: `conftest.py` と `test_real_repo_serialization.py` は既存の real-submodule nodeid を固定しており、外部 meta-test は通過しました。
- shared fixture: 新規テストは既存の `_REPO` と `GB` module loader のみを使用し、fixture 変更はありません。
- 残リスク: brief の P2 にある sanctioned path 借用経路の族欠陥は scope 外のままです。

## 総括

- sanctioned exact path を1件だけ追加し、判定分岐は変更していない。
- LOGIN正例4経路、exact性、兄弟拒否、COMPUTE受理を新規テストで固定した。
- `test_hooks.py` 全体は 75 passed / 1既存skip、rc=0。
- 外部meta-testと静的checkerもすべてrc=0。
- 残リスクは既知のP2借用経路のみで、本waveでは意図的に未修正。