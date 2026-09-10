## 実装方針

`tools/run_tests.py` の実行 bytes と land 時の照合基準を `tested_main` へ移す。さらに launcher は suite 起動前に `tested_main` と `tested_tip` の runner blob 一致を要求する。runner の bootstrap 例外は設けず、欠落、不一致、取得不能はすべて fail-closed とする。

`tools/dev_wave_wait.py` の tip 束縛と launcher 選択規則は変更しない。受領証は `dev-wave-acceptance-receipt/v5` のまま、root field も変更しない。

## `tools/acceptance_launcher.py`

- `tools/acceptance_launcher.py:173-196` `_read_runner_blob`
  - 引数名を `tested_tip` から一般的な `revision` へ変更する。
  - `git cat-file blob` の指定を `f"{revision}:{_RUNNER_PATH}"` にする。
  - 失敗文言も `tested-tip` 固定ではなく、要求された revision の runner を読めない旨に直す。
  - main 欠落時に tip へフォールバックする処理は入れない。

- `tools/acceptance_launcher.py:425-446` `_launch`
  - 現在の `source = blob_reader(..., config.tested_tip)` を次の順序へ変更する。
    1. `tested_main` から実行予定 bytes を取得する。
    2. `tested_tip` から比較用 bytes を別取得する。
    3. 両者の bytes、または同じ bytes から算出した SHA-256 の一致を確認する。
    4. 不一致なら `blob_runner` を一度も呼ばず `LauncherFailure` にする。
    5. 一致時だけ `tested_main` 由来の buffer を `_run_blob` へ渡す。
  - これにより suite 起動前の main/tip 一致が必須になる。tip の変更を黙って無視して main 版を走らせる形にはしない。

- `tools/acceptance_launcher.py:440-446` M3 独立再取得
  - 実行後の独立再取得対象を `config.tested_tip` から `config.tested_main` へ変更する。
  - `runner_executed_sha256` と、再取得した tested-main bytes の SHA-256 を比較する。
  - コメントと例外文言も tested-main 基準へ更新する。
  - 成功時の reader 呼出し順は `tested_main`、`tested_tip`、`tested_main` の3回となる。

- `tools/acceptance_launcher.py:347-398`
  - `runner_executed_sha256` の field 名、receipt の全 root field、canonical JSON 生成は変更しない。
  - `_SCHEMA_VERSION` (`tools/acceptance_launcher.py:22`) も v5 のままにする。

## `tools/dev_wave_land.py`

編集対象は `_verify_acceptance_receipt` 内の runner 検査である。

- `tools/dev_wave_land.py:1065-1067`
  - `tip_runner_entry` の取得直後に、`main_runner_entry = _runner_tree_entry(repository, tested_main)` を追加する。
  - どちらかが `None` なら verdict に関係なく permanent rejection とする。
  - `locked_main` ではなく、receipt が束縛した exact な `tested_main` を使う。

- `tools/dev_wave_land.py:1073-1084`
  - 共通検査へ次を追加する。
    - main/tip 両 entry の object type が `blob`。
    - 両 object ID が正しい SHA 形式。
    - `main_runner_entry[1] == tip_runner_entry[1]`。
  - `runner_executed_sha256` の照合先を `tip_runner_entry[1]` から `main_runner_entry[1]` へ変更する。
  - この共通 block は verdict 分岐後にあるため、`child-green` と `non-attributable-only` の両方へ掛かる。

- `tools/dev_wave_land.py:1085-1113`
  - `main_runner_entry` の初期化 (`:1089`) と、`non-attributable-only` 内だけでの取得 (`:1106-1108`) を削除する。
  - この枝には checker の main/tip 取得と照合だけを残す。

- `tools/dev_wave_land.py:1114-1133`
  - `non-attributable-only` 条件内にある runner の `None`、type、main/tip object ID 比較 (`:1126-1129`) を削除する。
  - checker の main/tip equality はそのまま維持する。

### `retryable_same_request`

既存の分類を保持し、新しい包括的な catch は追加しない。

- `_runner_tree_entry` の Git process failure (`tools/dev_wave_land.py:834-835`) は `retryable_same_request=True`。
- `_acceptance_blob_content_sha256` の `cat-file` failure (`:902-904`) も retryable。
- path 欠落、非 blob、SHA 形式不正、main/tip 不一致、receipt digest 不一致は `_acceptance_rejected()` の既定値を使い、`retryable_same_request=False`。
- quiescent な permanent rejection は外側の既存処理により `release_safe=True` となる。一時的な Git failure は lease を保持する。
- 新しい RC や理由文字列を外部契約へ追加しない。

