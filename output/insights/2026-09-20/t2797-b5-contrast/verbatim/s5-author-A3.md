## 変更の要約

**指定4ファイルの実装を完了し、未 commit の差分として残しました。**

- job body：B-5 環境検査、K2 の条件、prebuild 後の専用分岐を追加。
- launcher：262行で新設。submit-tree 検査、明示的な `-v`、4 job 固定、53≤60 の予算検査、dry-run／submit を実装。
- job 契約テスト：B-5 pin、実 shell 検査、変異検査を追加。
- launcher テスト：268行で新設。固定 HEAD の fake Git repository、argv、予算、投入時の副作用を検査。

変更前は `IZANAGI_S4_B5_MODE=series` が無視され、既定 fixture 経路へ進む挙動でした。

## 既定挙動不変の確認

- `candidate_rc=0` 以降の既存呼出し本文は、HEAD との **bytes 完全一致**を確認。
- fixture／proposal／stock-control の既存 argv・呼出し回数・rc テストは通過。
- 旧 module の呼出し3箇所を維持。B-5 は別 module の1箇所だけです。
- PBS の `03:00:00`、EXIT trap、compute-result schema、Python 解決、prebuild は変更していません。
- 既存期待値の変更は、指定された K2 proposal 必須条件の pin と対応変異のみです。

## launcher の使い方

```bash
python3 -B tools/pegasus/b5_contrast_launch.py \
  --repo-root /srv/submit-tree \
  --expected-head <full-HEAD> \
  --thirdparty-source-root /srv/thirdparty \
  --ledger-root /srv/ledgers \
  --evidence-root /srv/evidence \
  --knowledge-manifest /srv/knowledge.json \
  --knowledge-classification known_result_conditioned_derivative \
  --knowledge-de-novo-claim false \
  --dry-run
```

dry-run は各 job の `arm`・`environment`・最終 `argv` を JSON で出力します。random の `argv` 部分の例です（説明用のパス／HEAD）。

```json
["qsub","-v","IZANAGI_S4_REPO_ROOT=/srv/submit-tree,IZANAGI_S4_EXPECTED_HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,IZANAGI_S4_EVIDENCE_ROOT=/srv/evidence/random,IZANAGI_S4_THIRDPARTY_SOURCE_ROOT=/srv/thirdparty,IZANAGI_S4_B5_MODE=series,IZANAGI_S4_B5_ARM=random,IZANAGI_S4_B5_WORKLOAD=write-heavy,IZANAGI_S4_B5_SERIES=1,IZANAGI_S4_B5_BLOCK=1,IZANAGI_S4_B5_LEDGER_ROOT=/srv/ledgers/random","-l","elapstim_req=08:00:00","-o","/srv/evidence/random/job.stdout","-e","/srv/evidence/random/job.stderr","tools/pegasus/p3_s4_loop_pegasus.sh"]
```

`-v` の key はすべて `IZANAGI_S4_` 接頭辞で、共通10個です。

`REPO_ROOT`、`EXPECTED_HEAD`、`EVIDENCE_ROOT`、`THIRDPARTY_SOURCE_ROOT`、`B5_MODE`、`B5_ARM`、`B5_WORKLOAD`、`B5_SERIES`、`B5_BLOCK`、`B5_LEDGER_ROOT`

LLM のみ次の4個を追加します。

`KNOWLEDGE_MANIFEST`、`CODER_ROLE`、`KNOWLEDGE_CLASSIFICATION`、`KNOWLEDGE_DE_NOVO_CLAIM`

`--submit` は attempt directory を作ってから argv list で qsub を呼びます。投入失敗後の自動再投入はありません。workload は背景指示に合わせて write-heavy 固定です。

## 新 test 一覧

主要な独立根拠と変異対応です。全テスト名は ASCII です。

