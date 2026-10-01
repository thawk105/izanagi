## 変更 file と要旨

- [tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/astra-ultra-unit-b/tools/codex_worker_launch.py:1469)：共通検出関数 `_is_delegation_event` と致命 reason `delegation_detected` を追加。online／sealed は既存の共通消費経路から同じ判定を使います。
- [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/astra-ultra-unit-b/orchestrator/tests/test_codex_worker_launch.py:7535)：通常・wait・spawn の回帰、sealed 独立負例、`ultra` 語彙正例を追加。

schema は V5 のまま、終了時拒否を採用しました。docs・所有外ファイル・既存テスト期待値は変更せず、commit していません。

## 受理・拒否の含意 (2 文ずつ、通る正例つき)

**受理：** spawn のない attempt は従来どおり判定されます。通常実行と `wait_agent` の空振りは、他条件が正常なら accepted です。

**拒否：** 変更前は spawn があっても他条件が正常なら accepted でした。変更後は root の `response_item`／`function_call`／`name=spawn_agent` が一件でもあれば `delegation_detected` により accepted になりません。

## 実走したテスト (nodeid・結果)

**pytest 実走なし。** 次の二走行を `tools/run_tests.py -n 2` で試みましたが、両方とも `qstat -Q preflight rc=1`、runner rc=16、`child_started=false` で停止しました。

1. `test_codex_worker_launch.py -k 'delegation or all_repo_policy_reasoning_values or check_receipt_reads_v'`
   - `test_root_delegation_acceptance_and_sealed_recheck[normal/wait_agent/spawn_agent]`
   - `test_sealed_delegation_cannot_retain_accepted_receipt`
   - effort 語彙正例、既存 V1〜V4 読取互換テスト
2. 以下のファイル全体：
   - `test_plain_runner_coverage.py`
   - `test_pytest_collection_config.py`
   - `test_acceptance_schedule_order.py`
   - `test_update_acceptance_duration_ledger.py`
   - `test_growth_test_holds_contract.py`
   - `test_flaky_test_holds_contract.py`
   - `test_codex_worker_launch_budget.py`

静的検査では、変更ファイルと埋込み fake executable の AST 構文確認、`git diff --check` が成功しています。

## 期待赤と回帰

- `[ultra]` は単位 A の語彙追加が未統合のため期待赤です。ただし今回、その赤も未実走です。
- V1〜V5 の field 定義・世代分岐は不変で、既存 reason を削除していません。形式互換は静的に確認しましたが、読取回帰の実走確認は未完了です。
- 過去の accepted receipt でも、sealed 証拠に spawn があれば新判定で拒否されます。これは今回指定された受理集合の縮小です。
- 既存テストの反転・skip・削除、検出関数の stub 化はありません。

## 波及の静的列挙

- **`tools/dev_wave_codex.py`**：launcher 呼出側。引数契約は不変、委任 attempt の拒否結果を受けます。
- **`tools/codex_worker_ledger.py`／同テスト**：manifest＋rollout の読取形式は不変。子 token の会計は追加していません。
- **`tools/t1434_t1222_science_slice.py`**：既存の accepted／requested・recorded 値の照合は維持でき、拒否 receipt は既存条件で除外されます。
- **receipt 関連テスト**：launcher の V1〜V4 互換、V5 再検証、`test_codex_worker_launch_budget.py`、`test_dev_waves_git_state.py` が回帰確認対象です。
- **共有 fixture**：同一テストファイルの `_write_fake_codex` に新モードだけ追加。既存モードと外部 fixture は不変です。
- **制約 meta-test**：ファイル列挙、所要台帳の実 collection 被覆率、growth／flaky hold 契約を特定し、上記走行に含めました。

## 変異事前登録 m4〜m6 の位置と単一理由性

| 変異 | 位置・操作 | 検出するテスト |
|---|---|---|
| m4 | `_is_delegation_event` を常に False | online spawn 負例 |
| m5 | sealed ループの共通消費呼出し付近（4512 行）で spawn event だけを消費対象から外す | sealed 独立負例 |
| m6 | 名前比較を collaboration namespace 全体へ広げる | wait 正例 |

spawn 負例は、metering・validator・終了コード・終了確認が正常で、issue が `delegation_detected` 一件だけであることを要求します。sealed 独立負例は受理済み wait 証拠を spawn に置換して seal を更新するため、hash 不一致や online 拒否に依存しません。**変異実走は未実施です。**

## 総括

**実装済み・未実走**です。変更は所有する 2 ファイルのみです。

終了時拒否は子の実行・書込みを防止せず、子 token も会計しません。委任先 guard の有効性は未確認で、launcher を通らない `next_tasks_consult.sh` には本検出は及びません。