## `tools/dev_wave_wait.py`

変更しない。

- `tools/dev_wave_wait.py:2521-2559` の launcher source 選択は、tested-main launcher と launcher 導入時だけの `tested-tip-bootstrap` を引き続き扱う。
- `tools/dev_wave_wait.py:3746-3764` は tested main と tested tip の双方を launcher へ渡し続ける。
- `tools/dev_wave_wait.py:2158-2234` の waiter 自身の tip 束縛は D440 のとおり維持する。
- runner に対する bootstrap と、launcher 自身の既存 bootstrap を混同しない。

## provisional 裁定

- **P1: 修正して採用。**
  - tested-main から実行し、suite 起動前に main/tip runner 一致を要求し、runner bootstrap を設けない結論は採用する。
  - ただし「`tools/run_tests.py` は main に常在する」という根拠は事実ではない。履歴実測では同 file の初回追加 commit は `af829260e139c666e34077e6e85fda1cde73778c`、その親 `b03fb9d6ed9d04e4d01875b60dbfde9ca6bb2e6a` に対する `git cat-file -e <parent>:tools/run_tests.py` は rc=128 だった。したがって「main に無く tip で初めて追加される」状態は実在する。
  - その状態では新 launcher は main 読取時点で停止し、suite を起動せず receipt を発行しない。旧 launcher が tip を走らせて receipt を発行しても、新 land は main entry 欠落を permanent rejection にする。
  - 結論を維持する根拠は常在性ではなく、D838 が runner 変更 wave の受入不能を明示的に受容しており、tip bootstrap は同じ汚染経路を再度開くためである。

- **P2: 採用。**
  - v5 と root field 集合を維持する。本 wave の receipt は tested-main 側の旧 launcher が発行するため、field 追加や v6 化は自己締め出しになる。
  - `runner_executed_sha256` の意味だけを tested-main bytes の SHA-256 へ移す。

- **P3: 採用。**
  - `main_runner_entry` の取得と main/tip equality を verdict 分岐の外へ出す。
  - receipt digest の照合先も tested-main entry にする。
  - checker equality は従来どおり `non-attributable-only` のみに残す。

- **P4: 採用。**
  - acceptance 投入直前に、両 revision の entry が blob であり object ID が一致することを実測する。
  - 現時点の実測では `HEAD == main == bb7753fa36daf7af4a47303858af573ecbeda4b0`、双方の runner は `100755 blob b1b1b374dbd68bd3c7b5e8087b04db2fda5e9769` で一致している。ただし実装 commit 後と最終投入直前に再確認する。

## テスト計画

### `orchestrator/tests/test_acceptance_launcher.py`

- `::test_matching_main_and_tip_runner_blobs_execute_tested_main_source`
  - 通る正例。reader 呼出し順が main、tip、mainで、suite が一度だけ起動され、receipt が発行されることを確認する。
  - テスト結果は旧実装で赤、新実装で緑。

- `::test_main_tip_runner_blob_mismatch_is_rejected_before_execution`
  - main/tip に異なる bytes を返し、`blob_runner`、outcome、completion、receipt 書込のいずれにも到達しないことを確認する。
  - 旧実装で赤、新実装で緑。受理シナリオ自体は変更前緑、変更後赤。

- `::test_m3_runner_digest_mismatch_is_rejected` (`orchestrator/tests/test_acceptance_launcher.py:83-112`)
  - reader を main、tip、mainの3回に対応させ、最初の2回は一致、実行後の main 再取得だけ drift させる。
  - 旧実装で赤、新実装で緑。

- `::test_missing_tested_main_runner_is_rejected_before_execution`
  - main 読取だけを失敗させ、tip に runner があっても suite が起動されないことを固定する。
  - 旧実装で赤、新実装で緑。

- `orchestrator/tests/test_acceptance_launcher.py:170-228`
  - exact receipt bytes は field 追加なしで維持する。reader の revision 呼出し記録だけ追加して tested-main semantics を固定する。

### `orchestrator/tests/test_dev_wave_land.py`

