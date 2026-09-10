実装済みですが、Pegasus の dispatch 障害により pytest は未実走です。commit・docs 編集・所有外ファイル変更はしていません。

## 総括

1. 実装ファイルと行数

- [env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py): 398 行、新規
- [00000001.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activations/00000001.json): 1 行、新規
- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py): 668 行、net +210 行
- [issue_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/issue_env_contract_activation.py): 141 行、新規
- [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py): 541 行、新規
- [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py): 1,254 行、net +14 行

実装内容:

- pegasus g2 を `dataclasses.replace` で登録し、contract hash が指定値 `1346c20b…ad1c` と一致しなければ import を拒否。
- bootstrap fuse を除去し、世代構造検査は維持。
- canonical JSON、exact schema/type、hash chain、registry/env exact 整合、symlink/non-regular 拒否を実装。
- head serial/state hash を Python source に固定し、rollback・suffix・余分な record を拒否。
- 世代 delta 述語は実装せず、no-op・skip・downgrade の受理テストを追加。
- lazy `Mapping`、current 行だけの較正検証、歴史行の解決時検証、PID/lock/at-fork cache を実装。
- issuer は argparse 後に authority をロードし、`O_CREAT|O_EXCL|O_NOFOLLOW` で create-only 発行。

受理集合は次のように変わります。

- 変更前: 複数世代登録を一律拒否。current は登録列末尾。登録済み hash は全て historical 解決可。
- 変更後: g2 登録を受理するが、初期 record により current は両 env とも g1のまま。historical 解決は ever-active の g1 のみ。未知 hash と登録済み never-active g2 は異なる理由で拒否。

2. 走らせた検査と結果

- g2 calibration bytes SHA-256: 指定値と一致。
- g2 contract SHA-256: `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c`
- 初期 authority: pegasus g1 を選択。
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: OK
- 担当 Python 5 ファイルの `ast.parse`: OK
- 初期 record: 476 bytes、末尾 LF 1 個

pytest 実走コマンド:

```text
python3 tools/run_tests.py -n 1 \
  orchestrator/tests/test_env_contract_activation.py \
  orchestrator/tests/test_env_contract.py \
  orchestrator/tests/test_plain_runner_coverage.py
```

結果は runner rc=16、`qstat -Q preflight rc=1`。収集・実行された nodeid は 0 件です。したがって緑は主張しません。

3. 未実走・未達

- 新規 activation test 19 node、既存 `test_env_contract.py`、plain-runner meta-testは未実走。
- 単位3の activation receipt と `execution_guard` 結線は未実装。
- 単位4の qualification/silo/T419 identity pin は未実装。
- docs、commit、全走、mutation は親担当として未実施。

4. 期待される赤

次単位テストを先に導入した場合の事前指定:

- `test_campaign.py::test_m0_activation_receipt_refusal_precedes_any_sink_write`
- `test_campaign.py::test_activation_receipt_check_precedes_registry_runtime_site_and_selector_checks`
- T126 の required code identity 閉包テスト
- `test_silo_ladder_rung1_driver.py::test_runtime_binding_covers_all_execution_semantics_modules`
- T419 の activation leaf/record directory dirty-scope テスト

また、所有外に古い bootstrap 前提が残っています。これは次単位由来の期待赤ではなく、親が回帰として扱うべき波及候補です。

- `test_s8b_ratified_verify.py::test_public_reverify_accepts_recorded_g1_under_g2_current_while_live_refuses`
- `test_s8b_floor_campaign.py` の `_patch_current_contract_to_synthetic_successor` を使う4テスト

5. 次単位への申し送り

- receipt は `current_activation_state()` の検証済み state を束縛し、guard で `lookup()` を呼び直さず receipt 指定 state から解決する。
- at-fork callback へ receipt/seal のリセットを追加する。
- identity pin は activation leaf、calibration verifier、execution guard を追加する。JSON recordを世代ごとの固定 path 集合へ加えず、`env_contract.py` の head pinで束縛する。
- 所有外 caller・consumer は `execution_guard`、`pipeline/loop`、floor/oracle/selector、T126、silo、PBS preflight、historical freeze/oracle report。
- module-level `lookup()` を持つ `test_campaign.py` と `test_screening_driver.py` は collection 時に authority loadするため、import-I/O 検査は引き続き fresh subprocess を使う。