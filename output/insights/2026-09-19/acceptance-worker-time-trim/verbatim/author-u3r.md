## 変更面

変更は [orchestrator/tests/test_run_tests_preflight.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/awtt-u3r-author/orchestrator/tests/test_run_tests_preflight.py) のみです。

| file:line（変更後） | 内容 |
|---|---|
| 同 file:94 | function scope の `_small_login_repo`。`_clean_runner_env` 完了後に `_tracked_repo` で構築し、`RT._REPO` を注入 |
| 同 file:101 | 指定の正例 test 1 本追加 |
| 同 file:1325, 1560, 1858, 2225, 2246, 2390, 2414, 2434 | 既存 8 関数に fixture 引数だけ追加 |

fingerprint 関数・5 command・既存 mock は変更していません。`git add` / `git commit` は実行していません。

## 対象 node の表

行番号は変更前。関数名はいずれも `test_` 接頭辞を省略しています。

| node | 経路 | `_REPO` の他用途なし | 判定 |
|---|---|---|---|
| R:477 `nonacceptance_bounded_child_marker_warns_exactly_once_in_parent` | LOCAL → fingerprint → 内側 `main` | **いいえ**。内側で cwd・記録処理に使用 | 非対象 |
| R:1304 `without_force_dispatch_login_with_headroom_still_runs_local` | LOCAL → fingerprint → CHILD_RC 0 | はい | 対象 |
| R:1382 `login_headroom_and_queue_four_quadrants` | 3 枝 LOCAL、1 枝 DISPATCH | 関数全体では保証対象外 | 全枝非対象。fixture の一括適用で非到達 node まで変えるため |
| R:1539 `m7_local_enters_scope_before_parent_preflights` | LOCAL → fingerprint → CHILD_RC 0 | はい。parent preflight 前に return | 対象 |
| R:1837 `local_child_test_failure_never_falls_back` | LOCAL → fingerprint → CHILD_RC 5 | はい | 対象 |
| R:2204 `login_non_immediate_dispatch_exempt_flags_enter_bounded_scope` | 7 flags → LOCAL → fingerprint → CHILD_RC 0 | はい | 全 7 node 対象 |
| R:2225 `login_collect_only_from_pytest_addopts_enters_bounded_scope` | LOCAL → fingerprint → CHILD_RC 0 | はい | 対象 |
| R:2314 `previous_full_cap_estimate_dispatches_without_local_scope` | DISPATCH。fingerprint 非到達 | **いいえ**。acceptance preflight に使用 | 非対象 |
| R:2369 `small_partial_estimate_still_tries_local_scope` | LOCAL → fingerprint → CHILD_RC 0 | はい | 対象 |
| R:2393 `login_local_scope_releases_budget_lease_on_infra` | LOCAL → fingerprint → DISPATCH_INFRA | はい | 対象 |
| R:2413 `login_local_scope_releases_budget_lease_on_interrupt` | LOCAL → fingerprint → KeyboardInterrupt | はい | 対象 |

適用範囲は既存 **8 関数・14 node 相当**です。

## RecordingSession の確認

`repo_root=Path(_REPO)` は import 時束縛のため、fixture では変更されません。正規 runner の子環境は auto record が `0` となり、非記録経路に進みます。

対象 8 関数では、既存 `_run_bounded_scope` mock が `ensure_started()` を呼びません。auto record 未設定でも `_automatic_run` と task run ID は設定されず、`record()` / `finish()` は書込み前に戻ります。

除外した R:477 は内側 `main` → `_call_and_record()` → `ensure_started()` に到達し、実 repo を記録開始先として渡します。対策候補は fixture 内の `monkeypatch.setenv("IZANAGI_TASK_RUN_AUTO_RECORD", "0")` ですが、指示どおり実装していません。

## 直接呼出しの検証結果

**未実行。`DIRECT_CALL_PASS` は得られていません。**

module import、`tempfile.mkdtemp()` 下での fixture 構築、実 fingerprint の前後比較を行うコマンドは、実行前に `guard_bash` hook に拒否されました。

実行できた検証：

- `python3 -m py_compile`：成功。cache 出力先は `/tmp`。
- AST 照合：test 関数 **113 → 114**。追加は指定の 1 本だけ。
- 既存全 test の名前・本文・decorator・parametrize は不変。引数変更は対象 8 関数への fixture 追加のみ。
- `git diff --check`：成功。

## 未実走・未確認

pytest collection・test 実走・変異 matrix・A/B・性能削減量は未確認です。直接 fingerprint 呼出しも親環境での検証が必要です。

## 総括

指定 1 ファイルに function scope fixture と正例 1 本を実装しました。
既存 8 関数に適用し、経路上の懸念がある 3 関数は除外しました。
構文・AST 不変性・diff 検査は成功、実走結果は未取得です。

自動承認レビューに相当する `guard_bash` hook が直接呼出し検証を拒否しました。理由は「防護ツリーパスと不透明構文の同居は分類不能」であり、検証処理自体は開始されていません。