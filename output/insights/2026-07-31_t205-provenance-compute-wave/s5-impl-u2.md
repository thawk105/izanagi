# 段 5 実装子 U2 (dispatch・hook) 完了報告 — Claude opus

**pytest は 1 度も走らせていない** (ログインノード `pegasus02`)。静的検査のみ。

## 変更

- **`tools/pegasus/dispatch_compute.py`** (+168/-44): `_TaskSpec` / `TASKS` / `DEFAULT_TASK="tests"` を新設し
  `_REQUEST_ENV_ALLOWLIST` を `TASKS["tests"].env_allowlist` へ移した。`provenance` は
  `child_script=("tools","check_ai_provenance.py")` / **env allowlist 空** / `probe_imports=()`。
  `_interpreter_probe_source(task=DEFAULT_TASK)` は既定引数あり (既存 2 テストが無引数で呼ぶ)。
  `sys.version_info < (3,10)` の検査は task に依らず常置 (二層冗長 gate を保存)。
  **`_resolve_request()` を新設し v1 / v2 の両方を受理**、v1 は `task="tests"` + `pytest_args` として読む。
  未知 schema_version だけ `DispatchError`。`_dispatch_impl` 冒頭で `task not in TASKS` を `ValueError`
  (scheduler・submission dir に触れる前)。`main()` は `--task` を `choices=tuple(TASKS)` で追加 = 三層目の fail-closed。
- **`hooks/guard_bash.py`** (+73/-3): `_SANCTIONED_PATHS` に checker を追加し、`_provenance_entry()` /
  `_provenance_violation()` を **`_is_sanctioned` の早期 allow より前**で評価するよう `_heavy_segment_violation` を分割。
  `-m <module>` 形では module 側を実体とみなし、位置引数の script に sanctioned 判定を借りさせない (B-R8 の穴)。
  判定対象は head が python 系か checker 自身のときだけ (`cat`/`git show`/`rg` を巻き込まない)。
- **`tools/run_tests.py`** (+1): `_default_dispatch` に `task="tests"` のみ。`main()` の seam は不変。
- **`tools/dev_waves/checker.py`** (+2): `run_check_specs` の理由決定に `returncode == 16 → CHECK_FAILED` を
  先頭分岐として追加 (B-R7)。

## 静的検査

`python3 -m py_compile` を 6 ファイル (guard_bash / test_hooks / test_pegasus_dispatch_compute /
dev_waves.checker / dispatch_compute / run_tests) に対して実行し全て成功。
これ以外は grep / Read / `git diff` のみ。**pytest・qsub は 1 度も実行していない。緑の主張はしない。**

## 新規テストと KILL する変異

`test_pegasus_dispatch_compute.py`: `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc` (**M11**) /
`test_provenance_task_binds_child_script_and_empty_env_allowlist` /
`test_provenance_probe_omits_pytest_and_xdist_imports` /
`test_job_run_accepts_v1_request_as_tests_task` (**M12**) /
`test_job_run_rejects_unknown_schema_and_task[unknown-schema|unknown-task|non-string-task]` /
`test_job_run_launches_task_specific_child_script[tests|provenance]` /
`test_tests_task_remains_default_and_receipt_records_task` /
`test_run_tests_default_dispatch_passes_tests_task` (**B-R11**、従来 0 テスト) /
`test_dev_wave_check_maps_dispatch_infra_rc_to_infra_reason` (**B-R7**、rc=1 が `PROVENANCE_FAILED` のままである正例つき)。

`test_hooks.py`: `test_bash_login_sanctioned_entries_are_exact` (拡張) /
`test_bash_login_blocks_nonsanctioned_provenance_entrypoints[outside-repo-copy|outside-repo-copy-direct|home-relative-copy|cwd-relative|parent-relative|shell-command-string|dash-m-pytest]` (**M13**。
`_is_sanctioned` の後ろへ移すと **`[dash-m-pytest]` だけが赤** = 帰属が一意) /
`test_bash_login_allows_nonexecuting_provenance_flags` (正例) / `test_bash_compute_allows_provenance_forms` /
`test_bash_login_provenance_branch_does_not_capture_readers`。

