結論は、schema を `task-run/v1` のまま保ち、repo 外の世代 root に pytest 1 走行＝1 synthetic task-run として自動記録する案です。直接の v1 root は従来どおり cap で拒否し、自動配線だけが「閉鎖済み世代」を次世代へ rollover します。

本段では実装・pytest 実走とも行っていません。worktree は変更なしです。

## P1〜P4 の裁定

- **P1 — 採用:** 分析機能は足さず、まず連続して `test_run` を蓄積できる状態だけを作る。
- **P2 — 変更提案:** ID 不要の自動 run を既定にする一方、明示 ID の既存経路は互換用に残し、dispatch 子の再帰記録を専用環境 marker で禁止する。
- **P3 — 変更提案:** repo 外既定を採用し、git common-dir の digest で同一 clone の worktree 間共有を維持する。別 clone 間の共有は明示 base 設定に限定する。
- **P4 — 採用:** schema 世代は増やさず、production 差分は `ledger.py` 約10行、新規世代 helper 約75行、`run_tests.py` 約55行、CLI help 約2行の計142行以内を目標にする。

## 変更計画

### 1. pilot 閉鎖と破損を型で分離する

対象: [tools/task_runs/ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/ledger.py:43) `:43-44,527-563`

置換前の骨子:

```python
def start_run(root, *, slug, objective, task_class, task_kind):
    ...
    if final_marker:
        raise LedgerError(...)
    if published >= max_task_runs:
        raise LedgerError(...)
    if now >= pilot_started + max_days:
        raise LedgerError(...)
    base_commit = _git_head(root)
```

置換後の骨子:

```python
class PilotClosedError(LedgerError):
    pass

def start_run(
    root, *, slug, objective, task_class, task_kind,
    repo_root: Path | None = None,
):
    ...
    # final / max_task_runs / max_days だけ
    raise PilotClosedError(...)
    base_commit = _git_head(root if repo_root is None else repo_root)
```

- `PilotClosedError` は `LedgerError` の subclass とし、既存の直接 caller は従来どおり赤になる。
- damaged、unknown、I/O、schema 不整合は通常の `LedgerError` のままにし、次世代へ逃がさない。
- `repo_root` は base commit 値ではなく、writer が git を実測する cwd。`base_commit` の caller 指定は引き続き不可能。
- 外部 root の自動 run だけ `_REPO` を渡す。既存 checkout-local caller は引数省略で現状を維持する。
- `tools/task_runs/schema.py:309-473` と `schema_v1.json` は変更しない。

### 2. repo 外の自動世代 manager を追加する

対象: `tools/task_runs/generation.py:new:1-75`（新規）

置換前: 世代概念なし。単一 v1 root が cap に達すると `start_run()` が拒否する。

置換後の骨子:

```python
def default_base(repo_root):
    # IZANAGI_TASK_RUNS_BASE
    # → XDG_STATE_HOME
    # → HOME/.local/state
    # の順。絶対 path かつ repo 外のみ。

def repo_namespace(repo_root):
    # clean git env で --git-common-dir を実測
    # realpath の SHA-256 先頭12桁だけを path に使う

def start_automatic_test_run(repo_root, base=None):
    namespace = base / repo_digest
    with exclusive_series_lock(namespace):
        generation = latest_generation_or_create()
        try:
            return generation, start_run(
                generation,
                slug="pytest-run",
                objective="automatic tools/run_tests.py observation",
                task_class=1,
                task_kind="other",
                repo_root=repo_root,
            )
        except PilotClosedError:
            generation = create_next_generation()
            init_pilot(generation)
            return generation, start_run(..., repo_root=repo_root)
```

世代レイアウト:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/izanagi/task-runs/
└── <git-common-dir-digest>/
    ├── .generation.lock
    ├── generation-000001/   # そのまま task-run/v1 root
    │   ├── pilot.json
    │   └── <task-run-id>/...
    └── generation-000002/