- `::test_land_rejects_child_green_runner_blob_divergence`
  - 現在の `test_child_green_accepts_different_main_and_tip_runner_blobs` (`:1519-1535`) を改名し、期待値を `RC_AUDIT`、`acceptance-receipt-rejected`、main 不変へ反転する。
  - 改稿後のテスト結果は旧実装で赤、新実装で緑。現在のテストをそのまま残すと変更前緑、変更後赤。

- `::test_land_accepts_child_green_matching_main_and_tip_runner_blobs`
  - 通る正例。異なる commit だが runner object ID が同一の child-green receipt を使い、main と tip の両 revision が検索されたうえで land できることを spy で確認する。
  - 旧実装で赤、新実装で緑。

- `::test_land_child_green_runner_path_absence_is_permanent_rejection`
  - `:1558-1582` の欠落テストを child-green にも広げる。旧 launcher 相当の tip digest を receipt に入れて、main 欠落そのものだけが拒否理由になるようにする。
  - `release_safe=True`、`retryable_same_request=False` を確認する。
  - 旧実装で赤、新実装で緑。

- `::test_land_child_green_runner_lookup_process_failure_is_retryable`
  - `:1585-1615` と同型だが、tested-main lookup のみ Git rc=128 にし、child-green でも `retryable_same_request=True` になることを確認する。
  - 旧実装で赤、新実装で緑。

- `::test_land_rejects_non_attributable_runner_blob_divergence` (`:1538-1555`)
  - 既存負例として維持する。共通化後も checker 枝とは独立に runner equality が効くことを確認する。

- fixture 修正:
  - `_Repo._acceptance_receipt` の runner digest (`:350-354`) を tested-tip から tested-main へ変更する。
  - `_assert_v5_binding_baseline` (`:673-687`) も main 基準へ変更し、正例では tip blob との equality を別 assertion で明示する。

### 既存のままでは壊れるテスト

- `orchestrator/tests/test_dev_wave_land.py::test_child_green_accepts_different_main_and_tip_runner_blobs` (`:1519-1535`)
  - 現在は変更前緑、変更後赤。前述の拒否テストへ反転する。

- `orchestrator/tests/test_dev_wave_land.py::test_real_waiter_receipt_is_consumed_by_real_land_end_to_end` (`:1800-1881`)
  - `:1813-1825` が runner を tip 側だけで変更しているため、変更前緑、変更後赤。
  - synthetic runner を `:1803-1808` の main commit へ含め、wave 側では waiter と lease helper だけを追加する正例へ直す。

- `orchestrator/tests/test_acceptance_launcher.py::test_m3_runner_digest_mismatch_is_rejected` (`:83-112`)
  - 実装次第で偶然緑を保てるが、現在の2読取 fixture は新しい M3 を検査しないため改稿必須。

- `orchestrator/tests/test_dev_wave_land.py::test_real_child_green_waiter_receipt_passes_real_land_end_to_end` (`:1884-1981`) は main/tip runner が同一であり、新契約の既存通過正例として維持する。

## 本 wave 自身の受入

本 wave は次の条件で受入可能である。

1. tested-main 側の旧 launcher が v5 receipt を発行する。
2. 旧 launcher は tip runner を実行して `runner_executed_sha256` を tip bytes から作る。
3. `main:tools/run_tests.py` と `tip:tools/run_tests.py` が同一 blob なら、その値は新 land が再計算する main bytes の SHA-256 とも一致する。
4. 新 land は tested-main launcher の blob と実行 digestを検査するが、main/tip の launcher equality は要求しない。このため tip 側で launcher を変更した本 waveを締め出さない。
5. receipt schema と root field が v5 のままである。
6. non-attributable verdict を使う場合は、runner に加えて checker の main/tip equality も必要である。

したがって `tools/run_tests.py` を編集しない本 wave は通せる。現時点では main/tip runner blob はともに `b1b1b374dbd68bd3c7b5e8087b04db2fda5e9769` である。main の進行や merge 後の tip 生成で条件が変わり得るため、P4 の再実測を最終投入直前に行う。なお本 wave の受入は旧 launcher を使うため、新 launcher 実装そのものの動作証明は焦点テストが担う。

## docs と consumer

- `docs/pegasus-runbook.md:879-900`
  - `:881` の runner 読み元を tested-tip から tested-main へ更新し、suite 前の main/tip equality を追記する。
  - `:895-900` は「runner 変更 wave は全 verdict で受入不能」「checker 変更 waveは non-attributable-only だけ不能、child-green は可能」と分離する。
  - launcher の `tested-tip-bootstrap` (`:889-891`) は変更しない。

