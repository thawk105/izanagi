## 実装した内容

- [`_TaskSpec` と `TASKS`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:100): `env_mode` と `argv_policy` を追加し、閉集合を `{tests, provenance, mutation, generic}` に拡張しました。既存 2 task は `inherit` / `passthrough` のままです。
- [`mutation`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:143): `mutation_worktree.py`、clean env、`pytest` / `xdist` / `packaging` probe を設定しました。probe 根拠は wrapper が同じ interpreter で harness と `run_tests.py` を起動し、後者が `packaging` を import、compute では pytest / xdist を要求するためです。
- [`generic`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:151): 非空 string list を直接 `shell=False`、`stdin=DEVNULL`、repo cwd、clean env で起動します。`<argv>` は静的 inventory 用 sentinel です。
- [argv validator](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:745): `mutation` では tracked test file 引数を許し、`-k`、`-m`、nodeid、`--deselect`、`--ignore*`、`-p`、pytest 環境注入、`--force-dispatch` を拒否します。親と子の双方から同じ関数を呼びます。
- [v1 allowlist](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:166): `git show a34266d2:tools/pegasus/dispatch_compute.py` で歴史的 4 キーを確認し、`IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` を含む集合を凍結しました。
- [`_job_run`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:821): allowlist 外 key を `child_env.update()` 前に拒否し、clean env、stdin 閉鎖、generic の直接 argv、子 rc 伝播を実装しました。
- [request hash 束縛](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:608): canonical request bytes の SHA-256 を job script に埋め、子が実読 bytes と照合し、result と receipt に結びました。親も result hash を検査します。
- [in-flight 互換](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py:795): 旧 v1/v2 の `tests` / `provenance` は、PBS job 内の既存 `dispatch.sh` / probe envelope に限り無 hash 起動を維持します。新規 marker 付き request、新規 2 task、任意 path は無束縛では起動しません。新 script も旧 dispatcher が解釈できる 1 引数 `--job-run` 形を維持しています。
- 編集は指定された [実装ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/tools/pegasus/dispatch_compute.py) と [テストファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py) のみです。add、commit、push はしていません。

## 受理集合の変化

- task 名:
  - 変更前: `tests` / `provenance`
  - 変更後: `tests` / `provenance` / `mutation` / `generic`
- `tests` / `provenance` の正規親経路:
  - 変更前: 現行 allowlist へ環境を射影し、任意の既存 argv を受理
  - 変更後: 不変。`env_mode=inherit`、`argv_policy=passthrough`
- forged child request:
  - 変更前: string mapping なら allowlist 外 key も child へ到達
  - 変更後: allowlist 外 key は child 起動前に拒否
- v1:
  - 変更前: 歴史的正規 4 キーを生成
  - 変更後: 同じ 4 キーを受理。正規受理集合は不変
- `mutation`:
  - 変更前: 未知 task として拒否
  - 変更後: clean request env と限定 argv policy 内で受理。exact full-suite 固定はしていません
- `generic`:
  - 変更前: 未知 task として拒否
  - 変更後: 非空の Python list である string argv のみ受理。tuple、shell string、空 executable、request env は拒否
- stdin:
  - 変更前: dispatcher child が親 stdin を継承
  - 変更後: 全 task で `DEVNULL`
- request:
  - 変更前: queue 待ち中の bytes 差し替えを検出不能
  - 変更後: 新規全 task は job script hash と一致する bytes のみ受理。旧 in-flight envelope は限定互換
- rc:
  - 変更前:会計確認済み child rc を伝播
  - 変更後: 不変。generic の child rc=16 も receipt の `outcome.kind=child` により dispatcher infra と区別

## テスト

追加・変更は [テスト群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:3988) です。