| テスト | 根拠・変異 |
|---|---|
| `test_b5_actual_shell_one_driver_and_trap_rc` | 4 arm × rc 0／7、完全 argv、1起動、trap 転記。M13 |
| `test_b5_fallthrough_mutant_is_killed_by_shell_call_count` | exit 除去で実際に2起動となり、1起動の期待値が拒否 |
| `test_b5_set_empty_mode_alone_is_refused_before_paths` | 空値単独でも repository 検査前に拒否。M14 |
| `test_b5_empty_mode_mutant_is_killed_by_early_rc2` | 空値検査を弱めた変異を上記テストが拒否 |
| `test_b5_fragment_mutants_have_one_static_failure` | B-5 pin の各変異で static failure がちょうど1個 |
| `test_b5_invalid_env_precedes_repository_resolution` | 空値・値域違反を実 shell で早期拒否 |
| `test_b5_partial_environment_refused_before_paths` | 必須 env の各欠落 |
| `test_b5_legacy_modes_are_exclusive_before_paths` | proposal／fixture／stock-control 併用 |
| `test_b5_llm_requires_all_k2_before_paths` | K2 各値の欠落・空値 |
| `test_b5_non_llm_excludes_k2_before_paths` | random／sweep／stock の K2 禁止 |
| `test_b5_stock_off_preserves_single_b5_call` | stock-control 未設定／0 |
| `test_b5_duplicate_driver_and_late_branch_are_rejected` | B-5 呼出し数・順序 |
| `test_b5_ledger_inside_repository_refused_before_trap` | repo／common repo／symlink 経由の拒否 |
| `test_four_qsub_argv_and_explicit_environment_are_exact` | 4 job、walltime、全 env の固定期待値 |
| `test_pilot_cap_is_literal_60_and_four_jobs_53_sessions` | 独立定数60・4 job・53 session。M18 |
| `test_m18_mutants_fail_independent_pilot_cap_test` | cap=61／5 job の両変異を拒否 |
| `test_changed_budget_cannot_construct_pilot` | B=11 などの予算変更を拒否 |
| `test_dry_run_prints_final_argv_without_runner_or_mkdir` | subprocess／mkdir 不実行 |
| `test_submit_only_mkdir_then_argv_runner` | 空の attempt directory、cwd、argv、失敗 rc |

加えて `test_validate_submit_tree_*` 6本、座標拡張・不正 path・repository 内出力・既存 attempt・main の dry-run を検査しています。

## 実走結果

`::*` は当該ファイルの全収集 nodeid です。

| 対象 | 結果 |
|---|---|
| `test_p3_s4_loop_job_contract.py::*`、指定 plain harness | **184 passed** |
| `test_b5_contrast_launch.py::*`、指定 plain harness | **36 passed** |
| `test_pegasus_tools.py -k 'p3_s4_loop or job_body'` | 0件選択、72 deselected、rc=5 |
| `test_hooks.py -k p3_s4_loop` | 0件選択、484 deselected、rc=5 |
| `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` | passed |
| `test_pegasus_tools.py::test_certify_glog_stage_is_pinned_fail_closed_and_precedes_ccbench` | passed |
| `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` | passed |
| `test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized` | **failed：新 launcher の登録待ち** |
| `test_plain_runner_coverage.py::*` | 3 passed |
| `git diff --check` | 通過 |

M13・M14・M18 の変異ケースは上記単位テスト内で実走して kill 済みです。

`tools/run_tests.py` は qstat preflight 失敗で rc=16、子テスト未起動でした。その後、今回指定された直接実行コマンドで検証しました。

## 波及

親担当の README §7 には、次を追記してください。

- B-5 env 表：mode、arm、workload、series、block、repository 外 ledger。
- 未設定だけ off、空値／部分設定／旧 mode 併用の拒否。
- LLM の K2 4 env 必須、他 arm では禁止。
- 上記 launcher 使用例と、明示 `-v`・8h／3h の qsub 例。
- dry-run は directory を作らず、submit は attempt に mkdir 以外の書込みをしないこと。

README の既存テストは job body を含む bash fence 数を固定しています。例の追加時は、その期待値との同期が必要です。

launcher 登録候補は **`local-ok`** です。先例は `submit_b10_backoff_grid.sh`／`submit_floor_pair.sh`。計算処理は既存 compute-only job body に委譲するためです。証拠表記候補は `static login-side submitter classification` で、資源実測済みとはしません。

親による `admission_registry.json` 登録に加え、`test_hooks.py` の class／entry／local evidence の固定表更新が必要です。所有外ファイルは変更していません。

## 未了・懸念

- launcher の registry 登録は親担当のため未実施。inventory テストの失敗理由はこれだけです。
- 実 qsub、実機 build／bench、LLM handshake の統合実走は未実施。
- dry-run の tree 検証では読み取り専用の Git subprocess を使います。qsub と mkdir は実行しません。

## 総括

**A3 の実装と単位内変異検証は完了。単位テスト220件が通過しました。** 差分は指定4ファイルのみで、commit は作成していません。親側の登録・関連固定表更新と統合検証を残しています。