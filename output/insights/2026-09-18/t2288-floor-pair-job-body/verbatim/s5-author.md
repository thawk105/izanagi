## 実装

所有 5 path のみ編集しました。commit・実 qsub・実 driver 起動はしていません。

| file | 実装内容・行範囲 |
|---|---|
| `tools/pegasus/floor_pair_campaign.sh` | 1–233 行。PBS header、bootstrap、環境整理、interpreter、入力束縛、site → time → scratch → time → driver、create-only result。`run_driver()` は background child の rc を回収し、signal 後に再 wait。mode 0755 |
| `tools/pegasus/submit_floor_pair.sh` | 1–283 行。引数閉集合、D2138 pin、detached/clean checkout、spec/binary、A1/A2、evidence、dry-run/qsub、receipt。walltime は `select_walltime()` に集約。mode 0755 |
| `tools/pegasus/admission_registry.json` | path ソート順で 2 entry を追加。既存 entry 不変 |
| `orchestrator/tests/test_hooks.py` | class golden、全 field golden、local-ok evidence 表に計 15 行追加。local-ok 表への追加は submitter のみ |
| `orchestrator/tests/test_floor_pair_job_contract.py` | 1–380 行、18 test 関数と自走 harness。全 6 窓の境界、hostname、到達順、argv、dry-run、child rc/signal、A1/A2、receipt、pin 三者一致を検査する実装 |

## 実走

**実装済み・テスト未実走です。緑・closed とは報告しません。**

| command | 結果 |
|---|---|
| `python3 tools/run_tests.py --help` | rc=0、引数形式確認 |
| `bash -n tools/pegasus/submit_floor_pair.sh` | rc=0 |
| `bash -n tools/pegasus/floor_pair_campaign.sh` | hook が実行前に拒否。shell rc は未取得 |
| 指定の `run_tests.py` 4 file 走行 | rc=16。`qstat -Q preflight rc=1`、`child_started=false` |
| 新規契約 test 単独走行 | 同じ dispatch 障害、rc=16 |
| 追加 meta-test 選択走行 | 同じ dispatch 障害、rc=16 |
| `python3 tools/check_codex_agents.py` | rc=0 |
| `python3 tools/check_docs.py` | rc=1、期待赤 1 件のみ |
| `git diff --check` | rc=0 |

指定走行は次の command を実行しました。最終修正後にも同じ結果でした。

```text
python3 tools/run_tests.py orchestrator/tests/test_floor_pair_job_contract.py orchestrator/tests/test_hooks.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_ccbench_spawn_sites.py
```

追加選択した node は以下です。**いずれも child 未起動、実走件数 0** です。

- `test_codex_hooks.py::test_pinned_guard_paths_are_exact_and_independent_of_copy_paths`
- `test_codex_hooks.py::test_installation_rejects_each_pinned_guard_bytes_drift`
- `test_check_docs.py::test_admission_registry_mutations_have_exact_attributed_finding_sets`
- `test_check_docs.py::test_admission_measured_table_requires_exact_registry_path_set`
- `test_codex_worker_launch.py::test_guard_bytes_mismatch_is_launch_error`

`check_docs` の全 finding は次の 1 件でした。追加回帰は報告されていません。

```text
registry_only=[
 ('tools/pegasus/floor_pair_campaign.sh', 'dispatch-required', 'static job-body classification'),
 ('tools/pegasus/submit_floor_pair.sh', 'local-ok', 'static login-side submitter classification')
], runbook_only=[]
```

## 変異の exact old

以下の node は新規契約 test 内です。**殺傷結果は未観測**です。J = `tools/pegasus/floor_pair_campaign.sh`、S = `tools/pegasus/submit_floor_pair.sh`。