- `test_task_kind_enum_is_closed_and_unknown_task_is_setup_infra_rc`: 無いと task 追加漏れや未知 task の scheduler 到達が静かに通ります。
- `test_new_task_specs_bind_closed_environment_argv_and_probe_contracts`: 無いと child、probe、clean env、policy の誤配線を検出できません。
- `test_job_run_rejects_allowlist_external_environment_before_child`: 無いと forged env が child へ注入されます。
- `test_valid_current_and_v1_environment_overlays_survive_child_enforcement`: 無いと強化が正規 tests、provenance、v1 を過剰拒否しても見逃します。
- `test_mutation_argv_policy_rejects_before_qsub[...]`: 9 個の拒否軸それぞれが無い場合、selector、plugin、環境注入などが qsub されます。
- `test_mutation_argv_policy_fires_independently_in_job_run`: 無いと forged request が親 validator を迂回します。
- `test_mutation_argv_policy_allows_tracked_test_file_before_qsub`: 無いと exact full-suite 固定への退行を検出できません。
- `test_job_run_closes_stdin_uses_repo_cwd_and_cleans_mutation_env`: 無いと TTY 待ち、cwd 依存、pytest/Python 注入が再発します。
- `test_generic_job_run_executes_direct_argv_with_clean_contract`: 無いと generic が sentinel pathや shell 経由へ誤配線されます。
- `test_generic_job_run_refuses_non_compute_before_child`: 無いと login などで任意 argv が起動します。
- `test_generic_rejects_empty_argv_and_shell_string_before_qsub`: 無いと空 command、tuple、shell string が scheduler へ届きます。
- `test_job_run_rejects_request_hash_mismatch_before_child`: 無いと queue 待ち中の request 差し替えが実行されます。期待 hash は固定不一致値で、fixture に現行 hash を差し込んでいません。
- `test_parent_binds_canonical_request_hash_into_script_result_and_receipt`: 無いと job script、result、receipt の結び付け漏れを検出できません。
- `test_parent_rejects_result_request_hash_mismatch_as_infrastructure`: 無いと別 request の result を child 成功として受理します。
- `test_unbound_new_request_is_rejected_but_inflight_v2_tests_survives`: 無いと新 request の無束縛受理、または旧 queue job の一方向破壊を見逃します。
- `test_public_job_run_cli_rejects_unbound_arbitrary_request_path`: 無いと既存 PBS context を偽装した任意 path が公開分岐を通ります。
- `test_generic_child_rc_16_is_receipted_as_child_not_dispatch_infra`: 無いと同じ数値 16 の child 終端と transport infra を混同します。
- `test_job_run_accepts_v1_request_as_tests_task`: 歴史的 deletion key を追加し、v1 互換の過剰拒否を直接固定しました。
- `test_job_run_launches_task_specific_child_script[mutation-mutation_worktree.py]`: 無いと mutation が harness や別 script へ誤配線されます。
- `test_job_run_passes_sidecar_and_auto_off_to_tests_child`: forged manual ID を正例から除き、現行 allowlist 内 marker の正例として維持しました。
- `_job_script` の必須 hash 引数追加に合わせ、既存の job-script、marker、provenance 回帰 node も更新しました。これらが無いと既存の unset、probe、compute marker の検査が新 signature 後に到達不能になります。

制約 meta-test は `flaky_test_holds.py`、`test_skip_classification.py`、`conftest.py`、`check_docs` の test inventory を静的に検索しました。新 nodeid の追加登録を要求する列挙は見つかりませんでした。既存 flaky hold は別 node のみです。

## 未実走

- pytest は一切実走していません。実装済み・未実走です。
- `tools/run_tests.py`、`check_docs.py`、`check_codex_agents.py`、provenance 監査、実 queue、live dogfood も親実行に残しています。
- 実施した静的検査は、両ファイルの AST parse、test 関数名重複検査、親子 validator call site が 2 箇所であることの AST 確認、`git diff --check`、所有ファイル限定の `git status` 確認です。
- Web 検索は使用していません。

## 波及可能性

事前に分かる未 land 依存は次です。

- `docs/pegasus-runbook.md` の task 表が旧 2 行のため、現時点の `check_docs.py` は `mutation` と `generic -> <argv>` の不足で赤になります。これは親 docs land 待ちです。
- `orchestrator/tests/test_check_docs.py` の real dispatcher 期待写像も旧 2 task のため、実装子 C の更新前は赤になります。
- `hooks/guard_bash.py` の generic gateway 対応が未 land のため、特に `python -m pytest` 綴りの generic 呼び出しは hook に拒否され得ます。
- DW-M07 の bundled 経路条件は親 docs 未 land です。

所有外 consumer の静的確認結果です。

- `tools/mutation_harness.py`: request schema v2 と追加 field を許す読み方で、`request_binding` 追加による即時破壊はありません。outer mutation receipt の運用接続は実装子 B・親側の確認対象です。
- `tools/check_docs.py`: `_TaskSpec.child_script` を読むため、generic は `<argv>` sentinel として inventory に現れます。
- `orchestrator/tests/test_check_docs.py`: 上記期待写像更新が必要です。
- `orchestrator/tests/conftest.py`: dispatcher から relay limit 定数だけを importしており、task 拡張の直接影響は見つかりませんでした。
- `tools/dev_wave_wait.py`: dispatcher cleanup 猶予の記述だけで、request/result schema を解釈していません。
- `tools/acceptance_shards.py`: `recover_dispatch_intents` を importするだけで、TASKS や request field を列挙していません。
- `tools/mutation_worktree.py`: clean env、stdin 閉鎖、repo cwd の新しい起動条件を受けます。local site gateなど実装子 B の変更との統合実走が必要です。

## 裏取りできなかったこと

推測で埋めた実装箇所はありません。v1 allowlist は履歴 commit から裏取りしました。

ただし、旧 queue job の実機起動、NQSV が渡す実際の PBS 環境、mutation/generic の live dogfood は実走不能条件のため静的確認だけです。

## 総括

裁定 §1、§4、§5、§8 を所有 2 ファイルだけで実装し、変更は working tree に残しました。task 閉集合、親子 argv gate、全キー env 強制、v1 互換、stdin 閉鎖、generic compute-only 実行、request bytes 束縛、rc 区別をテストで固定しています。pytest と統合検査は未実走で、親による実走と docs・hook・実装子 B/C 変更との統合が必要です。