```

契約:

- `IZANAGI_TASK_RUNS_BASE` 未設定時は上記 XDG/HOME 順で解決する。
- base が解決不能、相対 path、repo 内、書込不能なら記録だけを諦め、pytest は通常実行する。
- 同一 clone の linked worktree は git common-dir digest が同じなので同一系列を共有する。
- `.generation.lock` は owner-only、`O_NOFOLLOW`、regular-file 検査付きの排他 lock とする。
- 世代名以外の entry、symlink、非 directory を見つけたら rollover せず記録を諦める。
- `PilotClosedError` だけを捕捉する。damaged/unknown を新世代作成で隠さない。
- 各 pytest invocation は synthetic `task_run` を1件作り、`test_run` 成功後に `task_end=completed` を追記する。pytest の成否は従来どおり `exit_status` が表し、`completed` は wrapper invocation が終了した意味に限定する。
- series root 自体は ledger ではない。validate/report の入力は必ず個々の `generation-*` とする。
- 自動 final report や世代横断分析は追加しない。

### 3. 三つの実行経路へ同じ lazy recording session を通す

対象: [tools/run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/run_tests.py:65) `:65-68,814-899,905-912,948-995,1484-1534,1638-1664,1667-1814,1859-1868`

置換前の骨子:

```python
task_run_id = os.environ.get(_TASK_RUN_ID_ENV)
if not task_run_id:
    return plain_execution(...)
return *_and_record(..., task_run_id)
```

置換後の骨子:

```python
recording = _RecordingSession()  # I/O はまだしない