## 所有外への波及 (静的列挙)

- `dispatch_compute.dispatch` の production caller は `tools/run_tests.py:831` **1 箇所のみ** (repo 全 grep)。
  `pytest_args=` キーワード呼出はゼロ。
- `pegasus-dispatch-receipt` / `-request` の consumer は repo 内に存在しない (grep 0 hit)。
  `pytest_args` の残存参照は `_resolve_request` の v1 互換読みと既存 M5 fixture の 2 箇所のみ。
  **M5 fixture は v1 のまま据え置いた** — 版数 gate が先に発火して request を parse しないため無害で、
  かつ v1 互換の副次的な pin になる。
- `test_site_policy.py:259` の FA-3 は future import 1 本の存在のみを要求 → 保存済み。
- `test_dev_waves_integration.py:823` の `[provenance→PROVENANCE_FAILED]` は rc=1 なので新分岐に触れない。
- `run_tests.py` と `dev_waves/checker.py` は diff で +1 / +2 行のみ。共有 fixture の変更なし。

## 期待される赤 (これ以外は回帰)

1. hook の sanctioned 宣言は checker 側 site gate (C-2) の着地を前提とする。C-2 未着地の tree では
   **宣言だけが真**になる (統合 commit で解消)。**テストは赤くならない**が、中間 tree で
   「防壁が効いている」と主張してはならない。
2. `TASKS["provenance"].child_script` は checker の存在に依存 (既存ファイルなので現時点で緑)。
3. `test_bash_login_sanctioned_entries_are_exact` の `os.path.isfile` は U1 が checker を削除/改名した場合のみ赤。

## 受理集合の差分 (hook・login/suspect site 限定)

| 綴り | 変更前 | 変更後 |
|---|---|---|
| `python3 tools/check_ai_provenance.py --range …` | 許可 (素通り) | 許可 (sanctioned として明示) |
| `./tools/…` / `python3 -m tools.check_ai_provenance` | 許可 (素通り) | 許可 (sanctioned) |
| repo 外 copy / `~/…` / cwd 相対 / `../…` / `bash -lc` 経由 | **許可 (素通り)** | **拒否** ← C-3 の唯一の純増 |
| `python3 -mpytest tools/check_ai_provenance.py` | 拒否 | **拒否のまま** (sanctioned 追加による反転を新分岐が閉じた) |
| `--message-file` / `--help` / `-h` / `--collect-only` / `--version` 付き | 許可 | 許可 (免除集合で保存) |
| `cat`/`rg`/`git show`/`wc` が引数で名指し | 許可 | 許可 (head 制限で保存) |
| 計算ノードの全形 | 許可 | 許可 |

dispatcher 側: `dispatch()` に `task` が加わり (既定 `tests` で従来と同一)、request/receipt が v2 へ。
`_job_run` は **v1/v2 を受理し未知 schema と未知 task を拒否** (従来は schema を読まず fail-open)。

## 親裁定を要した点と親の裁定

1. **免除 flag に `--collect-only` / `--version` を追加した** — 含めないと
   `python3 -mpytest tools/check_ai_provenance.py --collect-only` が許可から拒否へ**指示外の縮小**をするため。
   → **親裁定: 採用。** 受理集合の過剰縮小を避ける判断として正しい (DW-M01 後段の正例と同じ趣旨)。
2. **`_script_target` の第 1 非 option 引数昇格そのものは直していない** — 同じ穴は
   `python3 -mpytest tools/run_tests.py` にも既存で存在するが、修正は `run_tests.py` の受理集合を縮める
   未裁定の変更になる。→ **親裁定: 今回 scope 外で正しい。既存欠陥として worklog へ起票する。**
3. **B-R7 の検査を `test_pegasus_dispatch_compute.py` に置いた** (`tools/dev_waves/` のテストは所有外)。
   → **親裁定: そのままでよい。** rc 契約の消費側検査として配置に筋が通る。
4. `checker.py` の分岐は `16` を直値 + D103 参照コメント (定数追加は「1 分岐のみ」の指示を超えるため)。
   → **親裁定: 可。** 定数化は所有境界を越えるので今回は直値でよい。