| ID | file | old 1 行 | new | 殺す node |
|---|---|---|---|---|
| M0 | J | `  # Window admission is checked again after scratch preparation.` | `  # Window admission is checked again after scratch preparation, deliberately.` | 等価・SURVIVED 期待 |
| M1 | registry、job entry | `      "class": "dispatch-required",` | `      "class": "local-ok",` | `test_registry_entries`、`test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` |
| M2 | S | `      SPEC_SHA256=990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619 ;;` | 同行の先頭 hash 文字 `9` → `8` | `test_frozen_spec_pins` |
| M3 | J | `  (( now + duration <= not_after )) \|\| fail 4 window insufficient_remaining_time` | 同行の `<=` → `<` | `test_window_gate_boundaries` |
| M4 | J | `  [[ "$label" =~ ^bnode[0-9]+$ ]] \|\| fail 4 site compute_node_required` | `  : \|\| fail 4 site compute_node_required` | `test_hostname_gate` |
| M5 | J | `    window) driver_argv+=(--execute-window "$FP_WINDOW_ID") ;;` | `    window) driver_argv+=(--validate-only) ;;` | `test_driver_argv` |
| M6 | 親の runbook | 下記参照 | 行削除 | `python3 tools/check_docs.py` |
| M7 | J | `  require_compute_hostname "$HOST_OBSERVED"` | `  if false; then require_compute_hostname "$HOST_OBSERVED"; fi` | `test_gate_order_and_calls` |
| M8 | S | `  if (( DRY_RUN )); then` | `  if (( ! DRY_RUN )); then` | `test_dry_run_has_no_execution` |
| M9 | J | `  export TMPDIR=/scr/${PBS_JOBID//:/_}` | `  export TMPDIR=/scr/${PBS_JOBID}` | `test_scratch_name_normalizes_colon` |
| M10 | S | `            if header.get("loaded_head") != head: refuse("loaded_head_mismatch")` | `            if False: refuse("loaded_head_mismatch")` | `test_submitter_head_consistency_preflight` |

M1 の class 行は canonical JSON 内で重複するため、**単独 1 行で file 全体に一意 match する指定はできません**。親の変異 spec は `entries["tools/pegasus/floor_pair_campaign.sh"]` の範囲に限定してください。canonical 契約を崩して一意化していません。

M6 は親所有で、対象行はこの worktree にまだ存在しません。予定行は以下ですが、親の実装後に exact old を確定する必要があります。

```markdown
| `tools/pegasus/floor_pair_campaign.sh` | `dispatch-required` | `static job-body classification` |
```

## 波及と未実走

- scope 前は登録簿 74 entry、`tools/pegasus/` の未登録実行体は login/suspect で拒否。今回 76 entry とし、新規 job は `dispatch-required`、submitter は `local-ok`。既存 74 entry の受理集合は変更していません。
- `test_hooks` の再帰 inventory、sanctioned 集合、login/suspect 拒否、登録簿 golden が consumer。指定 4 file 走行に含めましたが未起動です。
- `test_plain_runner_coverage` の allowlist は不変。新規 test は自走 harness を持ちます。
- `test_ccbench_spawn_sites` の build sink・行番号 pin を静的確認。新規 shell に build sink はなく、既存 production 行は動かしていません。
- hook installer・worker launcher の registry HEAD-blob 束縛に波及します。親による commit 前は新 registry bytes と HEAD が異なります。
- `test_check_docs` の合成 fixture、共有 fixture、duration ledger は変更していません。runbook 投影表は親の追加待ちです。
- driver・site policy・issuer・凍結 spec・禁止 docs は変更していません。
- runner が dispatch 障害 receipt を `output/pegasus-dispatch/` に自動生成しました。
- compute の依存解決、実 PBS 配送、walltime、scheduler signal、実測・finalize 成功は未観測。18 test の所要時間も未計測です。

## 総括

所有 5 path の実装を置き、commit はしていません。
submitter 構文、Codex agent checker、diff whitespace は通過しました。
docs は親の投影表待ちによる期待赤 1 件だけです。
テストは dispatch infrastructure failure で実走 0 件のため、状態は **実装済み・未実走**です。
M1 は entry 文脈限定、M6 は親の docs 実装後の exact old 確定が必要です。

自動 hook は job body の `bash -n` を `dispatch-required` として実行前に拒否しました。ソース生成用 shell command も保護 path／未登録実行体として拒否されたため、許可されたファイルの編集は patch で行い、拒否された実行を迂回していません。