# direct / dispatch / bounded scope の全経路へ同じ object を渡す
return _call_and_record(cmd, args, recording)
return _dispatch_result(dispatch_fn, args, recording)
return _launch_local_scope(args, cap, recording=recording)
```

`_RecordingSession.resolve()` の規則:

- `IZANAGI_TASK_RUN_AUTO_RECORD=0`: 明示 opt-out。現行の plain call shape を維持する。
- `IZANAGI_TASK_RUN_ID` あり: 既存 manual-owned run。`IZANAGI_TASK_RUNS_ROOT` または従来 root を使い、自動 `task_end` は書かない。
- ID なし: `generation.start_automatic_test_run()` を一度だけ lazy 実行する。
- 初期化失敗は `Exception` のみ捕捉して記録なしへ倒す。`KeyboardInterrupt` / `SystemExit` は飲み込まない。
- bounded scope が `CAP_OOM` から dispatch へ fallback しても、同じ session を再利用し synthetic run を二重作成しない。

追加変更:

- `run_tests.py:814-842` の `_record_task_run()` を `None` 返却から成功時 `True`、記録不能時 `False` へ変える。
- auto-owned のときだけ、`True` を受けた後に `finish_run(..., "completed")` を best-effort で呼ぶ。append 失敗時は finish せず、欠測を unfinished run として残す。
- `run_tests.py:905-912` の `_dispatch_environment()` は ID/root/sidecar を除くだけでなく、`IZANAGI_TASK_RUN_AUTO_RECORD=0` を設定する。bounded-scope 子も同 helper を使うため、子自身の新規自動 run を防げる。
- recording 初期化は lazy にし、site/gate 拒否だけの invocation で空 run を作らない。
- trigger、suite identity、duration、sidecar digest の計算は現状維持する。

明示的な非変更面:

- `run_tests.py:367-385` の pytest argv 組立は変更しない。
- `run_tests.py:388-560` の4 gate は変更しない。
- pytest argv に TestOps 用 flag を追加しない。所有制御は親子間の環境 marker のみで行う。
- `pytest_stats.py:17-180` は変更せず、node ID は12桁 digest 以外を保存しない。

### 4. manual CLI の境界を明記する

対象: [tools/task_runs/cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/tools/task_runs/cli.py:25) `:25-45`

置換前:

```python
_DEFAULT_ROOT = _REPO / "output" / "task-runs"
help="ledger root (default: checkout-local output/task-runs)"
```

置換後:

- `_DEFAULT_ROOT` と direct-generation CLI の意味は変更しない。
- help を「manual single-generation root。`run_tests.py` の自動世代 root とは別」と明記する。
- 外部世代を CLI で読む場合は `--root .../generation-NNNNNN` を必須にする。

CLI 全体を外部既定へ変える案は却下する。commit event の git 実在確認も現在 root を cwd にしており、そこまで変更すると P1〜P4 を超えて production 差分と攻撃面が増えるため。

### 5. 世代・権威・運用文書を更新する

対象: [output/task-runs/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-testops-observation/output/task-runs/README.md:14) `:14-50,53-81,91-99`

置換前:

- checkout-local の単一 pilot
- ID を設定した opt-in 記録
- cap 到達後の世代名は未裁定

置換後:

- tracked `output/task-runs` は終了済み pilot の凍結 archive と明記する。
- live 自動記録、XDG/HOME fallback、base override、明示 opt-out、manual ID 互換を記載する。
- `generation-*` はすべて exact `task-run/v1` root であり、schema 世代ではないと明記する。
- direct root は cap で拒否、自動 series manager は final/max-runs/max-days のみ rollover、と責務を分ける。
- generation 単位の fail-closed validate/report、世代横断 reader は未実装、と明記する。
- synthetic run は `task_kind=other` cohort とし、通常の implementation task と比較しない。
- `authority: development-observation-not-evidence`、proof chain/fitness/benchmark への参照禁止、削減推奨禁止を再掲する。
- 自動生成 task の objective、slug に argv・selector・node ID を含めない。
- 従来の0.005〜0.131秒は append 部分だけであり、新しい start/event/end/fsync overhead は別途親が実測すると明記する。

段7で親が追加する記録:

- `docs/spool/decisions/<land時採番>-testops-observation.md:new:1` — D66 の追補として、外部自動系列・世代 rollover・v1 維持・非証拠性を記録。
- `docs/spool/worklog/<land時採番>-testops-observation.md:new:1` — 実装結果、実走した node、overhead 実測、未実施項目だけを記録。

spool の実 basename と書式は段7で正本を再読して決め、段2では既成事実化しない。

## 新規・更新テストと kill 対応

新規ファイル `orchestrator/tests/test_task_run_generation.py`:

| nodeid 案 | 具体的に落とす変異 |
|---|---|
| `::test_external_start_observes_supplied_repo_head` | `start_run()` を `_git_head(root)` のままに戻すと、repo 外 generation で start が失敗して赤。 |
| `::test_default_base_is_outside_repo_and_shared_by_linked_worktrees` | 既定を `_REPO/output/task-runs` に戻す、または worktree path を hash すると、外部性または同一 namespace assertion が赤。 |
| `::test_cap_rollover_creates_second_v1_generation` | `PilotClosedError` の捕捉を削ると11走目が例外。直接 cap 判定自体を削ると第1世代が11件になり赤。 |
| `::test_closed_generation_rolls_over[final]` | final marker の raise だけ通常 `LedgerError` に戻すと新世代が作られず赤。 |
| `::test_closed_generation_rolls_over[max-days]` | max-days の raise だけ通常 `LedgerError` に戻すと赤。 |
| `::test_damaged_generation_is_not_treated_as_closed` | `except PilotClosedError` を `except LedgerError` に広げると破損世代を隠して次世代を作るため赤。 |
| `::test_series_lock_serializes_tenth_and_eleventh_start` | series lock を削ると並行 start の一方が cap error、または世代番号衝突になり赤。 |
| `::test_unknown_or_symlink_series_entry_is_rejected` | unknown 無視、`follow_symlinks=True`、`O_NOFOLLOW` 削除のいずれでも新世代が作られて赤。 |
| `::test_generation_documents_remain_task_run_v1` | schema/version field や generation field を task/event に足すと exact-key validator が赤。 |

新規ファイル `orchestrator/tests/test_run_tests_testops_observation.py`:

| nodeid 案 | 具体的に落とす変異 |
|---|---|
| `::test_unset_configuration_records_once_without_task_run_id` | `run_tests.py:1865-1867` の旧 ID 必須分岐を戻すと event が0件で赤。 |
| `::test_auto_recording_preserves_exact_pytest_argv_and_nonzero_rc` | pytest argv に記録 flag を足す、または記録 rc で child rc を上書きすると赤。 |
| `::test_recording_bootstrap_failure_preserves_rc_stdout_and_stderr` | generation 初期化例外を外へ出す、警告を出す、固定 rc を返すと赤。 |
| `::test_force_dispatch_records_once_without_manual_id` | `_dispatch_result()` に lazy session を渡し忘れると0件、親子双方で resolve すると2件になり赤。 |
| `::test_cap_oom_fallback_reuses_one_auto_owned_run` | bounded scope と fallback dispatch が別 session を作ると synthetic run が2件になり赤。 |
| `::test_dispatch_and_scope_children_disable_recursive_recording` | `_dispatch_environment()` の `AUTO_RECORD=0` を削ると子側 start mock が呼ばれて赤。 |
| `::test_auto_owned_run_finishes_only_after_successful_test_event` | event 失敗後にも `task_end` を書く、または event 前に finish すると赤。 |
| `::test_manual_task_run_override_is_not_auto_finished` | manual ID run を無条件 finish する変異で赤。 |
| `::test_auto_payload_contains_digest_but_no_target_selector_or_nodeid` | argv/selector/nodeid を objective、suite ID、追加 field のいずれかへ保存すると文字列検査または exact-key validator が赤。 |
| `::test_repo_internal_auto_base_is_fail_open_noop` | repo 外検査を削ると repo 内に generation が作られて赤。 |

既存テストの更新:

- `orchestrator/tests/test_run_tests_task_run.py:41-67`  
  `test_opt_out_preserves_exact_command_and_call_shape` を `test_explicit_auto_off_preserves_exact_command_and_call_shape` へ変更し、環境不在ではなく `IZANAGI_TASK_RUN_AUTO_RECORD=0` を opt-out 契約にする。
- 同 `:141-178,261-281,360-404`  
  dispatch / scope child から ID/root/sidecar が消える既存 assertion に、`AUTO_RECORD == "0"` を追加する。
- `orchestrator/tests/test_task_run_ledger.py:885-908`  
  direct root の count/age cap は引き続き拒否されることを保ちつつ、期待例外を `PilotClosedError` に狭める。これにより「direct root の cap を消して解決する」変異も拒否する。

## 静的検査と親実走

この段では pytest を実行しておらず、緑とは報告しない。実装後はまず以下を静的確認する。

- `git diff --check`
- changed Python を `ast.parse` し、pycache を生成せず構文確認
- `git diff -U0 -- tools/run_tests.py` で `:367-560` に hunk がないことを確認
- `schema.py`、`schema_v1.json`、`pytest_stats.py` が無差分であることを確認
- production の追加＋削除行を数え、150行目標を確認
- source scan で raw argv/nodeid を generation/task payload に渡す経路がないことを確認

親環境で実測する場合だけ、上記新規2ファイル、既存の `test_run_tests_task_run.py` と `test_task_run_ledger.py`、続いて関連全走を必ず `tools/run_tests.py` 経由で実行する。完了時は `tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の `tools/check_ai_provenance.py` も親が行う。

## 総括

- 骨子: ID 不要の synthetic v1 runを repo 外系列へ作り、親だけが1件記録し、閉鎖済み世代だけを rollover する。
- 最大のリスク: 旧 append-only 実測より start/event/end と series lock の fsync が増えるため、連続記録の overhead は未実測。
- 最大の正しさリスク: default-on 化した子プロセスの二重記録。`AUTO_RECORD=0` の親所有 marker と CAP/OOM fallback の同一 lazy session で防ぐ。
- 未確認: 世代横断 report/aggregate、`task_run_check.py` の自動化、別 clone 間の共有は今回の scope 外。
- 未確認: 指定上もっとも関連する既存2テストだけを開いたため、`test_run_tests_preflight.py` の個別 node 被覆は未確認。4 gate 本体は編集禁止面として固定し、新規 argv/経路テストで補強する。
- 実装・ファイル変更・pytest 実走は行っていない。