- `docs/decisions.md:21650-21694` の D524 は当時の裁定記録なので書き換えず、`docs/decisions.md:31681-31697` の D838 が supersede する形を維持する。

母集合と除外: tracked text の code=`*.py` から `orchestrator/tests/**` を除いたもの、test=`orchestrator/tests/**`、docs=`*.md` として `git grep -F` と path 検索を併用し、code 12 file・test 20 file・docs 7 fileの計39 fileを母集合とした。凍結・生成証拠の `output/**` 911 file、`docs/archive/**` 107 file、`docs/spool/**` 0 file、および分類外 config の `pytest.ini` 1 fileを除外した。

- `runner_executed_sha256`: code 3 file/15 hit (`tools/acceptance_launcher.py`, `tools/dev_wave_land.py`, `tools/dev_wave_wait.py`)、test 4 file/13 hit (`test_acceptance_launcher.py`, `test_dev_wave_land.py`, `test_dev_wave_wait.py`, `test_resume_gate_acceptance_boundary.py`)、docs 2 file/5 hit (`docs/decisions.md`, `docs/pegasus-runbook.md`)。
- `resolved_runner_path`: code 3 file/4 hit（上記3 tools）、test 3 file/9 hit (`test_acceptance_launcher.py`, `test_dev_wave_land.py`, `test_dev_wave_wait.py`)、docs 0。
- `tools/run_tests.py`: code 12 file/22 hit (`hooks/guard_bash.py`, `tools/acceptance_launcher.py`, `tools/check_ai_provenance.py`, `tools/dev_wave_land.py`, `tools/dev_wave_wait.py`, `tools/dev_waves/checker.py`, `tools/dev_waves/cli.py`, `tools/dev_waves/git_state.py`, `tools/mutation_fanout_contract.py`, `tools/mutation_harness.py`, `tools/pegasus/run_acceptance_nproc_study.py`, `tools/run_tests.py`)。
- 同 path literal の test は20 file/95 hit: `orchestrator/tests/README.md`, `conftest.py`, `test_acceptance_launcher.py`, `test_acceptance_nproc_study.py`, `test_acceptance_schedule_order.py`, `test_check_acceptance_reds.py`, `test_check_docs.py`, `test_dev_wave_land.py`, `test_dev_wave_wait.py`, `test_dev_waves_checker.py`, `test_fold_gate_nodes_contract.py`, `test_hooks.py`, `test_mutation_fanout.py`, `test_mutation_fanout_contract.py`, `test_mutation_worktree.py`, `test_pytest_collection_config.py`, `test_resume_gate_acceptance_boundary.py`, `test_run_tests_nproc.py`, `test_run_tests_preflight.py`, `test_run_tests_testops_observation.py`。
- 同 path literal の docs は7 file/105 hit: `AGENTS.md`, `docs/decisions.md`, `docs/failures.md`, `docs/pegasus-runbook.md`, `docs/ruleops.md`, `docs/worklog.md`, `hooks/README.md`。契約更新が必要なのは runbook で、他は一般的な実行手順または履歴記録である。

## 検証順

1. launcher の4 nodeidを `tools/run_tests.py` 経由で実行する。
2. land の runner 関連 nodeidと2本の real waiter E2Eを実行する。
3. `test_dev_wave_wait.py` と `test_resume_gate_acceptance_boundary.py` の既存 receipt consumerを回帰確認する。
4. `python3 tools/check_codex_agents.py` と `python3 tools/check_docs.py` を実行する。
5. commit 後に `python3 tools/check_ai_provenance.py` を実行する。
6. acceptance 投入直前に main/tip の runner mode、type、object IDを再取得し、一致を記録する。

## 総括

- launcher は tested-main runner を実行し、suite 前に main/tip の一致を要求する。
- 実行後の M3 再取得も tested-main を対象にする。
- land は runner の main取得、blob equality、receipt digest照合を全 verdictへ広げる。
- runner bootstrap は設けず、main 欠落は suite 未起動または permanent land rejectionとなる。
- waiter の tip 束縛、launcher bootstrap、receipt v5 schemaとroot fieldは変更しない。
- 本 waveは runnerを編集しないため、main/tip blob一致を再確認すれば旧 launcher receiptで通せる。
- 主要な既存破壊は child-green divergence正例と、tipだけrunnerを変えるreal E2Eの2本である。
- 新しい負例に加え、main/tip一致時に実際に通る正例を追加する。